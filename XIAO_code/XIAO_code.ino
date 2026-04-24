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

      // 2. Read the 2 microphones with Peak detection to avoid catching the swing of the sandbag
      int topPeak = 0;
      int bottomPeak = 0;

      // Every 20 miliseconds, the XIAO will listen continuously for 5 milliseconds to catch the peak of the soundwave
      for (int j = 0; j < 25; j++) {
        int t = analogRead(micPins[0]);
        if (t > topPeak) topPeak = t;

        int b = analogRead(micPins[1]);
        if (b > bottomPeak) bottomPeak = b;

        delayMicroseconds(200);
      }
    
      int16_t micValues[2]; 
      micValues[0] = (topPeak > NOISE_THRESHOLD) ? topPeak : 0;
      micValues[1] = (bottomPeak > NOISE_THRESHOLD) ? bottomPeak : 0;

      // Pack and send Mic Array
      micArrayChar.writeValue((byte*)micValues, sizeof(micValues));

      // 3. Read and send Battery Level (Only update once per second to save power)
      if (currentMillis - previousBatteryMillis >= 1000) {
        previousBatteryMillis = currentMillis;
        
        int vbatRaw = analogRead(PIN_VBAT);
        Serial.print("Raw Battery Number: ");
        Serial.println(vbatRaw);
        // Map raw ADC values roughly to 0-100% 
        // (You may need to tweak 250 and 430 based on your specific lipo battery capacity)
        int batteryPercentage = map(vbatRaw, 250, 430, 0, 100);
        batteryPercentage = constrain(batteryPercentage, 0, 100);
        
        batteryLevelChar.writeValue((uint8_t)batteryPercentage);
      }

      delay(15); // Send action data 20 times per second
    }
    
    digitalWrite(LED_BUILTIN, HIGH); 
    Serial.println("Disconnected from laptop");
  }
}
