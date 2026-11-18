import bcrypt
import pytest

from app.core.security import hash_password, verify_password


def test_hash_uses_bcrypt_with_random_salt():
    password = "Senha-segura-á123"
    first = hash_password(password)
    second = hash_password(password)

    assert first != second
    assert first != password
    assert bcrypt.checkpw(password.encode("utf-8"), first.encode("ascii"))
    assert verify_password(password, first)
    assert not verify_password("senha-incorreta", first)


@pytest.mark.parametrize("password", ["", "a" * 73, "á" * 37])
def test_invalid_password_is_rejected_without_truncation(password):
    with pytest.raises(ValueError, match="72 bytes"):
        hash_password(password)
    assert not verify_password(password, hash_password("a" * 72))


def test_password_at_utf8_byte_limit():
    password = "á" * 36
    assert verify_password(password, hash_password(password))


@pytest.mark.parametrize("stored_hash", ["", "plaintext", "$2b$invalid", "inválido"])
def test_invalid_stored_hash_returns_false(stored_hash):
    assert not verify_password("senha", stored_hash)
