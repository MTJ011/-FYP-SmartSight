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
KNOWN_PRODUCTS = [
    # Lays
    "Lay's French Cheese",
    "Lay's Masala",
    "Lay's Yogurt and Herb",
    "Lay's Wavy Texas BBQ",
    "Lay's Classic",
    "Lay's Salt and Vinegar",

    # Pringles
    "Pringles Original",
    "Pringles Sour Cream",
    "Pringles BBQ",
    "Pringles Cheddar",

    # Cheetos
    "Cheetos Crunchy",
    "Cheetos Puffs",
    "Cheetos Flamin Hot",
    "Cheetos Ocean Safari",
    "Cheetos Twisted",

    # Drinks
    "Coca Cola",
    "Pepsi",
    "7UP",
    "Sprite",
    "Fanta",
    "Mountain Dew",
    "Sting Energy Drink",

    # Nestle drinks
    "Nestle Fruita Vitals Apple Nectar",
    "Nestle Fruita Vitals Mango Nectar",
    "Nestle Fruita Vitals Orange Juice",
    "Nestle Fruita Vitals Red Grapes",
    "Nestle Fruita Vitals Chaunsa Nectar",

    # Dairy
    "Nestle Milkpak",
    "Olpers Milk",
    "Nurpur Milk",
    "Good Milk",

    # Biscuits
    "Oreo",
    "Prince Biscuit",
    "TUC Crackers",
    "Sooper Biscuit",
    "Rio Biscuit",
    "Bonus Biscuit",
    "Marvi Biscuit",

    # Chocolates
    "KitKat",
    "Dairy Milk",
    "Snickers",
    "Bounty",
    "Mars",

    # Other snacks
    "Kurkure Masala Munch",
    "Doritos Nacho Cheese",
    "Doritos Cool Ranch",
    "Nimcolla Mix Nimco",
    "Nimco Mix",
    "Kolson Nimco",
    "Super Crisp",
    "Peek Freans",
    "Shan Masala",
    "National Foods",
    "Knorr Noodles",
    "Indomie Noodles",

    # Slanty
    "Slanty Vegetable",
    "Slanty Jalapeno",
    "Slanty Salted",
]


BRAND_ONLY_WORDS = {
    "nestle", "lays", "lay", "pringles", "cheetos",
    "pepsi", "sprite", "fanta", "oreo", "tuc",
    "knorr", "shan", "national", "kolson", "slanty"
}


