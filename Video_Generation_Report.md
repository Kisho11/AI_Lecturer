# Video Generation Module — Technical Report

## Overview

The system produces **two distinct video outputs** from a single lecture video upload, handled by two modules inside `pipeline/`:

| Module | File | Output |
|--------|------|--------|
| Slideshow Video | `pipeline/slideshow_video.py` | AI-generated summary video with voiceover |
| Highlight Reel | `pipeline/highlight_video.py` | Trimmed clips from the original video |

---

## System-Level Pipeline (where video generation fits)

```
┌─────────────────────────────────────────────────────────────────┐
│                        app.py  (Streamlit UI)                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────▼──────────────────────┐
         │             STAGE 1 — audio.py              │
         │  Extract audio → Whisper transcription      │
         └─────────────────────┬──────────────────────┘
                               │  transcript_segments[]
         ┌─────────────────────▼──────────────────────┐
         │             STAGE 2 — visual.py             │
         │  Detect slide changes → OCR (GPT-4o Vision) │
         └─────────────────────┬──────────────────────┘
                               │  slide_changes[]
         ┌─────────────────────▼──────────────────────┐
         │             STAGE 3 — fusion.py             │
         │  Align transcript ↔ slides → select highlights│
         └─────────────────────┬──────────────────────┘
                               │  fused_slides[], highlight_slides[]
         ┌─────────────────────▼──────────────────────┐
         │           STAGE 4 — summarizer.py           │
         │  GPT-4o: summarize each slide, overall recap │
         └──────────┬──────────────────────┬───────────┘
                    │                      │
     ┌──────────────▼──────┐    ┌──────────▼─────────────┐
     │  slideshow_video.py │    │  highlight_video.py     │
     │   OUTPUT B          │    │   OUTPUT A              │
     └─────────────────────┘    └────────────────────────┘
```

---

## Output A — Highlight Reel (`highlight_video.py`)

### What it does
Cuts the **most important segments** directly from the original video and stitches them together with transition cards and chapter banners.

### Process Flow

```
highlight_slides[]  ──►  create_highlight_reel()
                                │
                    ┌───────────▼────────────┐
                    │  Title card (3 sec)     │  ← PIL ImageDraw
                    └───────────┬────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │   extract_highlight_clips()         │
              │   for each highlight_slide:         │
              │   ┌──────────────────────────┐     │
              │   │ source.subclipped(s, e)  │     │  ← MoviePy VideoFileClip
              │   │ + FadeIn / FadeOut       │     │  ← MoviePy FX
              │   │ + chapter banner overlay │     │  ← PIL → ImageClip
              │   └──────────────────────────┘     │
              └─────────────────┬─────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ Transition cards between│  ← PIL ImageDraw
                    │ each clip (1.5 sec)     │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  Closing card (5 sec)   │  ← Key Takeaways
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ concatenate_videoclips()│  ← MoviePy
                    │ write_videofile() MP4   │  ← libx264 / aac
                    └────────────────────────┘
```

### Libraries Used

| Library | Role |
|---------|------|
| `moviepy` | Video clipping, compositing, FX (fade), writing MP4 |
| `Pillow (PIL)` | Drawing chapter banners, transition cards, text overlays |
| `textwrap` | Word-wrapping text on image frames |

---

## Output B — Slideshow Video (`slideshow_video.py`)

### What it does
Builds a **brand-new summary video** from scratch — no original footage. Each slide is rendered as a 1920×1080 image, paired with AI-generated TTS voiceover, then assembled into MP4.

### Process Flow

