# SmartDoor - STM32 Firmware

Firmware cho STM32F103C8 (Blue Pill), điều khiển phần cứng cửa thông minh với FreeRTOS.

## Tech Stack

- **PlatformIO** - Build system
- **STM32FreeRTOS** - Real-time operating system
- **MFRC522** - Thư viện RFID reader
- **LiquidCrystal_I2C** - Thư viện LCD I2C

## Vai trò trong hệ thống

```
RFID Reader ──┐
PIR Sensor ───┤
Limit Switch ─┤──→ STM32F103C8 ←── Serial (115200) ──→ ESP32
Motor ────────┤
LCD I2C ──────┤
Buzzer ───────┘
```

STM32 xử lý tất cả phần cứng và logic điều khiển cửa:
- Đọc thẻ RFID và gửi lên ESP32
- Điều khiển motor mở/đóng cửa
- Hiển thị thông tin trên LCD
- Phát hiện chuyển động qua PIR
- Tự động đóng cửa sau 5 giây
- Kiểm tra limit switches để dừng motor

## Phần cứng kết nối

### RFID Reader (MFRC522)
| Pin MFRC522 | Pin STM32 | Mô tả |
|-------------|-----------|-------|
| SDA/SS      | PA4       | Slave Select |
| SCK         | PA5       | SPI Clock |
| MOSI        | PA7       | SPI MOSI |
| MISO        | PA6       | SPI MISO |
| RST         | PA3       | Reset |
| 3.3V        | 3.3V      | Nguồn (KHÔNG DÙNG 5V!) |
| GND         | GND       | Ground |

### LCD I2C (16x2)
| Pin LCD | Pin STM32 | Mô tả |
|---------|-----------|-------|
| SDA     | PB7       | I2C Data |
| SCL     | PB6       | I2C Clock |
| VCC     | 5V        | Nguồn |
| GND     | GND       | Ground |

**Địa chỉ I2C:** 0x27 (có thể là 0x3F, dùng I2C scanner để kiểm tra)

### Motor DC + Driver (L298N)
| Pin Driver | Pin STM32 | Mô tả |
|------------|-----------|-------|
| IN1        | PB0       | Điều khiển chiều 1 |
| IN2        | PB1       | Điều khiển chiều 2 |
| ENA        | PA8       | PWM tốc độ |
| Motor +    | Motor     | Kết nối motor |
| Motor -    | Motor     | Kết nối motor |
| 12V        | 12V PSU   | Nguồn motor (riêng) |
| GND        | GND       | Ground chung |

**Tốc độ motor:** 150/255 (có thể điều chỉnh trong code)

### Cảm biến PIR
| Pin PIR | Pin STM32 | Mô tả |
|---------|-----------|-------|
| OUT     | PA0       | Digital output |
| VCC     | 5V        | Nguồn |
| GND     | GND       | Ground |

### Buzzer
| Pin Buzzer | Pin STM32 | Mô tả |
|------------|-----------|-------|
| +          | PA1       | Digital output |
| -          | GND       | Ground |

### Limit Switches
| Switch | Pin STM32 | Mô tả |
|--------|-----------|-------|
| Limit Open  | PC13 | INPUT_PULLUP (LOW = đã chạm) |
| Limit Close | PC14 | INPUT_PULLUP (LOW = đã chạm) |

**Lưu ý:** Limit switches dùng INPUT_PULLUP, đọc LOW khi chạm, HIGH khi không chạm.

### UART Communication
| UART | RX Pin | TX Pin | Baud | Mục đích |
|------|--------|--------|------|----------|
| Serial1 | PA10 | PA9 | 115200 | Giao tiếp với ESP32 |
| Serial3 | PB11 | PB10 | 9600 | Debug log (optional) |

## Giao thức Serial với ESP32

### STM32 → ESP32
```
RFID:xxxxxxxx        // UID thẻ RFID (hex uppercase)
PIR:Motion           // Phát hiện chuyển động
Door:Opening         // Cửa đang mở
Door:Opened          // Cửa đã mở xong
Door:Closing         // Cửa đang đóng
Door:Closed          // Cửa đã đóng xong
```

### ESP32 → STM32
```
ALLOW:Tên người      // Cho phép mở cửa
DENY                 // Từ chối (thẻ không hợp lệ hoặc hệ thống khóa)
CLOSE                // Lệnh đóng cửa
LOCKED               // Hệ thống đã khóa
UNLOCKED             // Hệ thống đã mở khóa
TIME:HH:MM:SS        // Cập nhật thời gian (khi khóa)
```

## FreeRTOS Tasks

