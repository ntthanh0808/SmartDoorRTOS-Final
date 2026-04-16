#include "ble_beacon.h"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        Serial.println("[BLE] Device connected");
    };

    void onDisconnect(BLEServer* pServer) {
        Serial.println("[BLE] Device disconnected");
        // Restart advertising
        BLEDevice::startAdvertising();
    }
};

BLEBeacon::BLEBeacon() {
    deviceConnected = false;
}

void BLEBeacon::begin(String deviceName, String id) {
    beaconId = id;
    
    Serial.println("[BLE] Initializing BLE Beacon...");
    
    // Initialize BLE
    BLEDevice::init(deviceName.c_str());
    
    // Create BLE Server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());
    
    // Create BLE Service
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Create BLE Characteristic
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ |
        BLECharacteristic::PROPERTY_NOTIFY
    );
    
    // Set beacon ID as characteristic value
    pCharacteristic->setValue(beaconId.c_str());
    
    // Add descriptor
    pCharacteristic->addDescriptor(new BLE2902());
    
    // Start service
    pService->start();
    
    // Start advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("[BLE] Beacon started!");
    Serial.print("[BLE] Beacon ID: ");
    Serial.println(beaconId);
}

void BLEBeacon::update() {
    deviceConnected = (pServer->getConnectedCount() > 0);
}

bool BLEBeacon::isConnected() {
    return deviceConnected;
}

String BLEBeacon::getBeaconId() {
    return beaconId;
}
