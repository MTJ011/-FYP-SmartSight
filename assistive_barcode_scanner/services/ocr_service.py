import cv2
import re
import unicodedata
import easyocr
from rapidfuzz import process, fuzz

# ── INIT ────────────────────────────────────────────────────────────────
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        print("🔤 Loading EasyOCR model (first time only)...")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        print("✅ EasyOCR ready.")
    return _reader


# ── PRODUCT DATABASE ────────────────────────────────────────────────────
# Add products from your SQLite database here or fetch dynamically later
KNOWN_PRODUCTS = [
    "Lay's French Cheese",
    "Lay's Masala",
    "Lay's Yogurt and Herb",
    "Lay's Wavy Texas BBQ",
    "Pringles Original",
    "Pringles Sour Cream",
    "Coca Cola",
    "Pepsi",
    "Nestle Milkpak",
    "Olpers Milk",
]


# ── NOISE FILTERS ───────────────────────────────────────────────────────
_NOISE_PATTERNS = [
    r"^(net|wt|weight|oz|ml|kg|g|lb|lbs|fl|www\.|http).*",
    r"^\d+(\.\d+)?\s*(g|kg|ml|l|oz|lb|mg|calories|cal|kcal)$",
    r"^[^a-zA-Z]*$",
    r"^\W+$",
    r"^.{1,2}$",
    r"ingredients?",
    r"nutrition(al)?",
    r"serving(s)?",
    r"daily value",
    r"contains?",
    r"manufactured",
    r"distributed",
    r"allergen",
    r"(best before|exp(iry)?|use by|mfg)",
    r"^\d{4,}$",
]

_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)


# ── HELPERS ─────────────────────────────────────────────────────────────
def _clean_text(text: str) -> str:
    """Normalize OCR text."""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\x20-\x7E]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_noise(text: str) -> bool:
    return bool(_NOISE_RE.search(text.strip()))


def _fix_common_ocr_errors(text: str) -> str:
    """Fix frequent OCR mistakes."""
    replacements = {
        "Lays": "Lay's",
        "Lays": "Lay's",
        "Cheeve": "Cheese",
        "Cheve": "Cheese",
        "Checse": "Cheese",
        "Coka Cola": "Coca Cola",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text


# ── IMAGE PREPROCESSING ────────────────────────────────────────────────
def _preprocess_for_ocr(frame):
    """
    Generate multiple image variants for OCR.
    """
    variants = []

    h, w = frame.shape[:2]

    # upscale if small
    if w < 640:
        frame = cv2.resize(
            frame,
            (w * 2, h * 2),
            interpolation=cv2.INTER_CUBIC
        )

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 1. CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )
    clahe_img = clahe.apply(gray)
    variants.append(clahe_img)

    # 2. Sharpen
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    variants.append(sharpened)

    # 3. Original frame
    variants.append(frame)

    return variants


# ── MAIN OCR DETECTOR ──────────────────────────────────────────────────
def detect_product_name_ocr(frame, min_confidence=0.4):
    """
    Detect product name from image using OCR fallback.
    Returns matched product or combined OCR text.
    """
    reader = _get_reader()
    variants = _preprocess_for_ocr(frame)

    collected_texts = []

    for img in variants:
        try:
            results = reader.readtext(
                img,
                detail=1,
                paragraph=False
            )
        except Exception as e:
            print(f"⚠️ OCR error: {e}")
            continue

        for (_, text, conf) in results:
            if conf < min_confidence:
                continue

            cleaned = _clean_text(text)

            if not cleaned or _is_noise(cleaned):
                continue

            collected_texts.append(cleaned)

    if not collected_texts:
        print("❌ No OCR text detected.")
        return None

    # remove duplicates while preserving order
    unique_texts = list(dict.fromkeys(collected_texts))

    combined_text = " ".join(unique_texts)
    combined_text = _fix_common_ocr_errors(combined_text)

    print(f"🔤 OCR combined text: {combined_text}")

    # fuzzy match against known products
    match = process.extractOne(
        combined_text,
        KNOWN_PRODUCTS,
        scorer=fuzz.token_sort_ratio
    )

    if match:
        product_name, score, _ = match
        print(f"✅ OCR matched product: {product_name} ({score})")

        if score > 45:
            return product_name

    print("⚠️ No strong database match. Returning OCR text.")
    return combined_text


# ── DRAW RESULT ────────────────────────────────────────────────────────
def draw_ocr_result(frame, product_name):
    """Overlay OCR result on frame."""
    overlay = frame.copy()
    h, w = frame.shape[:2]

    cv2.rectangle(
        overlay,
        (0, h - 50),
        (w, h),
        (0, 0, 0),
        -1
    )

    cv2.addWeighted(
        overlay,
        0.5,
        frame,
        0.5,
        0,
        frame
    )

    cv2.putText(
        frame,
        f"OCR: {product_name}",
        (10, h - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )

    return frame