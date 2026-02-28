"""
pipeline/slideshow_video.py
Output B: Generates a summary slideshow video with:
- Clean summary slides (Pillow)
- Neural TTS voiceover (edge-tts)
- Assembled into MP4 (moviepy)
"""

import os
import asyncio
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

# Video dimensions (16:9 1080p)
WIDTH, HEIGHT = 1920, 1080

# Color palette
BG_COLOR = (18, 18, 24)           # Dark background
ACCENT_COLOR = (99, 102, 241)     # Indigo accent
TITLE_COLOR = (255, 255, 255)     # White
TEXT_COLOR = (226, 232, 240)      # Light gray
CODE_BG = (30, 30, 46)            # Darker code block
CODE_COLOR = (139, 233, 253)      # Cyan for code
BULLET_COLOR = (167, 243, 208)    # Green for bullets
SLIDE_NUM_COLOR = (100, 116, 139) # Muted gray

# TTS Voice
TTS_VOICE = "en-US-AriaNeural"   # High quality Microsoft neural voice


def get_font(size: int, bold: bool = False):
    """Load a font, falling back to default if custom fonts unavailable."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()


def get_mono_font(size: int):
    """Load monospace font for code blocks."""
    mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in mono_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()


def create_intro_slide(overall_summary: dict, output_path: str) -> str:
    """Create the intro title slide."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Accent bar at top
    draw.rectangle([0, 0, WIDTH, 8], fill=ACCENT_COLOR)

    # Title
    title = overall_summary.get("lecture_title", "Lecture Summary")
    font_title = get_font(72, bold=True)
    wrapped = textwrap.wrap(title, width=40)

    y = HEIGHT // 2 - 120
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        w = bbox[2] - bbox[0]
        draw.text(((WIDTH - w) // 2, y), line, font=font_title, fill=TITLE_COLOR)
        y += 90

    # Main topic
    topic = overall_summary.get("main_topic", "")
    if topic:
        font_sub = get_font(36)
        wrapped_topic = textwrap.wrap(topic, width=70)
        y += 20
        for line in wrapped_topic:
            bbox = draw.textbbox((0, 0), line, font=font_sub)
            w = bbox[2] - bbox[0]
            draw.text(((WIDTH - w) // 2, y), line, font=font_sub, fill=TEXT_COLOR)
            y += 50

    # Accent bar at bottom
    draw.rectangle([0, HEIGHT - 8, WIDTH, HEIGHT], fill=ACCENT_COLOR)

    # "Summary Video" label
    label_font = get_font(28)
    draw.text((40, HEIGHT - 55), "AI-Generated Summary", font=label_font, fill=SLIDE_NUM_COLOR)

    img.save(output_path, "PNG")
    return output_path


def create_summary_slide(slide_data: dict, slide_index: int, total_slides: int, output_path: str) -> str:
    """Create a summary slide for a single lecture slide."""
    summary = slide_data.get("summary", {})

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([0, 0, WIDTH, 6], fill=ACCENT_COLOR)

    # Slide counter (top right)
    counter_font = get_font(28)
    counter_text = f"{slide_index} / {total_slides}"
    draw.text((WIDTH - 160, 20), counter_text, font=counter_font, fill=SLIDE_NUM_COLOR)

    # Title
    title = summary.get("title", f"Slide {slide_data.get('slide_number', slide_index)}")
    font_title = get_font(54, bold=True)
    wrapped_title = textwrap.wrap(title, width=50)

    y = 50
    for line in wrapped_title:
        draw.text((60, y), line, font=font_title, fill=TITLE_COLOR)
        y += 70

    # Divider line
    draw.line([(60, y + 10), (WIDTH - 60, y + 10)], fill=ACCENT_COLOR, width=2)
    y += 35

    # Summary text
    summary_text = summary.get("summary", "")
    if summary_text:
        font_body = get_font(34)
        wrapped = textwrap.wrap(summary_text, width=72)
        for line in wrapped[:4]:  # Max 4 lines
            draw.text((60, y), line, font=font_body, fill=TEXT_COLOR)
            y += 48
        y += 10

    # Key concepts as bullets
    concepts = summary.get("key_concepts", [])
    if concepts:
        font_bullet = get_font(30)
        bullet_title_font = get_font(32, bold=True)
        draw.text((60, y), "Key Concepts:", font=bullet_title_font, fill=ACCENT_COLOR)
        y += 45
        for concept in concepts[:4]:  # Max 4 bullets
            draw.text((80, y), f"▸  {concept}", font=font_bullet, fill=BULLET_COLOR)
            y += 42
        y += 10

    # Code block
    code = summary.get("code_example", "").strip()
    if code and y < HEIGHT - 200:
        code_lines = code.split("\n")[:6]  # Max 6 lines of code
        code_height = len(code_lines) * 38 + 30
        code_rect = [60, y, WIDTH - 60, y + code_height]
        draw.rectangle(code_rect, fill=CODE_BG)
        draw.rectangle(
            [60, y, 60 + 4, y + code_height],
            fill=ACCENT_COLOR
        )

        mono_font = get_mono_font(28)
        cy = y + 15
        for line in code_lines:
            draw.text((80, cy), line, font=mono_font, fill=CODE_COLOR)
            cy += 38

    # Bottom bar
    draw.rectangle([0, HEIGHT - 6, WIDTH, HEIGHT], fill=ACCENT_COLOR)

    # Timestamp
    ts = slide_data.get("timestamp", 0)
    ts_text = f"@ {int(ts // 60):02d}:{int(ts % 60):02d}"
    ts_font = get_font(26)
    draw.text((40, HEIGHT - 48), ts_text, font=ts_font, fill=SLIDE_NUM_COLOR)

    img.save(output_path, "PNG")
    return output_path


def create_outro_slide(overall_summary: dict, output_path: str) -> str:
    """Create the outro slide with key takeaways."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, WIDTH, 6], fill=ACCENT_COLOR)

    font_title = get_font(60, bold=True)
    draw.text((60, 50), "Key Takeaways", font=font_title, fill=TITLE_COLOR)
    draw.line([(60, 135), (WIDTH - 60, 135)], fill=ACCENT_COLOR, width=2)

    font_item = get_font(36)
    y = 165
    takeaways = overall_summary.get("key_takeaways", [])
    for i, takeaway in enumerate(takeaways[:6]):
        wrapped = textwrap.wrap(takeaway, width=68)
        draw.text((80, y), f"{i+1}.", font=get_font(36, bold=True), fill=ACCENT_COLOR)
        for line in wrapped:
            draw.text((130, y), line, font=font_item, fill=TEXT_COLOR)
            y += 48
        y += 12

    draw.rectangle([0, HEIGHT - 6, WIDTH, HEIGHT], fill=ACCENT_COLOR)

    img.save(output_path, "PNG")
    return output_path


async def generate_tts(text: str, output_path: str, voice: str = TTS_VOICE):
    """Generate TTS audio using edge-tts."""
    if not text or len(text.strip()) < 5:
        text = "Moving to the next topic."

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_tts_sync(text: str, output_path: str):
    """Synchronous wrapper for async TTS generation."""
    asyncio.run(generate_tts(text, output_path))


def create_slideshow_video(
    fused_slides: list[dict],
    overall_summary: dict,
    output_path: str,
    temp_dir: str,
    progress_callback=None
) -> str:
    """
    Create the full slideshow summary video.
    1. Generate slide images
    2. Generate TTS audio for each
    3. Combine into MP4
    """
    temp_dir = Path(temp_dir) / "slideshow"
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(output_path)

    clips = []
    total_steps = len(fused_slides) + 3  # +3 for intro, outro, final assembly

    print("[Slideshow] Creating intro slide...")
    intro_img = str(temp_dir / "intro.png")
    create_intro_slide(overall_summary, intro_img)

    intro_script = overall_summary.get("intro_voiceover", "Welcome to this lecture summary.")
    intro_audio = str(temp_dir / "intro_audio.mp3")
    generate_tts_sync(intro_script, intro_audio)

    intro_clip = ImageClip(intro_img).with_duration(
        AudioFileClip(intro_audio).duration
    ).with_audio(AudioFileClip(intro_audio))
    clips.append(intro_clip)

    if progress_callback:
        progress_callback(1 / total_steps)

    # Generate slides
    content_slides = [s for s in fused_slides if s.get("summary", {}).get("voiceover_script")]
    total_content = len(content_slides)

    for i, slide in enumerate(content_slides):
        summary = slide.get("summary", {})
        voiceover = summary.get("voiceover_script", "")

        if not voiceover:
            continue

        print(f"[Slideshow] Creating slide {i+1}/{total_content}...")

        slide_img_path = str(temp_dir / f"slide_{i+1:04d}.png")
        slide_audio_path = str(temp_dir / f"slide_{i+1:04d}_audio.mp3")

        create_summary_slide(slide, i + 1, total_content, slide_img_path)
        generate_tts_sync(voiceover, slide_audio_path)

        try:
            audio_clip = AudioFileClip(slide_audio_path)
            # Min 3 seconds per slide
            duration = max(audio_clip.duration, 3.0)
            img_clip = ImageClip(slide_img_path).with_duration(duration).with_audio(audio_clip)
            clips.append(img_clip)
        except Exception as e:
            print(f"[Slideshow] Warning: skipping slide {i+1}: {e}")

        if progress_callback:
            progress_callback((i + 2) / total_steps)

    # Outro slide
    print("[Slideshow] Creating outro slide...")
    outro_img = str(temp_dir / "outro.png")
    create_outro_slide(overall_summary, outro_img)

    outro_text = "And those are the key takeaways from this lecture. Happy coding!"
    outro_audio = str(temp_dir / "outro_audio.mp3")
    generate_tts_sync(outro_text, outro_audio)

    outro_audio_clip = AudioFileClip(outro_audio)
    outro_clip = ImageClip(outro_img).with_duration(
        max(outro_audio_clip.duration, 5.0)
    ).with_audio(outro_audio_clip)
    clips.append(outro_clip)

    if not clips:
        raise RuntimeError("No slides were generated!")

    # Assemble final video
    print(f"[Slideshow] Assembling {len(clips)} clips into video...")
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None
    )

    print(f"[Slideshow] Slideshow video saved to: {output_path}")
    return str(output_path)
