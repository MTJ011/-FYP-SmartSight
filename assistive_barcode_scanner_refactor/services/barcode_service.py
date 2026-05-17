import cv2
import zxingcpp
from ultralytics import YOLO

VALID_LENGTHS = [8, 12, 13, 14]

model = YOLO("services/models/barcode_model.pt")

frame_counter = 0


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


def _decode(img):
    try:
        results = zxingcpp.read_barcodes(img)
        valid = []

        for r in results:
            code = r.text.strip()

            if is_valid_barcode(code):
                valid.append(code)

        return list(dict.fromkeys(valid))

    except Exception as e:
        print("Decode error:", e)
        return []


def _make_variants(roi):
    variants = []

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    variants.append(gray)

    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    sharp = cv2.addWeighted(gray, 2.0, blur, -1.0, 0)
    variants.append(sharp)

    thresh = cv2.threshold(
        sharp,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]
    variants.append(thresh)

    return variants


def _decode_roi(frame, x1, y1, x2, y2):
    h, w = frame.shape[:2]

    padding = 60

    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)

    roi = frame[y1:y2, x1:x2]

    if roi.size == 0:
        return []

    roi = cv2.resize(
        roi,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )

    for variant in _make_variants(roi):
        codes = _decode(variant)

        if codes:
            return codes

    return []


def detect_barcode(frame):
    global frame_counter

    frame_counter += 1

    # performance mode
    if frame_counter % 4 != 0:
        return []

    detected_codes = []

    try:
        results = model(frame, verbose=False)

        for r in results:
            if r.boxes is None:
                continue

            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()

            for i, box in enumerate(boxes):
                conf = float(confs[i])

                if conf < 0.30:
                    continue

                x1, y1, x2, y2 = map(int, box)

                codes = _decode_roi(frame, x1, y1, x2, y2)

                for code in codes:
                    if code not in detected_codes:
                        detected_codes.append(code)

                        h, w = frame.shape[:2]
                        px1 = max(0, x1 - 60)
                        py1 = max(0, y1 - 60)
                        px2 = min(w, x2 + 60)
                        py2 = min(h, y2 + 60)

                        cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 255, 0), 2)
                        cv2.putText(
                            frame,
                            code,
                            (px1, max(30, py1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2
                        )

    except Exception as e:
        print("YOLO error:", e)

    return detected_codes