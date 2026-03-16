"""FastAPI shared dependencies — auth + RBAC."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify JWT access_token and return the authenticated User.

    Runs synchronously — FastAPI executes it in a thread pool.
    """
    from apps.authentication.models import User

    token_str = credentials.credentials
    try:
        token = AccessToken(token_str)
        user_id = token["user_id"]
    except (TokenError, InvalidToken):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*roles: str):
    """RBAC dependency factory.

    Usage:
        @router.get("/reportes/")
        def get_reportes(user=Depends(require_role("doctora"))):
    """

    def dep(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles requeridos: {', '.join(roles)}.",
            )
        return current_user

    return dep
