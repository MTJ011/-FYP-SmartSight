import time
from services.voice_service import speak

products = [
    "Lay's French Cheese",
    "Pringles Original",
    "Coca Cola",
    "Nestle Milkpak",
    "Pepsi"
]

for product in products:
    speak(product)
    time.sleep(2)

print("Done")