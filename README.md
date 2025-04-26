# PiCam

A Raspberry Pi image capture + ESC/POS printing utility with LED feedback and button trigger.

- Captures images from a USB camera (OpenCV).  
- Processes and dither-quantizes them for thermal/ESC/POS printers.  
- Prints with adjustable darkness and a date footer.  
- Gives visual feedback via an LED blink sequence.  
- Triggered by a physical button (GPIO).

---

## Features

- 📸  Image capture (OpenCV)  
- 🖨️  ESC/POS printing (python-escpos)  
- 💡  LED blink sequences for status  
- 🔘  Button-press trigger with lock-out debounce  
- ⚙️  Fully configurable via `.env`  
- 🎛️  CLI interface (`poetry run picam`)  

---

## Requirements

- **Hardware**  
  - Raspberry Pi (ARM/Linux)  
  - USB webcam (e.g. `/dev/video0`)  
  - ESC/POS thermal printer (e.g. QR204) on USB (`/dev/usb/lp0`)  
  - Momentary push-button wired to a GPIO pin  
  - LED (with resistor) wired to a GPIO pin  

- **Software**  
  - Python ≥ 3.12  
  - [Poetry](https://python-poetry.org/)  
  - System packages: `libglib2.0-0`, `libsm6`, `libxrender1`, `libxext6` (for OpenCV)

---

## Installation

1. **Clone and enter project**  
   ```bash
   git clone https://github.com/wlwatkins/PiCam.git
   cd picam
   ```

2. **Create your `.env`**  
   Copy and adjust the example:
   ```dotenv
    # GPIO pins
    BUTTON_PIN=17
    LED_PIN=12

    # Printer device path
    PRINTER_DEVICE=/dev/usb/lp0

    # Image processing
    IMAGE_WIDTH=384          # width in pixels for ESC/POS page
    NUM_COLORS=254           # number of grayscale/color levels

    # Printer darkness (0–255)
    DARKNESS_LEVEL=42        # e.g. 0x2A = 42

    # (Optional) Camera index (0 = default USB webcam)
    CAMERA_INDEX=0

   ```

3. **Install dependencies**  
   ```bash
   poetry install
   ```

4. **Activate virtual environment** (optional)  
   ```bash
   poetry shell
   ```

---

## Usage

```bash
poetry run picam [--env path/to/.env]
```

- **--env**: Path to your `.env` file (defaults to `./.env`).

On startup, the script will immediately grab and print one image, then wait for button presses. After each print, the button is locked for ~3 s to debounce.  
Press **Ctrl + C** to exit and clean up GPIO.

---

## Autostart on Reboot

To have **picam** start automatically on system boot, add it to your crontab:

1. Open the root crontab (GPIO access typically requires root):
   ```bash
   sudo crontab -e
   ```

2. Add this line at the end (adjust paths as needed):
   ```cron
   @reboot /usr/bin/env bash -lc "cd /home/pi/picam && poetry run picam --env /home/pi/picam/.env >> /home/pi/picam/picam.log 2>&1"
   ```

   - `@reboot` runs the command once on startup.
   - `bash -lc` ensures the Poetry environment is loaded correctly.
   - Redirecting output to `picam.log` helps with debugging.

3. Save and exit. On next reboot, **picam** will start automatically.

---

## Contributing

1. Fork the repo & create a feature branch  
2. Write your code and tests  
3. Run linting/formatting (e.g. `black`, `flake8`)  
4. Submit a pull request with a clear description

---

## License

This project is not open source.  
© 2025 Will Watkins
