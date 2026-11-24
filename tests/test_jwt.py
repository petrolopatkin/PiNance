from app.security import create_access_token, decode_access_token
from datetime import datetime, timedelta, timezone
import jwt
from app.config import secret_key
import base64
import json

def test_create_access_token():
    token = create_access_token(15)

    payload = decode_access_token(token)

    assert payload["sub"] == "15"


def test_decode_token_changed():
    token = create_access_token(15)

    header, payload, signature = token.split(".")

    decoded_payload = base64.urlsafe_b64decode(payload + "===")

    decoded_payload = json.loads(decoded_payload)

    decoded_payload["sub"] = "1"

    new_payload = json.dumps(decoded_payload).encode()

    new_payload = base64.urlsafe_b64encode(new_payload).decode().rstrip("=")

    tampered_result = f"{header}.{new_payload}.{signature}"

    result = decode_access_token(tampered_result)

    assert result is None


def test_decode_token_expired():
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)

    payload = {
        "sub": 15,
        "exp": expire
    }

    decoded_expire = jwt.encode(payload, secret_key, algorithm="HS256")

    result = decode_access_token(decoded_expire)

    assert result is None