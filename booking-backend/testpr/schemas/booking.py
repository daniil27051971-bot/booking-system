from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date


class BookingSeriesCreate(BaseModel):
    repeat_type: str  # "daily" или "weekly"
    repeat_count: Optional[int] = None
    end_date: Optional[date] = None


class BookingCreate(BaseModel):
    resource_id: int
    start_datetime: datetime
    end_datetime: datetime
    purpose: Optional[str] = None
    seats: int = Field(default=1, ge=1, description="Количество мест (FR-24)")
    is_recurring: bool = False
    series: Optional[BookingSeriesCreate] = None

    @field_validator('end_datetime')
    @classmethod
    def validate_end(cls, v, info):
        if 'start_datetime' in info.data and v <= info.data['start_datetime']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v


class BookingUpdate(BaseModel):
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    purpose: Optional[str] = None

    @field_validator('end_datetime')
    @classmethod
    def validate_end(cls, v, info):
        if v is not None and 'start_datetime' in info.data and info.data['start_datetime'] is not None:
            if v <= info.data['start_datetime']:
                raise ValueError('Время окончания должно быть позже времени начала')
        return v


class BookingTransfer(BaseModel):
    """Для переноса брони (FR-14)"""
    new_resource_id: int
    new_start_datetime: datetime
    new_end_datetime: datetime

    @field_validator('new_end_datetime')
    @classmethod
    def validate_end(cls, v, info):
        if 'new_start_datetime' in info.data and v <= info.data['new_start_datetime']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v


class BookingResponse(BaseModel):
    id: int
    user_id: int
    resource_id: int
    series_id: Optional[int]
    start_datetime: datetime
    end_datetime: datetime
    purpose: Optional[str]
    seats: int
    status: str
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingAdminCancel(BaseModel):
    """Принудительная отмена администратором (FR-21)"""
    reason: str = Field(min_length=1, max_length=255)