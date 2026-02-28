"""
pipeline/summarizer.py
Uses GPT-4o to generate structured summaries from fused slide+transcript data.
Produces per-slide summaries and an overall course summary.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SLIDE_SUMMARY_PROMPT = """You are an expert programming instructor creating concise study notes.

You are given content from ONE slide of a programming lecture:

SLIDE TEXT (from OCR):
{ocr_text}

INSTRUCTOR'S SPEECH (during this slide):
{transcript}

SLIDE DURATION: {duration:.0f} seconds

Your task:
1. Write a clear, concise summary of what was taught in this slide (2-4 sentences)
2. Extract key concepts, functions, or syntax introduced (as a list)
3. If code is present, include a clean version of the key code example
4. Write a short "voiceover script" (30-60 words) for a summary video — clear and engaging

Respond ONLY with valid JSON in this exact format:
{{
  "title": "Slide topic in 5-8 words",
  "summary": "2-4 sentence explanation of what was taught",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "code_example": "clean code example if present, otherwise empty string",
  "voiceover_script": "30-60 word script for summary video narration"
}}"""


OVERALL_SUMMARY_PROMPT = """You are creating an executive summary for a programming lecture.

Here are the summaries from each slide section:

{slide_summaries}

Write a comprehensive overall summary of the entire lecture:
1. What was the main topic?
2. What were the 5-7 most important things taught?
3. What should a student be able to do after watching this lecture?

Respond ONLY with valid JSON:
{{
  "lecture_title": "Descriptive title for the lecture",
  "main_topic": "One sentence describing the main topic",
  "key_takeaways": ["takeaway1", "takeaway2", "takeaway3", "takeaway4", "takeaway5"],
  "learning_outcomes": ["outcome1", "outcome2", "outcome3"],
  "intro_voiceover": "60-80 word intro script for the summary video"
}}"""


def summarize_slide(slide: dict) -> dict:
    """
    Generate a structured summary for a single slide.
    Returns the slide dict enriched with 'summary' field.
    """
    ocr_text = slide.get("ocr_text", "").strip() or "No slide text detected"
    transcript = slide.get("full_transcript", "").strip() or "No speech detected for this slide"
    duration = slide.get("slide_end", 0) - slide.get("slide_start", 0)

    # Skip slides with very little content
    if len(ocr_text) < 10 and len(transcript) < 20:
        slide["summary"] = {
            "title": f"Slide {slide['slide_number']}",
            "summary": "No significant content detected on this slide.",
            "key_concepts": [],
            "code_example": "",
            "voiceover_script": ""
        }
        return slide

    prompt = SLIDE_SUMMARY_PROMPT.format(
        ocr_text=ocr_text[:2000],       # Limit to avoid token overflow
        transcript=transcript[:3000],
        duration=duration
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        summary_json = json.loads(response.choices[0].message.content)
        slide["summary"] = summary_json

    except Exception as e:
        print(f"[Summarizer] Warning: failed on slide {slide['slide_number']}: {e}")
        slide["summary"] = {
            "title": f"Slide {slide['slide_number']}",
            "summary": transcript[:200] if transcript else "Content unavailable",
            "key_concepts": [],
            "code_example": "",
            "voiceover_script": transcript[:100] if transcript else ""
        }

    return slide


def summarize_all_slides(fused_slides: list[dict], progress_callback=None) -> list[dict]:
    """
    Summarize all slides. Returns enriched list with 'summary' on each slide.
    """
    total = len(fused_slides)
    print(f"[Summarizer] Summarizing {total} slides with GPT-4o...")

    for i, slide in enumerate(fused_slides):
        print(f"[Summarizer] Slide {i+1}/{total}...")
        summarize_slide(slide)

        if progress_callback:
            progress_callback((i + 1) / total)

    print("[Summarizer] All slides summarized.")
    return fused_slides


def generate_overall_summary(fused_slides: list[dict]) -> dict:
    """
    Generate an overall lecture summary from all slide summaries.
    """
    print("[Summarizer] Generating overall lecture summary...")

    # Build condensed slide summary list for the prompt
    slide_summaries_text = ""
    for slide in fused_slides:
        summary = slide.get("summary", {})
        if summary.get("summary"):
            slide_summaries_text += f"\n[Slide {slide['slide_number']}] {summary.get('title', '')}\n"
            slide_summaries_text += f"Summary: {summary.get('summary', '')}\n"
            concepts = summary.get("key_concepts", [])
            if concepts:
                slide_summaries_text += f"Key concepts: {', '.join(concepts)}\n"

    if not slide_summaries_text:
        return {
            "lecture_title": "Lecture Summary",
            "main_topic": "Unable to generate summary",
            "key_takeaways": [],
            "learning_outcomes": [],
            "intro_voiceover": ""
        }

    prompt = OVERALL_SUMMARY_PROMPT.format(
        slide_summaries=slide_summaries_text[:6000]
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        overall = json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"[Summarizer] Overall summary failed: {e}")
        overall = {
            "lecture_title": "Lecture Summary",
            "main_topic": "Summary generation failed",
            "key_takeaways": [],
            "learning_outcomes": [],
            "intro_voiceover": "In this lecture, we covered important programming concepts."
        }

    print(f"[Summarizer] Lecture title: {overall.get('lecture_title', 'N/A')}")
    return overall


def build_full_summary_report(fused_slides: list[dict], overall_summary: dict) -> dict:
    """
    Build the complete summary report combining overall + per-slide summaries.
    """
    return {
        "overall": overall_summary,
        "slides": [
            {
                "slide_number": s["slide_number"],
                "timestamp": s["timestamp"],
                "slide_start": s.get("slide_start", 0),
                "slide_end": s.get("slide_end", 0),
                "screenshot_path": s.get("screenshot_path", ""),
                "summary": s.get("summary", {}),
                "importance_score": s.get("importance_score", 0)
            }
            for s in fused_slides
        ]
    }