```
fused_slides[] + overall_summary  ──►  create_slideshow_video()
                                              │
                          ┌───────────────────▼──────────────────────┐
                          │           INTRO SLIDE                     │
                          │  create_intro_slide()  → intro.png        │  ← Pillow
                          │  generate_tts_sync(intro_script)          │  ← edge-tts
                          │  ImageClip + AudioFileClip                │  ← MoviePy
                          └───────────────────┬──────────────────────┘
                                              │
                     ┌────────────────────────▼──────────────────────────┐
                     │        FOR EACH CONTENT SLIDE                      │
                     │                                                    │
                     │   create_summary_slide()  →  slide_XXXX.png       │
                     │   ┌────────────────────────────────────────────┐  │
                     │   │ • Title + divider line                      │  │  ← Pillow
                     │   │ • Summary text (max 4 lines)               │  │
                     │   │ • Key Concepts bullet list (▸ green)       │  │
                     │   │ • Code block (monospace, cyan on dark bg)  │  │
                     │   │ • Slide counter + timestamp                 │  │
                     │   └────────────────────────────────────────────┘  │
                     │                                                    │
                     │   generate_tts_sync(voiceover_script)             │  ← edge-tts
                     │   → slide_XXXX_audio.mp3                         │
                     │                                                    │
                     │   ImageClip.with_duration(max(audio_dur, 3s))    │  ← MoviePy
                     │   .with_audio(AudioFileClip(...))                │
                     └────────────────────────┬──────────────────────────┘
                                              │
                          ┌───────────────────▼──────────────────────┐
                          │           OUTRO SLIDE                     │
                          │  create_outro_slide() → Key Takeaways     │  ← Pillow
                          │  generate_tts_sync("key takeaways...")    │  ← edge-tts
                          └───────────────────┬──────────────────────┘
                                              │
                          ┌───────────────────▼──────────────────────┐
                          │  concatenate_videoclips(clips)            │
                          │  write_videofile()  fps=24, libx264/aac  │  ← MoviePy
                          └──────────────────────────────────────────┘
```

### Libraries Used

| Library | Role |
|---------|------|
| `moviepy` | Assembling image+audio clips, concatenating, writing MP4 |
| `Pillow (PIL)` | Rendering all slide frames at 1920×1080 px |
| `edge-tts` | Microsoft Neural TTS (`en-US-AriaNeural`) → MP3 voiceover |
| `asyncio` | Running `edge-tts` async API in a synchronous context |
| `textwrap` | Wrapping long text into display lines |

---

## Shared Design Decisions

| Decision | Detail |
|----------|--------|
| Resolution | 1920 × 1080 px (16:9 1080p) |
| Video codec | `libx264` |
| Audio codec | `aac` |
| Threads | 4 (MoviePy write) |
| Min slide duration | 3 seconds (slideshow) |
| Max highlight reel | 300 sec (5 min, configurable from UI) |
| Clip padding | ±1 second around each cut (highlight) |
| TTS Voice | `en-US-AriaNeural` (Microsoft Neural) |
| Color theme | Dark (`#121218`) + Indigo accent (`#6366f1`) |

---

## Data Flow Summary

```
                      ┌──────────────────────────────────┐
Input:  fused_slides  │  [{ slide_number, timestamp,      │
        (from         │     slide_start, slide_end,       │
         summarizer)  │     summary: {                    │
                      │       title, summary,             │
                      │       key_concepts[],             │
                      │       code_example,               │
                      │       voiceover_script } }]       │
                      └────────────────┬─────────────────┘
                                       │
                     ┌─────────────────▼──────────────────┐
                     │         overall_summary             │
                     │  { lecture_title, main_topic,       │
                     │    key_takeaways[], intro_voiceover,│
                     │    learning_outcomes[] }            │
                     └─────────────────┬──────────────────┘
                                       │
                     ┌─────────────────▼──────────────────┐
Output:              │  *_slideshow.mp4  (Output B)        │
                     │  *_highlight.mp4  (Output A)        │
                     └────────────────────────────────────┘
```

---

## Key Takeaways

- **Output A (Highlight Reel)** is a *non-destructive cut* of the original video — no AI content is generated, only selection and overlaying.
- **Output B (Slideshow)** is *fully synthetic* — every frame is drawn by Pillow, every word is spoken by Microsoft Neural TTS, nothing comes from the original video.
- Both videos use **MoviePy → libx264/AAC → MP4** as the final rendering backend.
- The two modules are fully independent and can be toggled on/off from the Streamlit UI.
