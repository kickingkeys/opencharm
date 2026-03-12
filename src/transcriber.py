"""Transcriber — converts audio clips to text using MLX Whisper."""

import time

from config import WHISPER_MODEL


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}][{tag}] {msg}")


def transcribe(audio_path):
    """Transcribe an audio file to text. Returns the transcript string."""
    try:
        import mlx_whisper

        log("whisper", f"Transcribing {audio_path}...")
        start = time.time()

        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=WHISPER_MODEL,
        )
        text = result["text"].strip()
        elapsed = time.time() - start

        log("whisper", f"Done in {elapsed:.1f}s: \"{text}\"")
        return text

    except ImportError:
        log("whisper", "mlx-whisper not installed. Run: pip install mlx-whisper")
        return ""
    except Exception as e:
        log("whisper", f"Transcription failed: {e}")
        return ""
