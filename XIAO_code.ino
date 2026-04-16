#include <ArduinoBLE.h>
#include "LSM6DS3.h"
#include "Wire.h"

// Create an instance of class LSM6DS3
LSM6DS3 myIMU(I2C_MODE, 0x6A);

// --- 1. IMU & MICROPHONE SERVICE ---
BLEService imuService("19b10000-e8f2-537e-4f6c-d104768a1214");

BLEIntCharacteristic xChar("19b10001-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify);
BLEIntCharacteristic yChar("19b10002-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify);
BLEIntCharacteristic zChar("19b10003-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify);

// We allocate 4 bytes of space (2 microphones * 2 bytes per integer)
BLECharacteristic micArrayChar("19b10004-e8f2-537e-4f6c-d104768a1214", BLERead | BLENotify, 4);

// --- 2. STANDARD BATTERY SERVICE ---
// 180F is the official BLE UUID for Battery Service
BLEService batteryService("180F");
// 2A19 is the official BLE UUID for Battery Level (0-100%)
BLEUnsignedCharCharacteristic batteryLevelChar("2A19", BLERead | BLENotify);

// The 2 analog pins for the microphones (Top and Bottom)
const int micPins[2] = {A0, A1}; 

// Noise Gate Threshold -> TO BE ADJUSTED
const int NOISE_THRESHOLD = 10; 

// Timer to prevent reading the battery too fast
unsigned long previousBatteryMillis = 0;

void setup() {
  Serial.begin(9600);
  
  // Initialize IMU
  if (myIMU.begin() != 0) {
    Serial.println("IMU error");
  } else {
    Serial.println("IMU OK!");
  }

  // Configure Seeed XIAO Battery Reading Pins
  pinMode(PIN_VBAT_ENABLE, OUTPUT);
  digitalWrite(PIN_VBAT_ENABLE, LOW); // LOW turns the battery reading circuit ON
  
  pinMode(LED_BUILTIN, OUTPUT); 

  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  // Setup Bluetooth Details
  BLE.setLocalName("Sandbag");
  
  // Add IMU/Mic Service
  BLE.setAdvertisedService(imuService); 
  imuService.addCharacteristic(xChar); 
  imuService.addCharacteristic(yChar); 
  imuService.addCharacteristic(zChar);    
  imuService.addCharacteristic(micArrayChar); 
  BLE.addService(imuService); 

  // Add Battery Service
  batteryService.addCharacteristic(batteryLevelChar);
  BLE.addService(batteryService);

  // Start Broadcasting
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
      unsigned long currentMillis = millis();

      // 1. Read and send IMU Data 
      int x = (int)(myIMU.readFloatAccelX() * 100);
      xChar.writeValue(x);      
      
      int y = (int)(myIMU.readFloatAccelY() * 100);
      yChar.writeValue(y);

      int z = (int)(myIMU.readFloatAccelZ() * 100);
      zChar.writeValue(z);   

      // 2. Read the 2 microphones with NOISE GATE
      int16_t micValues[2]; 
      for (int i = 0; i < 2; i++) {
        int rawReading = analogRead(micPins[i]);
        
        if (rawReading > NOISE_THRESHOLD) {
            micValues[i] = rawReading; // Real hit
        } else {
            micValues[i] = 0;          // Background static
        }
      }

      // Pack and send Mic Array
      micArrayChar.writeValue((byte*)micValues, sizeof(micValues));

      // 3. Read and send Battery Level (Only update once per second to save power)
      if (currentMillis - previousBatteryMillis >= 1000) {
        previousBatteryMillis = currentMillis;
        
        int vbatRaw = analogRead(PIN_VBAT);
        Serial.print("Raw Battery Number: ");
        Serial.println(vbatRaw);
        // Map raw ADC values roughly to 0-100% 
        // (You may need to tweak 600 and 850 based on your specific lipo battery capacity)
        int batteryPercentage = map(vbatRaw, 330, 430, 0, 100);
        batteryPercentage = constrain(batteryPercentage, 0, 100);
        
        batteryLevelChar.writeValue((uint8_t)batteryPercentage);
      }

      delay(50); // Send action data 20 times per second
    }
    
    digitalWrite(LED_BUILTIN, HIGH); 
    Serial.println("Disconnected from laptop");
  }
}
