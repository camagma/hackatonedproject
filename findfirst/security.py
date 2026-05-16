import hashlib
import hmac
import secrets


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def password_is_hashed(value: str | None) -> bool:
    return bool(value and value.startswith(f"{PASSWORD_SCHEME}$"))


def verify_password(stored: str | None, provided: str) -> bool:
    if not stored:
        return False
    if not password_is_hashed(stored):
        return hmac.compare_digest(stored, provided or "")
    try:
        scheme, iterations, salt, expected = stored.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            (provided or "").encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False
