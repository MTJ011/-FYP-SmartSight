import cv2
import numpy as np


def find_barcode_region(frame):
    """
    Detects WHERE barcode likely is using edge density.
    Works even when barcode is tilted or unreadable.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    diff = cv2.subtract(
        cv2.convertScaleAbs(sobelx),
        cv2.convertScaleAbs(sobely)
    )

    blurred = cv2.blur(diff, (9, 9))
    _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 800:
        return None

    return cv2.boundingRect(largest)


def get_guidance(frame, region):
    """
    Chest mount specific — camera points forward/downward.
    Guides user to rotate/tilt product in their hands.
    Returns (instruction, clarity_score 0.0-1.0)
    """
    h, w = frame.shape[:2]
    x, y, rw, rh = region

    cx = x + rw // 2
    cy = y + rh // 2
    frame_cx = w // 2
    frame_cy = h // 2

    TOLERANCE = 70
    instructions = []
    penalties = 0

    # Chest mount: left/right means rotate product in hands
    if cx < frame_cx - TOLERANCE:
        instructions.append("rotate product to your right")
        penalties += 2
    elif cx > frame_cx + TOLERANCE:
        instructions.append("rotate product to your left")
        penalties += 2

    # Chest mount: up/down means tilt product face up or down
    if cy < frame_cy - TOLERANCE:
        instructions.append("tilt the barcode side toward you")
        penalties += 2
    elif cy > frame_cy + TOLERANCE:
        instructions.append("tilt the barcode side away from you")
        penalties += 2

    # Too far — user needs to bring product up toward chest camera
    if rw < w * 0.20:
        instructions.append("hold product closer to your chest")
        penalties += 3
    elif rw > w * 0.85:
        instructions.append("move product slightly away")
        penalties += 1

    # Barcode is sideways — needs 90 degree rotation
    if rh > rw * 1.5:
        instructions.append("turn product so barcode faces the camera")
        penalties += 3

    clarity = max(0.0, 1.0 - (penalties / 10.0))

    if not instructions:
        return "hold still", clarity

    return instructions[0], clarity  # one instruction at a time