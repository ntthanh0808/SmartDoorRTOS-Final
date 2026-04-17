# SmartDoor - Backend

Server API cho hệ thống khóa cửa thông minh với tích hợp nhận diện khuôn mặt AI.

## Tech Stack

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM (SQLite)
- **python-jose** - JWT authentication
- **passlib** - Bcrypt password hashing
- **WebSocket** - Giao tiếp real-time với ESP32 và Frontend
- **PyTorch** - Deep learning framework
- **OpenCV** - Computer vision
- **ResNet18** - Face recognition model

## Cấu trúc thư mục

```
be/
├── main.py              # Entry point, khởi tạo app + seed admin
├── config.py            # Cấu hình (SECRET_KEY, DB, DEVICE_TOKEN)
├── database.py          # SQLAlchemy engine + session
├── requirements.txt
├── train.py             # Script train model nhận diện khuôn mặt
├── savedata.py          # Script lưu ảnh khuôn mặt từ ESP32
├── rfid_face_client.py  # Client WebSocket test
├── get_token.py         # Script lấy JWT token
├── models/
│   ├── user.py          # Bảng users
│   ├── history.py       # Bảng history
│   └── system_state.py  # Bảng system_state (singleton)
├── schemas/             # Pydantic request/response schemas
│   ├── auth.py
│   ├── user.py
│   └── history.py
├── routers/
│   ├── auth.py          # POST /api/auth/login
│   ├── users.py         # CRUD /api/users (admin)
│   ├── door.py          # /api/door/open|close|lock|unlock|status
│   ├── history.py       # GET /api/history
│   └── face_recognition.py  # /api/face/* - Nhận diện khuôn mặt
├── services/
│   ├── auth_service.py  # JWT + password utilities
│   ├── door_service.py  # Gửi lệnh tới ESP32 qua WebSocket
│   ├── notification.py  # Broadcast thông báo tới frontend
│   └── scheduler_service.py  # Lịch tự động
├── ws/
│   ├── device_ws.py     # WS /ws/device - endpoint cho ESP32
│   └── client_ws.py     # WS /ws/client - endpoint cho Frontend
├── middleware/
│   └── auth_middleware.py  # JWT auth dependency
├── ai_model/
│   ├── face_recognition.py  # Model nhận diện khuôn mặt
│   └── train_model.py       # Train model
└── dataset/             # Thư mục chứa ảnh khuôn mặt
    └── [user_id]/       # Mỗi user có 1 thư mục
        ├── 1.jpg
        ├── 2.jpg
        └── ...
```

## Cài đặt & Chạy

```bash
cd be
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server chạy tại `http://localhost:8000`. Docs tại `http://localhost:8000/docs`.

## Tài khoản mặc định

| Username | Password   | Vai trò |
|----------|------------|---------|
| admin    | admin123   | admin   |

Tài khoản admin được tạo tự động khi khởi động lần đầu.

## API Endpoints

| Method | Path                | Auth   | Mô tả                     |
|--------|---------------------|--------|----------------------------|
| POST   | `/api/auth/login`   | -      | Đăng nhập, trả JWT        |
| GET    | `/api/users`        | Admin  | Danh sách người dùng      |
| POST   | `/api/users`        | Admin  | Tạo người dùng mới        |
| PUT    | `/api/users/{id}`   | Admin  | Sửa người dùng            |
| DELETE | `/api/users/{id}`   | Admin  | Xóa người dùng            |
| GET    | `/api/door/status`  | User+  | Trạng thái cửa hiện tại   |
| POST   | `/api/door/open`    | User+  | Mở cửa                    |
| POST   | `/api/door/close`   | User+  | Đóng cửa                  |
| POST   | `/api/door/lock`    | Admin  | Khóa hệ thống             |
| POST   | `/api/door/unlock`  | Admin  | Mở khóa hệ thống          |
| GET    | `/api/history`      | Admin  | Lịch sử mở/đóng cửa      |
| POST   | `/api/face/register`| User+  | Đăng ký khuôn mặt         |
| POST   | `/api/face/recognize`| -     | Nhận diện khuôn mặt       |
| GET    | `/api/face/users/{id}/images`| Admin | Lấy ảnh khuôn mặt |
| DELETE | `/api/face/users/{id}/images`| Admin | Xóa ảnh khuôn mặt |
| GET    | `/api/schedules`    | Admin  | Danh sách lịch tự động    |
| POST   | `/api/schedules`    | Admin  | Tạo lịch tự động          |
| PATCH  | `/api/schedules/{id}`| Admin | Cập nhật lịch            |
| DELETE | `/api/schedules/{id}`| Admin | Xóa lịch                 |
| WS     | `/ws/device`        | Token  | WebSocket cho ESP32        |
| WS     | `/ws/client`        | JWT    | WebSocket cho Frontend     |

## WebSocket Protocol

### ESP32 → Server

```json
{"event": "card_scanned", "card_uid": "AB:CD:EF:12"}
{"event": "door_status", "status": "opened|opening|closed|closing"}
{"event": "motion_detected"}
{"event": "face_captured", "image": "base64_encoded_image"}
```

### Server → ESP32

```json
{"action": "open_door", "name": "Nguyen Van A"}
{"action": "close_door"}
{"action": "deny", "reason": "invalid|locked"}
{"action": "system_locked"}
{"action": "system_unlocked"}
{"action": "face_recognized", "user_id": 1, "name": "Nguyen Van A"}
{"action": "face_unknown"}
```

### Server → Frontend

```json
{"type": "door_status", "status": "opened|opening|closed|closing"}
{"type": "notification", "message": "...", "category": "access|alert|motion"}
{"type": "system_state", "is_locked": true|false}
```

