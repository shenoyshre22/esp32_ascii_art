import serial
import time
import cv2
import numpy as np
import os
import sys

# --- CONFIGURATION ---
# Replace with Ishita's actual Bluetooth assigned Incoming COM Port from Device Manager
BLUETOOTH_COM_PORT = "COM6"  
BAUD_RATE = 115200

# Defines the maximum character width allowed for the ASCII image on your terminal
TARGET_WIDTH = 80 

# The smooth density character ramp (from darkness/less dense to brightness/most dense)
ASCII_CHARS = [" ", ".", ",", "-", "~", ":", ";", "=", "!", "i", "l", "I", "x", "O", "Z", "$", "#", "@"]

def clear_terminal():
    # ANSI escape code that clears the terminal cursor space instantly (much faster than os.system)
    # Allows a much smoother, higher-fidelity experience with no tearing.
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()

def convert_to_ascii(frame, new_width=TARGET_WIDTH):
    # Flatten the 3-channel color data (0-255 RGB) into a single 8-bit Gray channel (0-255).
    # This matrix directly represents the brightness map needed for ASCII density.
    grayscale_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Scale the gray matrix width down significantly to fit standard terminal rows.
    (original_height, original_width) = grayscale_img.shape
    aspect_ratio = original_height / float(original_width)
    new_height = int(aspect_ratio * new_width * 0.55) # Adjusted for tall terminal typography
    resized_img = grayscale_img.resize((new_width, new_height))
    
    # Map each single Gray value index chunk into an ASCII character slot.
    scale_factor = 255 / (len(ASCII_CHARS) - 1)
    ascii_str = "".join([ASCII_CHARS[int(pixel / scale_factor)] for pixel in pixels])
    
    # Map the linear 1D text array back into individual horizontal text rows
    width = resized_img.width
    return [ascii_str[index:index + width] for index in range(0, len(ascii_str), width)]

def main():
    print(f"Opening Bluetooth listener channel on {BLUETOOTH_COM_PORT}...")
    try:
        # A 5-second timeout is critical here! Raw image data payloads are massive
        # and can take several seconds to stream over the 115200 baud pipeline.
        ser = serial.Serial(BLUETOOTH_COM_PORT, BAUD_RATE, timeout=5)
    except Exception as e:
        print(f"Connection failure! Ensure you are actively paired: {e}")
        return

    # Clear screen and ready dashboard
    clear_terminal()
    print("=====================================================================")
    print("             REMOTE ASCII ART PHOTORENDERER TERMINAL                 ")
    print("=====================================================================")
    print("Awaiting wireless raw image signals via the ESP32 data bridge...")
    print("=====================================================================\n")

    try:
        while True:
            if ser.in_waiting > 0:
                # 1. Listen for the Start-of-Frame flag header
                raw_line = ser.readline()
                try:
                    line = raw_line.decode('utf-8').rstrip('\r\n')
                except UnicodeDecodeError:
                    continue

                if line == "---START_FRAME---":
                    print("\n📸 START OF NEW FRAME DETECTED! Awaiting data matrix...")
                    
                    # 2. Listen for the second critical header defining the binary data size
                    size_line_raw = ser.readline()
                    try:
                        size_line = size_line_raw.decode('utf-8').rstrip('\r\n')
                        if size_line.startswith("SIZE:"):
                            total_bytes_expected = int(size_line.split(":")[1])
                            print(f"🔧 Expected binary image data payload: {total_bytes_expected} bytes.")
                    except (UnicodeDecodeError, IndexError, ValueError):
                        print("Error parsing image size header.")
                        continue
                    
                    print("🚀 Syncing and pulling raw bytes matrix from Bluetooth buffer...")
                    
                    # 3. Use specialized read() to pull the *exact* number of expected raw bytes.
                    # This prevents mixing header text data with image pixel data.
                    raw_image_data = ser.read(total_bytes_expected)
                    
                    total_bytes_received = len(raw_image_data)
                    print(f"✨ Successfully pulled {total_bytes_received} bytes.")

                    # 4. Critical Verification: Ensure the complete file arrived.
                    if total_bytes_received < total_bytes_expected:
                        print("⚠ MAJOR ERROR: Frame truncated or data lost over airwaves! Dropping frame.")
                        # This avoids the script crashing from corrupt binary data, which
                        # would happen if it tried to decode an incomplete image file.
                        continue
                    
                    # 5. DATA COMPLETE! Process image logic.
                    # Listen for the closing End-of-Frame flag to clear the serial channel.
                    ser.readline() 
                    
                    print("🎨 DATA VERIFIED! System 2 now initiating pixel-to-text mapping matrix...")
                    
                    # 6. Decode the raw binary blob back into a functional OpenCV numpy pixel array.
                    # This acts like opening the raw JPEG file directly from memory.
                    np_arr = np.frombuffer(raw_image_data, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMWRITE_UNCHANGED)
                    
                    if frame is None:
                        print("Error decoding image data matrix.")
                        continue
                        
                    # 7. Convert the fully verified and decoded portrait into beautiful ASCII Art.
                    ascii_rows = convert_to_ascii(frame)
                    
                    # 8. Render the final ASCII portrait to the screen instantly.
                    # We print a clean header first for dashboard status management.
                    clear_terminal()
                    print(f"\n=====================================================================")
                    print(f"  IMAGE RECEIVED SUCCESSFULLY!  ({total_bytes_received} bytes)     ")
                    print(f"=====================================================================")
                    print("\n".join(ascii_rows))
                    print("\n=====================================================================")
                    print("Awaiting next capture signal from ESP32...")
                
    except KeyboardInterrupt:
        print("\nShutting down Photorenderer Terminal engine.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()