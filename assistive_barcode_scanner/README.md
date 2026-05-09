# 🔍 Barcode Scanner

A real-time barcode scanner with **voice feedback**, **OCR fallback**, and a **local SQLite price database** — built for Pakistan (PKR pricing).

---

## ✨ Features

- **YOLO-powered barcode detection** — custom-trained model for fast ROI localization
- **zxing-cpp decoding** — no Java, no temp files; pure native speed
- **EasyOCR fallback** — reads product names when no barcode is found after 30 frames
- **Text-to-speech** via `pyttsx3` — speaks results aloud
- **Voice commands** — control the scanner hands-free (scan, repeat, stop, help, yes/no)
- **Local SQLite price DB** — stores and retrieves product prices in PKR
- **Smart mic muting** — microphone pauses while TTS is active to avoid echo loops

---

## 🗂️ Project Structure

```
├── controllers/
│   └── scanner_controller.py   # Main app loop
├── database/
│   ├── prices.db               # SQLite price store
│   └── products.db             # SQLite product store
├── models/                     # (reserved)
├── modes/
│   ├── alignment_mode.py
│   ├── rotation_mode.py
│   ├── scan_mode.py
│   └── search_mode.py
├── services/
│   ├── models/
│   │   └── barcode_model.pt    # Custom YOLO weights
│   ├── barcode_service.py      # YOLO + zxing-cpp detection pipeline
│   ├── beep_service.py
│   ├── camera_service.py       # OpenCV camera init
│   ├── database_service.py     # SQLite CRUD
│   ├── guidance_service.py
│   ├── ocr_service.py          # EasyOCR product-name detection
│   ├── product_service.py
│   ├── scan_service.py
│   ├── voice_command_service.py # Speech recognition + command parsing
│   └── voice_service.py        # pyttsx3 TTS with mic-muting event
├── utils/
│   └── create_table.py
├── main.py
└── requirements.txt
```

---

## ⚙️ Requirements

- Python **3.10+**
- A working **webcam**
- Microphone (for voice commands)
- Speakers or headphones (for TTS)

---

## 🚀 Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/barcode-scanner.git
cd barcode-scanner
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **PyAudio on Windows** may need a pre-built wheel:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 4. Add the YOLO model

Place your trained `barcode_model.pt` file at:

```
services/models/barcode_model.pt
```

---

## ▶️ Usage

```bash
python main.py
```

The app will:
1. Initialize the SQLite database
2. Open the camera
3. Start listening for voice commands
4. Begin scanning for barcodes in real time

---

## 🎤 Voice Commands

| Say | Action |
|-----|--------|
| `scan` / `start` / `begin` | Start scanning |
| `repeat` / `again` / `what` | Repeat last result |
| `stop` / `pause` / `quit` | Pause scanner |
| `help` / `how` / `instructions` | Read instructions |
| `yes` / `okay` / `haan` | Confirm prompt |
| `no` / `nahi` / `wait` | Decline prompt |

---

## 🔄 Detection Pipeline

```
Camera frame
    │
    ├─► YOLO → crop ROI → preprocess → zxing-cpp decode
    │
    ├─► (fallback) full-frame preprocess → zxing-cpp decode
    │
    └─► (OCR fallback after 30 no-barcode frames)
            EasyOCR → product name → TTS speak
```

Frame skipping (`frame_counter % 3`) keeps CPU usage low.

---

## 🗃️ Database Schema

**`database/prices.db`**

```sql
CREATE TABLE prices (
    barcode   TEXT PRIMARY KEY,
    name      TEXT,
    brand     TEXT,
    category  TEXT,
    price     INTEGER,          -- in PKR
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧩 Key Dependencies

| Package | Purpose |
|---------|---------|
| `opencv-python` | Camera capture & image processing |
| `ultralytics` | YOLOv8 barcode region detection |
| `zxing-cpp` | Native barcode decoding (EAN, UPC, QR, etc.) |
| `easyocr` | OCR fallback for product name reading |
| `pyttsx3` | Offline text-to-speech |
| `SpeechRecognition` | Google Speech API voice commands |
| `pyaudio` | Microphone access |

---

## 🛠️ Troubleshooting

**Camera not opening**
- Make sure no other app is using the webcam
- Try changing `VideoCapture(0)` to `VideoCapture(1)` in `camera_service.py`

**EasyOCR slow on first run**
- It downloads model weights (~200 MB) on first use — subsequent runs are instant

**`pyaudio` install fails**
- Linux: `sudo apt-get install portaudio19-dev` then `pip install pyaudio`
- Windows: use `pipwin install pyaudio`

**TTS not working**
- Linux may need: `sudo apt-get install espeak`

---

## 📄 License

MIT License — feel free to use, modify, and distribute.