from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, time

class ResourceTypeCreate(BaseModel):
    name: str


class ResourceTypeResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ResourceCreate(BaseModel):
    type_id: int
    name: str = Field(min_length=1, max_length=200)
    capacity: int = Field(ge=1, description="Вместимость должна быть >= 1")
    location: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ResourceUpdate(BaseModel):
    type_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    capacity: Optional[int] = Field(None, ge=1)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_archived: Optional[bool] = None


class ResourceResponse(BaseModel):
    id: int
    type_id: int
    name: str
    capacity: int
    location: str
    description: Optional[str]
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== РАСПИСАНИЕ (FR-3) ==========

class ResourceScheduleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0=Воскресенье, 1=Понедельник, ..., 6=Суббота")
    start_time: time
    end_time: time

    @field_validator('end_time')
    @classmethod
    def validate_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v


class ResourceScheduleResponse(BaseModel):
    id: int
    resource_id: int
    weekday: int
    start_time: time
    end_time: time

    class Config:
        from_attributes = True


# ========== НЕДОСТУПНОСТЬ (FR-4) ==========

class UnavailablePeriodCreate(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    reason: str = Field(min_length=1, max_length=255)

    @field_validator('end_datetime')
    @classmethod
    def validate_end(cls, v, info):
        if 'start_datetime' in info.data and v <= info.data['start_datetime']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v


class UnavailablePeriodResponse(BaseModel):
    id: int
    resource_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== ЛИМИТЫ (FR-6, FR-7, FR-8, FR-23) ==========

class BookingLimitCreate(BaseModel):
    min_duration_minutes: int = Field(ge=1)
    max_duration_minutes: int = Field(ge=1)
    max_active_bookings: int = Field(ge=1)
    booking_horizon_days: int = Field(ge=1)
    buffer_minutes: int = Field(default=0, ge=0)


class BookingLimitResponse(BaseModel):
    id: int
    min_duration_minutes: int
    max_duration_minutes: int
    max_active_bookings: int
    booking_horizon_days: int
    buffer_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True