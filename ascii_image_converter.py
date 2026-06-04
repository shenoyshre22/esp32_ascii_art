import serial
import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont

# ============================================================
#  PHOTOBOOTH RECEIVER — System2
#  Receives ASCII lines, renders as proper image, saves + shows
# ============================================================

COM_PORT    = "COM9"   # <-- System2's Bluetooth COM port
BAUD_RATE   = 115200
SAVE_FOLDER = r"D:\Shreya\Projects_PES\esp32_photobooth\esp32_ascii_art\ascii_photostrip"


ASCII_WIDTH = 120

def render_ascii_image(ascii_lines):
    char_w = 10
    char_h = 18
    img_w  = ASCII_WIDTH * char_w
    img_h  = len(ascii_lines) * char_h

    canvas = Image.new("RGB", (img_w, img_h), color=(0, 0, 0))
    draw   = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("cour.ttf", 14)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/cour.ttf", 14)
        except:
            font = ImageFont.load_default()

    for i, line in enumerate(ascii_lines):
        draw.text((0, i * char_h), line, fill=(255, 255, 255), font=font)

    return canvas

def main():
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    print(f"Connecting to ESP32 Bluetooth on {COM_PORT}...")
    try:
        bt = serial.Serial(COM_PORT, BAUD_RATE, timeout=60)
        time.sleep(2)
        bt.reset_input_buffer()
        print("Connected! Waiting for photo...\n")
    except serial.SerialException as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    lines      = []
    receiving  = False
    total      = 0

    try:
        while True:
            raw  = bt.readline()
            line = raw.decode("utf-8", errors="ignore").rstrip("\n").rstrip("\r")

            if line.startswith("ASCII_START"):
                parts     = line.split("|")
                total     = int(parts[1]) if len(parts) > 1 else 0
                lines     = []
                receiving = True
                print(f"Receiving {total} lines of ASCII art...")

            elif line == "ASCII_END" and receiving:
                receiving = False
                print(f"\nReceived all {len(lines)} lines!")
                print("Rendering image...")

                # Render to image
                canvas    = render_ascii_image(lines)
                timestamp = time.strftime("%H%M%S")
                save_path = os.path.join(SAVE_FOLDER, f"ascii_photo_{timestamp}.png")
                canvas.save(save_path)

                print(f"\n your photobooth strip is saved at: {save_path}")

                # Auto open the image
                os.startfile(save_path)

                print("\nWaiting for next photo...")
                lines = []

            elif receiving:
                lines.append(line)
                print(f"  {len(lines)}/{total}", end="\r")

    except KeyboardInterrupt:
        print("\nStopped.")
        # Save whatever arrived
        if lines:
            canvas    = render_ascii_image(lines)
            save_path = os.path.join(SAVE_FOLDER, "ascii_partial.png")
            canvas.save(save_path)
            print(f"Partial image saved: {save_path}")
    finally:
        bt.close()

if __name__ == "__main__":
    main()