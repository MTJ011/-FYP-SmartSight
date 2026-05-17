from services.scan_context import scan_context
from services.voice_service import speak


def run():

    barcode = scan_context.detected_barcode

    if barcode:

        result = f"Barcode detected: {barcode}"

        scan_context.final_result = result
        scan_context.scan_complete = True

        speak(result)

        return result

    # OCR fallback
    if scan_context.ocr_text:

        result = f"No barcode found. Product text reads: {scan_context.ocr_text}"

        scan_context.final_result = result
        scan_context.scan_complete = True

        speak(result)

        return result

    # total failure
    result = "I could not identify the product."

    scan_context.final_result = result
    scan_context.scan_complete = True

    speak(result)

    return result