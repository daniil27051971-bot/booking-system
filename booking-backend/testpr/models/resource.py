from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base


class ResourceType(Base):
    __tablename__ = "resource_types"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type_id = Column(BigInteger, ForeignKey("resource_types.id"), nullable=False)
    name = Column(String(200), nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)  # <-- ИЗМЕНЕНО
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())