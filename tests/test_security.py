from app.security import hash_password, verify_password

def test_password_hash_and_verify():
    ps_hash = hash_password("MyPassword123!")

    ps_verify = verify_password("MyPassword123!", ps_hash)
    ps_verify2 = verify_password("MyPassword124!", ps_hash)

    assert ps_verify is True
    assert ps_verify2 is False