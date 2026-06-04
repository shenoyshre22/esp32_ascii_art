import cv2
import serial
import time
import os
import sys
from PIL import Image

# ============================================================
#  PHOTOBOOTH SENDER — System1
#  Takes photo via webcam, converts to ASCII, sends over ESP32
# ============================================================

ESP32_PORT  = "COM7"    # <-- System1's ESP32 USB port
BAUD_RATE   = 115200
ASCII_WIDTH = 80        # characters wide (adjust for detail)

# ASCII characters from darkest to lightest
ASCII_CHARS = "@%#*+=-:. "

def capture_photo():
    """Open webcam, show countdown, capture photo."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam!")
        sys.exit(1)

    print("\n ASCII PHOTOBOOTH — Get ready & Smile widee !")
    print("Press SPACE to take photo, Q to quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Show live preview with instructions
        display = frame.copy()
        cv2.putText(display, "Press SPACE to capture!", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("PHOTOBOOTH - Press SPACE", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            # Countdown
            for i in range(3, 0, -1):
                ret, frame = cap.read()
                countdown = frame.copy()
                cv2.putText(countdown, str(i), (300, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 8, (0, 0, 255), 10)
                cv2.imshow("PHOTOBOOTH - Press SPACE", countdown)
                cv2.waitKey(1000)

            # Capture
            ret, frame = cap.read()
            cv2.imshow("PHOTOBOOTH - Press SPACE", frame)
            cv2.waitKey(500)
            print("📸 Photo captured!")
            break

        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)

    cap.release()
    cv2.destroyAllWindows()
    return frame

def image_to_ascii(frame, width=80):
    """Convert OpenCV frame to ASCII art string."""
    # Convert BGR to RGB then to PIL
    rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img   = Image.fromarray(rgb)

    # Resize — maintain aspect ratio (characters are taller than wide so multiply height by 0.45)
    aspect = img.height / img.width
    height = int(width * aspect * 0.45)
    img    = img.resize((width, height))

    # Convert to greyscale
    img = img.convert("L")

    # Map each pixel to ASCII character
    pixels = list(img.getdata())
    ascii_str = ""
    for i, pixel in enumerate(pixels):
        # Map pixel value (0-255) to ASCII chars index
        ascii_str += ASCII_CHARS[pixel * (len(ASCII_CHARS) - 1) // 255]
        if (i + 1) % width == 0:
            ascii_str += "\n"

    return ascii_str

def send_over_bluetooth(ascii_art, esp):
    """Send ASCII art over ESP32 Bluetooth bridge."""
    lines      = ascii_art.split("\n")
    total_lines = len(lines)

    print(f"\nSending {total_lines} lines of ASCII art over Bluetooth...")

    # Send header
    header = f"ASCII_START|{total_lines}\n"
    esp.write(header.encode())
    esp.flush()
    time.sleep(0.2)

    # Send each line
    for i, line in enumerate(lines):
        esp.write((line + "\n").encode())
        esp.flush()
        time.sleep(0.01)  # Small delay to not overflow buffer
        print(f"  Sent line {i+1}/{total_lines}", end="\r")

    # Send footer
    time.sleep(0.1)
    esp.write(b"ASCII_END\n")
    esp.flush()
    print(f"\nAll {total_lines} lines sent!")

def main():
    # Step 1: Connect to ESP32
    print(f"Connecting to ESP32 on {ESP32_PORT}...")
    try:
        esp = serial.Serial()
        esp.port     = ESP32_PORT
        esp.baudrate = BAUD_RATE
        esp.timeout  = 10
        esp.rts      = False   # Prevent ESP32 reset
        esp.dtr      = False   # Prevent ESP32 reset
        esp.open()
        time.sleep(2)
        esp.reset_input_buffer()
        print("ESP32 connected!\n")
    except serial.SerialException as e:
        print(f"ERROR connecting to ESP32: {e}")
        sys.exit(1)

    # Step 2: Take photo
    frame = capture_photo()

    # Step 3: Convert to ASCII
    print("Converting to ASCII art...")
    ascii_art = image_to_ascii(frame, width=ASCII_WIDTH)

    # Preview in terminal on System1 too
    print("\n--- ASCII PREVIEW (System1) ---")
    print(ascii_art[:500] + "...\n")  # Show first 500 chars

    # Save locally too
    with open("captured_ascii.txt", "w") as f:
        f.write(ascii_art)
    print("Saved locally as captured_ascii.txt")

    # Step 4: Send over Bluetooth
    print("\nMake sure photobooth_receiver.py is running on System2!")
    input("Press ENTER when System2 is ready...")

    send_over_bluetooth(ascii_art, esp)
    esp.close()
    print("\n Done! Check System2 for the ASCII art.")

if __name__ == "__main__":
    main()