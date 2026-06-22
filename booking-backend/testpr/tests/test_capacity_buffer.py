import pytest
from datetime import datetime, timedelta
from tests.conftest import client, auth_token, test_resource_small


def test_capacity_mode(test_resource_small, auth_token):
    """Тест режима вместимости (FR-24)."""
    # Создаём 2 брони по 1 месту (вместимость = 2)
    for i in range(2):
        start = (datetime.utcnow() + timedelta(days=i+1, hours=10)).isoformat()
        end = (datetime.utcnow() + timedelta(days=i+1, hours=11)).isoformat()
        response = client.post(
            "/bookings/",
            json={
                "resource_id": test_resource_small.id,
                "start_datetime": start,
                "end_datetime": end,
                "purpose": f"Встреча {i+1}",
                "seats": 1
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
    
    # Пытаемся создать 3-ю бронь на то же время (превышение вместимости)
    start = (datetime.utcnow() + timedelta(days=1, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=11)).isoformat()
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource_small.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Лишняя встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "вместимость" in response.json()["detail"].lower()


def test_capacity_mode_multiple_seats(test_resource_small, auth_token):
    """Тест режима вместимости с несколькими местами в одной брони."""
    # Создаём бронь на 2 места (полная вместимость)
    start = (datetime.utcnow() + timedelta(days=5, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=5, hours=11)).isoformat()
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource_small.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Большая встреча",
            "seats": 2
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    
    # Пытаемся создать ещё одну бронь на 1 место (превышение)
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource_small.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Ещё одна встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "вместимость" in response.json()["detail"].lower()


def test_buffer_time(test_resource, auth_token, test_limits):
    """Тест буферного времени (FR-23)."""
    # Создаём бронь с 10:00 до 11:00
    start1 = (datetime.utcnow() + timedelta(days=3, hours=10)).isoformat()
    end1 = (datetime.utcnow() + timedelta(days=3, hours=11)).isoformat()
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start1,
            "end_datetime": end1,
            "purpose": "Первая встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    
    # Пытаемся создать бронь в 11:05 (в пределах буфера 15 минут)
    start2 = (datetime.utcnow() + timedelta(days=3, hours=11, minutes=5)).isoformat()
    end2 = (datetime.utcnow() + timedelta(days=3, hours=12)).isoformat()
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start2,
            "end_datetime": end2,
            "purpose": "Вторая встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "буфер" in response.json()["detail"].lower() or "конфликт" in response.json()["detail"].lower()