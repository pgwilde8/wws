from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.client import Client
from sqlalchemy import select, func
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.get("/")
async def client_cards(
    request: Request,
    page: int = Query(1, ge=1),
    search: str | None = None,
    db: AsyncSession = Depends(get_session)
):
    per_page = 12
    offset = (page - 1) * per_page

    query = select(Client)
    count_q = select(func.count(Client.id))

    if search:
        query = query.where(Client.name.ilike(f"%{search}%"))
        count_q = count_q.where(Client.name.ilike(f"%{search}%"))

    query = query.offset(offset).limit(per_page)

    total = (await db.execute(count_q)).scalar() or 0
    clients = (await db.execute(query)).scalars().all()

    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "admin/clients.html",
        {"request": request, "clients": clients, "page": page, "total_pages": total_pages, "search": search or ""}
    )
