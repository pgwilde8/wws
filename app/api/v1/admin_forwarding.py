from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.templating import Jinja2Templates

from app.db.session import get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/forwarding")
async def list_forwarding(request: Request, db: AsyncSession = Depends(get_session)):
    res = await db.execute(
        text(
            """
            SELECT id, email, created_at
            FROM lead_forward_emails
            ORDER BY created_at DESC
            """
        )
    )
    rows = res.mappings().all()
    return templates.TemplateResponse(
        "admin/forwarding.html",
        {"request": request, "rows": rows},
    )

