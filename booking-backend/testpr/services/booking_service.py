from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.booking import Booking
from models.limits import BookingLimit
from models.schedule import ResourceSchedule
from models.unavailable import UnavailablePeriod
from models.resource import Resource
from datetime import datetime, timedelta


def check_conflict(
    db: Session,
    resource_id: int,
    start: datetime,
    end: datetime,
    exclude_booking_id: int = None
) -> bool:
    """
    Проверяет, есть ли конфликт с существующими бронями.
    Возвращает True, если конфликт есть.
    
    Условие пересечения интервалов:
    (start1 < end2) AND (end1 > start2)
    """
    query = db.query(Booking).filter(
        Booking.resource_id == resource_id,
        Booking.status == "confirmed",
        Booking.start_datetime < end,
        Booking.end_datetime > start
    )
    
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    
    conflict = query.first()
    return conflict is not None


def check_conflict_with_buffer(
    db: Session,
    resource_id: int,
    start: datetime,
    end: datetime,
    buffer_minutes: int = 15,
    exclude_booking_id: int = None
) -> bool:
    """
    Проверяет конфликт с учетом буферного времени (FR-23).
    """
    buffer = timedelta(minutes=buffer_minutes)
    
    query = db.query(Booking).filter(
        Booking.resource_id == resource_id,
        Booking.status == "confirmed",
        Booking.start_datetime < (end + buffer),
        Booking.end_datetime > (start - buffer)
    )
    
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    
    conflict = query.first()
    return conflict is not None


def get_conflicting_bookings(
    db: Session,
    resource_id: int,
    start: datetime,
    end: datetime
) -> list:
    """
    Возвращает список конфликтующих броней.
    """
    conflicts = db.query(Booking).filter(
        Booking.resource_id == resource_id,
        Booking.status == "confirmed",
        Booking.start_datetime < end,
        Booking.end_datetime > start
    ).all()
    
    return conflicts


def check_capacity_mode(
    db: Session,
    resource_id: int,
    start: datetime,
    end: datetime,
    capacity: int,
    seats: int = 1,
    exclude_booking_id: int = None
) -> bool:
    """
    Проверяет, не превышен ли лимит вместимости (FR-24).
    Возвращает True, если можно забронировать.
    """
    overlapping_bookings = db.query(Booking).filter(
        Booking.resource_id == resource_id,
        Booking.status == "confirmed",
        Booking.start_datetime < end,
        Booking.end_datetime > start
    )
    
    if exclude_booking_id:
        overlapping_bookings = overlapping_bookings.filter(Booking.id != exclude_booking_id)
    
    # Суммируем все занятые места
    total_seats = sum(b.seats for b in overlapping_bookings)
    return (total_seats + seats) <= capacity


def check_booking_limits(
    db: Session,
    user_id: int,
    start: datetime,
    end: datetime
) -> dict:
    """
    Проверяет лимиты бронирования (FR-6, FR-7, FR-8).
    Возвращает словарь с результатами проверки.
    """
    limits = db.query(BookingLimit).first()
    if not limits:
        return {"valid": True, "errors": []}
    
    errors = []
    
    # Проверка длительности (FR-6)
    duration_minutes = (end - start).total_seconds() / 60
    if duration_minutes < limits.min_duration_minutes:
        errors.append(f"Минимальная длительность: {limits.min_duration_minutes} минут")
    if duration_minutes > limits.max_duration_minutes:
        errors.append(f"Максимальная длительность: {limits.max_duration_minutes} минут")
    
    # Проверка горизонта бронирования (FR-8)
    now = datetime.utcnow()
    horizon = now + timedelta(days=limits.booking_horizon_days)
    if start > horizon:
        errors.append(f"Нельзя бронировать дальше чем на {limits.booking_horizon_days} дней")
    
    # Проверка лимита активных броней (FR-7)
    active_count = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.status == "confirmed",
        Booking.start_datetime > now
    ).count()
    if active_count >= limits.max_active_bookings:
        errors.append(f"Достигнут лимит активных броней: {limits.max_active_bookings}")
    
    return {"valid": len(errors) == 0, "errors": errors}


def check_schedule_availability(
    db: Session,
    resource_id: int,
    start: datetime,
    end: datetime
) -> bool:
    """
    Проверяет, попадает ли бронь в рабочее время ресурса (FR-3, FR-12).
    Возвращает True, если доступно.
    """
    weekday = start.weekday()
    start_time = start.time()
    end_time = end.time()
    
    schedule = db.query(ResourceSchedule).filter(
        ResourceSchedule.resource_id == resource_id,
        ResourceSchedule.weekday == weekday
    ).first()
    
    if not schedule:
        return False
    
    return (schedule.start_time <= start_time and 
            schedule.end_time >= end_time)


def check_unavailable_periods(
    db: Session,
    resource_id: int,
    start: datetime,
    end: datetime
) -> list:
    """
    Проверяет пересечение с периодами недоступности (FR-4).
    Возвращает список конфликтующих периодов.
    """
    conflicts = db.query(UnavailablePeriod).filter(
        UnavailablePeriod.resource_id == resource_id,
        UnavailablePeriod.start_datetime < end,
        UnavailablePeriod.end_datetime > start
    ).all()
    
    return conflicts


def validate_booking(
    db: Session,
    resource_id: int,
    user_id: int,
    start: datetime,
    end: datetime,
    seats: int = 1,
    exclude_booking_id: int = None
) -> dict:
    """
    Комплексная проверка бронирования.
    Возвращает словарь с результатами всех проверок.
    """
    errors = []
    
    # 1. Проверка времени (FR-9)
    if start < datetime.utcnow():
        errors.append("Нельзя бронировать в прошлом")
    if end <= start:
        errors.append("Время окончания должно быть позже времени начала")
    
    # 2. Проверка расписания (FR-3, FR-12)
    if not check_schedule_availability(db, resource_id, start, end):
        errors.append("Время не входит в рабочее расписание ресурса")
    
    # 3. Проверка недоступности (FR-4)
    unavailable = check_unavailable_periods(db, resource_id, start, end)
    if unavailable:
        periods = ", ".join([f"{u.start_datetime}-{u.end_datetime}" for u in unavailable])
        errors.append(f"Ресурс недоступен в периоды: {periods}")
    
    # 4. Проверка лимитов (FR-6, FR-7, FR-8)
    limit_result = check_booking_limits(db, user_id, start, end)
    if not limit_result["valid"]:
        errors.extend(limit_result["errors"])
    
    # 5. Проверка вместимости (FR-24)
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if resource and resource.capacity > 0:
        if not check_capacity_mode(db, resource_id, start, end, resource.capacity, seats, exclude_booking_id):
            errors.append(f"Превышена вместимость ресурса ({resource.capacity} мест)")
    
    # 6. Проверка конфликтов с буфером (FR-23)
    limits = db.query(BookingLimit).first()
    buffer_minutes = limits.buffer_minutes if limits else 0
    
    if check_conflict_with_buffer(db, resource_id, start, end, buffer_minutes, exclude_booking_id):
        errors.append("Конфликт с существующей бронью (с учетом буферного времени)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }