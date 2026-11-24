"""Hash e verificação de senhas usando bcrypt diretamente."""

import bcrypt


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if not password_bytes or len(password_bytes) > 72:
        raise ValueError("A senha deve conter entre 1 e 72 bytes em UTF-8.")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_bytes = password.encode("utf-8")
        if not password_bytes or len(password_bytes) > 72:
            return False
        return bcrypt.checkpw(password_bytes, password_hash.encode("ascii"))
    except (ValueError, UnicodeError):
        return False
