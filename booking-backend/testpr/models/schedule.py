from sqlalchemy import Column, BigInteger, Integer, Time, ForeignKey
from database import Base


class ResourceSchedule(Base):
    __tablename__ = "resource_schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    resource_id = Column(BigInteger, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0-6 (0=Вс, 1=Пн, ..., 6=Сб)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)