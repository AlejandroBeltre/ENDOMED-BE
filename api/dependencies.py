"""FastAPI shared dependencies.

Phase 1: stubs only.
Phase 2: full JWT verification against SimpleJWT tokens + sede scope check.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Decode and validate the JWT access_token. Returns the User instance.

    Raises 401 if the token is missing, expired, or invalid.
    Full implementation in Phase 2.
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticación requerida.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*roles: str):
    """FastAPI dependency factory for RBAC.

    Usage:
        @router.get("/reportes/")
        async def get_reportes(user=Depends(require_role("doctora"))):
            ...
    """

    async def dep(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles requeridos: {', '.join(roles)}.",
            )
        return current_user

    return dep
