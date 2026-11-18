


"""Authentication for Gabrino.

- Users live in users.json: {username: password_hash} (werkzeug hashes).
  Manage with adduser.py — never edit hashes by hand.
- Login issues a signed, expiring token (itsdangerous). The token is
  required both for the HTTP session and to open the control WebSocket.
- A separate static DEVICE_TOKEN (env) lets the robot/firmware connect
  without a user account.
"""

import json
import os
import secrets
from pathlib import Path

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

USERS_FILE = Path(__file__).with_name("users.json")
TOKEN_TTL = 12 * 60 * 60  # seconds — 12 hours
_SALT = "gabrino-auth-v1"

# Signing secret. Set GABRINO_SECRET in production so tokens survive restarts
# and can't be forged. Without it we generate a per-process key (all sessions
# are invalidated on restart) and warn.
_SECRET = os.environ.get("GABRINO_SECRET")
if not _SECRET:
    _SECRET = secrets.token_urlsafe(32)
    print("[WARN] GABRINO_SECRET not set — using a random per-process key. "
          "Tokens will not survive a restart. Set GABRINO_SECRET for production.")

# Optional static token for the robot/firmware to authenticate the WebSocket.
DEVICE_TOKEN = os.environ.get("GABRINO_DEVICE_TOKEN") or None

_serializer = URLSafeTimedSerializer(_SECRET, salt=_SALT)


def _load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def add_user(username, password):
    """Create or update a user with a hashed password."""
    users = _load_users()
    users[username] = generate_password_hash(password)
    _save_users(users)


def verify_password(username, password):
    """True when username exists and password matches its hash."""
    users = _load_users()
    stored = users.get(username)
    if not stored:
        # Hash anyway to keep timing roughly constant against user enumeration.
        check_password_hash(generate_password_hash("_"), password)
        return False
    return check_password_hash(stored, password)


def create_token(username):
    """Sign a session token for username."""
    return _serializer.dumps({"u": username})


def verify_token(token):
    """Return the username for a valid, unexpired token.

    Also accepts the static DEVICE_TOKEN, returning 'gabrino-device'.
    Returns None for anything invalid or expired.
    """
    if not token:
        return None
    if DEVICE_TOKEN and secrets.compare_digest(token, DEVICE_TOKEN):
        return "gabrino-device"
    try:
        data = _serializer.loads(token, max_age=TOKEN_TTL)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("u")


def has_users():
    return bool(_load_users())
