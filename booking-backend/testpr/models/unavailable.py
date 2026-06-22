from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class UnavailablePeriod(Base):
    __tablename__ = "unavailable_periods"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    resource_id = Column(BigInteger, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())