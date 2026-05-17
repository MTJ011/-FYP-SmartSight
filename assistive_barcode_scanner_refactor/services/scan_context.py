class ScanContext:

    def __init__(self):
        self.reset()

    def reset(self):

        # OCR
        self.ocr_text = None
        self.ocr_captured = False

        # Barcode
        self.detected_barcode = None
        self.barcode_confirmations = 0

        # Scan state
        self.scan_complete = False
        self.product_found = False

        # Guidance
        self.last_guidance = ""
        self.last_spoken = ""

        # Rotation
        self.rotation_step = 0

        # Result
        self.final_result = None


# global shared context
scan_context = ScanContext()