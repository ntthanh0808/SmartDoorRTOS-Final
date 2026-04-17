"""
Script để thu thập ảnh khuôn mặt từ webcam
Chụp liên tục trong 10 giây và lưu tất cả frames

Usage:
    python savedata.py
"""

import cv2
import os
import time

def collect_face_images():
    """Thu thập ảnh khuôn mặt từ webcam trong 10 giây"""
    
    print("\n" + "="*60)
    print("THU THẬP ẢNH KHUÔN MẶT")
    print("="*60)
    
    # Nhập tên người dùng
    user_name = input("\n👤 Nhập tên người dùng (VD: Nguyen Van A): ").strip()
    
    if not user_name:
        print("❌ Tên không được để trống!")
        return
    
    # Tạo thư mục lưu ảnh
    output_dir = os.path.join("dataset", user_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Mở webcam (0 là camera mặc định)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Không thể mở webcam!")
        return
    
    frame_count = 0
    start_time = time.time()
    duration = 10  # thời gian chụp (giây)
    
    print(f"\n✅ Webcam đã sẵn sàng")
    print(f"📁 Ảnh sẽ được lưu vào: {output_dir}")
    print(f"\n📸 Bắt đầu chụp ảnh trong {duration} giây...")
    print(f"💡 Nhấn 'q' để thoát sớm\n")
    
    window_name = f"Thu thap anh - {user_name}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Không đọc được khung hình!")
            break
        
        current_time = time.time()
        elapsed_time = current_time - start_time
        remaining_time = duration - elapsed_time
        
        # Hiển thị thông tin trên frame
        display_frame = frame.copy()
        
        # Header
        cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 80), (0, 0, 0), -1)
        cv2.putText(display_frame, f"User: {user_name}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, f"Da chup: {frame_count} anh | Thoi gian con: {int(remaining_time)}s", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Lưu khung hình
        filename = os.path.join(output_dir, f"face{frame_count + 1}.jpg")
        cv2.imwrite(filename, frame)
        print(f"✅ [{frame_count + 1}] Đã lưu: {filename}")
        frame_count += 1
        
        # Hiển thị khung hình
        cv2.imshow(window_name, display_frame)
        
        # Dừng sau 10 giây
        if elapsed_time > duration:
            print(f"\n🎉 Hoàn thành chụp ảnh sau {duration} giây.")
            break
        
        # Nhấn 'q' để thoát sớm
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n⚠️ Thoát sớm theo yêu cầu.")
            break
    
    # Dọn dẹp
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n{'='*60}")
    print(f"✅ HOÀN TẤT")
    print(f"{'='*60}")
    print(f"👤 Người dùng: {user_name}")
    print(f"📸 Tổng số ảnh: {frame_count}")
    print(f"📁 Thư mục: {output_dir}")
    
    if frame_count >= 20:
        print(f"\n✅ Đã đủ ảnh để training!")
        print(f"📝 Bước tiếp theo: Chạy 'python train.py' để train model")
    else:
        print(f"\n⚠️ Nên có ít nhất 20 ảnh để training tốt (hiện có {frame_count})")
        print(f"💡 Chạy lại script này để chụp thêm ảnh")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        collect_face_images()
    except KeyboardInterrupt:
        print("\n\n⚠️ Đã hủy thu thập ảnh")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

