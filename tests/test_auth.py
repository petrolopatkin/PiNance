from app.models import User
from app.security import hash_password, decode_access_token

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