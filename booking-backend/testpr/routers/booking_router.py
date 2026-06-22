from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from auth import get_db, get_current_user, get_current_admin_user
from models.user import User
from models.resource import Resource
from models.booking import Booking, BookingSeries
from models.limits import BookingLimit
from models.notification import Notification
from models.audit import AuditLog
from schemas.booking import (
    BookingCreate, BookingUpdate, BookingResponse, 
    BookingTransfer, BookingAdminCancel, BookingSeriesCreate
)
from services.booking_service import (
    check_conflict,
    check_conflict_with_buffer,
    get_conflicting_bookings,
    check_capacity_mode,
    check_booking_limits,
    check_schedule_availability,
    check_unavailable_periods,
    validate_booking
)

router = APIRouter(prefix="/bookings", tags=["Бронирования"])


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def log_action(db: Session, user_id: int, action: str, entity_type: str, entity_id: int, details: dict = None):
    """Логирование действий (ОБ-7)."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )
    db.add(log)
    db.commit()


def create_notification(db: Session, user_id: int, booking_id: int, notif_type: str, message: str):
    """Создание уведомления (FR-19)."""
    notification = Notification(
        user_id=user_id,
        booking_id=booking_id,
        notification_type=notif_type,
        message=message,
        is_read=False,
        sent_at=datetime.utcnow()
    )
    db.add(notification)
    db.commit()


# ========== СОЗДАНИЕ БРОНИ (FR-10) ==========

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание брони с проверкой всех ограничений."""
    
    # 1. Проверяем существование ресурса
    resource = db.query(Resource).filter(Resource.id == booking_data.resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс не найден"
        )
    
    # 2. Проверяем, что ресурс не архивирован (FR-5)
    if resource.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ресурс архивирован и недоступен для бронирования"
        )
    
    # 3. Проверяем время (FR-9: нельзя бронировать в прошлом)
    now = datetime.utcnow()
    if booking_data.start_datetime < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя создать бронь на прошедшее время"
        )
    
    # 4. Проверяем, что время окончания позже начала (FR-10)
    if booking_data.end_datetime <= booking_data.start_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Время окончания должно быть позже времени начала"
        )
    
    # 5. Получаем лимиты для проверок
    limits = db.query(BookingLimit).first()
    if not limits:
        # Создаём лимиты по умолчанию, если их нет
        limits = BookingLimit(
            min_duration_minutes=15,
            max_duration_minutes=480,
            max_active_bookings=5,
            booking_horizon_days=30,
            buffer_minutes=0
        )
        db.add(limits)
        db.commit()
        db.refresh(limits)
    
    # 6. Комплексная проверка брони
    validation = validate_booking(
        db=db,
        resource_id=booking_data.resource_id,
        user_id=current_user.id,
        start=booking_data.start_datetime,
        end=booking_data.end_datetime,
        seats=booking_data.seats,
        exclude_booking_id=None
    )
    
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation["errors"][0] if validation["errors"] else "Ошибка валидации"
        )
    
    # 7. Проверка вместимости (FR-24) - дополнительная, уже есть в validate_booking
    if not check_capacity_mode(
        db, 
        booking_data.resource_id, 
        booking_data.start_datetime, 
        booking_data.end_datetime,
        resource.capacity,
        booking_data.seats
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Превышена вместимость ресурса ({resource.capacity} мест)"
        )
    
    # 8. Создаем бронь
    new_booking = Booking(
        resource_id=booking_data.resource_id,
        user_id=current_user.id,
        start_datetime=booking_data.start_datetime,
        end_datetime=booking_data.end_datetime,
        purpose=booking_data.purpose,
        seats=booking_data.seats,
        status="confirmed"  # <-- ИСПРАВЛЕНО: было "active"
    )
    
    db.add(new_booking)
    db.flush()  # Чтобы получить ID
    
    # 9. Если серийная бронь (FR-15)
    if booking_data.is_recurring and booking_data.series:
        series = BookingSeries(
            repeat_type=booking_data.series.repeat_type,
            repeat_count=booking_data.series.repeat_count,
            end_date=booking_data.series.end_date
        )
        db.add(series)
        db.flush()
        new_booking.series_id = series.id
        
        # Создаём остальные брони в серии
        # TODO: реализовать генерацию серии
    
    db.commit()
    db.refresh(new_booking)
    
    # 10. Логируем действие (ОБ-7)
    log_action(
        db=db,
        user_id=current_user.id,
        action="create",
        entity_type="booking",
        entity_id=new_booking.id,
        details={
            "resource_id": booking_data.resource_id,
            "start": booking_data.start_datetime.isoformat(),
            "end": booking_data.end_datetime.isoformat(),
            "seats": booking_data.seats
        }
    )
    
    # 11. Создаем уведомление о подтверждении (FR-19)
    create_notification(
        db=db,
        user_id=current_user.id,
        booking_id=new_booking.id,
        notif_type="confirmation",
        message=f"Бронь #{new_booking.id} подтверждена. {booking_data.start_datetime} - {booking_data.end_datetime}"
    )
    
    return new_booking


