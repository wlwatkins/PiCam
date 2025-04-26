#!/usr/bin/env python3
"""
Camera capture and ESC/POS printing utility with LED feedback and button trigger.
Works for QR204 printer
"""
import time
import uuid
import threading
import datetime
import argparse
from pathlib import Path

import cv2
from PIL import Image, ImageEnhance
from escpos.printer import File as EscposPrinter
import RPi.GPIO as GPIO
from dotenv import load_dotenv
import os


def load_config(env_path: Path):
    """
    Load environment variables from .env file.
    """
    load_dotenv(dotenv_path=env_path)
    config = {
        'BUTTON_PIN': int(os.getenv('BUTTON_PIN', 17)),
        'LED_PIN': int(os.getenv('LED_PIN', 12)),
        'PRINTER_DEVICE': os.getenv('PRINTER_DEVICE', '/dev/usb/lp0'),
        'IMAGE_WIDTH': int(os.getenv('IMAGE_WIDTH', 384)),
        'NUM_COLORS': int(os.getenv('NUM_COLORS', 254)),
        'DARKNESS_LEVEL': int(os.getenv('DARKNESS_LEVEL', 0x2A,)),
    }
    return config


class Camera:
    """
    Handles camera operations: capture and save images.
    """
    def __init__(self, device_index: int = 0):
        self.device_index = device_index

    def capture(self, output_path: Path) -> None:
        """
        Capture an image from the camera and save to output_path.
        """
        cap = cv2.VideoCapture(self.device_index)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError("Failed to capture image from camera")
        cv2.imwrite(str(output_path), frame)


class ImageProcessor:
    """
    Converts and processes images for ESC/POS printing.
    """
    def __init__(self, width: int, num_colors: int):
        self.width = width
        self.num_colors = num_colors

    def convert(self, input_path: Path) -> Image.Image:
        """
        Load, rotate, resize, enhance, and quantize image.
        """
        img = Image.open(input_path)
        img = img.rotate(-90, expand=True)
        height = int(self.width * img.height / img.width)
        img = img.resize((self.width, height))
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.0)
        return img.convert('P', palette=Image.ADAPTIVE, colors=self.num_colors)


class Printer:
    """
    ESC/POS printer wrapper with darkness configuration.
    """
    def __init__(self, device: str, darkness: int):
        self.device = device
        self.darkness = darkness

    def print_image(self, img: Image.Image) -> None:
        """
        Print given PIL image with configured darkness and date footer.
        """
        printer = EscposPrinter(self.device)
        # Set darkness
        printer._raw(bytes([0x1D, 0x42, self.darkness]))
        time.sleep(0.1)
        # Print image
        printer._raw(bytes([0x1D, 0x28, 0x01]))
        printer.image(img, impl='bitImageRaster')
        printer.text('\n')
        # Footer date
        date_str = datetime.datetime.now().strftime('%d-%m-%Y')
        printer.text(f"           {date_str}\n")
        printer.print_and_feed(1)
        printer.cut()
        printer.close()


class LEDIndicator:
    """
    LED blinking sequences for user feedback.
    """
    def __init__(self, pin: int):
        self.pin = pin

    def setup(self):
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH)

    def blink(self, duration: float, interval: float) -> None:
        """
        Blink LED for duration at given interval.
        """
        end_time = time.time() + duration
        while time.time() < end_time:
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(interval)
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(interval)

    def sequence(self):
        """
        Execute predefined blink sequence.
        """
        for dur, intv in [(3, 0.5), (3, 0.25), (3, 0.1)]:
            self.blink(dur, intv)
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Capture image and print via ESC/POS with LED feedback.")
    parser.add_argument('--env', type=Path, default=Path('.env'), help='Path to .env file')
    args = parser.parse_args()

    config = load_config(args.env)

    GPIO.setmode(GPIO.BCM)
    # Initialize components
    led = LEDIndicator(config['LED_PIN'])
    led.setup()
    camera = Camera()
    processor = ImageProcessor(config['IMAGE_WIDTH'], config['NUM_COLORS'])
    printer = Printer(config['PRINTER_DEVICE'], config['DARKNESS_LEVEL'])

    button_locked = False

    def unlock_button():
        nonlocal button_locked
        button_locked = False
        GPIO.output(config['LED_PIN'], GPIO.HIGH)
        print("Button unlocked.")

    def on_button(channel):
        nonlocal button_locked
        if button_locked:
            return
        button_locked = True
        led.sequence()
        # Generate filename
        date_str = datetime.datetime.now().strftime('%Y_%m_%d')
        filename = f"{date_str}_{uuid.uuid4()}.png"
        output_path = Path.cwd() / filename
        try:
            camera.capture(output_path)
            img = processor.convert(output_path)
            GPIO.output(config['LED_PIN'], GPIO.LOW)
            printer.print_image(img)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            threading.Timer(3, unlock_button).start()

    # Setup button
    GPIO.setup(config['BUTTON_PIN'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(config['BUTTON_PIN'], GPIO.FALLING, callback=on_button, bouncetime=1500)

    print("Waiting for button press... (Ctrl+C to exit)")
    # Initial capture
    on_button(None)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