| Task | Priority | Stack | Chức năng |
|------|----------|-------|-----------|
| taskStartup | 4 | 256 | Khởi động hệ thống, đóng cửa ban đầu, tự xóa sau khi xong |
| taskSerial | 3 | 256 | Nhận lệnh từ ESP32 qua UART1 |
| taskRFID | 2 | 256 | Quét thẻ RFID liên tục, gửi UID lên ESP32 |
| taskMotor | 2 | 256 | Điều khiển motor, kiểm tra limit switches |
| taskPIR | 1 | 256 | Phát hiện chuyển động, tự động mở cửa (nếu không khóa) |
| taskAutoClose | 1 | 128 | Đếm ngược 5 giây, tự động đóng cửa |

**Lưu ý:** Priority càng cao càng ưu tiên. taskStartup có priority cao nhất để đảm bảo khởi động đúng.

## Luồng hoạt động

### Khởi động
1. Hiển thị "Xin chao!" trên LCD
2. Đóng cửa về vị trí ban đầu (chạm limit close)
3. Hiển thị "Moi quet the..."
4. Sẵn sàng hoạt động

### Quét thẻ RFID (hệ thống mở)
1. Đọc UID thẻ → gửi `RFID:xxxxxxxx` lên ESP32
2. Hiển thị "Dang kiem tra..." trên LCD
3. Chờ phản hồi từ server qua ESP32
4. Nhận `ALLOW:Tên` từ ESP32
5. Kêu 1 tiếng beep (200ms)
6. Hiển thị "Xin chao Tên!" trên LCD
7. Mở cửa → gửi `Door:Opening` → `Door:Opened`
8. Đếm ngược 5 giây
9. Tự động đóng cửa → gửi `Door:Closing` → `Door:Closed`
10. Hiển thị "Moi quet the..." trở lại

### Quét thẻ RFID (hệ thống khóa)
1. Đọc UID thẻ → gửi `RFID:xxxxxxxx` lên ESP32
2. Nhận `DENY` từ ESP32
3. Kêu 3 tiếng beep (150ms x3)
4. LCD không đổi (vẫn hiển thị "He thong da khoa!" và thời gian)
5. Không mở cửa

### Phát hiện chuyển động (PIR)
1. PIR sensor phát hiện chuyển động
2. Gửi `PIR:Motion` lên ESP32
3. Nếu hệ thống không khóa: Tự động mở cửa
4. Nếu hệ thống khóa: Không làm gì

### Khóa hệ thống
1. Nhận `LOCKED` từ ESP32
2. Kêu 2 tiếng beep (200ms x2)
3. LCD hiển thị "He thong da khoa!" (dòng 1)
4. Nhận `TIME:HH:MM:SS` mỗi giây và hiển thị (dòng 2)
5. PIR sensor bị vô hiệu hóa
6. RFID vẫn quét nhưng không mở cửa

### Mở khóa hệ thống
1. Nhận `UNLOCKED` từ ESP32
2. Kêu 2 tiếng beep (200ms x2)
3. LCD hiển thị "Moi quet the..."
4. PIR sensor hoạt động trở lại

### Điều khiển motor
1. Mở cửa: IN1=HIGH, IN2=LOW, PWM=150
2. Đóng cửa: IN1=LOW, IN2=HIGH, PWM=150
3. Dừng: IN1=LOW, IN2=LOW, PWM=0
4. Kiểm tra limit switches liên tục
5. Dừng motor khi chạm limit switch

## Âm thanh Buzzer

| Số tiếng beep | Thời lượng | Ý nghĩa |
|---------------|------------|---------|
| 1 beep | 200ms | Thẻ hợp lệ, mở cửa thành công |
| 2 beep | 200ms x2 | Khóa/mở khóa hệ thống |
| 3 beep | 150ms x3 | Thẻ không hợp lệ hoặc quét khi khóa |

## Build & Upload

```bash
# Build
pio run

# Upload lên STM32
pio run --target upload

# Monitor Serial (debug qua UART3)
pio device monitor -b 9600
```

## Upload method

STM32F103C8 có thể upload bằng:

1. **ST-Link V2**: Kết nối SWDIO, SWCLK, GND, 3.3V
2. **USB Serial (FTDI)**: Kết nối PA9 (TX), PA10 (RX), GND, 3.3V, đặt BOOT0=1
3. **USB DFU**: Nếu đã flash bootloader USB

Trong `platformio.ini`:
```ini
upload_protocol = stlink  ; hoặc serial, dfu
```

## Debug Log

Kết nối UART3 (PB10-TX) với USB-Serial adapter (9600 baud) để xem:

