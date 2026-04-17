"""
Script để lấy JWT token cho việc kết nối WebSocket
Token sẽ được lưu vào file token.txt

Usage:
    python get_token.py
"""

import requests
import json

# Configuration
API_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    """Lấy JWT token từ API"""
    print("\n" + "="*60)
    print("LẤY JWT TOKEN")
    print("="*60)
    
    print(f"\n🔹 Đang đăng nhập...")
    print(f"   URL: {API_URL}/api/auth/login")
    print(f"   Username: {USERNAME}")
    
    try:
        # Gửi request đăng nhập
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={
                "username": USERNAME,
                "password": PASSWORD
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            
            if token:
                # Lưu token vào file
                with open("token.txt", "w") as f:
                    f.write(token)
                
                print(f"\n✅ Đăng nhập thành công!")
                print(f"📝 Token đã được lưu vào: token.txt")
                print(f"\n🔑 Token: {token[:50]}...")
                print(f"\n💡 Bây giờ bạn có thể chạy: python rfid_face_client.py")
                print("="*60 + "\n")
                return token
            else:
                print(f"\n❌ Không tìm thấy token trong response")
                return None
        else:
            print(f"\n❌ Đăng nhập thất bại!")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Không thể kết nối tới server!")
        print(f"   Kiểm tra backend có đang chạy không")
        print(f"   URL: {API_URL}")
        return None
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout khi kết nối tới server")
        return None
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        return None


if __name__ == "__main__":
    try:
        get_token()
    except KeyboardInterrupt:
        print("\n\n⚠️ Đã hủy")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
