"""Authentication and authorization test suite."""

import pytest


def test_register_success(client, db_session):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.operator@biztelai.com",
            "password": "StrongPassword123!",
            "full_name": "Alice Smith",
            "department": "Assembly",
            "role": "operator",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "new.operator@biztelai.com"


def test_register_duplicate_email(client, supervisor_user):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": supervisor_user.email,
            "password": "Password123!",
            "full_name": "Duplicate User",
        },
    )
    assert res.status_code == 409
    data = res.get_json()
    assert data["success"] is False
    assert "already exists" in data["error"]["message"]


def test_register_weak_password(client, db_session):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@biztelai.com",
            "password": "123",  # Under 8 chars
            "full_name": "Short Pass",
        },
    )
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_login_success(client, supervisor_user):
    res = client.post(
        "/api/v1/auth/login",
        json={
            "email": supervisor_user.email,
            "password": "Password123!",
        },
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_login_invalid_password(client, supervisor_user):
    res = client.post(
        "/api/v1/auth/login",
        json={
            "email": supervisor_user.email,
            "password": "WrongPassword!",
        },
    )
    assert res.status_code == 401
    assert res.get_json()["success"] is False


def test_get_me_profile(client, supervisor_auth_headers):
    res = client.get("/api/v1/auth/me", headers=supervisor_auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["role"] == "supervisor"
    assert data["data"]["is_supervisor"] is True

