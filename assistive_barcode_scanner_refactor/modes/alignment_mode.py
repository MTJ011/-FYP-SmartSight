import time

from services.scan_context import scan_context
from services.voice_service import speak

HOLD_TIME = 1.0

first_seen_time = None


def reset():
    global first_seen_time
    first_seen_time = None


def run(frame):
    global first_seen_time

    if not scan_context.detected_barcode:
        reset()
        return "SEARCH", None

    now = time.time()

    if first_seen_time is None:
        first_seen_time = now
        speak("Hold still, scanning.")
        return "ALIGNMENT", None

    if now - first_seen_time >= HOLD_TIME:
        barcode = scan_context.detected_barcode
        reset()
        return "SCAN", barcode

    return "ALIGNMENT", None