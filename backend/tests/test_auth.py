from app.models.user import User


def test_login_success(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user.email,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    assert data["user"]["email"] == admin_user.email
    assert data["user"]["role"] == "ADMIN"


def test_login_wrong_password(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user.email,
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@test.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 401


def test_login_inactive_user(client, db):
    inactive_user = User(
        email="inactive@test.com",
        hashed_password="$pbkdf2-sha256$invalid",
        full_name="Inactive User",
        role="CARRIER",
        is_active=False,
    )

    from app.core.security import hash_password

    inactive_user.hashed_password = hash_password(
        "TestPassword123"
    )

    db.add(inactive_user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": inactive_user.email,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 403


def test_profile_without_token(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_profile_with_valid_token(client, admin_token, admin_user):
    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == admin_user.id
    assert data["email"] == admin_user.email
    assert data["role"] == "ADMIN"