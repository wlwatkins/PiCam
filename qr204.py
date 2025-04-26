#!/usr/bin/env python3
from escpos.printer import File
from PIL import Image, ImageEnhance
import time
import cv2
import math
import datetime
import uuid
import numpy as np
import threading
import RPi.GPIO as GPIO

button_locked = False
BUTTON_PIN = 17
OUTPUT_PIN = 12  # GPIO pin configured as output
PRINTER_DEVICE = "/dev/usb/lp0"

def say_cheeze(image_name):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(image_name, frame)
        print("Image saved as", image_name)
    else:
        print("Failed to capture image")
    cap.release()

def convert_image(input_path, width=384, num_colors=254):
    img = Image.open(input_path)
    img = img.rotate(-90, expand=True)
    img = img.resize((width, int(width * img.height / img.width)))
    img = img.convert("L")
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1)
    img = img.convert("P", palette=Image.ADAPTIVE, colors=num_colors)
    return img

def print_image_with_darkness(printer_dev, img, darkness=0x1E):
    p = File(printer_dev)
    p._raw(bytes([0x1D, 0x42, darkness]))
    time.sleep(0.1)
    p._raw(bytes([0x1D, 0x28, 0x01]))
    p.image(img, impl="bitImageRaster")
    p.text("\n")
    current_date = datetime.datetime.now().strftime("%d-%m-%Y")
    p.text(f"           {current_date}")
    p.print_and_feed(1)
    p.cut()
    p.close()


# def print_image_with_darkness(printer_dev, image_input, darkness=0x1E, delay=0.2, block_height=15):
#     """
#     Print the current date (centered) and then print the image in horizontal strips
#     so that the printer has time to render dark areas.
    
#     Parameters:
#       printer_dev: Device path for the printer.
#       image_input: Either a file path (string) or a PIL Image object.
#       darkness: Darkness level command value.
#       delay: Delay (in seconds) between each printed block.
#       block_height: Height (in pixels) for each printed block.
#     """
#     p = File(printer_dev)
    
#     # 1) Set darkness and initialize printer
#     p._raw(bytes([0x1D, 0x42, darkness]))
#     time.sleep(0.1)  # Allow time for the printer to apply the darkness level
#     p._raw(bytes([0x1D, 0x28, 0x01]))
    
#     # 2) Get the current date and print it centered
#     current_date = datetime.datetime.now().strftime("%Y-%m-%d")
#     p.set(align="center")
#     p.text(current_date + "\n\n")
#     p.set(align="left")
    
#     # 3) Process the input: if a string, open the image; if already an Image object, use it.
#     if isinstance(image_input, str):
#         img = Image.open(image_input).convert("1")
#     elif isinstance(image_input, Image.Image):
#         img = image_input.convert("1")
#     else:
#         raise ValueError("image_input must be a file path (str) or a PIL Image object")
    
#     width, height = img.size
#     num_blocks = math.ceil(height / block_height)

#     for i in range(num_blocks):
#         top = i * block_height
#         bottom = min((i + 1) * block_height, height)
#         block = img.crop((0, top, width, bottom))
#         p.image(block, impl="bitImageRaster")
#         time.sleep(delay)
    
#     # 4) Finalize printing
#     p.print_and_feed(2)
#     p.cut()
#     p.close()

def blink_led_for_duration(duration, blink_interval):
    start_time = time.time()
    while time.time() - start_time < duration:
        GPIO.output(OUTPUT_PIN, GPIO.HIGH)
        time.sleep(blink_interval)
        GPIO.output(OUTPUT_PIN, GPIO.LOW)
        time.sleep(blink_interval)

def blink_led_sequence():
    sequence = [(3, 0.5), (3, 0.25), (3, 0.1)]
    for duration, interval in sequence:
        blink_led_for_duration(duration, interval)
    GPIO.output(OUTPUT_PIN, GPIO.HIGH)
    time.sleep(1)

def picture(channel):
    global button_locked
    if button_locked:
        return
    button_locked = True
    blink_led_sequence()
    current_date = datetime.datetime.now().strftime("%Y_%m_%d")
    image_name = f"{current_date}_{uuid.uuid4()}.png"
    say_cheeze(image_name)
    img = convert_image(image_name)
    GPIO.output(OUTPUT_PIN, GPIO.LOW)
    print_image_with_darkness(PRINTER_DEVICE, img, darkness=0x2A)
    threading.Timer(3, unlock_button).start()

def unlock_button():
    global button_locked
    button_locked = False
    GPIO.output(OUTPUT_PIN, GPIO.HIGH)
    print("Button unlocked.")

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(OUTPUT_PIN, GPIO.OUT)
    GPIO.output(OUTPUT_PIN, GPIO.HIGH)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=picture, bouncetime=1500)
    print("Waiting for a button press... (Press Ctrl+C to exit)")
    picture(2)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        GPIO.cleanup()