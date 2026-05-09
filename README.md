# Navigation Demo (FYDP)

This repository contains a simple indoor navigation demo and supporting servers for step/gyro sensors, instruction generation, and a navigation controller that speaks directions.

## Prerequisites
- Python 3.8+ (3.10 or 3.11 recommended)
- Git (optional)
- On Windows: PowerShell is used as a TTS fallback (present by default).
- On Linux: install `python3-tk` if you want the gyro GUI.

## Python dependencies
Install packages into a virtual environment for a clean setup:

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

requirements.txt includes:
- Flask (HTTP endpoints)
- requests (HTTP client)
- pyttsx3 (offline TTS)
- opencv-python (camera helper scripts)

Optional packages:
- pywin32 (sometimes required on Windows for TTS backends)

## Ports used (defaults)
- Gyro server (gyro_server.py): HTTP POST `/data` and GET `/gyro` on port `8000`.
- Refined acceleration server (acceleration_server.py) and Android variant: POST `/data` and GET `/steps` on port `8002`.

## Quick start / Recommended demo flow

1. Start the gyro server (starts a small Tk GUI to display accumulated angle):

```bash
python gyro_server.py
```

2. Start the acceleration step server (accepts Sensor Logger POSTs):

```bash
python acceleration_server_android.py
# or the refined server
python acceleration_server.py
```

3. (Optional) Verify the instructor pathing and steps:

```bash
# interactive: prompts for destination
python instructor.py

# automated check printing approach cells + path + steps
python test_instructor_paths.py
```

4. Run the navigation controller (speaks instructions and waits for sensors):

```bash
python navigation_controller.py
```

The controller will prompt for a destination via `generate_instructions()` (same choices as `instructor.py`). It uses the step server at `http://localhost:8002/steps` and gyro at `http://localhost:8000/gyro`.

## Running without physical sensors (testing)
- To just see generated instructions without speaking or sensor waits:

```bash
python -c "from instructor import generate_instructions; print(generate_instructions('food'))"
```

- To simulate step detection unit tests:

```bash
python simulate_steps.py
```

- To run the automated path check:

```bash
python test_instructor_paths.py
```

## Troubleshooting
- No audio / TTS not heard
  - Check console for messages starting with `[WARN]` or `[ERROR]` from `navigation_controller.py`.
  - `pyttsx3` is used by default; if it fails, the code attempts a PowerShell System.Speech fallback on Windows.
  - To force the PowerShell fallback (Windows):

```powershell
$env:FORCE_POWERSHELL_TTS='1'
python -c "from navigation_controller import speak; speak('Hello')"
```

- `tkinter` GUI for gyro server missing on Linux
  - Install using your distro package, for example on Debian/Ubuntu:

```bash
sudo apt-get install python3-tk
```

- `opencv-python` camera scripts (only used by `camera_test.py` and `find_cameras.py`) may require additional system libs on Linux. Use your package manager or consult the opencv installation notes.

## Files of interest
- `gyro_server.py` — exposes `/data` POST and `/gyro` GET, provides Tk GUI
- `acceleration_server.py` / `acceleration_server_android.py` — collect accelerometer data and detect steps (expose `/data` and `/steps`)
- `instructor.py` — grid mapping, table placement, path finding and instruction generation
- `navigation_controller.py` — uses TTS and sensor APIs to deliver instructions to a human
- `simulate_steps.py` & `test_instructor_paths.py` — small test utilities

## Notes and configuration
- Grid/table/obstacle layout and step sizing are configurable in `instructor.py` via `GRID_ROWS`, `GRID_COLS`, `TABLES`, `OBSTACLES`, `AVG_STEP_FT` and `CELL_STEP_MULT`.
- Timeouts and tolerances in `navigation_controller.py` are configurable (`INSTR_TIMEOUT`, `TURN_TOL`, `STEP_PAUSE`).

If you'd like, I can also add simple CLI flags to each script (`--port`, `--test`, `--no-tts`) or provide a small `Makefile` / PowerShell script to start the demo services together. Want me to add that? 
