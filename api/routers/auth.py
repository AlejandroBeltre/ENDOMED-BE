"""Auth endpoints — token issuance, refresh, logout."""

from decouple import config as _env
from fastapi import APIRouter, HTTPException, Request, Response, status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from api.schemas.auth import LoginRequest, TokenResponse
from apps.authentication.services import authenticate_user, get_user_sedes

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_NAME = "refresh_token"
_COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 days in seconds
_SECURE_COOKIE: bool = _env("SECURE_COOKIES", default=False, cast=bool)


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=_SECURE_COOKIE,
        samesite="strict",
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


@router.post("/token", response_model=TokenResponse)
def login(data: LoginRequest, response: Response):
    user = authenticate_user(data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    refresh = RefreshToken.for_user(user)
    _set_refresh_cookie(response, str(refresh))

    sedes_raw = get_user_sedes(user)
    sedes = [
        {
            "id": s["id"],
            "nombre": s["nombre"],
            "ciudad": s["ciudad"],
            "is_primary": s["is_primary"],
        }
        for s in sedes_raw
    ]

    return {
        "access_token": str(refresh.access_token),
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "role": user.role,
        },
        "sedes": sedes,
    }


@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    token_str = request.cookies.get(_COOKIE_NAME)
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no encontrado.",
        )

    try:
        refresh = RefreshToken(token_str)
        new_access = str(refresh.access_token)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado.",
        )

    # Rotate: issue a new refresh token and update the cookie
    _set_refresh_cookie(response, str(refresh))
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(key=_COOKIE_NAME, path="/")
