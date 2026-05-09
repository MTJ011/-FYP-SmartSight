import cv2
from services.camera_service import open_camera
from services.voice_service import speak
from services.beep_service import start_beep_loop, stop_beep
from services.voice_command_service import start_listening, get_command
from services.barcode_service import detect_barcode

from modes import search_mode, scan_mode, rotation_mode, alignment_mode

# ── GLOBAL STATE ───────────────────────────────────────────────
scan_completed = False
current_mode = "SEARCH"
detected_barcode = None
last_result = None

def start_scanner():
    global current_mode, detected_barcode, last_result, scan_completed

    start_listening()
    start_beep_loop()

    cap = open_camera()

    speak(
        "Assistive barcode scanner ready. "
        "Hold a product in front of you and I will find the barcode. "
        "Say help anytime for instructions."
    )

    print("Scanner started")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ── 🔴 STOP LOOP AFTER SUCCESS ───────────────────────────
        if scan_completed:
            cv2.putText(frame, "SCAN COMPLETE — say 'scan' for next",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

            cmd = get_command()
            if cmd == "scan":
                scan_completed = False
                current_mode = "SEARCH"
                speak("Ready for next product")

            cv2.imshow("Assistive Barcode Scanner", frame)
            # Use waitKey here as well to keep the window responsive during completion state
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        # ── GLOBAL VOICE COMMANDS ────────────────────────────────
        cmd = get_command()

        if cmd == "repeat":
            if last_result:
                speak(last_result)
            else:
                speak("No result yet. Hold a product in front of the camera.")

        elif cmd == "scan" and current_mode == "PAUSED":
            current_mode = "SEARCH"
            speak("Scanning resumed.")

        # ── MODE LOGIC ──────────────────────────────────────────

        # 🟢 SEARCH MODE
        if current_mode == "SEARCH":
            next_mode, barcode = search_mode.run(frame)

            if next_mode == "SCAN" and barcode:
                detected_barcode = barcode
                rotation_mode.reset()
                current_mode = "SCAN"

            elif next_mode == "ROTATION":
                rotation_mode.reset()
                current_mode = "ROTATION"

            elif next_mode == "PAUSED":
                current_mode = "PAUSED"

            else:
                current_mode = "SEARCH"

        # 🟡 ROTATION MODE
        elif current_mode == "ROTATION":
            status, barcode = rotation_mode.run(frame)

            if status == "FOUND":
                detected_barcode = barcode
                rotation_mode.reset()
                speak("Barcode found")
                current_mode = "SCAN"

        # 🔵 ALIGNMENT MODE
        elif current_mode == "ALIGNMENT":
            next_mode, _ = alignment_mode.run(frame)

            if next_mode == "SCAN":
                current_mode = "SCAN"

            elif next_mode == "SEARCH":
                current_mode = "SEARCH"

        # 🔴 SCAN MODE
        elif current_mode == "SCAN":
            result = scan_mode.run(detected_barcode)

            if result:
                last_result = result
                scan_completed = True  # ✅ HARD STOP

            rotation_mode.reset()
            detected_barcode = None
            current_mode = "PAUSED"  # ✅ DO NOT RETURN TO SEARCH

        # ⏸ PAUSED MODE
        elif current_mode == "PAUSED":
            cv2.putText(frame, "PAUSED — say 'Scan' to resume",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)

        # ── DISPLAY ─────────────────────────────────────────────
        color = (
            (0, 255, 0) if current_mode == "SCAN" else
            (255, 0, 0) if current_mode == "ALIGNMENT" else
            (0, 165, 255) if current_mode == "ROTATION" else
            (0, 0, 255) if current_mode == "PAUSED" else
            (0, 255, 255)
        )

        cv2.putText(frame, f"Mode: {current_mode}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Assistive Barcode Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            stop_beep()
            break

    cap.release()
    cv2.destroyAllWindows()