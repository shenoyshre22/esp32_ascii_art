import cv2
import serial
import time
import sys
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageEnhance as IE
import PIL.ImageOps

# ============================================================
#  PHOTOBOOTH SENDER — System1
# ============================================================

ESP32_PORT  = "COM4"
BAUD_RATE   = 115200
ASCII_WIDTH = 160

# Reference image style:
# BRIGHT skin/highlights → dense packed chars like @#%8&W
# MID shadows            → medium chars like *+=-:
# DARK/background        → sparse dots or spaces
# This goes from BRIGHT → DARK (inverted mapping)
ASCII_CHARS = "MMMWWW###@@@%%%888&&&***+++===---:::...   "

def capture_photo():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam!")
        sys.exit(1)
    print("\nPHOTOBOOTH — Press SPACE to take photo, Q to quit\n")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        preview = frame.copy()
        cv2.putText(preview, "Press SPACE to capture!", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("PHOTOBOOTH", preview)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            for i in range(3, 0, -1):
                ret, frame = cap.read()
                cd = frame.copy()
                cv2.putText(cd, str(i), (280, 260),
                            cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 0, 255), 15)
                cv2.imshow("PHOTOBOOTH", cd)
                cv2.waitKey(1000)
            ret, frame = cap.read()
            print("Photo captured!")
            break
        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)
    cap.release()
    cv2.destroyAllWindows()
    return frame

def frame_to_ascii_image(frame, width=160):
    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img    = Image.fromarray(rgb)

    # Resize — 0.45 corrects character aspect ratio
    aspect = img.height / img.width
    height = int(width * aspect * 0.45)
    img    = img.resize((width, height), Image.LANCZOS)

    # Heavy contrast boost to separate bright skin from dark shadows
    img = IE.Contrast(img).enhance(2.5)
    img = IE.Sharpness(img).enhance(2.0)

    # Grayscale
    img = img.convert("L")

    # Stretch tonal range so we use the full 0-255 spectrum
    img = PIL.ImageOps.autocontrast(img, cutoff=2)

    pixels      = list(img.getdata())
    ascii_lines = []
    row         = ""
    n           = len(ASCII_CHARS) - 1

    for i, pixel in enumerate(pixels):
        # INVERT mapping:
        # pixel=255 (white/bright skin) → index 0 → dense char 'M'
        # pixel=0   (black/shadow)      → index n → space ' '
        idx  = int((255 - pixel) / 255 * n)
        row += ASCII_CHARS[idx]
        if (i + 1) % width == 0:
            ascii_lines.append(row)
            row = ""

    # ── Render: BLACK background, WHITE dense chars for bright areas ──
    char_w = 8
    char_h = 14
    img_w  = width * char_w
    img_h  = len(ascii_lines) * char_h

    canvas = Image.new("RGB", (img_w, img_h), color=(0, 0, 0))
    draw   = ImageDraw.Draw(canvas)

    font = None
    for path in [
        "C:/Windows/Fonts/lucon.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, 12)
            print(f"Font: {path}")
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    for row_idx, line in enumerate(ascii_lines):
        draw.text((0, row_idx * char_h), line, fill=(255, 255, 255), font=font)

    return canvas, ascii_lines

def send_ascii_over_bt(ascii_lines, esp):
    total = len(ascii_lines)
    print(f"\nSending {total} lines over Bluetooth...")
    esp.write(f"ASCII_START|{total}\n".encode())
    esp.flush()
    time.sleep(0.2)
    for i, line in enumerate(ascii_lines):
        esp.write((line + "\n").encode())
        esp.flush()
        time.sleep(0.01)
        print(f"  Line {i+1}/{total}", end="\r")
    time.sleep(0.1)
    esp.write(b"ASCII_END\n")
    esp.flush()
    print(f"\nAll {total} lines sent!")

def main():
    print(f"Connecting to ESP32 on {ESP32_PORT}...")
    try:
        esp          = serial.Serial()
        esp.port     = ESP32_PORT
        esp.baudrate = BAUD_RATE
        esp.timeout  = 10
        esp.rts      = False
        esp.dtr      = False
        esp.open()
        time.sleep(2)
        esp.reset_input_buffer()
        print("ESP32 connected!\n")
    except serial.SerialException as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    frame = capture_photo()

    print("Converting to ASCII art...")
    canvas, ascii_lines = frame_to_ascii_image(frame, width=ASCII_WIDTH)

    canvas.save("ascii_preview.png")
    print("Preview saved as ascii_preview.png")

    arr     = np.array(canvas)
    cv2_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    h, w    = cv2_img.shape[:2]
    scale   = min(1400/w, 900/h)
    cv2_img = cv2.resize(cv2_img, (int(w*scale), int(h*scale)))
    cv2.imshow("ASCII Preview — press any key to send", cv2_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("\nMake sure photobooth_receiver.py is running on System2!")
    input("Press ENTER to send...\n")
    send_ascii_over_bt(ascii_lines, esp)
    esp.close()
    print("\nDone! Check System2.")

if __name__ == "__main__":
    main()