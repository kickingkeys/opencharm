"""OpenCharm — main app. Connects to bracelet, processes captures with Claude."""

import asyncio
import time
import os

from ble_bridge import BraceletBridge
from claude_bridge import call_claude
from transcriber import transcribe
from feedback import send_success, send_error, send_busy
from config import CAPTURE_DIR


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}][{tag}] {msg}")


class OpenCharmApp:
    def __init__(self):
        self.bridge = BraceletBridge()
        self.pending_image = None
        self.pending_audio = None
        self.processing = False

    def _on_image(self, path):
        """Called when a complete image arrives from the bracelet."""
        log("app", f"Image received: {path}")
        self.pending_image = path
        self._try_process()

    def _on_audio(self, path):
        """Called when a complete audio clip arrives from the bracelet."""
        log("app", f"Audio received: {path}")
        self.pending_audio = path
        self._try_process()

    def _try_process(self):
        """Process image (+ optional audio) once we have what we need."""
        if self.processing:
            log("app", "Already processing, queuing...")
            return
        if self.pending_image is None:
            return

        self.processing = True
        image_path = self.pending_image
        audio_path = self.pending_audio
        self.pending_image = None
        self.pending_audio = None

        # Send busy ACK
        asyncio.get_event_loop().create_task(send_busy(self.bridge))

        # Transcribe audio if we have it
        transcript = None
        if audio_path and os.path.exists(audio_path):
            transcript = transcribe(audio_path)

        log("app", f"Calling Claude (transcript: {transcript or 'none'})...")

        def on_response(response, has_preview):
            log("claude", f"Response ({len(response)} chars, preview={has_preview})")
            log("claude", response[:200])

            # Send success ACK
            loop = asyncio.get_event_loop()
            if self.bridge.connected:
                loop.create_task(send_success(self.bridge))

            self.processing = False

        call_claude(image_path, transcript=transcript, callback=on_response)

    async def run(self):
        print("=" * 50)
        print("  OPENCHARM — Bracelet AI Bridge")
        print("=" * 50)

        os.makedirs(CAPTURE_DIR, exist_ok=True)

        # Register callbacks
        self.bridge.on_image(self._on_image)
        self.bridge.on_audio(self._on_audio)

        # Connect
        await self.bridge.connect()

        print()
        log("app", "Waiting for captures from bracelet...")
        log("app", "Press Ctrl+C to quit.")
        print("=" * 50)

        try:
            while self.bridge.connected:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            await self.bridge.disconnect()
            log("app", "Done.")


if __name__ == "__main__":
    app = OpenCharmApp()
    asyncio.run(app.run())
