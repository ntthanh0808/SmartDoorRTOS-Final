# SmartDoor Mobile App

Ứng dụng di động React Native (Expo) để điều khiển và giám sát hệ thống cửa thông minh với tích hợp BLE (Bluetooth Low Energy) và nhận diện khuôn mặt.

## Công nghệ

- React Native 0.81.5
- Expo ~54.0.0
- React Navigation 7.0.0
- Axios - HTTP client
- WebSocket - Kết nối realtime
- Expo Secure Store - Lưu trữ token
- react-native-ble-plx - BLE scanning
- @react-native-community/datetimepicker - Time picker
- Expo Camera - Chụp ảnh khuôn mặt

## Yêu cầu

- Node.js 18+
- npm hoặc yarn
- Android Studio (build APK)
- Android SDK (đã cài đặt qua Android Studio)
- Gradle 8.14.3 (tự động cài qua Android Studio)

## Cài đặt

```bash
cd app
npm install
```

## Cấu hình

### 1. Cấu hình API URL

Chỉnh sửa `app.json`:

```json
{
  "expo": {
    "extra": {
      "apiUrl": "http://192.168.0.100:8000/api",
      "wsUrl": "ws://192.168.0.100:8000/ws"
    }
  }
}
```

Hoặc chỉnh sửa `src/utils/constants.js`:

```javascript
export const API_URL = 'http://192.168.0.100:8000/api';
export const WS_URL = 'ws://192.168.0.100:8000/ws';
```

### 2. Cấu hình Android SDK

Tạo file `android/local.properties`:

```properties
sdk.dir=C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Android\\Sdk
```

### 3. Cấu hình HTTP Cleartext Traffic

File `android/app/src/main/AndroidManifest.xml` đã được cấu hình:

```xml
<application
  android:usesCleartextTraffic="true"
  ...>
```

**Lưu ý:** Nếu chạy `npx expo prebuild --clean`, cần thêm lại dòng này.

## Chạy ứng dụng

### Development (Expo Go)

```bash
npm start
```

### Build APK cho Android

```bash
# Prebuild native code (nếu chưa có thư mục android)
npx expo prebuild

# Build APK Release
cd android
./gradlew --stop                    # Dừng Gradle daemon
./gradlew assembleRelease --no-daemon
```

APK sẽ nằm tại: `android/app/build/outputs/apk/release/app-release.apk`

**Lưu ý khi build:**
- Nếu gặp lỗi file locking, chạy `./gradlew --stop` trước
- Nếu gặp lỗi CMake, xóa thư mục `.cxx`: `Remove-Item -Recurse -Force android/app/.cxx`
- Build lần đầu có thể mất 5-10 phút

### Cài đặt APK lên điện thoại

```bash
adb install android/app/build/outputs/apk/release/app-release.apk
```

## Cấu trúc

```
app/
├── src/
│   ├── api/
│   │   └── axios.js              # Axios instance + JWT interceptor
│   ├── components/
│   │   ├── DoorControl.jsx       # Nút điều khiển cửa (Admin/User)
│   │   ├── DoorStatus.jsx        # Hiển thị trạng thái cửa
│   │   ├── HistoryTable.jsx      # Bảng lịch sử
│   │   ├── NotificationList.jsx  # Danh sách thông báo
│   │   ├── SystemLock.jsx        # Toggle khóa hệ thống
│   │   ├── UserForm.jsx          # Form thêm/sửa người dùng
│   │   └── UserTable.jsx         # Bảng người dùng
│   ├── context/
│   │   ├── AuthContext.jsx       # Auth state (login/logout/user)
│   │   └── WebSocketContext.jsx  # WebSocket provider
│   ├── hooks/
│   │   └── useWebSocket.js       # WebSocket hook
│   ├── navigation/
│   │   ├── AdminNavigator.jsx    # Tab navigation cho Admin
│   │   ├── AppNavigator.jsx      # Root navigator
│   │   └── UserNavigator.jsx     # Stack navigation cho User
│   ├── screens/
│   │   ├── DashboardScreen.jsx   # Admin: Dashboard
│   │   ├── HistoryScreen.jsx     # Admin: Lịch sử
│   │   ├── LoginScreen.jsx       # Đăng nhập
│   │   ├── ScheduleScreen.jsx    # Admin: Lịch tự động
│   │   ├── UserHomeScreen.jsx    # User: Trang chủ
│   │   └── UsersScreen.jsx       # Admin: Quản lý người dùng
│   ├── services/
│   │   └── bleService.js         # BLE beacon scanning
│   └── utils/
│       ├── constants.js          # API_URL, WS_URL
│       ├── jwt.js                # JWT decode
│       ├── websocket.js          # WebSocket utilities
│       └── websocket-polyfill.js # WebSocket polyfill
├── android/                      # Native Android code
├── App.jsx
├── index.js
└── app.json
```

## Tính năng

### Admin
- **Dashboard**: Điều khiển cửa trực tiếp (không cần BLE), khóa hệ thống
- **Quản lý người dùng**: CRUD người dùng, gán thẻ RFID, đăng ký khuôn mặt
- **Lịch sử**: Xem lịch sử mở/đóng cửa với filter
- **Lịch tự động**: Cấu hình tự động khóa/mở hệ thống theo giờ
- **Thông báo realtime**: Nhận thông báo qua WebSocket
- **Nhận diện khuôn mặt**: Chụp và đăng ký khuôn mặt cho người dùng

### User
- **Điều khiển cửa qua BLE**: Phải ở gần cửa (trong vòng 1m) để mở
- **Xem trạng thái realtime**: Trạng thái cửa cập nhật tức thì
- **Thông báo**: Nhận thông báo khi có sự kiện
- **Đăng ký khuôn mặt**: Chụp ảnh khuôn mặt để mở cửa bằng AI

