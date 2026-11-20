from app.schemas import UserRead
from types import SimpleNamespace

def test_user_read_schema():
    user_data = {
        "id": 1,
        "username": "Peter",
        "email": "peter@example.com"
    }

    user = UserRead(**user_data)

    assert user.username == "Peter"
    assert user.email == "peter@example.com"


def test_user_read_does_not_expose_password():
    user_data = {
        "id": 1,
        "username": "Peter",
        "email": "peter@example.com",
        "hashed_password": "some-hash-password"
    }


    user = UserRead(**user_data)

    assert hasattr(user, "hashed_password") is False


def test_user_read_from_attributes():
    user_object = SimpleNamespace(
        id=1,
        username="Peter",
        email="peter@example.com"
    )

    user = UserRead.model_validate(user_object)

    assert user.username == "Peter"
    assert user.email == "peter@example.com"