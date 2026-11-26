from app.models import User
from app.security import hash_password, decode_access_token, create_access_token
from app.main import get_current_user
import pytest
from fastapi import HTTPException


def test_create_new_user(test_client):
    response = test_client.post("/register", json={
        "username": "Peter",
        "email": "peter@example.com",
        "password": "MyPassword123!"
    })

    assert response.status_code == 200

    result = response.json()

    assert result["username"] == "Peter"
    assert result["email"] == "peter@example.com"
    assert "password" not in result
    assert "hashed_password" not in result


def test_already_existent_user(test_client, test_db):
    user = User(
        id=1,
        username="Peter",
        email="peter@example.com",
        hashed_password="test-password-hash"
    )

    test_db.add(user)
    test_db.commit()

    response = test_client.post("/register", json={
        "username": "Peter",
        "email": "peter@example.com",
        "password": "MyPassword123!"
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "A user with this email already exists"


def test_user_login(test_client, test_db):
    user = User(
        id=1,
        username="Peter",
        email="peter@example.com",
        hashed_password=hash_password("MyPassword123!")
    )

    test_db.add(user)
    test_db.commit()

    response = test_client.post("/login", json={
        "email": "peter@example.com",
        "password": "MyPassword123!"
    })

    assert response.status_code == 200

    result = response.json()

    token = result["access_token"]

    payload = decode_access_token(token)

    assert "access_token" in result
    assert result["token_type"] == "bearer"
    assert payload["sub"] == str(user.id)


def test_user_login_with_wrong_password(test_client, test_db):
    user = User(
        id=1,
        username="Peter",
        email="peter@example.com",
        hashed_password=hash_password("MyPassword123!")
    )
    
    test_db.add(user)
    test_db.commit()
    
    response = test_client.post("/login", json={
        "email": "peter@example.com",
        "password": "WrongPassword123!"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_user_login_with_nonexistent_email(test_client):
    response = test_client.post("/login", json={
        "email": "peter@wrongexample.com",
        "password": "MyPassword123!"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_get_current_user(test_db):
    user = User(
        id=1,
        username="Peter",
        email="peter@example.com",
        hashed_password=hash_password("MyPassword123!")
    )

    test_db.add(user)
    test_db.commit()

    test_token = create_access_token(user.id)
    current_user = get_current_user(token=test_token, db=test_db)

    assert current_user.id == user.id
    assert current_user.email == user.email


def test_get_current_user_not_found(test_db):
    test_token = create_access_token(1)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=test_token, db=test_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"


def test_get_current_user_invalid_token(test_db):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid_token", db=test_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "You are not authorised"


def test_read_users_me(test_client, test_db):
    user =  User(
        id=1,
        username="Peter",
        email="peter@example.com",
        hashed_password=hash_password("MyPassword123!")
    )

    test_db.add(user)
    test_db.commit()

    test_token = create_access_token(user.id)

    response = test_client.get("/users/me", headers={
        "Authorization": f"Bearer {test_token}"
    })

    assert response.status_code == 200

    result = response.json()

    assert result["id"] == user.id
    assert result["email"] == user.email


def test_read_users_me_without_token(test_client):
    response = test_client.get("/users/me")

    assert response.status_code == 401


def test_user_cannot_access_another_users_transactions(test_client, test_db):
    users = [
        User(
            id=1,
            username="Peter",
            email="peter@example.com",
            hashed_password=hash_password("MyPassword123!")
        ),
        User(
            id=2,
            username="Alex",
            email="alex@example.com",
            hashed_password=hash_password("MyPassword124!")
        )
    ]

    test_db.add_all(users)
    test_db.commit()

    test_token = create_access_token(users[0].id)

    response = test_client.get("/users/2/transactions", headers={
        "Authorization": f"Bearer {test_token}"
    })

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to access this resource"


def test_create_transaction_without_token(test_client):
    response = test_client.post("/transactions")

    assert response.status_code == 401


def test_delete_transaction_without_token(test_client):
    response = test_client.delete("/transactions/1")

    assert response.status_code == 401