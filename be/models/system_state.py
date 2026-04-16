from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time
from sqlalchemy.sql import func

from database import Base


class SystemState(Base):
    __tablename__ = "system_state"

    id = Column(Integer, primary_key=True, default=1)
    is_locked = Column(Boolean, default=False)
    door_status = Column(String, default="closed")  # opened, opening, closed, closing
    schedule_enabled = Column(Boolean, default=False)  # Bật/tắt lịch tự động
    schedule_start = Column(Time, nullable=True)  # Giờ bắt đầu mở cửa
    schedule_end = Column(Time, nullable=True)  # Giờ kết thúc mở cửa
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
