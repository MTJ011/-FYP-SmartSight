import cv2
import re
import easyocr

_reader = None


def _get_reader():
    global _reader

    if _reader is None:
        print("Loading EasyOCR once...")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        print("OCR ready")

    return _reader


def clean_text(text):
    text = re.sub(r"[^a-zA-Z0-9\s.'&-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def capture_product_ocr(frame, min_confidence=0.35):
    reader = _get_reader()

    small = cv2.resize(frame, (640, 480))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    results = reader.readtext(gray, detail=1, paragraph=False)

    texts = []

    for _, text, conf in results:
        if conf < min_confidence:
            continue

        cleaned = clean_text(text)

        if len(cleaned) < 3:
            continue

        texts.append(cleaned)

    if not texts:
        return None

    unique_texts = list(dict.fromkeys(texts))
    return " ".join(unique_texts)