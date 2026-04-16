# SmartDoor - Backend

Server API cho hệ thống khóa cửa thông minh.

## Tech Stack

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM (SQLite)
- **python-jose** - JWT authentication
- **passlib** - Bcrypt password hashing
- **WebSocket** - Giao tiếp real-time với ESP32 và Frontend

## Cấu trúc thư mục

```
be/
├── main.py              # Entry point, khởi tạo app + seed admin
├── config.py            # Cấu hình (SECRET_KEY, DB, DEVICE_TOKEN)
├── database.py          # SQLAlchemy engine + session
├── requirements.txt
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
│   └── history.py       # GET /api/history
├── services/
│   ├── auth_service.py  # JWT + password utilities
│   ├── door_service.py  # Gửi lệnh tới ESP32 qua WebSocket
│   └── notification.py  # Broadcast thông báo tới frontend
├── ws/
│   ├── device_ws.py     # WS /ws/device - endpoint cho ESP32
│   └── client_ws.py     # WS /ws/client - endpoint cho Frontend
└── middleware/
    └── auth_middleware.py  # JWT auth dependency
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
| WS     | `/ws/device`        | Token  | WebSocket cho ESP32        |
| WS     | `/ws/client`        | JWT    | WebSocket cho Frontend     |

## WebSocket Protocol

### ESP32 → Server

```json
{"event": "card_scanned", "card_uid": "AB:CD:EF:12"}
{"event": "door_status", "status": "opened|opening|closed|closing"}
{"event": "motion_detected"}
```

### Server → ESP32

```json
{"action": "open_door", "name": "Nguyen Van A"}
{"action": "close_door"}
{"action": "deny", "reason": "invalid|locked"}
{"action": "system_locked"}
{"action": "system_unlocked"}
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

## Lịch tự động

Backend hỗ trợ tự động khóa/mở hệ thống theo giờ:

### Endpoints

```
GET  /api/door/schedule      # Lấy cấu hình lịch
POST /api/door/schedule      # Lưu cấu hình lịch
Body: {
  "enabled": true,
  "start_time": "08:00",
  "end_time": "18:00"
}
```

### Cách hoạt động

- Background task chạy mỗi phút kiểm tra thời gian
- Nếu đến `start_time`: Tự động mở khóa hệ thống
- Nếu đến `end_time`: Tự động khóa hệ thống
- Gửi thông báo qua WebSocket cho frontend

## Quản lý lịch (Schedules)

CRUD lịch tự động cho các hành động:

### Endpoints

```
GET    /api/schedules           # Danh sách lịch
POST   /api/schedules           # Tạo lịch mới
PATCH  /api/schedules/{id}      # Cập nhật lịch
DELETE /api/schedules/{id}      # Xóa lịch
```

### Ví dụ tạo lịch

```json
{
  "time": "08:00",
  "action": "unlock",
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "is_active": true
}
```

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

## License

MIT
