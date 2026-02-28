"""
app.py — Lecture Summarizer
Streamlit UI for uploading lecture videos and generating summary content.
"""

import os
import json
import shutil
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lecture Summarizer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f17; }
    .stProgress .st-bo { background-color: #6366f1; }
    .stage-card {
        background: #1a1a2e;
        border: 1px solid #2d2d4e;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    .stage-done { border-left: 4px solid #22c55e; }
    .stage-active { border-left: 4px solid #6366f1; animation: pulse 1.5s infinite; }
    .stage-pending { border-left: 4px solid #374151; opacity: 0.6; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.7} }
    .metric-box {
        background: #1e1e30;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .download-btn { width: 100%; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=80)
    st.title("⚙️ Settings")

    st.subheader("OpenAI")
    api_key = st.text_input(
        "API Key",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        help="Your OpenAI API key for GPT-4o and Whisper API"
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    st.subheader("Transcription")
    whisper_mode = st.radio(
        "Whisper Mode",
        options=["local", "api"],
        index=0,
        help="Local: free but slower | API: fast but costs ~$0.006/min"
    )
    os.environ["WHISPER_MODE"] = whisper_mode

    if whisper_mode == "local":
        whisper_model = st.select_slider(
            "Model Size",
            options=["tiny", "base", "small", "medium", "large"],
            value="medium",
            help="Larger = more accurate but slower"
        )
        os.environ["WHISPER_MODEL"] = whisper_model

    st.subheader("Slide Detection")
    threshold = st.slider(
        "Change Sensitivity",
        min_value=0.60,
        max_value=0.95,
        value=0.85,
        step=0.05,
        help="Lower = more sensitive (detects more changes)"
    )

    st.subheader("OCR Method")
    use_gpt4v = st.toggle(
        "Use GPT-4o Vision for OCR",
        value=True,
        help="Much better for code. Costs a few API calls."
    )

    st.subheader("Output")
    gen_slideshow = st.toggle("Generate Slideshow Video", value=True)
    gen_highlight = st.toggle("Generate Highlight Reel", value=True)

    max_highlight = st.slider(
        "Max Highlight Duration (sec)",
        min_value=60,
        max_value=600,
        value=300,
        step=30
    )

    st.markdown("---")
    st.caption("💡 Tip: For CPU-only machines, use Whisper API for faster transcription.")


# ── Main UI ───────────────────────────────────────────────────────────────────
st.title("🎓 Lecture Summarizer")
st.markdown("*Upload a programming lecture video → get a summary video + highlight reel*")

# File uploader
uploaded_file = st.file_uploader(
    "Drop your lecture video here",
    type=["mp4", "mkv", "avi", "mov", "webm"],
    help="Supports MP4, MKV, AVI, MOV, WebM"
)

if uploaded_file:
    # Show video info
    col1, col2, col3 = st.columns(3)
    file_size_mb = uploaded_file.size / (1024 * 1024)
    col1.metric("File", uploaded_file.name)
    col2.metric("Size", f"{file_size_mb:.1f} MB")
    col3.metric("Type", uploaded_file.type)

    # Start button
    if st.button("🚀 Start Processing", type="primary", use_container_width=True):

        if not os.getenv("OPENAI_API_KEY"):
            st.error("⚠️ Please enter your OpenAI API key in the sidebar!")
            st.stop()

        # ── Setup ─────────────────────────────────────────────────────────────
        work_dir = Path(tempfile.mkdtemp(prefix="lecture_summarizer_"))
        temp_dir = work_dir / "temp"
        output_dir = work_dir / "outputs"
        temp_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)

        # Save uploaded file
        video_path = work_dir / uploaded_file.name
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())

        # Override settings from sidebar
        from pipeline import visual as visual_mod
        visual_mod.SLIDE_CHANGE_THRESHOLD = threshold

        from pipeline import fusion as fusion_mod
        fusion_mod.MAX_HIGHLIGHT_DURATION = max_highlight

        # ── Progress UI ────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 Processing Progress")

        stages = [
            ("🎵", "Audio Extraction & Transcription"),
            ("🖼️", "Slide Detection & OCR"),
            ("🔗", "Content Fusion"),
            ("🤖", "AI Summarization"),
            ("🎬", "Video Generation"),
        ]

        stage_containers = []
        for icon, name in stages:
            c = st.empty()
            stage_containers.append((c, icon, name))
            c.markdown(
                f'<div class="stage-card stage-pending">{icon} {name}</div>',
                unsafe_allow_html=True
            )

        overall_progress = st.progress(0, text="Starting...")
        status_text = st.empty()
        log_expander = st.expander("📋 Processing Log", expanded=False)
        log_area = log_expander.empty()
        logs = []

        def log(msg):
            logs.append(msg)
            log_area.text("\n".join(logs[-20:]))

        def set_stage(idx, state="active"):
            icon = stages[idx][0]
            name = stages[idx][1]
            stage_containers[idx][0].markdown(
                f'<div class="stage-card stage-{state}">{icon} {name}</div>',
                unsafe_allow_html=True
            )

        def update_progress(pct, msg=""):
            overall_progress.progress(min(pct, 1.0), text=msg)
            if msg:
                status_text.markdown(f"**{msg}**")

        try:
            # ── STAGE 1: Audio ─────────────────────────────────────────────────
            set_stage(0, "active")
            update_progress(0.02, "Extracting audio...")
            log("Stage 1: Audio extraction started")

            from pipeline.audio import extract_audio, transcribe, get_transcript_segments

            audio_path = extract_audio(str(video_path), str(temp_dir))
            log(f"Audio extracted: {audio_path}")
            update_progress(0.10, "Transcribing with Whisper...")

            transcription = transcribe(audio_path)
            transcript_segments = get_transcript_segments(transcription)
            log(f"Transcription complete: {len(transcript_segments)} segments")
            set_stage(0, "done")
            update_progress(0.20, f"✅ Transcribed {len(transcript_segments)} segments")

            # ── STAGE 2: Visual ────────────────────────────────────────────────
            set_stage(1, "active")
            update_progress(0.22, "Detecting slide changes...")
            log("Stage 2: Slide detection started")

            from pipeline.visual import detect_slide_changes, extract_slide_content

            def visual_progress(p):
                update_progress(0.22 + p * 0.12, f"Analyzing frames... {int(p*100)}%")

            slide_changes = detect_slide_changes(
                str(video_path), str(temp_dir), visual_progress
            )
            log(f"Detected {len(slide_changes)} slides")
            update_progress(0.35, f"Running OCR on {len(slide_changes)} slides...")

            def ocr_progress(p):
                update_progress(0.35 + p * 0.10, f"OCR processing... {int(p*100)}%")

            slide_changes = extract_slide_content(
                slide_changes, use_gpt4v=use_gpt4v, progress_callback=ocr_progress
            )
            log("OCR complete")
            set_stage(1, "done")
            update_progress(0.45, f"✅ Processed {len(slide_changes)} slides")

            # ── STAGE 3: Fusion ────────────────────────────────────────────────
            set_stage(2, "active")
            update_progress(0.46, "Aligning transcript with slides...")
            log("Stage 3: Fusion started")

            from pipeline.fusion import (
                align_transcript_to_slides, get_video_duration,
                select_highlight_slides
            )

            video_duration = get_video_duration(str(video_path))
            fused_slides = align_transcript_to_slides(
                transcript_segments, slide_changes, video_duration
            )
            highlight_slides = select_highlight_slides(fused_slides, max_highlight)
            log(f"Fusion complete: {len(fused_slides)} fused, {len(highlight_slides)} highlights")
            set_stage(2, "done")
            update_progress(0.50, f"✅ Aligned {len(fused_slides)} slide sections")

            # ── STAGE 4: Summarization ─────────────────────────────────────────
            set_stage(3, "active")
            update_progress(0.52, "Generating AI summaries...")
            log("Stage 4: Summarization started")

            from pipeline.summarizer import (
                summarize_all_slides, generate_overall_summary,
                build_full_summary_report
            )

            def summary_progress(p):
                update_progress(0.52 + p * 0.18, f"Summarizing slides... {int(p*100)}%")

            fused_slides = summarize_all_slides(fused_slides, summary_progress)
            overall_summary = generate_overall_summary(fused_slides)
            summary_report = build_full_summary_report(fused_slides, overall_summary)

            # Save JSON report
            report_path = output_dir / "summary_report.json"
            with open(report_path, "w") as f:
                json.dump(summary_report, f, indent=2)

            log(f"Summary complete: '{overall_summary.get('lecture_title', 'N/A')}'")
            set_stage(3, "done")
            update_progress(0.70, f"✅ Summarized: {overall_summary.get('lecture_title', 'Lecture')}")

            # ── STAGE 5: Video Generation ──────────────────────────────────────
            set_stage(4, "active")
            slideshow_path = None
            highlight_path = None
            video_step_size = 0.30 / max(int(gen_slideshow) + int(gen_highlight), 1)
            current_progress = 0.70

            if gen_slideshow:
                update_progress(current_progress, "Generating slideshow video...")
                log("Generating slideshow video (Output B)...")

                from pipeline.slideshow_video import create_slideshow_video

                def slideshow_progress(p):
                    update_progress(
                        current_progress + p * video_step_size,
                        f"Creating slideshow... {int(p*100)}%"
                    )

                slideshow_path = output_dir / "summary_slideshow.mp4"
                create_slideshow_video(
                    fused_slides, overall_summary,
                    str(slideshow_path), str(temp_dir),
                    slideshow_progress
                )
                current_progress += video_step_size
                log(f"Slideshow saved: {slideshow_path.name}")

            if gen_highlight:
                update_progress(current_progress, "Generating highlight reel...")
                log("Generating highlight reel (Output A)...")

                from pipeline.highlight_video import create_highlight_reel

                def highlight_progress(p):
                    update_progress(
                        current_progress + p * video_step_size,
                        f"Cutting highlights... {int(p*100)}%"
                    )

                highlight_path = output_dir / "highlight_reel.mp4"
                create_highlight_reel(
                    str(video_path), highlight_slides, overall_summary,
                    str(highlight_path), str(temp_dir),
                    highlight_progress
                )
                log(f"Highlight reel saved: {highlight_path.name}")

            set_stage(4, "done")
            update_progress(1.0, "✅ All done!")

            # ── Results ────────────────────────────────────────────────────────
            st.markdown("---")
            st.success(f"🎉 Processing complete! **{overall_summary.get('lecture_title', 'Lecture')}**")

            # Summary card
            with st.expander("📖 Lecture Summary", expanded=True):
                st.markdown(f"### {overall_summary.get('lecture_title', '')}")
                st.markdown(f"**Main Topic:** {overall_summary.get('main_topic', '')}")

                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown("**🏆 Key Takeaways:**")
                    for t in overall_summary.get("key_takeaways", []):
                        st.markdown(f"- {t}")
                with col_r:
                    st.markdown("**🎯 Learning Outcomes:**")
                    for o in overall_summary.get("learning_outcomes", []):
                        st.markdown(f"- {o}")

            # Stats
            st.markdown("### 📊 Stats")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Slides Detected", len(slide_changes))
            c2.metric("Transcript Segments", len(transcript_segments))
            c3.metric("Highlights Selected", len(highlight_slides))
            duration_min = video_duration / 60
            c4.metric("Video Duration", f"{duration_min:.1f} min")

            # Downloads
            st.markdown("### 📥 Downloads")
            dl_col1, dl_col2, dl_col3 = st.columns(3)

            if slideshow_path and slideshow_path.exists():
                with open(slideshow_path, "rb") as f:
                    dl_col1.download_button(
                        "🎬 Download Slideshow Video",
                        f, "summary_slideshow.mp4", "video/mp4",
                        use_container_width=True
                    )

            if highlight_path and highlight_path.exists():
                with open(highlight_path, "rb") as f:
                    dl_col2.download_button(
                        "✂️ Download Highlight Reel",
                        f, "highlight_reel.mp4", "video/mp4",
                        use_container_width=True
                    )

            with open(report_path, "rb") as f:
                dl_col3.download_button(
                    "📄 Download Summary JSON",
                    f, "summary_report.json", "application/json",
                    use_container_width=True
                )

            # Per-slide details
            with st.expander("🔍 Per-Slide Summaries", expanded=False):
                for slide in summary_report["slides"]:
                    s = slide.get("summary", {})
                    with st.container():
                        st.markdown(f"**Slide {slide['slide_number']}: {s.get('title', '')}**")
                        st.markdown(s.get("summary", ""))
                        concepts = s.get("key_concepts", [])
                        if concepts:
                            st.markdown("*Concepts:* " + " · ".join(f"`{c}`" for c in concepts))
                        code = s.get("code_example", "")
                        if code:
                            st.code(code)
                        st.divider()

        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            log(f"ERROR: {e}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

        finally:
            # Cleanup temp files (keep outputs)
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

else:
    # Landing state
    st.markdown("""
    ### How it works:

    1. **📤 Upload** your lecture video (MP4, MKV, MOV...)
    2. **🎵 Audio** is extracted and transcribed with Whisper
    3. **🖼️ Slides** are detected by analyzing frame changes
    4. **🔗 Content** is fused — transcript aligned with each slide
    5. **🤖 GPT-4o** generates structured summaries per slide
    6. **🎬 Two videos** are created:
       - **Slideshow Video** — clean slides with AI voiceover
       - **Highlight Reel** — best moments from original video

    ---
    👈 *Configure settings in the sidebar, then upload your video above.*
    """)

    col1, col2, col3 = st.columns(3)
    col1.info("✅ Best for **programming lectures** with clear slides")
    col2.info("⚡ **30-60 min** videos work best")
    col3.info("🔑 Requires **OpenAI API key** for GPT-4o + Whisper")
