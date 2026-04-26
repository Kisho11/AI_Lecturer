"""
pipeline/audio.py
Handles audio extraction from video and transcription via Whisper.
Supports both local Whisper model and OpenAI Whisper API.
"""

import os
import sys
import shutil
import subprocess
import importlib
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _add_project_venv_site_packages():
    """
    If the app is launched outside the repo virtualenv, try to load packages
    from the project's bundled venv before treating them as missing.
    """
    base_dir = Path(__file__).resolve().parents[1]
    venv_dir = base_dir / "venv"

    candidates = [
        venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
        venv_dir / "Lib" / "site-packages",
    ]

    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


def _import_optional_dependency(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        _add_project_venv_site_packages()
        try:
            return importlib.import_module(module_name)
        except ImportError:
            return None


imageio_ffmpeg = _import_optional_dependency("imageio_ffmpeg")
torch = _import_optional_dependency("torch")
whisper = _import_optional_dependency("whisper")

def _require_local_whisper_dependencies():
    """
    Local Whisper needs both PyTorch and the whisper package, but API mode
    should still work when those libraries are not installed.
    """
    missing = []
    if torch is None:
        missing.append("torch")
    if whisper is None:
        missing.append("openai-whisper")

    if missing:
        raise RuntimeError(
            "Local Whisper dependencies are missing: "
            + ", ".join(missing)
            + ". Install them or switch WHISPER_MODE to 'api'."
        )


def _get_ffmpeg_executable() -> str:
    """
    Resolve an ffmpeg binary only when audio extraction is needed.
    """
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    if imageio_ffmpeg is None:
        raise RuntimeError(
            "No ffmpeg binary is available. Install ffmpeg on your system or "
            "`pip install imageio-ffmpeg` to enable audio extraction."
        )

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = Path(ffmpeg_exe).parent

    # Keep Whisper-compatible ffmpeg naming where possible without forcing it
    # during module import.
    ffmpeg_std = ffmpeg_dir / "ffmpeg.exe"
    if os.name == "nt" and not ffmpeg_std.exists():
        shutil.copy2(ffmpeg_exe, ffmpeg_std)

    os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
    return ffmpeg_exe


def extract_audio(video_path: str, output_dir: str) -> str:
    """
    Extract audio from video file using ffmpeg.
    Returns path to extracted .wav file.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / f"{video_path.stem}_audio.wav"

    print(f"[Audio] Extracting audio from {video_path.name}...")
    ffmpeg_exe = _get_ffmpeg_executable()

    cmd = [
        ffmpeg_exe,
        "-y",                    # overwrite output
        "-i", str(video_path),
        "-vn",                   # no video
        "-acodec", "pcm_s16le",  # WAV format
        "-ac", "1",              # mono
        "-ar", "16000",          # 16kHz (Whisper requirement)
        str(audio_path),
    ]

    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr.decode()}")

    print(f"[Audio] Audio extracted to: {audio_path}")
    return str(audio_path)


def transcribe_local(audio_path: str, progress_callback=None) -> dict:
    """
    Transcribe audio using local Whisper model.
    Returns dict with 'text', 'segments' (with timestamps), and 'language'.
    """
    _require_local_whisper_dependencies()
    whisper_model = os.getenv("WHISPER_MODEL", "medium")
    print(f"[Whisper] Loading local model: {whisper_model}")

    # Auto-detect GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Whisper] Using device: {device}")

    if device == "cpu":
        print("[Whisper] No GPU detected — using CPU. This may take 10-15 min for a 1hr video.")

    model = whisper.load_model(whisper_model, device=device)

    print(f"[Whisper] Transcribing {audio_path}...")

    result = model.transcribe(
        audio_path,
        verbose=False,
        word_timestamps=True,   # Get word-level timestamps for alignment
        task="transcribe"
    )

    print(f"[Whisper] Transcription complete. Language detected: {result.get('language', 'unknown')}")
    return result


def transcribe_api(audio_path: str) -> dict:
    """
    Transcribe audio using OpenAI Whisper API.
    Faster than local, costs ~$0.006/minute.
    Returns dict compatible with local Whisper output format.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print(f"[Whisper API] Transcribing via OpenAI API...")

    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"]
        )

    # Normalize to match local Whisper output format
    result = {
        "text": response.text,
        "language": response.language,
        "segments": [
            {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "words": []
            }
            for seg in (response.segments or [])
        ]
    }

    print(f"[Whisper API] Transcription complete.")
    return result


def transcribe(audio_path: str, progress_callback=None) -> dict:
    """
    Main transcription entry point. Routes to local or API based on config.
    """
    whisper_mode = os.getenv("WHISPER_MODE", "local").strip().lower()
    if whisper_mode == "api":
        return transcribe_api(audio_path)
    else:
        return transcribe_local(audio_path, progress_callback)


def get_transcript_segments(transcription_result: dict) -> list[dict]:
    """
    Extract clean segment list from Whisper output.
    Returns list of: { start, end, text }
    """
    segments = []
    for seg in transcription_result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        })
    return segments


if __name__ == "__main__":
    # Quick test
    import sys
    if len(sys.argv) < 2:
        print("Usage: python audio.py <video_path>")
        sys.exit(1)

    video = sys.argv[1]
    audio = extract_audio(video, "temp/")
    result = transcribe(audio)

    print("\n--- Transcript Preview ---")
    for seg in get_transcript_segments(result)[:5]:
        print(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
