# 🎓 Lecture Summarizer

AI-powered tool that turns long programming lecture videos into concise summary videos.

## What it does

Upload a 30-60 minute lecture video → get:
- **Slideshow Video** — clean AI-generated slides with neural TTS voiceover
- **Highlight Reel** — best moments cut from the original video with overlays
- **Summary JSON** — structured per-slide summaries with key concepts + code

## How it works

```
Video → Audio Extraction (ffmpeg)
      → Whisper Transcription (timestamped)
      → Slide Change Detection (OpenCV)
      → OCR / GPT-4o Vision (slide text)
      → Content Fusion (align transcript ↔ slides)
      → GPT-4o Summarization (per slide + overall)
      → Slideshow Video (Pillow + edge-tts + moviepy)
      → Highlight Reel (moviepy clips + overlays)
```

## Setup

### 1. Prerequisites

Install system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg tesseract-ocr

# macOS
brew install ffmpeg tesseract
```

### 2. Python environment

```bash
cd lecture-summarizer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 4. Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Configuration

| Setting | Description | Default |
|---|---|---|
| `WHISPER_MODE` | `local` (free, slower) or `api` (fast, ~$0.006/min) | `local` |
| `WHISPER_MODEL` | `tiny/base/small/medium/large` | `medium` |
| `OPENAI_API_KEY` | Your OpenAI key (required) | — |

## Performance Expectations

| Video Length | CPU Transcription | GPU Transcription | API Transcription |
|---|---|---|---|
| 30 min | ~8-12 min | ~2-3 min | ~1 min |
| 60 min | ~15-25 min | ~4-6 min | ~2 min |

Slide detection + OCR adds ~2-5 minutes for a 60-min video.

## Project Structure

```
lecture-summarizer/
├── app.py                   ← Streamlit UI
├── pipeline/
│   ├── audio.py             ← ffmpeg + Whisper
│   ├── visual.py            ← OpenCV slide detection + EasyOCR / GPT-4V
│   ├── fusion.py            ← Align transcript with slides
│   ├── summarizer.py        ← GPT-4o summarization
│   ├── slideshow_video.py   ← Output B: slides + TTS voiceover
│   └── highlight_video.py   ← Output A: video clips + overlays
├── requirements.txt
├── .env.example
└── README.md
```

## Tips for Best Results

- **Clear slide transitions** work best (fade/cut between slides)
- **Screen recordings** of IDE/presentations work better than camera footage
- Use **GPT-4o Vision OCR** (toggle in sidebar) for code-heavy slides
- If transcription is slow, switch to **Whisper API mode** in sidebar
- Set **slide sensitivity** lower (0.70-0.80) for fast-transitioning slides

## Troubleshooting

**"ffmpeg not found"** → Install ffmpeg: `sudo apt install ffmpeg`

**Slow transcription** → Switch to Whisper API mode in sidebar, or use `tiny`/`base` model

**Poor OCR on code** → Enable GPT-4o Vision OCR toggle in sidebar

**Video assembly errors** → Make sure `moviepy` is installed: `pip install moviepy`

**Too many / too few slides detected** → Adjust "Change Sensitivity" slider in sidebar
