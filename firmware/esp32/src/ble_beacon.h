#ifndef BLE_BEACON_H
#define BLE_BEACON_H

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// UUID duy nhất cho cửa của bạn (thay đổi để bảo mật)
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

class BLEBeacon {
private:
    BLEServer* pServer;
    BLECharacteristic* pCharacteristic;
    bool deviceConnected;
    String beaconId;

public:
    BLEBeacon();
    void begin(String deviceName, String beaconId);
    void update();
    bool isConnected();
    String getBeaconId();
};

#endif
