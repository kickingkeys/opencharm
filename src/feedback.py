"""Feedback — sends ACK/status back to bracelet via BLE."""

import asyncio
from config import ACK_SUCCESS, ACK_ERROR, ACK_BUSY


async def send_success(bridge):
    """Tell bracelet: done, green LEDs + haptic."""
    await bridge.send_ack(ACK_SUCCESS)


async def send_error(bridge):
    """Tell bracelet: something failed, red LEDs."""
    await bridge.send_ack(ACK_ERROR)


async def send_busy(bridge):
    """Tell bracelet: processing, blue breathing."""
    await bridge.send_ack(ACK_BUSY)
