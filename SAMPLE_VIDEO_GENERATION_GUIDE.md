# Sample Video Generation Guide

A complete guide to understanding and running `Sample_video_generation.py` — a standalone script that generates an AI-narrated slideshow video from a plain Python summary, with no lecture video required.

---

## Table of Contents

1. [What This Script Does](#1-what-this-script-does)
2. [Project Structure](#2-project-structure)
3. [How Execution Works — Flow Diagram](#3-how-execution-works--flow-diagram)
4. [Slide Structure Diagram](#4-slide-structure-diagram)
5. [Data Structure Explained](#5-data-structure-explained)
6. [Setup and Installation](#6-setup-and-installation)
7. [How to Execute](#7-how-to-execute)
8. [Output Files](#8-output-files)
9. [What Each Stage Produces](#9-what-each-stage-produces)
10. [Customising the Summary](#10-customising-the-summary)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. What This Script Does

`Sample_video_generation.py` bypasses the full AI Lecturer pipeline and generates a polished MP4 slideshow video directly from a manually written summary. It requires **no video upload, no transcription, and no AI API calls**.

```
You write summary data  →  Script generates video  →  MP4 saved to disk
```

**Output:** A 1920×1080 MP4 video with:
- An intro title slide
- One content slide per topic (with bullet points and code blocks)
- Neural AI voiceover on every slide (Microsoft Edge TTS)
- A key takeaways outro slide

---

## 2. Project Structure

```
AI_Lecturer/
│
├── Sample_video_generation.py     ← You run this
├── requirements_sample.txt        ← Minimal dependencies for this script
├── SAMPLE_VIDEO_GENERATION_GUIDE.md  ← This file
│
├── pipeline/
│   └── slideshow_video.py         ← Core video generation logic (imported)
│
└── sample_output/                 ← Created automatically when you run
    ├── sample_slideshow.mp4       ← Final output video
    └── temp/
        └── slideshow/
            ├── intro.png
            ├── intro_audio.mp3
            ├── slide_0001.png
            ├── slide_0001_audio.mp3
            ├── slide_0002.png
            ├── slide_0002_audio.mp3
            ├── ...
            ├── outro.png
            └── outro_audio.mp3
```

---

## 3. How Execution Works — Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│               python Sample_video_generation.py                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1 — Read Input Data (from the script itself)              │
│                                                                  │
│  overall_summary  ──►  lecture_title, main_topic,               │
│                         intro_voiceover, key_takeaways           │
│                                                                  │
│  fused_slides     ──►  list of slides, each with:               │
│                         title, summary, key_concepts,            │
│                         code_example, voiceover_script           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2 — Create Intro Slide                                     │
│                                                                  │
│  create_intro_slide()  ──►  intro.png  (Pillow draws it)        │
│  generate_tts_sync()   ──►  intro_audio.mp3  (Edge TTS)         │
│                                                                  │
│  ImageClip(intro.png) + AudioFileClip(intro.mp3)                │
│                        ──►  intro video clip                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3 — Create Content Slides  (repeated for each slide)      │
│                                                                  │
│  For slide 1:                                                    │
│    create_summary_slide()  ──►  slide_0001.png                  │
│    generate_tts_sync()     ──►  slide_0001_audio.mp3            │
│    ImageClip + AudioClip   ──►  slide clip  (min 3 seconds)     │
│                                                                  │
│  For slide 2:                                                    │
│    create_summary_slide()  ──►  slide_0002.png                  │
│    generate_tts_sync()     ──►  slide_0002_audio.mp3            │
│    ImageClip + AudioClip   ──►  slide clip                      │
│                                                                  │
│  ... repeated for every slide in fused_slides ...               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4 — Create Outro Slide                                     │
│                                                                  │
│  create_outro_slide()  ──►  outro.png  (key takeaways list)     │
│  generate_tts_sync()   ──►  outro_audio.mp3                     │
│  ImageClip + AudioClip ──►  outro clip  (min 5 seconds)         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5 — Assemble Final Video                                   │
│                                                                  │
│  clips = [intro, slide1, slide2, ..., slideN, outro]            │
│                                                                  │
│  concatenate_videoclips(clips)                                   │
│       ──►  write_videofile()                                     │
│               codec:       libx264  (H.264 video)               │
│               audio_codec: aac                                   │
│               fps:         24                                    │
│               resolution:  1920 × 1080                          │
│                                                                  │
│  OUTPUT ──►  sample_output/sample_slideshow.mp4                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Slide Structure Diagram

Every content slide is rendered as a 1920×1080 PNG image by Pillow:

```
┌──────────────────────────────────────────────────────┐  ← accent bar (6px, indigo)
│                                              1 / 5   │  ← slide counter (top right)
│                                                      │
│  Slide Title Here                                    │  ← bold white, 54px
│ ─────────────────────────────────────────────────── │  ← divider line
│                                                      │
│  Summary text explaining the concept in 2-4          │  ← body text, 34px
│  sentences is displayed here across the slide.       │
│                                                      │
│  Key Concepts:                                       │  ← section heading (indigo)
│    ▸  First key concept                              │  ← green bullets, 30px
│    ▸  Second key concept                             │
│    ▸  Third key concept                              │
│    ▸  Fourth key concept                             │
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ ▌ code goes here line 1                          │   │  ← code block (dark bg)
│ ▌ code goes here line 2                          │   │  ← cyan monospace text
│ ▌ code goes here line 3                          │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ @ 02:00                                              │  ← timestamp (bottom left)
└──────────────────────────────────────────────────────┘  ← accent bar (6px, indigo)
```

**Color scheme used:**

| Element        | Color            | RGB              |
|----------------|------------------|------------------|
| Background     | Dark navy        | (18, 18, 24)     |
| Accent bars    | Indigo           | (99, 102, 241)   |
| Title text     | White            | (255, 255, 255)  |
| Body text      | Light gray       | (226, 232, 240)  |
| Bullet points  | Mint green       | (167, 243, 208)  |
| Code text      | Cyan             | (139, 233, 253)  |
| Code block bg  | Dark charcoal    | (30, 30, 46)     |
| Slide counter  | Muted gray       | (100, 116, 139)  |

---

## 5. Data Structure Explained

The script has two Python dictionaries you fill in:

### `overall_summary` — used for intro and outro slides

```python
overall_summary = {
    "lecture_title":   "Your Lecture Title",        # shown large on intro slide
    "main_topic":      "Subtitle / topic line",      # shown below title
    "intro_voiceover": "What the AI voice says ...", # spoken on the intro slide
    "key_takeaways": [                               # shown on the outro slide
        "Point one.",
        "Point two.",
        # up to 6 items
    ],
}
```

### `fused_slides` — one entry per content slide

```python
fused_slides = [
    {
        "slide_number": 1,       # used for display counter
        "timestamp":    60,      # seconds — shown as "@ 01:00" on the slide
        "summary": {
            "title":           "Slide heading (5–8 words)",
            "summary":         "2–4 sentence explanation shown as body text.",
            "key_concepts":    [          # up to 4 bullets shown on slide
                "Concept one",
                "Concept two",
            ],
            "code_example":    "code\nhere",  # leave "" if no code
            "voiceover_script": "30–60 words the AI voice reads aloud.",
        },
    },
    # ... add more slides
]
```

> **Important:** Only slides with a non-empty `voiceover_script` are included in the video. Any slide missing this field is silently skipped.

---

## 6. Setup and Installation

### Prerequisites

- Python 3.9 or higher
- FFmpeg installed and available on your system PATH

### Install FFmpeg (Windows)

1. Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract to a folder, e.g. `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify: open a terminal and run `ffmpeg -version`

### Install Python dependencies

```bash
# Navigate to the project folder
cd "D:\AI Research Project HErts copy\AI_Lecturer"

# (Recommended) Activate your virtual environment first
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install only what this script needs
pip install -r requirements_sample.txt
```

### What gets installed

| Package          | Version  | Purpose                              |
|------------------|----------|--------------------------------------|
| `Pillow`         | ≥ 10.0.0 | Draws slide images (PNG)             |
| `edge-tts`       | ≥ 6.1.9  | Microsoft neural text-to-speech      |
| `moviepy`        | ≥ 1.0.3  | Assembles clips into MP4             |
| `imageio-ffmpeg` | ≥ 0.4.9  | FFmpeg backend used by moviepy       |
| `numpy`          | ≥ 1.24.0 | Array support used internally        |
| `aiofiles`       | ≥ 23.2.1 | Async file I/O used by edge-tts      |

---

## 7. How to Execute

### Step 1 — Open the file and edit your summary

Open `Sample_video_generation.py` and fill in `overall_summary` and `fused_slides` with your content.

### Step 2 — Run the script

```bash
cd "D:\AI Research Project HErts copy\AI_Lecturer"
venv\Scripts\activate
python Sample_video_generation.py
```

### Step 3 — Watch the terminal output

```
============================================================
  Sample Slideshow Video Generator
============================================================
  Slides   : 5
  Output   : ...\sample_output\sample_slideshow.mp4
============================================================
[Slideshow] Creating intro slide...
  Progress : [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  20%
[Slideshow] Creating slide 1/5...
  Progress : [████████████████░░░░░░░░░░░░░░░░░░░░░░░░]  40%
...
[Slideshow] Assembling 7 clips into video...   ← slowest step, wait here
  Done! Video saved to:
  ...\sample_output\sample_slideshow.mp4
```

### Execution time estimates

| Number of Slides | Approx. Time |
|-----------------|--------------|
| 3 slides        | 1–2 minutes  |
| 5 slides        | 2–4 minutes  |
| 8 slides        | 4–7 minutes  |
| 10+ slides      | 7–12 minutes |

> The **assembling step** (the last step) is the slowest. It uses your CPU to encode H.264 video. The terminal will appear frozen — this is normal. Do not close the terminal.

---

## 8. Output Files

After a successful run, the following files are created:

```
sample_output/
├── sample_slideshow.mp4          ← Final video (open this)
└── temp/
    └── slideshow/
        ├── intro.png             ← Title slide image
        ├── intro_audio.mp3       ← TTS for intro
        ├── slide_0001.png        ← Slide 1 image
        ├── slide_0001_audio.mp3  ← TTS for slide 1
        ├── slide_0002.png
        ├── slide_0002_audio.mp3
        ├── ...
        ├── outro.png             ← Key takeaways slide
        └── outro_audio.mp3       ← TTS for outro
```

The `temp/slideshow/` folder contains all the intermediate files used to build the video. You can delete it after the video is created.

---

## 9. What Each Stage Produces

```
Stage                Function called              Output file
─────────────────    ────────────────────────     ──────────────────────────
Intro image          create_intro_slide()         temp/slideshow/intro.png
Intro audio          generate_tts_sync()          temp/slideshow/intro_audio.mp3
Slide N image        create_summary_slide()       temp/slideshow/slide_NNNN.png
Slide N audio        generate_tts_sync()          temp/slideshow/slide_NNNN_audio.mp3
Outro image          create_outro_slide()         temp/slideshow/outro.png
Outro audio          generate_tts_sync()          temp/slideshow/outro_audio.mp3
Final assembly       concatenate_videoclips()     sample_output/sample_slideshow.mp4
```

---

## 10. Customising the Summary

### Change the topic

Replace `overall_summary` and `fused_slides` with content for your subject. Keep each `voiceover_script` between 30–60 words for natural-sounding narration.

### Add more slides

Add more dictionaries to the `fused_slides` list:

```python
fused_slides = [
    { "slide_number": 1, "timestamp": 0,   "summary": { ... } },
    { "slide_number": 2, "timestamp": 120, "summary": { ... } },
    { "slide_number": 3, "timestamp": 240, "summary": { ... } },
    # keep adding ...
]
```

### Skip the code block

Set `"code_example": ""` — the code section will not appear on that slide.

### Change the output path

Edit these lines near the bottom of the script:

```python
OUTPUT_DIR   = "C:/MyVideos"               # folder where video is saved
OUTPUT_VIDEO = "C:/MyVideos/my_video.mp4"  # final video filename
TEMP_DIR     = "C:/MyVideos/temp"          # intermediate files folder
```

### Change the TTS voice

Open `pipeline/slideshow_video.py` and change line 31:

```python
TTS_VOICE = "en-US-AriaNeural"     # default — American female
# Other options:
# "en-GB-SoniaNeural"              # British female
# "en-US-GuyNeural"                # American male
# "en-AU-NatashaNeural"            # Australian female
```

---

## 11. Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: moviepy` | Dependencies not installed | Run `pip install -r requirements_sample.txt` |
| `FileNotFoundError: ffmpeg` | FFmpeg not on PATH | Install FFmpeg and add `bin/` to system PATH |
| Text on slides looks very small | No system fonts found | Install DejaVu or Liberation fonts, or add Windows font path to `get_font()` in `slideshow_video.py` |
| Script hangs at "Assembling clips" | Normal — H.264 encoding in progress | Wait; do not close the terminal |
| `RuntimeError: No slides were generated` | All slides missing `voiceover_script` | Add `"voiceover_script"` to every slide in `fused_slides` |
| `edge-tts` network error | No internet connection | edge-tts requires internet to generate speech |
| Output video has no audio | `aiofiles` not installed | Run `pip install aiofiles` |

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────┐
│              QUICK EXECUTION STEPS                   │
├──────────────────────────────────────────────────────┤
│  1. cd "D:\AI Research Project HErts copy\AI_Lecturer"│
│  2. venv\Scripts\activate                            │
│  3. Edit Sample_video_generation.py                  │
│     └─ fill in overall_summary                       │
│     └─ fill in fused_slides (one dict per slide)     │
│  4. python Sample_video_generation.py                │
│  5. Wait 2–10 minutes for encoding                   │
│  6. Open sample_output/sample_slideshow.mp4          │
└──────────────────────────────────────────────────────┘
```
