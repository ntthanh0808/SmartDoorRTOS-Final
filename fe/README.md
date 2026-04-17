# SmartDoor - Frontend

Giao diện web cho hệ thống khóa cửa thông minh với dashboard realtime, quản lý người dùng và nhận diện khuôn mặt.

## Tech Stack

- **React 19** - UI framework
- **Vite 8** - Build tool
- **Tailwind CSS 4** - Styling
- **React Router 7** - Điều hướng
- **Axios** - HTTP client
- **WebSocket** (native) - Cập nhật real-time
- **React Webcam** - Chụp ảnh khuôn mặt

## Cấu trúc thư mục

```
fe/src/
├── main.jsx                    # Entry point
├── App.jsx                     # Router setup
├── index.css                   # Tailwind import
├── api/
│   └── axios.js                # Axios instance + JWT interceptor
├── context/
│   └── AuthContext.jsx          # Auth state (login/logout/user)
├── hooks/
│   └── useWebSocket.js          # WebSocket real-time hook
├── pages/
│   ├── LoginPage.jsx            # Đăng nhập
│   ├── DashboardPage.jsx        # Admin: trạng thái + điều khiển + thông báo
│   ├── UsersPage.jsx            # Admin: CRUD người dùng + khuôn mặt
│   ├── HistoryPage.jsx          # Admin: lịch sử mở cửa
│   ├── SchedulePage.jsx         # Admin: lịch tự động
│   └── UserHomePage.jsx         # User: trạng thái + mở cửa
├── components/
│   ├── Navbar.jsx               # Thanh điều hướng
│   ├── ProtectedRoute.jsx       # Route guard (auth + role)
│   ├── DoorStatus.jsx           # Hiển thị trạng thái cửa
│   ├── DoorControl.jsx          # Nút mở/đóng cửa
│   ├── SystemLock.jsx           # Toggle khóa hệ thống
│   ├── NotificationList.jsx     # Danh sách thông báo real-time
│   ├── UserTable.jsx            # Bảng người dùng
│   ├── UserForm.jsx             # Form thêm/sửa người dùng
│   ├── FaceCaptureModal.jsx     # Modal chụp ảnh khuôn mặt
│   └── HistoryTable.jsx         # Bảng lịch sử
└── utils/
    ├── constants.js             # API_URL, WS_URL
    └── jwt.js                   # Decode JWT token
```

## Cài đặt & Chạy

```bash
cd fe
npm install
npm run dev
```

Mở trình duyệt tại `http://localhost:5173`.

## Cấu hình

Chỉnh sửa `src/utils/constants.js`:

```javascript
export const API_URL = 'http://192.168.0.100:8000/api';
export const WS_URL = 'ws://192.168.0.100:8000/ws';
```

