from services.voice_service import speak
from models.product_model import get_product_by_barcode
from services.database_service import get_local_price, save_local_price
from services.product_service import get_product_info, format_product_for_speech


def run(barcode):
    print(f"🔍 Looking up barcode: {barcode}")

    # ── STEP 1: CHECK PRODUCTS.DB ───────────────────────────────
    product = get_product_by_barcode(barcode)

    if product:
        name = product["name"]
        category = product["category"]
        price = product["price"]

        result = f"{name}. Category: {category}. Price: {price} rupees."
        print(f"✅ Found in products.db: {result}")
        speak(result)  # ✅ Single speak — terminal and voice stay in sync
        return result

    # ── STEP 2: CHECK LOCAL PRICE CACHE ─────────────────────────
    price, name, category = get_local_price(barcode)

    if name:
        result = f"{name}. Category: {category}. Price: {price} rupees."
        print(f"✅ Found in local cache: {result}")
        speak(result)  # ✅ Single speak
        return result

    # ── STEP 3: FETCH FROM API ─────────────────────────────────
    print("🌐 Searching online...")
    
    product_info = get_product_info(barcode)
    
    if product_info:
        name = product_info["name"]
        category = product_info["category"]
        brand = product_info["brand"]
    
        save_local_price(barcode, name, brand, category, 0)
    
        result = format_product_for_speech(product_info)
        print(f"✅ Found online: {result}")
        speak(result)
        return result

    # ── STEP 4: MANUAL ENTRY ───────────────────────────────────
    result = (
    f"Barcode {barcode} was detected, "
    "but the product was not found in local storage or online databases."
    )

    print(f"⚠️ {result}")
    speak(result)

    return result
    # print("⚠️ Product not found. Prompting manual entry.")
    # speak("Product not found. Please enter details manually.")

    # try:
    #     name = input("Enter product name: ")
    #     category = input("Enter category: ")
    #     brand = input("Enter brand: ")
    #     price = float(input("Enter price: "))

    #     insert_product(barcode, name, category, price)
    #     save_local_price(barcode, name, brand, category, price)

    #     result = f"{name} saved. Price is {price} rupees."
    #     print(f"✅ Saved: {result}")
    #     speak(result)  # ✅ Single speak
    #     return result

    # except Exception as e:
    #     print("Error saving product:", e)
    #     speak("There was an error saving the product.")
    #     return None