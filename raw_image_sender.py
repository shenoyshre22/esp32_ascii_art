import cv2
import serial
import time
import sys
import os
import struct
from PIL import Image, ImageDraw, ImageFont

# ============================================================
#  PHOTOBOOTH SENDER — System1
# ============================================================

ESP32_PORT  = "COM4"       # <-- change to your ESP32 USB port
BAUD_RATE   = 115200
ASCII_WIDTH = 120          # columns of characters

# Dense to light — gives good contrast like the reference image
ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmHMWZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^`'. "

def capture_photo():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam!")
        sys.exit(1)

    print("\n PHOTOBOOTH — Press SPACE to take photo, Q to quit\n")

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

def frame_to_ascii_image(frame, width=120):
    """Convert frame to ASCII art and render as a proper BLACK image with white text."""
    # Convert to PIL grayscale
    rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img  = Image.fromarray(rgb)

    # Resize for ASCII — chars are ~2x taller than wide so scale height by 0.45
    aspect = img.height / img.width
    height = int(width * aspect * 0.45)
    img    = img.resize((width, height))
    img    = img.convert("L")  # grayscale

    pixels   = list(img.getdata())
    ascii_lines = []
    row = ""
    for i, pixel in enumerate(pixels):
        # Map 0-255 to char index
        idx  = int(pixel / 255 * (len(ASCII_CHARS) - 1))
        row += ASCII_CHARS[idx]
        if (i + 1) % width == 0:
            ascii_lines.append(row)
            row = ""

    # ── Render ASCII lines onto a black image ──
    char_w   = 10   # pixels per character cell width
    char_h   = 18   # pixels per character cell height
    img_w    = width * char_w
    img_h    = len(ascii_lines) * char_h

    canvas   = Image.new("RGB", (img_w, img_h), color=(0, 0, 0))
    draw     = ImageDraw.Draw(canvas)

    # Use default PIL font (always available, no install needed)
    try:
        font = ImageFont.truetype("cour.ttf", 14)   # Courier — monospace
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/cour.ttf", 14)
        except:
            font = ImageFont.load_default()

    for row_idx, line in enumerate(ascii_lines):
        y = row_idx * char_h
        draw.text((0, y), line, fill=(255, 255, 255), font=font)

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
    # Connect to ESP32
    print(f"Connecting to ESP32 on {ESP32_PORT}...")
    try:
        esp        = serial.Serial()
        esp.port   = ESP32_PORT
        esp.baudrate = BAUD_RATE
        esp.timeout  = 10
        esp.rts    = False
        esp.dtr    = False
        esp.open()
        time.sleep(2)
        esp.reset_input_buffer()
        print("ESP32 connected!\n")
    except serial.SerialException as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Take photo
    frame = capture_photo()

    # Convert to ASCII image
    print("Converting to ASCII art...")
    canvas, ascii_lines = frame_to_ascii_image(frame, width=ASCII_WIDTH)

    # Save preview on System1
    canvas.save("ascii_preview.png")
    print("Saved preview as ascii_preview.png — open it to see how it looks!")

    # Show preview
    canvas_cv = cv2.cvtColor(
        cv2.resize(
            __import__('numpy').array(canvas),
            (900, 600)
        ),
        cv2.COLOR_RGB2BGR
    )
    cv2.imshow("ASCII Preview — press any key to send", canvas_cv)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Send
    print("\nMake sure photobooth_receiver.py is running on System2!")
    input("Press ENTER to send...\n")
    send_ascii_over_bt(ascii_lines, esp)
    esp.close()
    print("\nDone! Check System2.")

if __name__ == "__main__":
    main()