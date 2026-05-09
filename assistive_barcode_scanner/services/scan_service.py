import time
from services.database_service import get_local_price, save_local_price
from services.product_service import get_food_product, get_beauty_product
from services.voice_service import speak

last_barcode = None
last_scan_time = 0

VALID_LENGTHS = [8, 12, 13, 14]


def process_barcode(barcode):
    global last_barcode, last_scan_time

    # ── STRICT VALIDATION ─────────────────────────────────────────
    if not barcode.isdigit():
        print(f"❌ Rejected (not digits): {barcode}")
        return

    if len(barcode) not in VALID_LENGTHS:
        print(f"❌ Rejected (wrong length {len(barcode)}): {barcode}")
        return

    current_time = time.time()
    if barcode == last_barcode and (current_time - last_scan_time) < 10:
        return

    last_barcode = barcode
    last_scan_time = current_time

    print(f"\n✅ Barcode accepted: {barcode} (length: {len(barcode)})")

    # ── LOCAL DB CHECK ────────────────────────────────────────────
    local_price, local_name, local_category = get_local_price(barcode)

    if local_price is not None:
        print(f"✅ Found locally: {local_name} — {local_price} PKR")
        speak(f"{local_name}. Price {local_price} rupees.")
        return

    # ── ONLINE API CHECK ──────────────────────────────────────────
    beauty = get_beauty_product(barcode)
    food = get_food_product(barcode)

    if beauty[0]:
        name, category, brand, _ = beauty
        print(f"✅ Found online (beauty): {name}")

    elif food[0]:
        name, category, brand, _ = food
        print(f"✅ Found online (food): {name}")

    else:
        # ── NOT FOUND — COLLECT FROM USER ────────────────────────
        print("\n⚠️  Product not found online or locally.")
        speak("Product not found. Please enter details in terminal.")

        name = _safe_input("Enter product name: ")
        category = _safe_input("Enter category: ")
        brand = _safe_input("Enter brand (or press Enter to skip): ", allow_empty=True)
        price = _safe_price_input()

        save_local_price(barcode, name, brand, category, price)
        print(f"✅ Saved: {name} — {price} PKR")
        speak(f"{name} saved. Price {price} rupees.")
        return

    # ── FOUND ONLINE — ASK PRICE ONLY ────────────────────────────
    print(f"   Name    : {name}")
    print(f"   Category: {category}")
    print(f"   Brand   : {brand}")
    speak(f"Found {name}. Please enter price in terminal.")

    price = _safe_price_input()
    save_local_price(barcode, name, brand, category, price)
    print(f"✅ Price saved: {name} — {price} PKR")
    speak(f"{name}. Price {price} rupees.")


def _safe_input(prompt, allow_empty=False):
    """Keeps asking until a valid answer is given"""
    while True:
        try:
            value = input(prompt).strip()
            if value or allow_empty:
                return value
            print("⚠️  This field cannot be empty.")
        except EOFError:
            time.sleep(0.5)


def _safe_price_input():
    """Keeps asking until a valid float is entered"""
    while True:
        try:
            raw = input("Enter price in PKR: ").strip()
            if not raw:
                print("⚠️  Price cannot be empty.")
                continue
            price = float(raw)
            if price < 0:
                print("⚠️  Price cannot be negative.")
                continue
            return price
        except ValueError:
            print("❌ Invalid price. Enter a number e.g. 250 or 99.5")
        except EOFError:
            time.sleep(0.5)