### Chung
- Pull-to-refresh
- WebSocket realtime
- Auto-reconnect
- JWT authentication
- BLE beacon scanning

## BLE (Bluetooth Low Energy)

### Cách hoạt động

1. User nhấn nút "Mở cửa"
2. App quét BLE beacon từ ESP32 (10 giây)
3. Kiểm tra khoảng cách: RSSI > -50 (trong vòng 1m)
4. Đọc Beacon ID từ ESP32
5. Gửi request mở cửa kèm Beacon ID lên server
6. Server xác thực và cho phép mở cửa

### Cấu hình BLE

File `src/services/bleService.js`:

```javascript
const SERVICE_UUID = '4fafc201-1fb5-459e-8fcc-c5c9c331914b';
const CHARACTERISTIC_UUID = 'beb5483e-36e1-4688-b7f5-ea07361b26a8';

// Khoảng cách: RSSI > -50 = trong vòng 1m
if (device.rssi < -50) {
  // Quá xa, tiếp tục quét
  return;
}
```

### Quyền BLE (Android)

App yêu cầu các quyền sau:

- `BLUETOOTH`
- `BLUETOOTH_ADMIN`
- `BLUETOOTH_SCAN` (Android 12+)
- `BLUETOOTH_CONNECT` (Android 12+)
- `ACCESS_FINE_LOCATION`

## Phân quyền Admin vs User

### Admin
- Nút mở cửa màu xanh lá: Mở trực tiếp qua API (không cần BLE)
- Có thể khóa/mở khóa hệ thống
- Quản lý người dùng
- Xem lịch sử
- Cấu hình lịch tự động

### User
- Nút mở cửa màu xanh dương: Yêu cầu quét BLE (phải ở gần cửa)
- Chỉ xem trạng thái và điều khiển cửa
- Không thể khóa hệ thống

## Trạng thái cửa

| Trạng thái | Màu sắc | Icon | Mô tả |
|------------|---------|------|-------|
| opened | Xanh lá | 🟢 | Cửa đã mở (countdown 5s) |
| opening | Vàng | 🟡 | Cửa đang mở (nhấp nháy) |
| closed | Xám | ⚪ | Cửa đã đóng |
| closing | Vàng | 🟡 | Cửa đang đóng (nhấp nháy) |

## Thông báo

Màu sắc thông báo theo category:

| Category | Màu sắc | Ví dụ |
|----------|---------|-------|
| access | Xanh lá | Người dùng mở cửa thành công |
| unlock | Xanh lá | Hệ thống đã mở khóa |
| alert | Đỏ | Thẻ không hợp lệ |
| lock | Đỏ | Hệ thống đã khóa |
| motion | Vàng | Phát hiện chuyển động |
| schedule | Xanh dương | Lịch tự động kích hoạt |
| system | Xám | Thông báo hệ thống |

## Lịch tự động

Cấu hình tự động khóa/mở hệ thống theo giờ:

1. Vào tab "Lịch"
2. Bật toggle "Tự động đóng/mở hệ thống"
3. Chọn giờ bắt đầu (mở khóa)
4. Chọn giờ kết thúc (khóa)
5. Nhấn "Lưu cấu hình"

Ví dụ:
- Giờ bắt đầu: 08:00 → Hệ thống tự động mở khóa
- Giờ kết thúc: 18:00 → Hệ thống tự động khóa

## Tài khoản mặc định

| Username | Password | Vai trò |
|----------|----------|---------|
| admin | admin123 | admin |

## Troubleshooting

### Không kết nối được backend

1. Kiểm tra backend đang chạy: `http://192.168.0.100:8000`
2. Kiểm tra IP trong `app.json` và `constants.js`
3. Kiểm tra `usesCleartextTraffic="true"` trong AndroidManifest.xml
4. Kiểm tra firewall không chặn port 8000

### BLE không tìm thấy cửa

1. Kiểm tra ESP32 đang chạy và BLE beacon đã bật
2. Kiểm tra quyền Bluetooth và Location đã cấp
3. Đến gần cửa hơn (< 1m)
4. Kiểm tra UUID trong `bleService.js` khớp với ESP32

### Build APK thất bại

**Lỗi: Task 'assemleRelease' not found**
- Đánh máy sai, phải là `assembleRelease` (không phải `assemleRelease`)

**Lỗi: Unable to delete directory (file locking)**
```bash
# Giải pháp:
cd android
./gradlew --stop
Remove-Item -Recurse -Force app/.cxx
Remove-Item -Recurse -Force app/build
./gradlew assembleRelease --no-daemon
```

**Lỗi: CMake configuration failed**
- Xóa thư mục `.cxx` và build lại
- Kiểm tra Android NDK đã cài đặt

**Lỗi khác:**
1. Kiểm tra Android SDK đã cài đặt
2. Kiểm tra `local.properties` có đúng đường dẫn SDK
3. Chạy `./gradlew clean` trước khi build lại
4. Kiểm tra Java version (cần JDK 11 hoặc 17)
5. Đóng tất cả IDE và file explorer đang mở thư mục android

### WebSocket disconnect liên tục

1. Kiểm tra backend không bị crash
2. Kiểm tra kết nối mạng ổn định
3. Xem log backend để biết lý do disconnect

### Camera không hoạt động

1. Kiểm tra quyền Camera đã cấp
2. Kiểm tra Expo Camera đã cài đặt
3. Restart ứng dụng sau khi cấp quyền

## License

MIT
