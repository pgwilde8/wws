import itsdangerous
from fastapi import Request
from app.core.config import settings

SESSION_SECRET = getattr(settings, "SESSION_SECRET", None) or settings.SECRET_KEY
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET or SECRET_KEY must be set")

signer = itsdangerous.Signer(SESSION_SECRET, salt="session")


class SimpleUser:
    def __init__(self, user_id: int):
        self.id = user_id


async def load_user_middleware(request: Request, call_next):
    request.state.user = None
    cookie = request.cookies.get("session")
    if cookie:
        try:
            user_id = int(signer.unsign(cookie).decode())
            # For now, trust the signed cookie and attach a lightweight user object.
            request.state.user = SimpleUser(user_id)
        except Exception:
            pass  # invalid/missing cookie → stay unauthenticated
    return await call_next(request)


async def _get_client_id(request: Request) -> int:
    """
    Dependency to extract the authenticated user's id from request.state.user.
    Raises 401 if not present.
    """
    user = getattr(request.state, "user", None)
    if user and getattr(user, "id", None):
        return user.id
    from fastapi import HTTPException

    raise HTTPException(status_code=401, detail="Not authenticated")