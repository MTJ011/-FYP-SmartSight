import requests


def get_food_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

    try:
        res = requests.get(url, timeout=5).json()

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
        res = requests.get(url, timeout=5).json()

        if res.get("status") == 1:
            product = res.get("product", {})

            return (
                product.get("product_name"),
                product.get("categories"),
                product.get("brands"),
                "Personal care product"
            )

    except Exception as e:
        print(f"Error fetching beauty data: {e}")

    return None, None, None, None