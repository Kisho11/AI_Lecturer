"""
pipeline/fusion.py
Aligns transcript segments with detected slides by timestamp.
Produces a fused structure: each slide with its corresponding spoken content.
"""

from typing import Optional


def align_transcript_to_slides(
    transcript_segments: list[dict],
    slide_changes: list[dict],
    video_duration: float
) -> list[dict]:
    """
    Match each transcript segment to the slide that was visible at that time.
    
    transcript_segments: [{ start, end, text }]
    slide_changes: [{ slide_number, timestamp, screenshot_path, ocr_text, ... }]
    
    Returns fused list: [{
        slide_number,
        slide_start,
        slide_end,
        screenshot_path,
        ocr_text,
        transcript_segments: [{ start, end, text }],
        full_transcript: str
    }]
    """
    if not slide_changes:
        return []

    # Build slide time ranges
    slides_with_ranges = []
    for i, slide in enumerate(slide_changes):
        slide_start = slide["timestamp"]
        # Slide ends when next slide begins, or at video end
        if i + 1 < len(slide_changes):
            slide_end = slide_changes[i + 1]["timestamp"]
        else:
            slide_end = video_duration

        slides_with_ranges.append({
            **slide,
            "slide_start": slide_start,
            "slide_end": slide_end,
            "transcript_segments": [],
            "full_transcript": ""
        })

    # Assign each transcript segment to a slide
    for seg in transcript_segments:
        seg_midpoint = (seg["start"] + seg["end"]) / 2

        # Find which slide was active during this segment
        assigned = False
        for slide in slides_with_ranges:
            if slide["slide_start"] <= seg_midpoint < slide["slide_end"]:
                slide["transcript_segments"].append(seg)
                assigned = True
                break

        # Edge case: segment is before first slide or after last
        if not assigned and slides_with_ranges:
            if seg_midpoint < slides_with_ranges[0]["slide_start"]:
                slides_with_ranges[0]["transcript_segments"].append(seg)
            else:
                slides_with_ranges[-1]["transcript_segments"].append(seg)

    # Build full transcript string for each slide
    for slide in slides_with_ranges:
        slide["full_transcript"] = " ".join(
            seg["text"] for seg in slide["transcript_segments"]
        ).strip()

    print(f"[Fusion] Aligned {len(transcript_segments)} transcript segments across {len(slides_with_ranges)} slides")

    # Log coverage stats
    empty_slides = sum(1 for s in slides_with_ranges if not s["full_transcript"])
    if empty_slides:
        print(f"[Fusion] Warning: {empty_slides} slides have no transcript coverage")

    return slides_with_ranges


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using OpenCV."""
    import cv2
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return frame_count / fps if fps > 0 else 0.0


def score_slide_importance(fused_slide: dict) -> float:
    """
    Score a slide's importance for highlight reel selection.
    Higher score = more likely to be included in highlights.
    
    Factors:
    - Length of transcript (more speech = more content)
    - OCR text density (more content on slide)
    - Presence of code (programming lectures)
    """
    score = 0.0

    transcript = fused_slide.get("full_transcript", "")
    ocr_text = fused_slide.get("ocr_text", "")

    # Transcript length (normalized)
    word_count = len(transcript.split())
    score += min(word_count / 50.0, 2.0)  # Cap at 2.0

    # OCR text density
    ocr_words = len(ocr_text.split())
    score += min(ocr_words / 30.0, 1.5)

    # Code detection bonus (common programming keywords)
    code_indicators = [
        "def ", "class ", "import ", "return ", "function", "var ", "const ",
        "=>", "->", "{", "}", "for ", "while ", "if ", "else", "print(",
        "console.log", "SELECT", "FROM", "WHERE", "public ", "private "
    ]
    code_hits = sum(1 for kw in code_indicators if kw in ocr_text or kw in transcript)
    score += min(code_hits * 0.3, 1.5)

    # Slide duration (longer slides tend to be more important)
    duration = fused_slide.get("slide_end", 0) - fused_slide.get("slide_start", 0)
    score += min(duration / 60.0, 1.0)

    return round(score, 3)


def select_highlight_slides(fused_slides: list[dict], max_duration: float = 300.0) -> list[dict]:
    """
    Select the most important slides for the highlight reel.
    Tries to stay within max_duration seconds total.
    Returns sorted list of selected slides (by original order).
    """
    # Score all slides
    for slide in fused_slides:
        slide["importance_score"] = score_slide_importance(slide)

    # Sort by importance descending
    scored = sorted(fused_slides, key=lambda s: s["importance_score"], reverse=True)

    selected = []
    total_duration = 0.0

    for slide in scored:
        slide_duration = slide.get("slide_end", 0) - slide.get("slide_start", 0)
        if total_duration + slide_duration <= max_duration:
            selected.append(slide)
            total_duration += slide_duration

    # Re-sort by original order (slide_number)
    selected.sort(key=lambda s: s["slide_number"])

    print(f"[Fusion] Selected {len(selected)} highlight slides ({total_duration:.0f}s total)")
    return selected


if __name__ == "__main__":
    # Quick test with mock data
    mock_transcript = [
        {"start": 0, "end": 10, "text": "Welcome to this Python tutorial."},
        {"start": 10, "end": 25, "text": "Today we'll cover list comprehensions."},
        {"start": 30, "end": 55, "text": "A list comprehension is a concise way to create lists. For example: squares = [x**2 for x in range(10)]"},
    ]
    mock_slides = [
        {"slide_number": 1, "timestamp": 0.0, "screenshot_path": "s1.png", "ocr_text": "Python List Comprehensions"},
        {"slide_number": 2, "timestamp": 28.0, "screenshot_path": "s2.png", "ocr_text": "squares = [x**2 for x in range(10)]"},
    ]

    fused = align_transcript_to_slides(mock_transcript, mock_slides, 60.0)
    for s in fused:
        print(f"\nSlide {s['slide_number']}: {s['full_transcript'][:100]}")
        print(f"  Importance: {score_slide_importance(s)}")
