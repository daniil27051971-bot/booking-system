from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Text, Integer, Date, Index
from sqlalchemy.sql import func
from database import Base


class BookingSeries(Base):
    __tablename__ = "booking_series"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    repeat_type = Column(String(20), nullable=False)  # 'daily' или 'weekly'
    repeat_count = Column(Integer, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    resource_id = Column(BigInteger, ForeignKey("resources.id"), nullable=False)
    series_id = Column(BigInteger, ForeignKey("booking_series.id"), nullable=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    purpose = Column(Text, nullable=True)
    seats = Column(Integer, nullable=False, default=1)  # FR-24: количество мест
    status = Column(String(20), nullable=False)  # 'confirmed' или 'cancelled'
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Индексы для производительности
    __table_args__ = (
        Index('idx_booking_resource_time', 'resource_id', 'start_datetime', 'end_datetime'),
        Index('idx_booking_user_status', 'user_id', 'status'),
        Index('idx_booking_series', 'series_id'),
        Index('idx_booking_start', 'start_datetime'),
    )