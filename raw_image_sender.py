import serial
import time
import cv2
import sys

# --- CONFIGURATION ---
# Replace with the actual hardware USB COM Port of your ESP32 on System 1
SERIAL_PORT = "COM7"  
BAUD_RATE = 115200

# The JPEG quality factor (0-100). Higher = clearer but slower to send.
IMAGE_QUALITY = 80 

def main():
    print(f"Initializing hardware interface link on {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except Exception as e:
        print(f"Serial initialization error! Check your port: {e}")
        return
    time.sleep(2) # Stabilize bridge

    cap = cv2.VideoCapture(0) # 0 captures the default built-in hardware camera
    if not cap.isOpened():
        print("Error: Could not access laptop camera hardware.")
        return

    print("\n====================================================")
    print("             ESP32 RAW IMAGE TRANSPORTER            ")
    print("====================================================")
    print("Instructions:")
    print(" -> Pose and press [SPACEBAR] to send the raw photo!")
    print(" -> Press [Q] to close the application.")
    print("====================================================\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1) # Flip for natural mirror effect
        
        preview_window = frame.copy()
        cv2.putText(preview_window, "READY - PRESS SPACE TO SEND PHOTO", (15, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("System 1 Hardware Webcam Preview", preview_window)
        key = cv2.waitKey(1) & 0xFF
        
        # SPACEBAR captured! Send the photo.
        if key == ord(' '):
            print("\n📸 SAY CHEESE! Captured frame.")
            
            # Flash effect on preview screen
            flash_screen = frame.copy()
            flash_screen[:] = 255
            cv2.imshow("System 1 Hardware Webcam Preview", flash_screen)
            cv2.waitKey(100)

            print("🔧 Encoding frame as a high-quality JPEG binary blob...")
            # Convert the raw OpenCV frame (numpy array) into a JPEG file in memory
            # The encoding parameters define the image quality.
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), IMAGE_QUALITY]
            result, encimg = cv2.imencode('.jpg', frame, encode_param)
            
            if not result:
                print("Error encoding image frame.")
                continue

            # This is your raw image data! It is a massive binary array of bytes.
            raw_image_data = encimg.tobytes()
            total_bytes = len(raw_image_data)
            print(f"Image successfully encoded into {total_bytes} bytes of raw data.")

            print("🚀 Transmitting raw image stream asynchronously over the ESP32 bridge...")
            
            # We send special "Flag Headers" so System 2 knows exactly when a frame starts
            # and how many bytes to expect in the data payload block.
            ser.write(b"---START_FRAME---\n")
            
            # Use Python's built-in string formatting to convert the number (e.g., 54321)
            # into a string "54321" which we can encode and send seamlessly.
            data_size_header = (f"SIZE:{total_bytes}\n").encode('utf-8')
            ser.write(data_size_header)
            
            # Dumps the entire raw image byte sequence into the USB serial buffer.
            # Python waits until all bytes are pushed before moving to the next line.
            ser.write(raw_image_data)
            
            # Tells System 2 the entire block has been sent successfully.
            ser.write(b"\n---END_FRAME---\n")
            print("✨ Transmission complete! Image sent over airwaves.")
            
        elif key == ord('q'):
            print("Closing application.")
            break

    cap.release()
    cv2.destroyAllWindows()
    ser.close()

if __name__ == "__main__":
    main()