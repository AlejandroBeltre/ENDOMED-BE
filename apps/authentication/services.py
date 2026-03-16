from django.contrib.auth import authenticate

from apps.authentication.models import User, UserSede


def authenticate_user(email: str, password: str) -> User | None:
    """Return User if credentials are valid, None otherwise."""
    return authenticate(username=email, password=password)


def get_user_sedes(user: User) -> list[dict]:
    """Return the sedes the user has access to, with is_primary flag."""
    rows = (
        UserSede.objects.filter(user=user)
        .select_related("sede")
        .order_by("-is_primary", "sede__nombre")
    )
    return [
        {
            "id": str(us.sede.id),
            "nombre": us.sede.nombre,
            "ciudad": us.sede.ciudad,
            "is_primary": us.sede.is_active and us.is_primary,
        }
        for us in rows
        if us.sede.is_active
    ]


def validate_sede_access(user: User, sede_id) -> bool:
    """Check the user is assigned to the given sede."""
    return UserSede.objects.filter(user=user, sede_id=sede_id).exists()


def get_allowed_sede_ids(user: User) -> list:
    return list(UserSede.objects.filter(user=user).values_list("sede_id", flat=True))