## Database

SQLite, file `smartdoor.db` được tạo tự động. Gồm 3 bảng:

- **users** - Người dùng (username, password, role, card_uid)
- **history** - Lịch sử mở/đóng cửa
- **system_state** - Trạng thái hệ thống (khóa/mở, trạng thái cửa)

## Cấu hình

Sửa trong `config.py` hoặc đặt biến môi trường:

| Biến            | Mặc định                          | Mô tả                    |
|-----------------|------------------------------------|---------------------------|
| `SECRET_KEY`    | `smartdoor-secret-key-change-...`  | Khóa bí mật JWT          |
| `DATABASE_URL`  | `sqlite:///./smartdoor.db`         | Đường dẫn database        |
| `DEVICE_TOKEN`  | `esp32-secret-token`               | Token xác thực ESP32      |

## Tính năng BLE (Bluetooth Low Energy)

Backend hỗ trợ xác thực mở cửa qua BLE beacon:

### Endpoint BLE

```
POST /api/door/open-ble
Body: {"beacon_id": "SMARTDOOR_BEACON_001"}
```

### Luồng hoạt động

1. Mobile app quét BLE beacon từ ESP32
2. Kiểm tra khoảng cách (RSSI > -50 = trong vòng 1m)
3. Đọc Beacon ID từ ESP32
4. Gửi request mở cửa kèm Beacon ID
5. Server xác thực Beacon ID
6. Nếu hợp lệ, gửi lệnh mở cửa xuống ESP32

### Cấu hình Beacon

Trong `config.py`:

```python
VALID_BEACON_IDS = ["SMARTDOOR_BEACON_001"]
```

## Nhận diện khuôn mặt (Face Recognition)

Backend sử dụng PyTorch và ResNet18 để nhận diện khuôn mặt.

### Cách hoạt động

1. **Đăng ký khuôn mặt**: User chụp 5-10 ảnh khuôn mặt từ nhiều góc độ
2. **Lưu dataset**: Ảnh được lưu vào `dataset/[user_id]/`
3. **Train model**: Chạy `python train.py` để train model
4. **Nhận diện**: ESP32 gửi ảnh lên server, server nhận diện và trả về user_id

### Endpoints nhận diện khuôn mặt

```
POST /api/face/register
Body: {
  "user_id": 1,
  "image": "base64_encoded_image"
}

POST /api/face/recognize
Body: {
  "image": "base64_encoded_image"
}
Response: {
  "user_id": 1,
  "confidence": 0.95,
  "name": "Nguyen Van A"
}
```

### Train model

```bash
# Sau khi đăng ký khuôn mặt cho nhiều user
python train.py

# Model được lưu tại: resnet18_face.pth
```

### Cấu hình model

Trong `ai_model/face_recognition.py`:

```python
MODEL_PATH = "resnet18_face.pth"
CONFIDENCE_THRESHOLD = 0.7  # Ngưỡng tin cậy
IMAGE_SIZE = (224, 224)     # Kích thước ảnh input
```

### Yêu cầu

- Ảnh khuôn mặt rõ nét, đủ sáng
- Khuôn mặt chiếm ít nhất 30% ảnh
- Mỗi user cần ít nhất 5 ảnh để train
- Ảnh từ nhiều góc độ khác nhau

## Lịch tự động

Backend hỗ trợ tự động khóa/mở hệ thống theo giờ:

### Endpoints

```
GET  /api/schedules           # Danh sách lịch
POST /api/schedules           # Tạo lịch mới
Body: {
  "time": "08:00",
  "action": "unlock",
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "is_active": true
}

PATCH /api/schedules/{id}     # Cập nhật lịch
DELETE /api/schedules/{id}    # Xóa lịch
```

### Cách hoạt động

- Background task chạy mỗi phút kiểm tra thời gian
- Nếu đến giờ trong lịch: Thực hiện action (lock/unlock)
- Gửi thông báo qua WebSocket cho frontend
- Chỉ chạy vào các ngày được chọn

## Troubleshooting

### ESP32 không kết nối được WebSocket

1. Kiểm tra `DEVICE_TOKEN` trong `config.py` khớp với ESP32
2. Kiểm tra firewall không chặn port 8000
3. Kiểm tra ESP32 đã kết nối WiFi
4. Xem log backend: `uvicorn main:app --log-level debug`

### Frontend không nhận WebSocket

1. Kiểm tra JWT token hợp lệ
2. Kiểm tra WebSocket URL đúng: `ws://IP:8000/ws/client`
3. Kiểm tra CORS settings trong `main.py`

### Database bị lỗi

1. Xóa file `smartdoor.db` và khởi động lại
2. Kiểm tra quyền ghi file trong thư mục `be/`

### BLE không hoạt động

1. Kiểm tra `VALID_BEACON_IDS` trong `config.py`
2. Kiểm tra ESP32 đang broadcast BLE beacon
3. Xem log request `/api/door/open-ble`

### Nhận diện khuôn mặt không chính xác

1. Kiểm tra model đã train: `resnet18_face.pth` phải tồn tại
2. Chạy lại `python train.py` với nhiều ảnh hơn
3. Tăng số lượng ảnh training (ít nhất 10 ảnh/user)
4. Kiểm tra ảnh đủ sáng và rõ nét
5. Giảm `CONFIDENCE_THRESHOLD` nếu model quá strict

### Train model lỗi

1. Kiểm tra PyTorch đã cài đặt: `pip install torch torchvision`
2. Kiểm tra thư mục `dataset/` có ảnh
3. Kiểm tra GPU/CPU: Model tự động chọn device
4. Xem log chi tiết khi chạy `python train.py`

## License

MIT
