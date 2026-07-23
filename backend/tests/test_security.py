import pytest

from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_password_is_not_plaintext_and_verifies():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_access_token_round_trips_user_id_and_email():
    token = create_access_token(user_id=42, email="a@example.com")
    payload = decode_access_token(token)
    assert int(payload["sub"]) == 42
    assert payload["email"] == "a@example.com"


def test_expired_token_fails_to_decode(monkeypatch):
    import app.security as security

    monkeypatch.setattr(security, "JWT_EXPIRY_SECONDS", -1)
    token = create_access_token(user_id=1, email="a@example.com")
    with pytest.raises(Exception):
        decode_access_token(token)
