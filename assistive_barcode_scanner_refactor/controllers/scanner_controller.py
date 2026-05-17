import cv2
import msvcrt

from services.camera_service import (
    open_camera,
    read_frame,
    release_camera
)

from services.scan_context import scan_context

from modes import (
    search_mode,
    rotation_mode,
    alignment_mode,
    scan_mode
)

current_mode = "SEARCH"


def reset_all():

    scan_context.reset()

    search_mode.reset()
    rotation_mode.reset()
    alignment_mode.reset()


def start_scanner():

    global current_mode

    cap = open_camera(
        camera_index=0,
        width=640,
        height=480
    )

    print("Assistive barcode scanner started.")
    print("Press r to reset scan.")
    print("Press q to quit.")

    reset_all()

    while True:

        frame = read_frame(cap)

        if frame is None:
            print("No frame received")
            break

        # ─────────────────────────────────────
        # SEARCH MODE
        # ─────────────────────────────────────
        if current_mode == "SEARCH":

            next_mode, _ = search_mode.run(frame)

            current_mode = next_mode

        # ─────────────────────────────────────
        # ROTATION MODE
        # ─────────────────────────────────────
        elif current_mode == "ROTATION":

            next_mode, _ = rotation_mode.run(frame)

            current_mode = next_mode

        # ─────────────────────────────────────
        # ALIGNMENT MODE
        # ─────────────────────────────────────
        elif current_mode == "ALIGNMENT":

            next_mode, _ = alignment_mode.run(frame)

            current_mode = next_mode

        # ─────────────────────────────────────
        # SCAN MODE
        # ─────────────────────────────────────
        elif current_mode == "SCAN":

            scan_mode.run()

            current_mode = "DONE"

        # ─────────────────────────────────────
        # DONE MODE
        # ─────────────────────────────────────
        elif current_mode == "DONE":

            cv2.putText(
                frame,
                "SCAN COMPLETE | Press R to scan again",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # ─────────────────────────────────────
        # DISPLAY
        # ─────────────────────────────────────
        cv2.putText(
            frame,
            f"MODE: {current_mode}",
            (10, 470),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.imshow(
            "Assistive Barcode Scanner",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if msvcrt.kbhit():

            pressed = msvcrt.getch().decode(
                "utf-8",
                errors="ignore"
            ).lower()

            if pressed:
                key = ord(pressed)

        # quit
        if key == ord("q"):
            break

        # reset
        elif key == ord("r"):

            print("Resetting scanner...")

            reset_all()

            current_mode = "SEARCH"

    release_camera(cap)