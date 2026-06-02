#include "BluetoothSerial.h"

// Instantiate the Bluetooth classic serial object
BluetoothSerial SerialBT;

void setup() {
  // Open the hardware USB Serial pipeline at 115200 baudrate
  Serial.begin(115200);
  
  // Initialize the Bluetooth broadcast identity beacon
  // This is the name your friend's laptop will search for in Bluetooth settings
  SerialBT.begin("ESP32_ASCII_Bridge"); 
  
  Serial.println("=====================================================");
  Serial.println("            ESP32 WIRELESS DATA REPLAY BRIDGE        ");
  Serial.println("=====================================================");
  Serial.println("Status: Hardware Interfaces Initialized.");
  Serial.println("Action: Pair System 2 with 'ESP32_ASCII_Bridge' now.");
  Serial.println("=====================================================");
}

void loop() {
  // DIRECTION 1: Raw Image Data from System 1 (USB) ──> System 2 (Bluetooth Airwaves)
  // Check if System 1's Python script has dumped raw JPEG bytes into the USB serial buffer
  if (Serial.available()) {
    // Read a single byte from the hardware USB UART controller chip...
    char incomingByte = Serial.read(); 
    // ...and immediately cast it out over the airwaves via the internal Bluetooth antenna
    SerialBT.write(incomingByte);      
  }
  
  // DIRECTION 2: Handshake/Control Data from System 2 (Bluetooth) ──> System 1 (USB)
  // Check if System 2 sends any data or confirmation packets back over the airwaves
  if (SerialBT.available()) {
    // Read the single byte from the wireless radio subsystem controller...
    char incomingByte = SerialBT.read(); 
    // ...and pass it straight back up the USB cable to System 1's Python terminal
    Serial.write(incomingByte);          
  }
}