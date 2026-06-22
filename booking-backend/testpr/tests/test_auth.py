import pytest
from tests.conftest import client


def test_register_success():
    """Тест успешной регистрации."""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123",
            "role": "user"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "password_hash" not in data


def test_register_duplicate():
    """Тест регистрации с уже существующим пользователем."""
    # Сначала регистрируем
    client.post(
        "/auth/register",
        json={
            "username": "duplicate",
            "email": "dup@example.com",
            "password": "pass123",
            "role": "user"
        }
    )
    # Пытаемся зарегистрировать снова
    response = client.post(
        "/auth/register",
        json={
            "username": "duplicate",
            "email": "dup@example.com",
            "password": "pass123",
            "role": "user"
        }
    )
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]


def test_login_success(test_user):
    """Тест успешного входа."""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(test_user):
    """Тест входа с неверным паролем."""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "Неверное имя пользователя или пароль" in response.json()["detail"]