from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi.templating import Jinja2Templates
from app.db.session import get_session
from app.models.order import Order

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/orders")
async def client_orders(
    request: Request,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_session)
):
    per_page = 10
    offset = (page - 1) * per_page

    total = (await db.execute(select(func.count(Order.id)))).scalar()
    orders = (await db.execute(select(Order).offset(offset).limit(per_page))).scalars().all()

    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "dashboard/orders.html",
        {
            "request": request,
            "orders": orders,
            "page": page,
            "total_pages": total_pages,
        }
    )
