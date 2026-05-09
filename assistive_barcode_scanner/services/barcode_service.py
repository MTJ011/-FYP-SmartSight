import cv2
import zxingcpp
from ultralytics import YOLO

# ── INIT ─────────────────────────────────────────────
VALID_LENGTHS = [12, 13, 14]

model = YOLO("services/models/barcode_model.pt")

frame_counter = 0

# ── OCR FALLBACK TRACKING ─────────────────────────────
OCR_FALLBACK_THRESHOLD = 30
_no_barcode_streak = 0
_ocr_last_result = None


# ── PREPROCESS ───────────────────────────────────────
def preprocess(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    _, thresh = cv2.threshold(
        sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh


# ── VALIDATION ───────────────────────────────────────
def is_valid_barcode(code):
    if not code:
        return False
    code = code.strip()
    if not code.isdigit():
        return False
    if len(code) not in VALID_LENGTHS:
        return False
    if len(set(code)) <= 2:
        return False
    return True


# ── ZXING-CPP DECODE ─────────────────────────────────
def _decode(img):
    """Decode barcodes from numpy array using zxing-cpp. No Java, no temp files."""
    try:
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        results = zxingcpp.read_barcodes(img)
        return [r.text.strip() for r in results if is_valid_barcode(r.text.strip())]
    except Exception as e:
        print(f"⚠️  zxing-cpp decode error: {e}")
        return []


# ── MAIN DETECTION ───────────────────────────────────
def detect_barcode(frame):
    """
    Detect barcode in frame.

    Returns:
        (detected_codes, ocr_product_name)
        - detected_codes   : list of barcode strings (may be empty)
        - ocr_product_name : string from OCR fallback, or None
    """
    global frame_counter, _no_barcode_streak, _ocr_last_result
    frame_counter += 1

    detected_codes = []
    ocr_product_name = None

    # ⚡ PERFORMANCE: skip frames
    if frame_counter % 3 != 0:
        return detected_codes, None

    try:
        # 🔥 STEP 1 — YOLO detection
        results = model(frame, verbose=False)

        for r in results:
            if r.boxes is None:
                continue

            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()

            for i, box in enumerate(boxes):
                if confs[i] < 0.3:
                    continue

                x1, y1, x2, y2 = map(int, box)
                roi = frame[y1:y2, x1:x2]
                if roi.size == 0:
                    continue

                roi = cv2.resize(roi, None, fx=2, fy=2)
                processed = preprocess(roi)
                codes = _decode(processed)

                for code in codes:
                    if code not in detected_codes:
                        detected_codes.append(code)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, code, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    except Exception as e:
        print("YOLO barcode error:", e)

    # ── 🔁 FULL FRAME FALLBACK ────────────────────────
    if not detected_codes:
        try:
            processed = preprocess(frame)
            codes = _decode(processed)
            for code in codes:
                if code not in detected_codes:
                    detected_codes.append(code)
        except Exception as e:
            print("Fallback decode error:", e)

    # ── 🔤 OCR FALLBACK ───────────────────────────────
    if detected_codes:
        _no_barcode_streak = 0
        _ocr_last_result = None
    else:
        _no_barcode_streak += 1

        if _no_barcode_streak >= OCR_FALLBACK_THRESHOLD:
            if _no_barcode_streak % OCR_FALLBACK_THRESHOLD == 0:
                try:
                    from services.ocr_service import detect_product_name_ocr, draw_ocr_result
                    from services.voice_service import speak

                    product_name = detect_product_name_ocr(frame)

                    if product_name and product_name != _ocr_last_result:
                        _ocr_last_result = product_name
                        ocr_product_name = product_name
                        draw_ocr_result(frame, product_name)
                        print(f"🔤 OCR fallback detected: {product_name}")

                        # ✅ Speak directly here — don't rely on search_mode timing
                        speak(f"No barcode found. I can see: {product_name}")

                except Exception as e:
                    print(f"OCR fallback error: {e}")

    return detected_codes, ocr_product_name