#include <ArduinoBLE.h>
#include "LSM6DS3.h"
#include "Wire.h"

// Create an instance of class LSM6DS3
LSM6DS3 myIMU(I2C_MODE, 0x6A);

// USE LONG 128-BIT UUIDs 
BLEService imuService("19b10000-e8f2-537e-4f6c-d104768a1214");

BLEIntCharacteristic xChar("19b10001-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify);
BLEIntCharacteristic yChar("19b10002-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify);
BLEIntCharacteristic zChar("19b10003-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify);

// We allocate 12 bytes of space (6 microphones * 2 bytes per integer)
BLECharacteristic micArrayChar("19b10004-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify, 12);

// The 6 analog pins for the microphones
const int micPins[6] = {A0, A1, A2, A3, A4, A5}; 

// Noise Gate Threshold
// Any analog reading below this number will be forced to 0.
// This number need to be adjusted experimentally so avoid the sensors picking up random values (TO BE DECIDED LATER)
const int NOISE_THRESHOLD = 150; 

void setup() {
  Serial.begin(9600);
  
  if (myIMU.begin() != 0) {
    Serial.println("IMU error");
  } else {
    Serial.println("IMU OK!");
  }

  pinMode(LED_BUILTIN, OUTPUT); 

  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  BLE.setLocalName("Sandbag");
  BLE.setAdvertisedService(imuService); 
  
  imuService.addCharacteristic(xChar); 
  imuService.addCharacteristic(yChar); 
  imuService.addCharacteristic(zChar);    
  imuService.addCharacteristic(micArrayChar); 
  
  BLE.addService(imuService); 

  BLE.advertise();
  Serial.println("Bluetooth device active, waiting for connections...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to laptop: ");
    Serial.println(central.address());
    digitalWrite(LED_BUILTIN, LOW); 

    while (central.connected()) {
      // 1. Read and send IMU Data 
      int x = (int)(myIMU.readFloatAccelX() * 100);
      xChar.writeValue(x);      
      
      int y = (int)(myIMU.readFloatAccelY() * 100);
      yChar.writeValue(y);

      int z = (int)(myIMU.readFloatAccelZ() * 100);
      zChar.writeValue(z);   

      // 2. Read the 6 microphones with NOISE GATE
      int16_t micValues[6]; 
      for (int i = 0; i < 6; i++) {
        int rawReading = analogRead(micPins[i]);
        
        // Check if the reading beats the background static
        if (rawReading > NOISE_THRESHOLD) {
            micValues[i] = rawReading; // It's a real hit! Keep it.
        } else {
            micValues[i] = 0;          // It's just static. Force to 0.
        }
      }

      // 3. Pack and send! 
      micArrayChar.writeValue((byte*)micValues, sizeof(micValues));

      delay(50); // Send data 20 times per second
    }
    
    digitalWrite(LED_BUILTIN, HIGH); 
    Serial.println("Disconnected from laptop");
  }
}