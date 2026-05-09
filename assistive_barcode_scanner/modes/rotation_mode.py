import time
from services.voice_service import speak
from services.barcode_service import detect_barcode

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
INITIAL_SCAN_TIME = 10
STEP_INTERVAL = 10

instructions = [
    "Bring the product closer to the camera",
    "Move the product slightly to the left",
    "Move the product slightly back",
    "Move the product slightly to the right",
    "Move the product slightly away from the camera"
]

sides = ["front", "side 2", "side 3", "side 4", "top", "bottom"]

# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────
current_side = 0
current_step = -1
last_time = 0
mode = "INITIAL_SCAN"


def reset():
    global current_side, current_step, last_time, mode
    current_side = 0
    current_step = -1
    last_time = 0
    mode = "INITIAL_SCAN"


def run(frame):
    global current_side, current_step, last_time, mode

    current_time = time.time()

    # ── 🔍 ALWAYS TRY DETECT FIRST ─────────────
    barcodes, _ = detect_barcode(frame)   # ← unpack tuple, discard ocr_name
    if barcodes:
        return "FOUND", barcodes[0]

    # ── INITIAL SCAN (10s SILENT) ─────────────
    if mode == "INITIAL_SCAN":
        if last_time == 0:
            last_time = current_time
            speak(f"Scanning {sides[current_side]} side")

        if current_time - last_time > INITIAL_SCAN_TIME:
            mode = "GUIDE"
            current_step = 0
            last_time = current_time

    # ── GUIDED STEPS ──────────────────────────
    elif mode == "GUIDE":
        if current_time - last_time > STEP_INTERVAL:

            # 🔍 SCAN BEFORE NEXT INSTRUCTION
            barcodes, _ = detect_barcode(frame)   # ← unpack tuple
            if barcodes:
                return "FOUND", barcodes[0]

            if current_step < len(instructions):
                speak(instructions[current_step])
                current_step += 1
                last_time = current_time
            else:
                mode = "ROTATE"
                last_time = current_time

    # ── ROTATE ────────────────────────────────
    elif mode == "ROTATE":
        if current_side < len(sides) - 1:
            speak("Rotate the product ninety degrees")

            current_side += 1
            mode = "INITIAL_SCAN"
            current_step = -1
            last_time = current_time
        else:
            speak("I could not find a barcode. Please try again.")
            reset()

    return "ROTATION", None