# ── ALIAS MATCHING ──────────────────────────────────────────────────────
PRODUCT_ALIASES = {
    "Slanty Vegetable": [
        "SLANTY", "SLAHTY", "SLAHTV", "CLANTY", "SLANFY", "SLANTI",
        "VEGETABLE", "VCGCLABLE", "VCGCTABLE", "VEGCLABLE"
    ],
    "Nestle Fruita Vitals Apple Nectar": [
        "FRUITA VITALS", "FRUITA", "VITALS", "NECTAR", "NECIAR", "APPLE NECTAR"
    ],
}


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
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\x20-\x7E]", " ", text)
    text = re.sub(r"[^a-zA-Z0-9'\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_for_match(text: str) -> str:
    text = text.lower()
    text = text.replace("'", "")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _words(text: str):
    return set(_normalize_for_match(text).split())


def _is_noise(text: str) -> bool:
    return bool(_NOISE_RE.search(text.strip()))


def _fix_common_ocr_errors(text: str) -> str:
    replacements = {
        # Cheetos
        "heetos": "Cheetos",
        "cheeto": "Cheetos",
        "eetos": "Cheetos",
        "chetos": "Cheetos",

        # Lays
        "Lays": "Lay's",
        "lay s": "Lay's",

        # Cheese
        "Cheeve": "Cheese",
        "Cheve": "Cheese",
        "Checse": "Cheese",
        "Cheee": "Cheese",

        # Coca Cola
        "Coka Cola": "Coca Cola",
        "Coca-Cola": "Coca Cola",

        # Pringles
        "Pringel": "Pringles",
        "Pringle ": "Pringles ",

        # Ocean Safari
        "Oceen": "Ocean",
        "Occan": "Ocean",
        "Safar1": "Safari",

        # Fruita Vitals
        "FRUITA": "Fruita",
        "VITALS": "Vitals",
        "VTALS": "Vitals",
        "VLS": "Vitals",
        "BUITA": "Fruita",
        "RUITA": "Fruita",
        "NECTAR": "Nectar",
        "NECIAR": "Nectar",
        "NecTAR": "Nectar",

        # Slanty
        "SLAHTY": "SLANTY",
        "SLAHTV": "SLANTY",
        "CLANTY": "SLANTY",
        "SLANFY": "SLANTY",
        "SLANTI": "SLANTY",
        "Vcgclable": "Vegetable",
        "Vcgctable": "Vegetable",
        "Vegclable": "Vegetable",
    }

    for wrong, correct in replacements.items():
        text = re.sub(re.escape(wrong), correct, text, flags=re.IGNORECASE)

    return text


def _has_enough_overlap(ocr_text: str, product_name: str) -> bool:
    ocr_words = _words(ocr_text)
    product_words = _words(product_name)
    overlap = ocr_words.intersection(product_words)

    # Small products like Oreo, Pepsi, Sprite can match by one strong word.
    if len(product_words) <= 2:
        return len(overlap) >= 1

    # Multi-word products need at least 2 matching words.
    return len(overlap) >= 2


def _is_brand_only_match(ocr_text: str, product_name: str) -> bool:
    ocr_words = _words(ocr_text)
    product_words = _words(product_name)
    overlap = ocr_words.intersection(product_words)

    if len(overlap) == 1:
        only_word = list(overlap)[0]
        return only_word in BRAND_ONLY_WORDS

    return False


# ── IMAGE PREPROCESSING ────────────────────────────────────────────────
def _preprocess_for_ocr(frame):
    variants = []
    h, w = frame.shape[:2]

    # Upscale small frames for better OCR.
    scale = max(1, 900 // w)
    if scale > 1:
        frame = cv2.resize(frame, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    variants.append(clahe.apply(gray))

    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    sharpened = cv2.addWeighted(gray, 1.8, blurred, -0.8, 0)
    variants.append(sharpened)

    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(otsu)
    variants.append(cv2.bitwise_not(otsu))

    # Original colored frame also helps sometimes.
    variants.append(frame)

    return variants


# ── ALIAS DETECTION ─────────────────────────────────────────────────────
def _alias_match(text: str):
    upper_text = text.upper()

    # Special case: Slanty often appears clearly but vegetable is noisy.
    slanty_aliases = ["SLANTY", "SLAHTY", "SLAHTV", "CLANTY", "SLANFY", "SLANTI"]
    vegetable_aliases = ["VEGETABLE", "VCGCLABLE", "VCGCTABLE", "VEGCLABLE"]

    has_slanty = any(alias in upper_text for alias in slanty_aliases)
    has_vegetable = any(alias in upper_text for alias in vegetable_aliases)

    if has_slanty and has_vegetable:
        return "Slanty Vegetable", 95

    if has_slanty:
        # Return brand-level result instead of garbage OCR.
        return "Slanty Vegetable", 88

    for product_name, aliases in PRODUCT_ALIASES.items():
        hits = sum(1 for alias in aliases if alias.upper() in upper_text)
        if hits >= 2:
            return product_name, 90

    return None, 0


# ── FUZZY MATCHING ─────────────────────────────────────────────────────
def _fuzzy_match(text: str):
    """
    Safer fuzzy matching:
    - Matches full OCR phrase first.
    - Blocks single brand-only false positives.
    - Requires word overlap.
    """
    if not text or len(text.strip()) < 3:
        return None, 0

    fixed_text = _fix_common_ocr_errors(text)
    normalized_text = _normalize_for_match(fixed_text)

    candidates = []
    scorers = [
        fuzz.token_set_ratio,
        fuzz.token_sort_ratio,
        fuzz.WRatio,
        fuzz.partial_ratio,
    ]

    for scorer in scorers:
        match = process.extractOne(normalized_text, KNOWN_PRODUCTS, scorer=scorer)

        if not match:
            continue

        product_name, score, _ = match

        if not _has_enough_overlap(fixed_text, product_name):
            continue

        if _is_brand_only_match(fixed_text, product_name):
            continue

        candidates.append((product_name, score))

    if not candidates:
        return None, 0

    best_product, best_score = max(candidates, key=lambda x: x[1])

    if best_score >= 72:
        return best_product, best_score

    return None, best_score


# ── MAIN OCR DETECTOR ──────────────────────────────────────────────────
def detect_product_name_ocr(frame, min_confidence=0.35):
    reader = _get_reader()
    variants = _preprocess_for_ocr(frame)
    collected_texts = []

    for img in variants:
        try:
            results = reader.readtext(img, detail=1, paragraph=False)
        except Exception as e:
            print(f"⚠️ OCR error: {e}")
            continue

        for (_, text, conf) in results:
            if conf < min_confidence:
                continue

            cleaned = _clean_text(text)
            cleaned = _fix_common_ocr_errors(cleaned)

            if not cleaned or _is_noise(cleaned):
                continue

            collected_texts.append(cleaned)

    if not collected_texts:
        print("❌ No OCR text detected.")
        return None

    unique_texts = list(dict.fromkeys(collected_texts))
    combined_text = " ".join(unique_texts)
    combined_text = _fix_common_ocr_errors(combined_text)

    print(f"🔤 OCR combined text: {combined_text}")

    # 1. Alias match first. This fixes cases like:
    # SLANTY SLAHTV CLANTY Vcgclable → Slanty Vegetable
    alias_product, alias_score = _alias_match(combined_text)
    if alias_product:
        print(f"✅ OCR alias match: {alias_product} ({alias_score})")
        return alias_product

    # 2. Full phrase fuzzy matching.
    # Do NOT match single tokens first because it causes wrong matches like:
    # Nestle → Nestle Milkpak
    product, score = _fuzzy_match(combined_text)
    if product:
        print(f"✅ OCR matched product: {product} ({score})")
        return product

    # 3. Phrase fallback: useful 2-5 word chunks only.
    words = combined_text.split()
    phrase_candidates = []

    for size in range(5, 1, -1):
        for i in range(len(words) - size + 1):
            phrase = " ".join(words[i:i + size])
            product, score = _fuzzy_match(phrase)

            if product:
                phrase_candidates.append((product, score, phrase))

    if phrase_candidates:
        best_product, best_score, best_phrase = max(phrase_candidates, key=lambda x: x[1])
        print(f"✅ Phrase match: '{best_phrase}' → {best_product} ({best_score})")
        return best_product

    # IMPORTANT:
    # Never return combined_text here.
    # Returning raw OCR text makes the speaker say garbage like:
    # "SLANTY SLAHTV CLANTY Vcgclable"
    print("⚠️ No strong database match. Ignoring noisy OCR text.")
    return None


# ── DRAW RESULT ────────────────────────────────────────────────────────
def draw_ocr_result(frame, product_name):
    overlay = frame.copy()
    h, w = frame.shape[:2]

    cv2.rectangle(overlay, (0, h - 50), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

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
