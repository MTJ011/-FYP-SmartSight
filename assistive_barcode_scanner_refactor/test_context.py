from services.scan_context import scan_context

print(scan_context.ocr_text)

scan_context.ocr_text = "Lay's French Cheese"

print(scan_context.ocr_text)

scan_context.reset()

print(scan_context.ocr_text)