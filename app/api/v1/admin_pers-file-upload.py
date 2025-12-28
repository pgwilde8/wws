import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin_auth
from app.db.session import get_session
from app.middleware.auth import signer

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/file-upload/login")
async def file_upload_login(request: Request):
    """Render login page for private file storage."""
    return templates.TemplateResponse(
        "admin/file-upload-login.html",
        {"request": request},
    )


@router.post("/admin/file-upload/login")
async def file_upload_login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """Authenticate admin user then redirect to the upload console."""
    res = await db.execute(
        text(
            """
            SELECT id, hashed_password
            FROM users
            WHERE email = :email AND role = 'admin'
            LIMIT 1
            """
        ),
        {"email": email},
    )
    row = res.mappings().first()
    if not row:
        return RedirectResponse("/admin/file-upload/login?error=invalid", status_code=303)

    incoming_hash = hashlib.sha256(password.encode()).hexdigest()
    if row["hashed_password"] != incoming_hash:
        return RedirectResponse("/admin/file-upload/login?error=invalid", status_code=303)

    token = signer.sign(str(row["id"])).decode()
    resp = RedirectResponse("/admin/file-upload", status_code=303)
    resp.set_cookie(
        "admin_session",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return resp


@router.get(
    "/admin/file-upload",
    dependencies=[Depends(require_admin_auth)],
)
async def file_upload_console(request: Request):
    """Protected page to upload to private storage."""
    return templates.TemplateResponse(
        "admin/storage-file-o-upload.html",
        {"request": request},
    )
