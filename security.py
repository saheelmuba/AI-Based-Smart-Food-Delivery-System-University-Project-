import re
from functools import wraps
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN_LENGTH = 8


def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def check_password(password_hash, password):
    return check_password_hash(password_hash, password)


def is_valid_email(email):
    return bool(EMAIL_REGEX.fullmatch(email or ""))


def is_valid_password(password):
    return isinstance(password, str) and len(password) >= PASSWORD_MIN_LENGTH


def register_security_headers(app):
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
        if not app.config.get("DEBUG"):
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=63072000; includeSubDomains; preload"
        return response


def validate_json_payload(payload, required_fields):
    missing = []
    for field in required_fields:
        if field not in payload or payload[field] is None:
            missing.append(field)
        elif isinstance(payload[field], str) and not payload[field].strip():
            missing.append(field)
    return missing


def sanitize_input(value):
    if isinstance(value, str):
        return value.strip()
    return value


def authorize_role(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import get_jwt_identity
            from models import User

            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or user.role not in allowed_roles:
                return jsonify({"message": "You do not have permission to perform this action."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
