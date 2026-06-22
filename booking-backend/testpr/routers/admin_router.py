from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from auth import get_db, get_current_admin_user
from models.user import User
from models.booking import Booking
from models.resource import Resource
from models.audit import AuditLog
from models.notification import Notification
from schemas.booking import BookingResponse, BookingAdminCancel

router = APIRouter(prefix="/admin", tags=["Администрирование"])


def log_action(db: Session, user_id: int, action: str, entity_type: str, entity_id: int, details: dict = None):
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


# ========== ВСЕ БРОНИ (FR-20) ==========

@router.get("/bookings", response_model=List[BookingResponse])
def get_all_bookings(
    skip: int = 0,
    limit: int = 100,
    resource_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    start_from: Optional[datetime] = None,
    end_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Получить все брони с фильтрами (только админ, FR-20).
    """
    query = db.query(Booking)
    
    if resource_id:
        query = query.filter(Booking.resource_id == resource_id)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    if status:
        query = query.filter(Booking.status == status)
    if start_from:
        query = query.filter(Booking.start_datetime >= start_from)
    if end_to:
        query = query.filter(Booking.end_datetime <= end_to)
    
    query = query.order_by(Booking.start_datetime)
    bookings = query.offset(skip).limit(limit).all()
    return bookings


# ========== ПРИНУДИТЕЛЬНАЯ ОТМЕНА (FR-21) ==========

@router.post("/bookings/{booking_id}/cancel")
def admin_cancel_booking(
    booking_id: int,
    cancel_data: BookingAdminCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Принудительная отмена брони администратором (FR-21).
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронь не найдена"
        )
    
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Бронь уже отменена"
        )
    
    # Сохраняем причину
    booking.status = "cancelled"
    booking.cancellation_reason = cancel_data.reason
    db.commit()
    
    # Логируем действие
    log_action(
        db=db,
        user_id=current_user.id,
        action="admin_cancel",
        entity_type="booking",
        entity_id=booking.id,
        details={"reason": cancel_data.reason}
    )
    
    # Уведомляем пользователя (FR-19)
    create_notification(
        db=db,
        user_id=booking.user_id,
        booking_id=booking.id,
        notif_type="cancellation",
        message=f"Бронь #{booking.id} отменена администратором. Причина: {cancel_data.reason}"
    )
    
    return {"message": f"Бронь #{booking_id} отменена", "reason": cancel_data.reason}