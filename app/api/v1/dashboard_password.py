from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import hashlib

from app.db.session import get_session
from app.middleware.auth import _get_client_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/change-password")
async def change_password_page(
    request: Request,
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    """Render password change page for client users."""
    return templates.TemplateResponse(
        "dashboard/change-password.html",
        {
            "request": request,
        },
    )


@router.post("/change-password")
async def change_password_post(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    """Handle password change for client users."""
    
    # Validate new password length
    if len(new_password) < 8:
        return RedirectResponse(
            "/dashboard/change-password?error=length",
            status_code=303
        )
    
    # Get current password hash from database
    res = await db.execute(
        text(
            """
            SELECT hashed_password
            FROM users
            WHERE id = :user_id
            LIMIT 1
            """
        ),
        {"user_id": client_id},
    )
    row = res.mappings().first()
    
    if not row:
        return RedirectResponse(
            "/dashboard/change-password?error=notfound",
            status_code=303
        )
    
    # Verify current password
    current_hash = hashlib.sha256(current_password.encode()).hexdigest()
    if row["hashed_password"] != current_hash:
        return RedirectResponse(
            "/dashboard/change-password?error=invalid",
            status_code=303
        )
    
    # Hash new password
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    # Update password in database
    await db.execute(
        text(
            """
            UPDATE users
            SET hashed_password = :new_hash
            WHERE id = :user_id
            """
        ),
        {"user_id": client_id, "new_hash": new_hash},
    )
    await db.commit()
    
    return RedirectResponse(
        "/dashboard/change-password?success=true",
        status_code=303
    )

