import { PermissionsAndroid, Platform } from 'react-native';
import { BleManager } from 'react-native-ble-plx';
import { decode as base64Decode } from 'base-64';

// UUID phải khớp với ESP32
const SERVICE_UUID = '4fafc201-1fb5-459e-8fcc-c5c9c331914b';
const CHARACTERISTIC_UUID = 'beb5483e-36e1-4688-b7f5-ea07361b26a8';

class BLEService {
  constructor() {
    this.manager = new BleManager();
    this.device = null;
    this.beaconId = null;
  }

  // Yêu cầu quyền Bluetooth (Android)
  async requestPermissions() {
    if (Platform.OS === 'android') {
      if (Platform.Version >= 31) {
        // Android 12+
        const granted = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN,
          PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
        ]);
        return Object.values(granted).every(
          status => status === PermissionsAndroid.RESULTS.GRANTED
        );
      } else {
        // Android < 12
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION
        );
        return granted === PermissionsAndroid.RESULTS.GRANTED;
      }
    }
    return true; // iOS không cần request runtime permission
  }

  // Quét BLE beacon
  async scanForBeacon(timeout = 5000) {
    console.log('[BLE] Starting scan...');
    
    const hasPermission = await this.requestPermissions();
    if (!hasPermission) {
      throw new Error('Cần cấp quyền Bluetooth và Location');
    }

    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.manager.stopDeviceScan();
        reject(new Error('Không tìm thấy cửa. Hãy đến gần hơn!'));
      }, timeout);

      this.manager.startDeviceScan(
        [SERVICE_UUID],
        { allowDuplicates: false },
        async (error, device) => {
          if (error) {
            clearTimeout(timeoutId);
            this.manager.stopDeviceScan();
            reject(error);
            return;
          }

          if (device && device.serviceUUIDs?.includes(SERVICE_UUID)) {
            console.log('[BLE] Found beacon:', device.name, 'RSSI:', device.rssi);
            
            // Kiểm tra khoảng cách: RSSI > -50 = trong vòng 1m
            if (device.rssi < -50) {
              console.log('[BLE] Device too far, RSSI:', device.rssi);
              // Tiếp tục quét, không reject ngay
              return;
            }
            
            clearTimeout(timeoutId);
            this.manager.stopDeviceScan();
            
            try {
              // Kết nối và đọc beacon ID
              this.device = device;
              await device.connect();
              await device.discoverAllServicesAndCharacteristics();
              
              const characteristic = await device.readCharacteristicForService(
                SERVICE_UUID,
                CHARACTERISTIC_UUID
              );
              
              this.beaconId = base64Decode(characteristic.value);
              console.log('[BLE] Beacon ID:', this.beaconId);
              
              resolve({
                beaconId: this.beaconId,
                deviceName: device.name,
                rssi: device.rssi,
              });
            } catch (err) {
              reject(err);
            }
          }
        }
      );
    });
  }

  // Ngắt kết nối
  async disconnect() {
    if (this.device) {
      await this.device.cancelConnection();
      this.device = null;
      this.beaconId = null;
    }
  }

  // Lấy beacon ID hiện tại
  getBeaconId() {
    return this.beaconId;
  }
}

export default new BLEService();
