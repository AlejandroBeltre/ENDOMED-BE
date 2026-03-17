"""Telemedicina endpoint — issues signed JWT tokens for Jitsi Meet rooms."""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_user
from apps.agenda.services import get_cita

router = APIRouter(prefix="/telemedicina", tags=["telemedicina"])


@router.get("/token/{cita_id}")
def get_jitsi_token(cita_id: UUID, user=Depends(get_current_user)) -> dict:
    """Return a signed JWT for embedding the Jitsi room of a given cita.

    The JWT is signed with JITSI_APP_SECRET and accepted by the Jitsi JWT
    authentication plugin.  Room name = cita UUID.
    """
    import jwt
    from decouple import config

    cita = get_cita(cita_id, user)

    if cita.modalidad != "virtual":
        raise HTTPException(400, "Esta cita no es virtual.")

    app_id = config("JITSI_APP_ID", default="endomed")
    secret = config("JITSI_APP_SECRET", default="dev_secret_change_me")
    domain = config("VITE_JITSI_DOMAIN", default="meet.jit.si")

    now = int(time.time())
    payload = {
        "iss": app_id,
        "aud": "jitsi",
        "sub": domain,
        "room": str(cita_id),
        "iat": now,
        "exp": now + 3600,  # 1 hour
        "context": {
            "user": {
                "id": str(user.id),
                "name": f"{user.nombre} {user.apellido}",
                "email": user.email,
                "moderator": user.role == "doctora",
            },
        },
    }

    token = jwt.encode(payload, secret, algorithm="HS256")

    return {
        "token": token,
        "room": str(cita_id),
        "domain": domain,
    }