```
=== STM32 SmartDoor System ===
Initializing...
[LCD] Xin chao!
[LCD] Cua dang dong...
[Motor] Door fully closed
[LCD] Moi quet the...
[RFID] Card detected: AB12CD34
[Serial] Sent: RFID:AB12CD34
[Serial] Received: ALLOW:Nguyen Van A
[LCD] Xin chao Nguyen Van A!
[Motor] Opening door...
[Motor] Door fully opened
[Motor] Auto-close scheduled in 5 seconds
[Motor] Closing door...
[Motor] Door fully closed
```

## Troubleshooting

### RFID không đọc được thẻ
- Kiểm tra kết nối SPI (PA4-SS, PA5-SCK, PA6-MISO, PA7-MOSI, PA3-RST)
- Kiểm tra nguồn 3.3V cho MFRC522 (KHÔNG DÙNG 5V!)
- Thử thẻ khác hoặc đưa thẻ gần hơn (< 5cm)
- Kiểm tra thư viện MFRC522 đã cài đặt
- Dùng example code MFRC522 để test module

### LCD không hiển thị
- Kiểm tra kết nối I2C (PB6-SCL, PB7-SDA)
- Kiểm tra địa chỉ I2C: thử 0x27 hoặc 0x3F
- Dùng I2C scanner để tìm địa chỉ đúng
- Kiểm tra nguồn 5V cho LCD
- Điều chỉnh biến trở contrast trên LCD (xoay vít nhỏ)

### Motor không chạy
- Kiểm tra kết nối driver (PB0-IN1, PB1-IN2, PA8-ENA)
- Kiểm tra nguồn motor driver (12V riêng, không dùng chung STM32)
- Kiểm tra PWM trên PA8 (dùng oscilloscope hoặc LED)
- Thử tăng giá trị PWM trong code (hiện tại 150/255)
- Kiểm tra motor driver không bị hỏng
- Kiểm tra motor không bị kẹt

### Limit switch không hoạt động
- Kiểm tra kết nối PC13 (open), PC14 (close)
- Kiểm tra INPUT_PULLUP: đọc HIGH khi không chạm, LOW khi chạm
- Dùng multimeter kiểm tra switch đóng/mở
- Xem log Serial3 để kiểm tra giá trị đọc được
- Thử đổi switch hoặc dùng external pullup resistor (10kΩ)

### ESP32 không nhận được message
- Kiểm tra kết nối UART:
  - STM32 TX (PA9) → ESP32 RX (GPIO16)
  - STM32 RX (PA10) → ESP32 TX (GPIO17)
  - GND chung giữa STM32 và ESP32
- Kiểm tra baud rate: 115200 (cả 2 bên)
- Xem log trên Serial3 (STM32) và Serial (ESP32)
- Thử swap TX/RX nếu không nhận được
- Kiểm tra logic level: STM32 dùng 3.3V, ESP32 dùng 3.3V (OK)

### FreeRTOS crash hoặc hang
- Kiểm tra stack size đủ lớn (tối thiểu 128 words)
- Kiểm tra không có deadlock giữa các tasks
- Kiểm tra không có infinite loop trong tasks
- Dùng `vTaskDelay()` trong mỗi task để yield CPU
- Xem log để biết task nào bị crash

### PIR sensor không hoạt động
- Kiểm tra kết nối PA0, 5V, GND
- Kiểm tra PIR đã warm-up (chờ 30-60 giây sau khi bật nguồn)
- Điều chỉnh sensitivity và delay trên PIR (2 biến trở)
- Thử di chuyển trước PIR để test
- Kiểm tra không có vật cản che PIR

### Buzzer không kêu
- Kiểm tra kết nối PA1, GND
- Kiểm tra polarity: + vào PA1, - vào GND
- Thử buzzer khác (có thể bị hỏng)
- Kiểm tra code có gọi hàm beep đúng

## Lưu ý

- Board: `genericSTM32F103C8` (Blue Pill)
- Nguồn STM32: 5V qua USB hoặc 5V pin (tối thiểu 500mA)
- Motor cần nguồn riêng (12V), không dùng chung với STM32 (gây nhiễu và quá tải)
- Limit switches dùng INPUT_PULLUP (LOW = active)
- LCD I2C address: 0x27 (có thể khác, dùng I2C scanner)
- RFID dùng 3.3V (KHÔNG DÙNG 5V sẽ hỏng module!)
- FreeRTOS scheduler tự động quản lý tasks
- Không dùng `loop()`, tất cả logic trong tasks
- GND phải chung giữa tất cả thiết bị
- Motor driver cần heatsink nếu chạy lâu
- Không để motor chạy quá lâu (có thể cháy driver)
- Limit switches rất quan trọng để bảo vệ motor

## License

MIT