Hoặc cấu hình proxy trong `vite.config.js`:

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://192.168.0.100:8000',
      '/ws': {
        target: 'ws://192.168.0.100:8000',
        ws: true
      }
    }
  }
})
```

## Build production

```bash
npm run build
```

Output nằm trong thư mục `dist/`. Deploy bằng cách copy thư mục này lên web server (nginx, apache, etc.).

## Các trang

| Path         | Component      | Vai trò | Mô tả                                    |
|--------------|----------------|---------|-------------------------------------------|
| `/login`     | LoginPage      | Public  | Form đăng nhập                            |
| `/dashboard` | DashboardPage  | Admin   | Trạng thái cửa, điều khiển, thông báo    |
| `/users`     | UsersPage      | Admin   | Quản lý người dùng + thẻ RFID + khuôn mặt |
| `/history`   | HistoryPage    | Admin   | Lịch sử mở/đóng cửa (có filter)         |
| `/schedule`  | SchedulePage   | Admin   | Lịch tự động khóa/mở hệ thống            |
| `/home`      | UserHomePage   | User    | Xem trạng thái + mở cửa                  |

## Tính năng

### Admin Dashboard
- **Trạng thái cửa realtime**: Hiển thị trạng thái cửa (mở/đóng/đang mở/đang đóng)
- **Điều khiển cửa**: Nút mở/đóng cửa trực tiếp
- **Khóa hệ thống**: Toggle khóa/mở khóa toàn bộ hệ thống
- **Thông báo realtime**: Danh sách thông báo với màu sắc theo category
- **Countdown**: Đếm ngược 5 giây khi cửa mở

### Quản lý người dùng
- CRUD người dùng (thêm, sửa, xóa)
- Gán thẻ RFID cho người dùng
- Đăng ký khuôn mặt cho người dùng (chụp ảnh qua webcam)
- Xem ảnh khuôn mặt đã đăng ký
- Phân quyền admin/user
- Tìm kiếm và filter

### Lịch sử
- Xem lịch sử mở/đóng cửa
- Filter theo người dùng, thời gian
- Hiển thị thông tin chi tiết: người dùng, thời gian, phương thức

### Lịch tự động
- Cấu hình tự động khóa/mở hệ thống theo giờ
- Tạo lịch cho các ngày trong tuần
- Bật/tắt lịch
- Xóa lịch

### User Home
- Xem trạng thái cửa realtime
- Nút mở cửa (nếu hệ thống không khóa)
- Nhận thông báo
- Đăng ký khuôn mặt (chụp ảnh qua webcam)

### Nhận diện khuôn mặt
- Chụp ảnh khuôn mặt qua webcam
- Đăng ký nhiều ảnh cho 1 người dùng (5-10 ảnh)
- Xem danh sách ảnh đã đăng ký
- Xóa ảnh khuôn mặt
- Hướng dẫn chụp ảnh (góc độ, ánh sáng)

## Tính năng real-time

Frontend kết nối WebSocket tới server (`/ws/client`) để nhận:

### Trạng thái cửa
```json
{"type": "door_status", "status": "opened|opening|closed|closing"}
```

### Thông báo
```json
{
  "type": "notification",
  "message": "Nguyen Van A đã mở cửa",
  "category": "access"
}
```

Categories:
- `access` (xanh lá): Mở cửa thành công
- `alert` (đỏ): Cảnh báo, thẻ không hợp lệ
- `motion` (vàng): Phát hiện chuyển động
- `schedule` (xanh dương): Lịch tự động
- `system` (xám): Thông báo hệ thống
- `lock` (đỏ): Khóa hệ thống
- `unlock` (xanh lá): Mở khóa hệ thống

### Trạng thái hệ thống
```json
{"type": "system_state", "is_locked": true|false}
```

WebSocket tự động reconnect sau 3 giây nếu mất kết nối.

## Màu sắc thông báo

Mỗi thông báo có:
- Viền trái màu theo category
- Background màu nhạt theo category
- Text màu đậm theo category

## Tài khoản mặc định

| Username | Password | Vai trò |
|----------|----------|---------|
| admin | admin123 | admin |

## Troubleshooting

### Không kết nối được backend

1. Kiểm tra backend đang chạy: `http://192.168.0.100:8000`
2. Kiểm tra `API_URL` và `WS_URL` trong `constants.js`
3. Kiểm tra CORS settings trong backend
4. Kiểm tra firewall không chặn port 8000

### WebSocket disconnect liên tục

1. Kiểm tra backend không bị crash
2. Kiểm tra JWT token hợp lệ
3. Xem log backend để biết lý do disconnect
4. Kiểm tra proxy settings trong `vite.config.js`

### Build production lỗi

1. Chạy `npm run build` và xem error message
2. Kiểm tra tất cả imports đúng
3. Kiểm tra Tailwind CSS config
4. Xóa `node_modules` và `npm install` lại

### Thông báo không hiển thị màu

1. Kiểm tra category từ backend đúng format
2. Kiểm tra Tailwind CSS đã compile
3. Xem console log để debug

### Webcam không hoạt động

1. Kiểm tra quyền Camera đã cấp cho trình duyệt
2. Kiểm tra HTTPS (một số trình duyệt yêu cầu HTTPS cho camera)
3. Thử trình duyệt khác (Chrome, Firefox)
4. Kiểm tra camera không bị ứng dụng khác sử dụng

### Ảnh khuôn mặt không upload được

1. Kiểm tra kích thước ảnh (< 5MB)
2. Kiểm tra format ảnh (JPEG, PNG)
3. Kiểm tra backend có thư mục `dataset/`
4. Xem log backend để biết lỗi chi tiết

## License

MIT
