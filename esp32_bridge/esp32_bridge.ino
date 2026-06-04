#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

const int CHUNK_SIZE = 512;
uint8_t buffer[CHUNK_SIZE];

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT_Demo");
  delay(1000);
  Serial.println("BRIDGE_READY");
}

void loop() {
  // USB → Bluetooth
  if (Serial.available()) {
    int len = Serial.readBytes(buffer, CHUNK_SIZE);
    if (len > 0) {
      SerialBT.write(buffer, len);
    }
  }

  // Bluetooth → USB
  if (SerialBT.available()) {
    int len = SerialBT.readBytes(buffer, CHUNK_SIZE);
    if (len > 0) {
      Serial.write(buffer, len);
    }
  }
}
