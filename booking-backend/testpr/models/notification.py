from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    booking_id = Column(BigInteger, ForeignKey("bookings.id"), nullable=True)
    notification_type = Column(String(50), nullable=False)  # 'confirmation', 'reminder', 'cancellation'
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)  # Когда отправлено
    created_at = Column(DateTime, server_default=func.now())