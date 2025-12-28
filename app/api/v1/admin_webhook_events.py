from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_session
from app.models.webhook_event import WebhookEvent

router = APIRouter()

@router.get("/events")
async def webhook_events_listing(
    request: Request,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_session)
):
    per_page = 15
    offset = (page - 1) * per_page

    total = (await db.execute(select(func.count(WebhookEvent.id)))).scalar()
    events = (await db.execute(select(WebhookEvent).order_by(WebhookEvent.received_at.desc()).offset(offset).limit(per_page))).scalars().all()

    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "admin/webhook_events.html",
        {
            "request": request,
            "events": events,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        }
    )
