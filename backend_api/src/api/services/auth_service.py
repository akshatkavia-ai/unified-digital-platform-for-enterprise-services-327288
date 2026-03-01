from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException

from src.api.core.db import db_conn_cursor, get_database_config
from src.api.core.logging import get_logger, log_kv
from src.api.core.security import create_access_token, hash_password, verify_password

logger = get_logger(__name__)


@dataclass(frozen=True)
class UserRecord:
    id: UUID
    email: str
    password_hash: str
    is_active: bool
    mfa_enabled: bool


def _row_to_user(row) -> UserRecord:
    return UserRecord(
        id=UUID(str(row["id"])),
        email=row["email"],
        password_hash=row["password_hash"],
        is_active=bool(row["is_active"]),
        mfa_enabled=bool(row["mfa_enabled"]),
    )


# PUBLIC_INTERFACE
def register_user(*, email: str, password: str) -> UserRecord:
    """Register a new user.

    Contract:
      - Email must be unique.
      - Password is hashed using passlib before storage.

    Errors:
      - HTTPException(409) if email already exists.
    """
    cfg = get_database_config()
    log_kv(logger, "auth.register:start", email=email)
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute("SELECT id FROM iam_users WHERE email=%s", (email,))
        existing = cur.fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        user_id = uuid4()
        pw_hash = hash_password(password)
        cur.execute(
            """
            INSERT INTO iam_users (id, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (str(user_id), email, pw_hash),
        )
        cur.execute("SELECT * FROM iam_users WHERE id=%s", (str(user_id),))
        row = cur.fetchone()

    user = _row_to_user(row)
    log_kv(logger, "auth.register:done", user_id=str(user.id))
    return user


# PUBLIC_INTERFACE
def authenticate_user(*, email: str, password: str, mfa_code: Optional[str]) -> str:
    """Authenticate a user and return an access token.

    Contract:
      - Validates password hash.
      - If mfa_enabled is true, requires mfa_code (scaffolding only; no TOTP validation yet).

    Outputs:
      - JWT access token

    Errors:
      - HTTPException(401) for invalid credentials or missing MFA code.
      - HTTPException(403) if user is inactive.
    """
    cfg = get_database_config()
    log_kv(logger, "auth.login:start", email=email)
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute("SELECT * FROM iam_users WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = _row_to_user(row)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.mfa_enabled and not mfa_code:
        raise HTTPException(status_code=401, detail="MFA code required")

    token = create_access_token(subject=str(user.id), extra_claims={"email": user.email, "mfa": user.mfa_enabled})
    log_kv(logger, "auth.login:done", user_id=str(user.id))
    return token


# PUBLIC_INTERFACE
def enroll_mfa_stub(*, user_id: str) -> dict:
    """Enable MFA for a user (scaffolding).

    Contract:
      - Marks mfa_enabled=true.
      - Returns a placeholder provisioning_uri for future TOTP enrollment UX.

    NOTE:
      This is scaffolding only. Real MFA should implement:
        - secret generation (per-user)
        - TOTP validation
        - backup codes
        - device binding and step-up auth policies
    """
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute("UPDATE iam_users SET mfa_enabled=TRUE, updated_at=NOW() WHERE id=%s", (user_id,))
        cur.execute("SELECT mfa_enabled, email FROM iam_users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

    # Placeholder provisioning URI
    email = row["email"]
    provisioning_uri = f"otpauth://totp/UDP:{email}?secret=STUBSECRET&issuer=UDP"
    return {"mfa_enabled": bool(row["mfa_enabled"]), "provisioning_uri": provisioning_uri}
