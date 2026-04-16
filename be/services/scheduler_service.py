import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from database import SessionLocal
from models.system_state import SystemState
from services.door_service import command_system_locked, command_system_unlocked
from services.notification import notify_alert, notify_system_state

# Múi giờ Việt Nam (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))

# Biến lưu trạng thái trước đó để tránh spam thông báo
_last_auto_lock_state = None


async def check_schedule():
    """Kiểm tra lịch và tự động khóa/mở hệ thống"""
    global _last_auto_lock_state
    
    db: Session = SessionLocal()
    try:
        state = db.query(SystemState).first()
        if not state or not state.schedule_enabled:
            # Nếu lịch tắt, reset trạng thái và không can thiệp
            _last_auto_lock_state = None
            return
        
        if not state.schedule_start or not state.schedule_end:
            return
        
        # Lấy giờ hiện tại (Việt Nam) - chỉ lấy giờ:phút, bỏ giây
        now = datetime.now(VIETNAM_TZ).time()
        now_hm = now.replace(second=0, microsecond=0)
        
        # Lấy giờ cấu hình (chỉ giờ:phút)
        start_hm = state.schedule_start.replace(second=0, microsecond=0)
        end_hm = state.schedule_end.replace(second=0, microsecond=0)
        
        # Kiểm tra xem có trong khung giờ không
        # Trong khung giờ: start <= now < end (không bao gồm end)
        in_schedule = False
        
        if start_hm < end_hm:
            # Trường hợp bình thường: 08:00 - 22:55
            # Mở từ 08:00:00, khóa từ 22:55:00
            in_schedule = start_hm <= now_hm < end_hm
        else:
            # Trường hợp qua đêm: 22:00 - 06:00
            in_schedule = now_hm >= start_hm or now_hm < end_hm
        
        # Nếu trong khung giờ -> mở khóa, ngoài khung giờ -> khóa
        should_be_locked = not in_schedule
        
        # Chỉ thay đổi nếu trạng thái khác với hiện tại
        if state.is_locked != should_be_locked:
            state.is_locked = should_be_locked
            db.commit()
            
            if should_be_locked:
                await command_system_locked()
                await notify_system_state(True)  # Cập nhật UI
                await notify_alert("Hệ thống đã khóa!", "lock")
            else:
                await command_system_unlocked()
                await notify_system_state(False)  # Cập nhật UI
                await notify_alert("Hệ thống mở khóa!", "unlock")
            
            _last_auto_lock_state = should_be_locked
            
    except Exception as e:
        print(f"[Scheduler] Error: {e}")
    finally:
        db.close()


async def start_scheduler():
    """Chạy scheduler kiểm tra mỗi giây"""
    print("[Scheduler] Started - checking every second")
    while True:
        await check_schedule()
        await asyncio.sleep(1)  # Kiểm tra mỗi 1 giây để phản hồi tức thì
