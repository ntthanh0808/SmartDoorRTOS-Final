"""
Face Recognition Client (Standalone)
Script chạy trên laptop để:
1. Tự động mở webcam để quét khuôn mặt
2. Phát hiện khuôn mặt và chụp 20 ảnh
3. Xác thực khuôn mặt (≥10/20 ảnh khớp)
4. Gửi lệnh mở cửa nếu hợp lệ

Usage:
    python rfid_face_client.py
"""

import asyncio
import aiohttp
import cv2
import numpy as np
from datetime import datetime
from ai_model.face_recognition import face_recognition_model


# Configuration
API_URL = "http://localhost:8000"

# Load token from file or set manually
try:
    with open("token.txt", "r") as f:
        API_TOKEN = f.read().strip()
except FileNotFoundError:
    API_TOKEN = ""  # Chạy: python get_token.py để lấy token


class FaceRecognitionClient:
    def __init__(self):
        self.is_scanning = False
        self.door_opened = False
        
    async def send_open_door(self, user_name):
        """Gửi lệnh mở cửa tới server qua HTTP API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/door/open-face",
                    params={"user_name": user_name}
                ) as response:
                    if response.status == 200:
                        print("✅ Đã gửi lệnh mở cửa tới ESP32")
                        self.door_opened = True
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Lỗi gửi lệnh mở cửa: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Lỗi kết nối API: {e}")
            return False
    
    async def start_face_scan(self):
        """Mở webcam và quét khuôn mặt liên tục"""
        if self.is_scanning:
            print("⚠️ Đang quét khuôn mặt, vui lòng đợi...")
            return
        
        self.is_scanning = True
        
        print(f"\n🎥 Đang mở webcam để nhận diện khuôn mặt...")
        print(f"📸 Khi phát hiện khuôn mặt, hệ thống sẽ tự động quét 20 ảnh")
        print(f"✅ Điều kiện mở cửa: Khớp ≥10/20 ảnh")
        print(f"🔴 Nhấn 'R' để reset | Nhấn 'Q' để thoát\n")
        
        # Mở webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Không thể mở webcam")
            self.is_scanning = False
            return
        
        # Tạo cửa sổ
        window_name = "Face Recognition - Nhan dien khuon mat"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        print("🔄 Đang chờ phát hiện khuôn mặt...")
        
        recognized_person = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Hiển thị frame
            display_frame = frame.copy()
            
            # Header
            cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 80), (0, 0, 0), -1)
            
            if recognized_person:
                # Hiển thị kết quả nhận diện thành công
                cv2.putText(display_frame, f"Nhan dien thanh cong: {recognized_person}", (10, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, "Nhan 'R' de reset | 'Q' de thoat", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            else:
                cv2.putText(display_frame, "Dua khuon mat vao camera de nhan dien", (10, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(display_frame, "R: Reset | Q: Thoat", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Detect face (chỉ khi chưa nhận diện thành công)
            if not recognized_person:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_recognition_model.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60)
                )
                
                # Vẽ bounding box
                for (x, y, w, h) in faces:
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(display_frame, "Face Detected", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Nếu phát hiện khuôn mặt, bắt đầu quét
                if len(faces) > 0:
                    print(f"\n{'='*60}")
                    print(f"👤 Phát hiện khuôn mặt! Bắt đầu quét...")
                    print(f"{'='*60}")
                    
                    # Đóng cửa sổ hiện tại
                    cv2.destroyWindow(window_name)
                    
                    # Bắt đầu quét 20 ảnh
                    recognized_person = await self.capture_and_recognize(cap)
                    
                    # Mở lại cửa sổ
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    
                    if recognized_person:
                        print(f"✅ Nhận diện thành công: {recognized_person}")
                        print("💡 Nhấn 'R' để reset và quét lại, 'Q' để thoát")
                    else:
                        print("\n🔄 Đang chờ phát hiện khuôn mặt tiếp theo...")
            
            cv2.imshow(window_name, display_frame)
            
            # Kiểm tra phím tắt
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n⚠️ Đã thoát")
                break
            elif key == ord('r') or key == ord('R'):
                if recognized_person:
                    print("\n🔄 Reset - Đang chờ phát hiện khuôn mặt tiếp theo...")
                    recognized_person = None
                    self.door_opened = False
        
        # Đóng webcam
        cap.release()
        cv2.destroyAllWindows()
        
        self.is_scanning = False
    
    async def capture_and_recognize(self, cap):
        """Chụp 20 ảnh và nhận diện"""
        target_captures = 20
        capture_interval_ms = 250
        recognition_results = []
        capture_count = 0
        last_capture_time = datetime.now()
        
        # Tạo cửa sổ mới
        window_name = "Dang quet khuon mat..."
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        print("📸 Đang chụp 20 ảnh...")
        
        while capture_count < target_captures:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Hiển thị thông tin
            display_frame = frame.copy()
            
            # Header
            cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 80), (0, 0, 0), -1)
            cv2.putText(display_frame, "Dang quet khuon mat...", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Da quet: {capture_count}/{target_captures}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            
            # Kiểm tra đã đủ thời gian chưa
            elapsed_ms = (datetime.now() - last_capture_time).total_seconds() * 1000
            
            if elapsed_ms >= capture_interval_ms:
                face = face_recognition_model.crop_face_from_array(frame)
                
                if face is not None:
                    person, distance = face_recognition_model.recognize_face(face)
                    recognition_results.append((person, distance))
                    capture_count += 1
                    last_capture_time = datetime.now()
                    
                    print(f"[{capture_count}/{target_captures}] {person} (distance: {distance:.3f})")
                    
                    # Vẽ bounding box
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_recognition_model.face_cascade.detectMultiScale(
                        gray, scaleFactor=1.2, minNeighbors=5
                    )
                    
                    for (x, y, w, h) in faces:
                        color = (0, 255, 0)
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 3)
                        
                        label = f"{person} ({distance:.2f})"
                        cv2.putText(display_frame, label, (x, y-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
                else:
                    last_capture_time = datetime.now()
            
            cv2.imshow(window_name, display_frame)
            cv2.waitKey(1)
        
        # Đóng cửa sổ
        cv2.destroyWindow(window_name)
        
        # Phân tích kết quả
        return await self.analyze_results(recognition_results)
    
    async def analyze_results(self, results):
        """Phân tích kết quả nhận diện và quyết định mở cửa"""
        print(f"\n{'='*60}")
        print("📊 PHÂN TÍCH KẾT QUẢ")
        print(f"{'='*60}")
        
        if not results:
            print("❌ Không phát hiện khuôn mặt nào")
            print("🚫 KHÔNG MỞ CỬA")
            print(f"{'='*60}\n")
            return None
        
        # Đếm số lần nhận diện cho mỗi người
        vote_counter = {}
        for person, _ in results:
            if person not in vote_counter:
                vote_counter[person] = 0
            vote_counter[person] += 1
        
        total_count = len(results)
        
        print(f"Tổng số lần quét: {total_count}")
        print(f"Kết quả nhận diện:")
        for person, count in vote_counter.items():
            print(f"  - {person}: {count}/{total_count} lần")
        
        # Tìm người có số lần nhận diện cao nhất
        max_person = max(vote_counter.items(), key=lambda x: x[1])
        recognized_person = max_person[0]
        correct_count = max_person[1]
        
        # Quyết định: cần ít nhất 10/20 khớp (50%)
        required_matches = 10
        
        if correct_count >= required_matches and recognized_person != "Unknown":
            print(f"\n✅ XÁC THỰC THÀNH CÔNG!")
            print(f"👤 Nhận diện: {recognized_person}")
            print(f"📈 Đạt yêu cầu: {correct_count}/{total_count} ≥ {required_matches}/20")
            print(f"🚪 ĐANG MỞ CỬA...")
            
            # Gửi lệnh mở cửa tới server
            await self.send_open_door(recognized_person)
            
            print(f"{'='*60}\n")
            return recognized_person
        else:
            print(f"\n❌ XÁC THỰC THẤT BẠI!")
            print(f"⚠️ Không nhận diện được người dùng hợp lệ")
            print(f"📉 Không đạt yêu cầu: {correct_count}/{total_count} < {required_matches}/20")
            print(f"🚫 KHÔNG MỞ CỬA")
            print(f"{'='*60}\n")
            return None
    
    async def run(self):
        """Chạy client"""
        print("\n" + "="*60)
        print("FACE RECOGNITION CLIENT")
        print("="*60)
        
        # Khởi tạo model
        print("\n🔹 Đang khởi tạo model nhận diện khuôn mặt...")
        face_recognition_model.initialize()
        
        if not face_recognition_model.model:
            print("❌ Không thể khởi tạo model. Vui lòng train model trước.")
            return
        
        print(f"✅ Model đã sẵn sàng với {len(face_recognition_model.classes)} người dùng")
        
        print("\n🎯 Hệ thống nhận diện khuôn mặt đã sẵn sàng")
        print("💡 Đưa khuôn mặt vào camera để nhận diện và mở cửa\n")
        
        # Bắt đầu quét
        await self.start_face_scan()


async def main():
    client = FaceRecognitionClient()
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ Đã dừng client")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")


if __name__ == "__main__":
    asyncio.run(main())
