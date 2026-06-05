import requests

HEADERS = {
    "User-Agent": "SmartSight/1.0"
}


def get_food_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=5
        )

        if not response.text.strip():
            print("Food API returned empty response.")
            return None, None, None, None

        res = response.json()

        if res.get("status") == 1:
            product = res.get("product", {})

            return (
                product.get("product_name"),
                product.get("categories"),
                product.get("brands"),
                "Food"
            )

    except Exception as e:
        print(f"Error fetching food data: {e}")

    return None, None, None, None


def get_beauty_product(barcode):
    url = f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=5
        )

        if not response.text.strip():
            print("Beauty API returned empty response.")
            return None, None, None, None

        res = response.json()

        if res.get("status") == 1:
            product = res.get("product", {})

            return (
                product.get("product_name"),
                product.get("categories"),
                product.get("brands"),
                "Personal Care Product"
            )

    except Exception as e:
        print(f"Error fetching beauty data: {e}")

    return None, None, None, None


def get_product_info(barcode):
    """
    Try food API first, then beauty API.
    Returns a dictionary or None.
    """

    name, category, brand, product_type = get_food_product(barcode)

    if not name:
        name, category, brand, product_type = get_beauty_product(barcode)

    if not name:
        return None

    if category:
        category = category.split(",")[0].strip()

    return {
        "barcode": barcode,
        "name": name or "Unknown Product",
        "category": category or "Unknown Category",
        "brand": brand or "Unknown Brand",
        "product_type": product_type or "Product"
    }


def format_product_for_speech(product_info):
    """
    Creates a voice-friendly sentence.
    """

    if not product_info:
        return "Product not found."

    name = product_info.get("name", "Unknown Product")
    brand = product_info.get("brand", "")
    category = product_info.get("category", "")
    product_type = product_info.get("product_type", "")

    parts = [name]

    if brand and brand.lower() not in name.lower():
        parts.append(f"Brand {brand}")

    if category:
        parts.append(f"Category {category}")

    if (
        product_type
        and product_type.lower() != "food"
        and product_type.lower() != "unknown"
    ):
        parts.append(product_type)

    return ". ".join(parts) + "."