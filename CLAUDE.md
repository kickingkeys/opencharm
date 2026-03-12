# OpenCharm

Wearable AI bracelet host app. Receives images + audio from an ESP32S3 bracelet over BLE, processes with Claude vision, sends feedback back.

## Running

```bash
cd /Users/suryanarreddi/projects/experiments/prototypes/opencharm
python3 -u src/app.py
```

## Architecture

```
ESP32S3 bracelet → BLE → ble_bridge.py → claude_bridge.py → feedback.py → bracelet
                                        → transcriber.py ↗
```

## Files

- `src/app.py` — main event loop
- `src/ble_bridge.py` — BLE connection + chunk reassembly
- `src/claude_bridge.py` — sends image + transcript to Claude CLI
- `src/transcriber.py` — MLX Whisper audio → text
- `src/feedback.py` — sends ACK back to bracelet
- `src/config.py` — all constants, UUIDs, paths

## Status

MVP — waiting for ESP32 firmware from Fabri to test end-to-end.
OpenClaw integration planned for after MVP validation.
