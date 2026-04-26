"""
pipeline/visual.py
Detects slide changes in lecture video using OpenCV frame differencing.
Extracts slide screenshots and runs OCR via EasyOCR.
Also attempts GPT-4o Vision for better code extraction.
"""

import os
import cv2
import numpy as np
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

try:
    import easyocr
except ImportError:
    easyocr = None

load_dotenv()

# Sensitivity for slide change detection (0-1). Lower = more sensitive.
SLIDE_CHANGE_THRESHOLD = 0.85
# Minimum seconds between detected slide changes (avoid duplicate detections)
MIN_SLIDE_DURATION = 3.0
# Sample every N frames (higher = faster but might miss quick slides)
FRAME_SAMPLE_RATE = 5


def _build_easyocr_reader():
    """
    Initialize EasyOCR only when needed so the module can still import
    in environments where the dependency is not installed.
    """
    if easyocr is None:
        raise RuntimeError(
            "EasyOCR is not installed. Install it with "
            "`pip install easyocr` or use GPT-4o Vision-only extraction."
        )
    return easyocr.Reader(['en'], gpu=False)


def detect_slide_changes(video_path: str, output_dir: str, progress_callback=None) -> list[dict]:
    """
    Analyze video frames to detect slide changes.
    Returns list of: { timestamp, frame_number, screenshot_path }
    """
    video_path = Path(video_path)
    slides_dir = Path(output_dir) / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    print(f"[Visual] Video: {duration:.1f}s, {fps:.1f} FPS, {total_frames} frames")
    print(f"[Visual] Detecting slide changes...")

    slide_changes = []
    prev_hist = None
    last_change_time = -MIN_SLIDE_DURATION
    frame_idx = 0
    slide_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Sample every N frames for speed
        if frame_idx % FRAME_SAMPLE_RATE != 0:
            frame_idx += 1
            continue

        timestamp = frame_idx / fps

        # Convert to HSV and compute histogram for comparison
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist)

        if prev_hist is not None:
            # Compare histograms
            similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)

            is_slide_change = (
                similarity < SLIDE_CHANGE_THRESHOLD and
                (timestamp - last_change_time) >= MIN_SLIDE_DURATION
            )

            if is_slide_change or (slide_count == 0 and frame_idx == 0):
                slide_count += 1
                screenshot_path = slides_dir / f"slide_{slide_count:04d}_{timestamp:.1f}s.png"

                # Save high quality screenshot
                cv2.imwrite(str(screenshot_path), frame)

                slide_changes.append({
                    "slide_number": slide_count,
                    "timestamp": round(timestamp, 2),
                    "frame_number": frame_idx,
                    "screenshot_path": str(screenshot_path),
                    "similarity_score": round(float(similarity), 4)
                })

                last_change_time = timestamp
                print(f"[Visual] Slide {slide_count} detected at {timestamp:.1f}s (similarity: {similarity:.3f})")

        # Always capture the first frame as slide 1
        elif frame_idx == 0:
            slide_count += 1
            screenshot_path = slides_dir / f"slide_{slide_count:04d}_{timestamp:.1f}s.png"
            cv2.imwrite(str(screenshot_path), frame)
            slide_changes.append({
                "slide_number": slide_count,
                "timestamp": 0.0,
                "frame_number": 0,
                "screenshot_path": str(screenshot_path),
                "similarity_score": 1.0
            })
            last_change_time = 0.0

        prev_hist = hist
        frame_idx += 1

        # Progress callback
        if progress_callback and frame_idx % 100 == 0:
            progress = frame_idx / total_frames
            progress_callback(progress)

    cap.release()
    print(f"[Visual] Detected {len(slide_changes)} slides total.")
    return slide_changes


def extract_text_from_slide_ocr(screenshot_path: str, reader=None) -> str:
    """
    Extract text from slide image using EasyOCR.
    """
    if reader is None:
        print("[OCR] Initializing EasyOCR (first time may take a moment)...")
        reader = _build_easyocr_reader()

    results = reader.readtext(screenshot_path, detail=0, paragraph=True)
    text = "\n".join(results).strip()
    return text


def extract_text_from_slide_gpt4v(screenshot_path: str) -> str:
    """
    Extract text from slide using GPT-4o Vision.
    Better than OCR for code snippets and complex layouts.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with open(screenshot_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}",
                            "detail": "high"
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract ALL text content from this lecture slide. "
                            "If there is code, preserve its exact formatting. "
                            "Include slide title, bullet points, code blocks, and any annotations. "
                            "Return plain text only, preserving structure with newlines."
                        )
                    }
                ]
            }
        ],
        max_tokens=1000
    )

    return response.choices[0].message.content.strip()


def extract_slide_content(slide_changes: list[dict], use_gpt4v: bool = True, progress_callback=None) -> list[dict]:
    """
    Run OCR/Vision on all detected slides to extract text content.
    Returns enriched slide_changes list with 'ocr_text' field added.
    """
    reader = None
    if not use_gpt4v:
        print("[OCR] Initializing EasyOCR...")
        reader = _build_easyocr_reader()

    enriched = []
    total = len(slide_changes)

    for i, slide in enumerate(slide_changes):
        print(f"[OCR] Processing slide {i+1}/{total}...")

        try:
            if use_gpt4v:
                text = extract_text_from_slide_gpt4v(slide["screenshot_path"])
                slide["ocr_method"] = "gpt4v"
            else:
                text = extract_text_from_slide_ocr(slide["screenshot_path"], reader)
                slide["ocr_method"] = "easyocr"

            slide["ocr_text"] = text

        except Exception as e:
            print(f"[OCR] Warning: failed on slide {i+1}: {e}")
            # Fallback to EasyOCR if GPT-4V fails
            try:
                if reader is None:
                    reader = _build_easyocr_reader()
                text = extract_text_from_slide_ocr(slide["screenshot_path"], reader)
                slide["ocr_text"] = text
                slide["ocr_method"] = "easyocr_fallback"
            except Exception as e2:
                slide["ocr_text"] = ""
                slide["ocr_method"] = "failed"
                print(f"[OCR] Fallback also failed: {e2}")

        enriched.append(slide)

        if progress_callback:
            progress_callback((i + 1) / total)

    return enriched


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python visual.py <video_path>")
        sys.exit(1)

    slides = detect_slide_changes(sys.argv[1], "temp/")
    slides = extract_slide_content(slides, use_gpt4v=True)

    print("\n--- Slide Preview ---")
    for s in slides[:3]:
        print(f"\nSlide {s['slide_number']} @ {s['timestamp']}s")
        print(f"OCR Text: {s['ocr_text'][:200]}...")
