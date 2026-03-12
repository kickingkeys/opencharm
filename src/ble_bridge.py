"""BLE Bridge — connects to the ESP32S3 bracelet and reassembles chunked data."""

import os
import time
import asyncio
from bleak import BleakClient, BleakScanner

from config import (
    BRACELET_NAME,
    IMAGE_CHAR_UUID,
    AUDIO_CHAR_UUID,
    COMMAND_CHAR_UUID,
    STATUS_CHAR_UUID,
    IMAGE_START,
    IMAGE_CHUNK,
    IMAGE_END,
    AUDIO_START,
    AUDIO_CHUNK,
    AUDIO_END,
    ACK_SUCCESS,
    ACK_ERROR,
    ACK_BUSY,
    CAPTURE_DIR,
    LATEST_IMAGE,
    LATEST_AUDIO,
)


def log(tag, msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}][{tag}] {msg}")


class BraceletBridge:
    def __init__(self):
        self.client = None
        self.connected = False

        # Image reassembly
        self.image_buffer = bytearray()
        self.image_expected = 0
        self.image_received = 0

        # Audio reassembly
        self.audio_buffer = bytearray()
        self.audio_expected = 0
        self.audio_received = 0

        # Callbacks
        self._on_image_callback = None
        self._on_audio_callback = None

        os.makedirs(CAPTURE_DIR, exist_ok=True)

    def on_image(self, callback):
        """Register callback for when a complete image is received. callback(path)."""
        self._on_image_callback = callback

    def on_audio(self, callback):
        """Register callback for when a complete audio clip is received. callback(path)."""
        self._on_audio_callback = callback

    async def connect(self):
        """Scan for and connect to the bracelet."""
        log("ble", f"Scanning for {BRACELET_NAME}...")
        device = await BleakScanner.find_device_by_name(BRACELET_NAME, timeout=10)

        if device is None:
            raise RuntimeError(f"Bracelet '{BRACELET_NAME}' not found. Is it awake?")

        log("ble", f"Found {device.name} ({device.address}). Connecting...")
        self.client = BleakClient(device)
        await self.client.connect()
        self.connected = True
        log("ble", "Connected!")

        # Subscribe to notifications
        await self.client.start_notify(IMAGE_CHAR_UUID, self._on_image_data)
        await self.client.start_notify(AUDIO_CHAR_UUID, self._on_audio_data)
        await self.client.start_notify(STATUS_CHAR_UUID, self._on_status)
        log("ble", "Subscribed to image, audio, status characteristics.")

    async def send_ack(self, ack_type=ACK_SUCCESS):
        """Send an ACK/command back to the bracelet."""
        if self.client and self.connected:
            await self.client.write_gatt_char(COMMAND_CHAR_UUID, bytes([ack_type]))
            log("ble", f"Sent ACK: 0x{ack_type:02X}")

    async def disconnect(self):
        """Disconnect from the bracelet."""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            log("ble", "Disconnected.")

    def _on_image_data(self, sender, data):
        """Handle incoming image packets."""
        if len(data) < 5:
            return

        packet_type = data[0]
        seq = int.from_bytes(data[1:3], "little")
        total = int.from_bytes(data[3:5], "little")
        payload = data[5:]

        if packet_type == IMAGE_START:
            self.image_buffer = bytearray()
            self.image_expected = total
            self.image_received = 0
            log("ble", f"Image transfer started ({total} packets)")

        elif packet_type == IMAGE_CHUNK:
            self.image_buffer.extend(payload)
            self.image_received += 1
            if self.image_received % 20 == 0:
                pct = (self.image_received / max(self.image_expected, 1)) * 100
                log("ble", f"Image: {pct:.0f}% ({self.image_received}/{self.image_expected})")

        elif packet_type == IMAGE_END:
            self.image_buffer.extend(payload)
            self._save_image()

    def _save_image(self):
        """Save reassembled image and fire callback."""
        ts = time.strftime("%Y%m%d_%H%M%S")
        timestamped = os.path.join(CAPTURE_DIR, f"capture_{ts}.jpg")

        with open(timestamped, "wb") as f:
            f.write(self.image_buffer)
        with open(LATEST_IMAGE, "wb") as f:
            f.write(self.image_buffer)

        size_kb = len(self.image_buffer) / 1024
        log("ble", f"Image complete: {size_kb:.0f} KB → {timestamped}")

        if self._on_image_callback:
            self._on_image_callback(LATEST_IMAGE)

    def _on_audio_data(self, sender, data):
        """Handle incoming audio packets."""
        if len(data) < 5:
            return

        packet_type = data[0]
        payload = data[5:]

        if packet_type == AUDIO_START:
            self.audio_buffer = bytearray()
            self.audio_expected = int.from_bytes(data[3:5], "little")
            self.audio_received = 0
            log("ble", "Audio transfer started")

        elif packet_type == AUDIO_CHUNK:
            self.audio_buffer.extend(payload)
            self.audio_received += 1

        elif packet_type == AUDIO_END:
            self.audio_buffer.extend(payload)
            self._save_audio()

    def _save_audio(self):
        """Save reassembled audio and fire callback."""
        with open(LATEST_AUDIO, "wb") as f:
            f.write(self.audio_buffer)

        size_kb = len(self.audio_buffer) / 1024
        log("ble", f"Audio complete: {size_kb:.0f} KB")

        if self._on_audio_callback:
            self._on_audio_callback(LATEST_AUDIO)

    def _on_status(self, sender, data):
        """Handle status updates from bracelet."""
        if data:
            log("status", f"Bracelet status: {data.hex()}")