# ========== ПОЛУЧЕНИЕ БРОНЕЙ ==========

@router.get("/", response_model=List[BookingResponse])
def get_my_bookings(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    start_from: Optional[datetime] = None,
    end_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить свои брони с фильтрами (FR-17)."""
    query = db.query(Booking).filter(Booking.user_id == current_user.id)
    
    # Фильтр по статусу (FR-17)
    if status:
        query = query.filter(Booking.status == status)
    else:
        # По умолчанию показываем все, кроме отменённых
        query = query.filter(Booking.status == "confirmed")
    
    # Фильтр по дате (FR-17)
    if start_from:
        query = query.filter(Booking.start_datetime >= start_from)
    if end_to:
        query = query.filter(Booking.end_datetime <= end_to)
    
    # Сортировка по дате
    query = query.order_by(Booking.start_datetime)
    
    bookings = query.offset(skip).limit(limit).all()
    return bookings


@router.get("/upcoming", response_model=List[BookingResponse])
def get_upcoming_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить предстоящие брони (FR-17)."""
    now = datetime.utcnow()
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.status == "confirmed",
        Booking.start_datetime > now
    ).order_by(Booking.start_datetime).offset(skip).limit(limit).all()
    return bookings


@router.get("/past", response_model=List[BookingResponse])
def get_past_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить прошедшие брони (FR-17)."""
    now = datetime.utcnow()
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.status == "confirmed",
        Booking.end_datetime < now
    ).order_by(Booking.start_datetime.desc()).offset(skip).limit(limit).all()
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Получить бронь по ID."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронь не найдена"
        )
    
    # Пользователь может видеть только свои брони, админ - все (ОБ-2)
    if booking.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    return booking


# ========== ОТМЕНА БРОНИ (FR-13) ==========

@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отмена брони пользователем (FR-13)."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронь не найдена"
        )
    
    # Пользователь может отменить только свою бронь, админ - любую (ОБ-2)
    if booking.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    # Нельзя отменить уже отменённую
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Бронь уже отменена"
        )
    
    booking.status = "cancelled"
    db.commit()
    
    # Логируем действие (ОБ-7)
    log_action(
        db=db,
        user_id=current_user.id,
        action="cancel",
        entity_type="booking",
        entity_id=booking.id,
        details={"reason": "Отмена пользователем"}
    )
    
    # Уведомление об отмене (FR-19)
    create_notification(
        db=db,
        user_id=booking.user_id,
        booking_id=booking.id,
        notif_type="cancellation",
        message=f"Бронь #{booking.id} отменена"
    )
    
    return {"message": "Бронь отменена"}


# ========== ПЕРЕНОС БРОНИ (FR-14) ==========

@router.put("/{booking_id}/transfer", response_model=BookingResponse)
def transfer_booking(
    booking_id: int,
    transfer_data: BookingTransfer,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Перенос брони на другое время или ресурс (FR-14)."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронь не найдена"
        )
    
    # Только владелец может переносить
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя перенести отменённую бронь"
        )
    
    # Проверяем новый ресурс
    new_resource = db.query(Resource).filter(Resource.id == transfer_data.new_resource_id).first()
    if not new_resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс не найден"
        )
    
    if new_resource.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ресурс архивирован"
        )
    
    # Проверяем время
    if transfer_data.new_start_datetime < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя перенести на прошедшее время"
        )
    
    # Проверяем все ограничения
    validation = validate_booking(
        db=db,
        resource_id=transfer_data.new_resource_id,
        user_id=current_user.id,
        start=transfer_data.new_start_datetime,
        end=transfer_data.new_end_datetime,
        seats=booking.seats,
        exclude_booking_id=booking_id
    )
    
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation["errors"][0] if validation["errors"] else "Ошибка валидации"
        )
    
    # Сохраняем старые данные для логирования
    old_data = {
        "resource_id": booking.resource_id,
        "start": booking.start_datetime.isoformat(),
        "end": booking.end_datetime.isoformat()
    }
    
    # Обновляем бронь
    booking.resource_id = transfer_data.new_resource_id
    booking.start_datetime = transfer_data.new_start_datetime
    booking.end_datetime = transfer_data.new_end_datetime
    db.commit()
    db.refresh(booking)
    
    # Логируем перенос
    log_action(
        db=db,
        user_id=current_user.id,
        action="transfer",
        entity_type="booking",
        entity_id=booking.id,
        details={
            "old": old_data,
            "new": {
                "resource_id": transfer_data.new_resource_id,
                "start": transfer_data.new_start_datetime.isoformat(),
                "end": transfer_data.new_end_datetime.isoformat()
            }
        }
    )
    
    return booking


# ========== СЕТКА ЗАНЯТОСТИ (FR-16) ==========

@router.get("/schedule/{resource_id}")
def get_resource_schedule_grid(
    resource_id: int,
    week_start: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Получить сетку занятости ресурса на неделю (FR-16).
    Возвращает массив дней с доступными/занятыми слотами.
    """
    if not week_start:
        # Начало текущей недели (понедельник)
        today = datetime.utcnow().date()
        week_start = datetime.combine(
            today - timedelta(days=today.weekday()),
            datetime.min.time()
        )
    
    week_end = week_start + timedelta(days=7)
    
    # Получаем все брони на эту неделю
    bookings = db.query(Booking).filter(
        Booking.resource_id == resource_id,
        Booking.status == "confirmed",
        Booking.start_datetime >= week_start,
        Booking.end_datetime <= week_end
    ).all()
    
    # Генерируем сетку
    schedule = []
    for day in range(7):
        day_start = week_start + timedelta(days=day)
        day_end = day_start + timedelta(days=1)
        
        day_bookings = [b for b in bookings if b.start_datetime.date() == day_start.date()]
        
        schedule.append({
            "date": day_start.date().isoformat(),
            "bookings": [
                {
                    "id": b.id,
                    "start": b.start_datetime.isoformat(),
                    "end": b.end_datetime.isoformat(),
                    "purpose": b.purpose,
                    "user_id": b.user_id,
                    "seats": b.seats
                }
                for b in day_bookings
            ]
        })
    
    return {
        "resource_id": resource_id,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "schedule": schedule
    }


