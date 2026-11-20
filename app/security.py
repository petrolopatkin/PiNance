from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    hashed_password = password_hash.hash(password)

    return hashed_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    verified_password = password_hash.verify(plain_password, hashed_password)

    return verified_password