"""Claude Bridge — sends bracelet captures to Claude CLI for vision processing."""

import subprocess
import os
import threading

from config import (
    CLAUDE_PATH,
    CHROME_PATH,
    HTML_PATH,
    PREVIEW_PATH,
    PREVIEW_WIDTH,
    PREVIEW_HEIGHT,
    CLAUDE_TIMEOUT,
)

SYSTEM_CONTEXT = """You are the AI brain of a wearable spatial computing bracelet.
The user wears a bracelet with a camera on the underside of their wrist.
When activated, the bracelet captures what the user holds their hand over and sends it to you.

You see the captured image and help the user understand, analyze, or act on what they're looking at.

Rules:
- Describe what you see clearly and concisely.
- If you see a sketch, wireframe, or diagram — interpret it and offer to generate code/HTML if appropriate.
- If you see text, read it back.
- If you see a physical object or circuit, describe it and offer help.
- If the user provided a voice transcript, factor that into your response.
- Keep responses short — this goes back to a wearable with limited feedback.
- If generating HTML, save to /tmp/opencharm/output.html (single self-contained file, inline CSS).
"""


def render_html_to_png():
    """Render output HTML to PNG via Chrome headless."""
    if not os.path.exists(HTML_PATH):
        return False
    try:
        subprocess.run(
            [CHROME_PATH, "--headless", f"--screenshot={PREVIEW_PATH}",
             f"--window-size={PREVIEW_WIDTH},{PREVIEW_HEIGHT}",
             "--disable-gpu", "--hide-scrollbars",
             f"file://{HTML_PATH}"],
            capture_output=True, timeout=15,
        )
        return os.path.exists(PREVIEW_PATH)
    except Exception:
        return False


def call_claude(image_path, transcript=None, callback=None):
    """Call Claude CLI with an image and optional transcript.

    Runs in a background thread. Calls callback(response_text, has_preview) when done.
    """
    def _run():
        prompt_parts = [SYSTEM_CONTEXT, ""]
        prompt_parts.append(f"Read the image at {image_path} to see what the user captured.")

        if transcript and transcript.strip():
            prompt_parts.append(f'\nThe user said: "{transcript}"')

        prompt_parts.append("\nWhat do you see? Help the user. Be concise.")

        prompt = "\n".join(prompt_parts)

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        try:
            old_mtime = os.path.getmtime(HTML_PATH) if os.path.exists(HTML_PATH) else 0

            result = subprocess.run(
                [CLAUDE_PATH, "-p", "--output-format", "text",
                 "--allowedTools", "Read,Write,Bash"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=CLAUDE_TIMEOUT,
                env=env,
                cwd=os.path.dirname(os.path.dirname(__file__)),
            )

            response = result.stdout.strip()
            lines = [l for l in response.split("\n") if not l.startswith("[WARN]")]
            response = "\n".join(lines)

            new_mtime = os.path.getmtime(HTML_PATH) if os.path.exists(HTML_PATH) else 0
            html_updated = new_mtime > old_mtime

            has_preview = False
            if html_updated:
                has_preview = render_html_to_png()

            if callback:
                callback(response if response else "No response.", has_preview)

        except subprocess.TimeoutExpired:
            if callback:
                callback(f"Claude timed out ({CLAUDE_TIMEOUT}s).", False)
        except Exception as e:
            if callback:
                callback(f"Error: {e}", False)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