# ========== ПОИСК РЕСУРСОВ ПО ВРЕМЕНИ (FR-18) ==========

@router.get("/search/available")
def search_available_resources(
    start_datetime: datetime,
    end_datetime: datetime,
    type_id: Optional[int] = None,
    min_capacity: Optional[int] = None,
    seats: int = 1,
    db: Session = Depends(get_db)
):
    """
    Поиск ресурсов с свободным интервалом в заданном диапазоне (FR-18).
    """
    # Базовый запрос ресурсов
    query = db.query(Resource).filter(Resource.is_archived == False)
    
    if type_id:
        query = query.filter(Resource.type_id == type_id)
    
    if min_capacity:
        query = query.filter(Resource.capacity >= min_capacity)
    
    resources = query.all()
    
    available = []
    for resource in resources:
        # Проверяем конфликты
        has_conflict = check_conflict(db, resource.id, start_datetime, end_datetime)
        
        if not has_conflict:
            # Проверяем вместимость (FR-24)
            if check_capacity_mode(db, resource.id, start_datetime, end_datetime, resource.capacity, seats):
                available.append({
                    "resource": {
                        "id": resource.id,
                        "name": resource.name,
                        "capacity": resource.capacity,
                        "location": resource.location
                    }
                })
    
    return {"available": available}