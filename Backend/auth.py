from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import or_

from extensions import db
from models import User
from security import create_access_token, get_current_user_id


auth_bp = APIRouter(prefix="/api/auth")

PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE_REGEX = re.compile(r"^[6-9][0-9]{9}$")


def _error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse({"message": message}, status_code=status_code)


def _normalize_pan(pancard_number: str) -> str:
    return pancard_number.strip().upper()


async def _json_payload(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    return payload if isinstance(payload, dict) else {}


@auth_bp.post("/register")
async def register(request: Request):
    payload = await _json_payload(request)

    name = str(payload.get("name", "")).strip()
    pancard_number = _normalize_pan(str(payload.get("pancard_number", "")))
    password = str(payload.get("password", ""))
    mobile_number = str(payload.get("mobile_number", "")).strip()
    email = str(payload.get("email", "")).strip().lower()

    if not all([name, pancard_number, password, mobile_number, email]):
        return _error("name, pancard_number, password, mobile_number, and email are required.", 400)

    if not PAN_REGEX.fullmatch(pancard_number):
        return _error("Invalid PAN card number format.", 400)

    if not EMAIL_REGEX.fullmatch(email):
        return _error("Invalid email address.", 400)

    if not MOBILE_REGEX.fullmatch(mobile_number):
        return _error("Invalid mobile number. Use a 10-digit Indian mobile number.", 400)

    if len(password) < 8:
        return _error("Password must be at least 8 characters long.", 400)

    existing_user = User.query.filter(
        or_(
            User.email == email,
            User.pancard_number == pancard_number,
            User.mobile_number == mobile_number,
        )
    ).first()
    if existing_user:
        return _error("A user with this email, PAN card number, or mobile number already exists.", 409)

    user = User(
        name=name,
        pancard_number=pancard_number,
        mobile_number=mobile_number,
        email=email,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))

    return JSONResponse(
        {
            "message": "User registered successfully.",
            "access_token": access_token,
            "user": user.to_dict(),
        },
        status_code=201,
    )


@auth_bp.post("/login")
async def login(request: Request):
    payload = await _json_payload(request)

    identifier = str(payload.get("identifier", "")).strip()
    password = str(payload.get("password", ""))

    if not identifier or not password:
        return _error("identifier and password are required.", 400)

    normalized_identifier = identifier.lower()
    user = User.query.filter(
        or_(
            User.email == normalized_identifier,
            User.pancard_number == _normalize_pan(identifier),
        )
    ).first()

    if user is None or not user.check_password(password):
        return _error("Invalid credentials.", 401)

    access_token = create_access_token(identity=str(user.id))

    return {
        "message": "Login successful.",
        "access_token": access_token,
        "user": user.to_dict(),
    }


@auth_bp.get("/me")
def me(current_user_id: int = Depends(get_current_user_id)):
    user = db.session.get(User, int(current_user_id))

    if user is None:
        return _error("User not found.", 404)

    return {"user": user.to_dict()}
