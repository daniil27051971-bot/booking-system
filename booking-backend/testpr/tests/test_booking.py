import pytest
from datetime import datetime, timedelta
from tests.conftest import client, admin_token, auth_token, test_user, test_resource, test_limits


def test_create_booking_success(auth_token, test_resource):
    """Тест успешного создания брони (FR-10)."""
    start = (datetime.utcnow() + timedelta(days=1, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=11)).isoformat()
    
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Важная встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["resource_id"] == test_resource.id
    assert data["status"] == "confirmed"
    assert data["seats"] == 1


def test_create_booking_in_past(auth_token, test_resource):
    """Тест создания брони в прошлом (FR-9)."""
    start = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    end = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
    
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Прошлая встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "прошедшее" in response.json()["detail"]


def test_create_booking_conflict(auth_token, test_resource, test_booking):
    """Тест конфликта броней (FR-11)."""
    # Пытаемся создать бронь на то же время
    start = (datetime.utcnow() + timedelta(days=1, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=11)).isoformat()
    
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Конфликтная встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400 or response.status_code == 409
    # Может быть 400 или 409 в зависимости от проверки


def test_create_booking_outside_schedule(auth_token, test_resource, test_schedule):
    """Тест брони вне расписания (FR-12)."""
    # Пытаемся забронировать в 20:00 (после рабочего дня 09:00-18:00)
    start = (datetime.utcnow() + timedelta(days=1, hours=20)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=21)).isoformat()
    
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Вечерняя встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "расписание" in response.json()["detail"].lower()


def test_cancel_booking(auth_token, test_booking):
    """Тест отмены брони (FR-13)."""
    response = client.delete(
        f"/bookings/{test_booking.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Бронь отменена"
    
    # Проверяем статус
    get_response = client.get(
        f"/bookings/{test_booking.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.json()["status"] == "cancelled"


def test_transfer_booking(auth_token, test_booking, test_resource):
    """Тест переноса брони (FR-14)."""
    new_start = (datetime.utcnow() + timedelta(days=2, hours=14)).isoformat()
    new_end = (datetime.utcnow() + timedelta(days=2, hours=15)).isoformat()
    
    response = client.put(
        f"/bookings/{test_booking.id}/transfer",
        json={
            "new_resource_id": test_resource.id,
            "new_start_datetime": new_start,
            "new_end_datetime": new_end
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_booking.id
    assert data["start_datetime"].startswith(new_start[:16])


def test_get_my_bookings(auth_token, test_booking):
    """Тест получения своих броней (FR-17)."""
    response = client.get(
        "/bookings/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["user_id"] == test_booking.user_id