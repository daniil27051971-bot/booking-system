from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # create, update, delete, cancel, etc.
    entity_type = Column(String(50), nullable=False)  # booking, resource, user, etc.
    entity_id = Column(BigInteger, nullable=False)
    details = Column(JSON, nullable=True)  # Дополнительные данные
    ip_address = Column(String(45), nullable=True)  # IPv4 или IPv6
    created_at = Column(DateTime, server_default=func.now())