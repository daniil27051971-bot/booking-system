import pytest
from tests.conftest import client, admin_token


def test_create_resource_type(admin_token):
    """Тест создания типа ресурса (только админ)."""
    response = client.post(
        "/resources/types",
        json={"name": "Сервер"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Сервер"
    assert "id" in data


def test_create_resource_type_unauthorized(test_user):
    """Тест создания типа ресурса без прав администратора."""
    response = client.post(
        "/resources/types",
        json={"name": "Сервер"},
        headers={"Authorization": f"Bearer {test_user}"}
    )
    assert response.status_code == 403


def test_create_resource(admin_token):
    """Тест создания ресурса."""
    # Сначала создаём тип
    type_response = client.post(
        "/resources/types",
        json={"name": "Переговорная"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    type_id = type_response.json()["id"]
    
    response = client.post(
        "/resources",
        json={
            "type_id": type_id,
            "name": "Большая переговорная",
            "capacity": 20,
            "location": "4 этаж",
            "description": "Для больших встреч"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Большая переговорная"
    assert data["capacity"] == 20
    assert data["is_archived"] == False


def test_create_resource_invalid_capacity(admin_token):
    """Тест создания ресурса с неверной вместимостью."""
    type_response = client.post(
        "/resources/types",
        json={"name": "Офис"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    type_id = type_response.json()["id"]
    
    response = client.post(
        "/resources",
        json={
            "type_id": type_id,
            "name": "Офис",
            "capacity": 0,  # Неверная вместимость
            "location": "1 этаж"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


def test_archive_resource(admin_token, test_resource):
    """Тест архивирования ресурса (FR-5)."""
    response = client.delete(
        f"/resources/{test_resource.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Ресурс архивирован"
    
    # Проверяем, что ресурс стал архивированным
    get_response = client.get(f"/resources/{test_resource.id}")
    assert get_response.json()["is_archived"] == True