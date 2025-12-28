# /srv/projects/wws/app/core/security.py
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.middleware.auth import signer

bearer_scheme = HTTPBearer(auto_error=False)


async def require_admin_auth(
    request: Request,
    db: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Admin auth:
    - Preferred: admin_session cookie (signed user_id with role='admin')
    - Fallback: Bearer token admin-dev-token (legacy)
    """
    # Cookie-based admin session
    cookie = request.cookies.get("admin_session")
    if cookie:
        try:
            admin_id = int(signer.unsign(cookie).decode())
            res = await db.execute(
                text("SELECT id FROM users WHERE id = :id AND role = 'admin' LIMIT 1"),
                {"id": admin_id},
            )
            if res.scalar_one_or_none():
                return True
        except Exception:
            pass

    # Bearer token fallback
    if credentials and credentials.credentials == "admin-dev-token":
        return True

    raise HTTPException(status_code=403, detail="Invalid admin credentials")
