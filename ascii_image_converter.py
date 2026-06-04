import serial
import sys
import os
import time

# ============================================================
#  PHOTOBOOTH RECEIVER — System2
#  Receives ASCII art over Bluetooth and displays it
# ============================================================

COM_PORT    = "COM9"   # <-- System2's Bluetooth COM port
BAUD_RATE   = 115200
SAVE_FOLDER = r"D:\Shreya\Projects_PES\esp32_photobooth\esp32_ascii_art\ascii_photostrip"

def main():
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    print(f"Connecting to ESP32 Bluetooth on {COM_PORT}...")
    try:
        bt = serial.Serial(COM_PORT, BAUD_RATE, timeout=60)
        time.sleep(2)
        bt.reset_input_buffer()
        print("Connected! Waiting for ASCII art...\n")
    except serial.SerialException as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    lines        = []
    receiving    = False
    total_lines  = 0

    try:
        while True:
            raw  = bt.readline()
            line = raw.decode("utf-8", errors="ignore").rstrip("\n").rstrip("\r")

            if line.startswith("ASCII_START"):
                # Format: ASCII_START|total_lines
                parts       = line.split("|")
                total_lines = int(parts[1]) if len(parts) > 1 else 0
                lines       = []
                receiving   = True
                print(f"Receiving ASCII art ({total_lines} lines)...\n")

            elif line == "ASCII_END" and receiving:
                receiving = False

                # Clear terminal and print full ASCII art
                os.system("cls")
                full_art = "\n".join(lines)
                print(full_art)

                # Save to file
                timestamp = time.strftime("%H%M%S")
                save_path = os.path.join(SAVE_FOLDER, f"ascii_photo_{timestamp}.txt")
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(full_art)

                print(f"\n\n your ASCII art photostrip has been saved to: {save_path}")
                print("Waiting for next photo...\n")

            elif receiving:
                lines.append(line)
                print(f"  Receiving line {len(lines)}/{total_lines}", end="\r")

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        bt.close()

if __name__ == "__main__":
    main()