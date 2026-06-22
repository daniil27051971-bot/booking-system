from sqlalchemy import Column, BigInteger, Integer, DateTime
from sqlalchemy.sql import func
from database import Base


class BookingLimit(Base):
    __tablename__ = "booking_limits"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    min_duration_minutes = Column(Integer, nullable=False, default=15)
    max_duration_minutes = Column(Integer, nullable=False, default=480)  # 8 часов
    max_active_bookings = Column(Integer, nullable=False, default=5)
    booking_horizon_days = Column(Integer, nullable=False, default=30)
    buffer_minutes = Column(Integer, default=0)  # FR-23: буферное время
    created_at = Column(DateTime, server_default=func.now())