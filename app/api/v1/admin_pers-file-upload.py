import hashlib
import logging
from pathlib import Path
import boto3
import os
import uuid

from fastapi import APIRouter, Depends, Form, Request, File, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin_auth
from app.db.session import get_session
from app.middleware.auth import signer
from app.models import PortfolioFile

router = APIRouter()
# Resolve templates: __file__ is app/api/v1/admin_pers-file-upload.py -> go up to app/ then templates
_templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

# DigitalOcean Spaces (S3 compatible) client
s3 = boto3.client(
    "s3",
    region_name=os.getenv("DO_SPACE_REGION"),
    endpoint_url="https://sfo3.digitaloceanspaces.com",
    aws_access_key_id=os.getenv("DO_SPACE_KEY"),
    aws_secret_access_key=os.getenv("DO_SPACE_SECRET"),
)


# ============================================================================
# LOGIN ROUTES
# ============================================================================

@router.get("/admin/personal/login")
async def personal_login(request: Request):
    """Render login page for personal section."""
    return templates.TemplateResponse(
        "admin/personal/login.html",
        {"request": request},
    )


@router.post("/admin/personal/login")
async def personal_login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """Authenticate admin user then redirect to personal dashboard."""
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
        return RedirectResponse("/admin/personal/login?error=invalid", status_code=303)

    incoming_hash = hashlib.sha256(password.encode()).hexdigest()
    if row["hashed_password"] != incoming_hash:
        return RedirectResponse("/admin/personal/login?error=invalid", status_code=303)

    token = signer.sign(str(row["id"])).decode()
    resp = RedirectResponse("/admin/personal", status_code=303)
    resp.set_cookie(
        "admin_session",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return resp


@router.get("/admin/file-upload/login")
async def file_upload_login(request: Request):
    """Render login page for private file storage."""
    try:
        return templates.TemplateResponse(
            "admin/personal/file/file-upload-login.html",
            {"request": request},
        )
    except Exception as e:
        logging.exception("file_upload_login failed")
        raise


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


# ============================================================================
# PERSONAL DASHBOARD ROUTES
# ============================================================================

@router.get(
    "/admin/personal",
    dependencies=[Depends(require_admin_auth)],
    response_class=HTMLResponse,
)
async def personal_dashboard(request: Request):
    """Personal dashboard page with links to file storage and music."""
    return templates.TemplateResponse(
        "admin/personal/my-pers-dash.html",
        {"request": request},
    )


# ============================================================================
# MUSIC ROUTES
# ============================================================================

@router.get(
    "/admin/personal/music",
    dependencies=[Depends(require_admin_auth)],
    response_class=HTMLResponse,
)
async def music_main(request: Request):
    """Music library main page with folder links."""
    return templates.TemplateResponse(
        "admin/personal/music/music-main.html",
        {"request": request},
    )


@router.get(
    "/admin/personal/music/soc",
    dependencies=[Depends(require_admin_auth)],
    response_class=HTMLResponse,
)
async def soc(request: Request):
    """SOC music folder page."""
    return templates.TemplateResponse(
        "admin/personal/music/soc.html",
        {"request": request},
    )    


@router.get(
    "/admin/personal/music/true-solfeggio",
    dependencies=[Depends(require_admin_auth)],
    response_class=HTMLResponse,
)
async def true_solfeggio(request: Request):
    """True Solfeggio music folder page."""
    return templates.TemplateResponse(
        "admin/personal/music/True-Solfeggio.html",
        {"request": request},
    )


@router.get(
    "/admin/personal/music/relaxing",
    dependencies=[Depends(require_admin_auth)],
    response_class=HTMLResponse,
)
async def relaxing(request: Request):
    """Relaxing music folder page."""
    return templates.TemplateResponse(
        "admin/personal/music/relaxing.html",
        {"request": request},
    )


# ============================================================================
# FILE UPLOAD ROUTES
# ============================================================================

@router.get(
    "/admin/file-upload",
    dependencies=[Depends(require_admin_auth)],
)
async def file_upload_console(request: Request):
    """Protected page to upload to private storage."""
    return templates.TemplateResponse(
        "admin/personal/file/file-upload.html",
        {"request": request},
    )


def _safe_prefix(raw: str | None) -> str:
    """Sanitize folder prefix to prevent path traversal."""
    if not raw:
        return ""
    # strip leading slashes and prevent path traversal
    cleaned = raw.replace("..", "").lstrip("/").strip()
    if cleaned and not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned


@router.post("/upload-file", dependencies=[Depends(require_admin_auth)], response_class=JSONResponse)
async def upload_file(
    file: UploadFile = File(...),
    path: str | None = Form(None),
    db: AsyncSession = Depends(get_session),
):
    """Upload file to DigitalOcean Spaces (private ACL)."""
    # Optional folder prefix (for multi-file/folder uploads)
    prefix = _safe_prefix(path)
    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    suffix = f".{ext}" if ext else ""
    fname = f"{prefix}{uuid.uuid4()}{suffix}"
    try:
        file_content = await file.read()
        s3.put_object(
            Bucket=os.getenv("DO_SPACE_BUCKET"),
            Key=fname,
            Body=file_content,
            ACL="private",
        )
        url_path = f"/api/v1/file/{fname}"
        db.add(PortfolioFile(filename=fname, url_path=url_path))
        await db.commit()
        return JSONResponse({"status": "ok", "file": fname, "url_path": url_path})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@router.get("/api/v1/file/{filename:path}")
async def get_file(filename: str):
    """
    Generate a short-lived signed URL to fetch the private object.
    """
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": os.getenv("DO_SPACE_BUCKET"), "Key": filename},
            ExpiresIn=600,  # 10 minutes
        )
        return RedirectResponse(url)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
