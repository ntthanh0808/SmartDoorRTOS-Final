from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import time as dt_time
from typing import Optional

from database import get_db
from models.user import User
from models.history import History
from models.system_state import SystemState
from middleware.auth_middleware import get_current_user, require_admin
from services.door_service import command_open_door, command_close_door, command_system_locked, command_system_unlocked
from services.notification import notify_door_status, notify_system_state, notify_alert

router = APIRouter(prefix="/api/door", tags=["Door"])


class ScheduleConfig(BaseModel):
    enabled: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class BLEOpenRequest(BaseModel):
    beacon_id: str


# BLE Beacon ID hợp lệ
VALID_BEACON_ID = "SMARTDOOR_BEACON_001"


def get_system_state(db: Session) -> SystemState:
    state = db.query(SystemState).first()
    if not state:
        state = SystemState(id=1)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def detect_client_type(user_agent: str = Header(None)) -> str:
    """Phát hiện client là web hay app dựa vào User-Agent"""
    if user_agent and "Expo" in user_agent:
        return "app"
    return "web"


@router.get("/status")
def door_status(db: Session = Depends(get_db), _=Depends(get_current_user)):
    state = get_system_state(db)
    return {"door_status": state.door_status, "is_locked": state.is_locked}


@router.post("/open-face")
async def open_door_face(
    user_name: str,
    db: Session = Depends(get_db)
):
    """Mở cửa qua Face ID - không cần authentication"""
    state = get_system_state(db)
    if state.is_locked:
        raise HTTPException(status_code=403, detail="Hệ thống đang khóa")
    
    # Tìm user theo tên
    user = db.query(User).filter(User.full_name == user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    # Gửi lệnh mở cửa với tên người dùng
    await command_open_door(user.full_name)
    
    # Lưu lịch sử
    history = History(user_id=user.id, action="open", method="face-id", success=True)
    db.add(history)
    db.commit()
    
    # Gửi thông báo
    await notify_alert(f"{user.full_name} đã mở cửa bằng FACE ID", "access")
    
    return {"message": "Đã gửi lệnh mở cửa"}


@router.post("/open")
async def open_door(
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user),
    user_agent: str = Header(None)
):
    state = get_system_state(db)
    if state.is_locked:
        raise HTTPException(status_code=403, detail="Hệ thống đang khóa")
    
    client_type = detect_client_type(user_agent)
    await command_open_door(user.full_name)
    
    history = History(user_id=user.id, action="open", method=client_type, success=True)
    db.add(history)
    db.commit()
    
    await notify_alert(f"{user.full_name} đã mở cửa qua {client_type}", "access")
    return {"message": "Đã gửi lệnh mở cửa"}


@router.post("/open-ble")
async def open_door_ble(
    request: BLEOpenRequest,
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user),
    user_agent: str = Header(None)
):
    """Mở cửa qua BLE - yêu cầu beacon ID hợp lệ"""
    state = get_system_state(db)
    if state.is_locked:
        raise HTTPException(status_code=403, detail="Hệ thống đang khóa")
    
    # Xác thực BLE Beacon ID
    if request.beacon_id != VALID_BEACON_ID:
        history = History(user_id=user.id, action="open", method="app", success=False)
        db.add(history)
        db.commit()
        await notify_alert(f"⚠️ {user.full_name} thử mở cửa nhưng không ở gần", "alert")
        raise HTTPException(status_code=403, detail="Bạn không ở gần cửa. Hãy đến gần hơn!")
    
    # Mở cửa
    await command_open_door(user.full_name)
    
    history = History(user_id=user.id, action="open", method="app", success=True)
    db.add(history)
    db.commit()
    
    await notify_alert(f"{user.full_name} đã mở cửa qua app", "access")
    return {"message": "Đã mở cửa thành công"}


@router.post("/close")
async def close_door(
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user),
    user_agent: str = Header(None)
):
    client_type = detect_client_type(user_agent)
    await command_close_door()
    
    history = History(user_id=user.id, action="close", method=client_type, success=True)
    db.add(history)
    db.commit()
    
    await notify_alert(f"{user.full_name} đã đóng cửa qua {client_type}", "access")
    return {"message": "Đã gửi lệnh đóng cửa"}


@router.post("/lock")
async def lock_system(db: Session = Depends(get_db), _=Depends(require_admin)):
    state = get_system_state(db)
    state.is_locked = True
    db.commit()
    await command_system_locked()
    await notify_system_state(True)
    await notify_alert("Hệ thống đã khóa!", "lock")
    return {"message": "Đã khóa hệ thống"}


@router.post("/unlock")
async def unlock_system(db: Session = Depends(get_db), _=Depends(require_admin)):
    print("[Door Router] Unlock system called")
    state = get_system_state(db)
    print(f"[Door Router] Current lock state: {state.is_locked}")
    state.is_locked = False
    db.commit()
    print("[Door Router] Database updated, is_locked = False")
    await command_system_unlocked()
    print("[Door Router] command_system_unlocked() called")
    await notify_system_state(False)
    print("[Door Router] notify_system_state(False) called")
    await notify_alert("Hệ thống mở khóa!", "unlock")
    return {"message": "Đã mở khóa hệ thống"}


@router.get("/schedule")
def get_schedule(db: Session = Depends(get_db), _=Depends(require_admin)):
    """Lấy cấu hình lịch mở cửa tự động"""
    state = get_system_state(db)
    return {
        "enabled": state.schedule_enabled or False,
        "start_time": state.schedule_start.strftime("%H:%M") if state.schedule_start else None,
        "end_time": state.schedule_end.strftime("%H:%M") if state.schedule_end else None
    }


@router.post("/schedule")
async def update_schedule(
    config: ScheduleConfig,
    db: Session = Depends(get_db), 
    _=Depends(require_admin)
):
    """Cập nhật cấu hình lịch mở cửa tự động"""
    state = get_system_state(db)
    
    state.schedule_enabled = config.enabled
    
    if config.enabled:
        if not config.start_time or not config.end_time:
            raise HTTPException(status_code=400, detail="Cần nhập giờ bắt đầu và kết thúc")
        
        try:
            # Parse time strings to time objects
            start_parts = config.start_time.split(":")
            end_parts = config.end_time.split(":")
            state.schedule_start = dt_time(int(start_parts[0]), int(start_parts[1]))
            state.schedule_end = dt_time(int(end_parts[0]), int(end_parts[1]))
            
            # Format time for display (AM/PM)
            start_hour = int(start_parts[0])
            end_hour = int(end_parts[0])
            start_ampm = "AM" if start_hour < 12 else "PM"
            end_ampm = "AM" if end_hour < 12 else "PM"
            start_display = f"{start_hour if start_hour <= 12 else start_hour - 12}:{start_parts[1]} {start_ampm}"
            end_display = f"{end_hour if end_hour <= 12 else end_hour - 12}:{end_parts[1]} {end_ampm}"
            
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Định dạng giờ không hợp lệ (HH:MM)")
    
    db.commit()
    
    if config.enabled:
        await notify_alert(f"Lịch tự động đã bật: {start_display} - {end_display}", "schedule")
    else:
        await notify_alert("Lịch tự động đã tắt", "schedule")
    
    return {"message": "Đã cập nhật lịch mở cửa"}
