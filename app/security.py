from pwdlib import PasswordHash
import jwt
import datetime
from datetime import datetime, timedelta, timezone
from app.config import secret_key

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    hashed_password = password_hash.hash(password)

    return hashed_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    verified_password = password_hash.verify(plain_password, hashed_password)

    return verified_password


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        return None
    except jwt.InvalidTokenError as e:
        return None

    return payload