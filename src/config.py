"""Configuration constants for OpenCharm."""

# --- BLE ---
BRACELET_NAME = "SpatialBracelet"
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
IMAGE_CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
AUDIO_CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"
COMMAND_CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26aa"
STATUS_CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26ab"

# --- Packet types (bracelet → host) ---
IMAGE_START = 0x01
IMAGE_CHUNK = 0x02
IMAGE_END = 0x03
AUDIO_START = 0x11
AUDIO_CHUNK = 0x12
AUDIO_END = 0x13
STATUS = 0x20

# --- Commands (host → bracelet) ---
ACK_SUCCESS = 0xA0
ACK_ERROR = 0xA1
ACK_BUSY = 0xA2

# --- Paths ---
CAPTURE_DIR = "/tmp/opencharm"
LATEST_IMAGE = "/tmp/opencharm/latest.jpg"
LATEST_AUDIO = "/tmp/opencharm/latest.wav"
HTML_PATH = "/tmp/opencharm/output.html"
PREVIEW_PATH = "/tmp/opencharm/preview.png"

# --- Claude ---
CLAUDE_PATH = "/Users/suryanarreddi/.local/bin/claude"
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PREVIEW_WIDTH = 900
PREVIEW_HEIGHT = 600
CLAUDE_TIMEOUT = 90

# --- Whisper ---
WHISPER_MODEL = "mlx-community/whisper-tiny"
