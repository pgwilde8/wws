from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.webhook_event import WebhookEvent

router = APIRouter(prefix="/admin/stripe/webhooks", tags=["Admin UI"])

@router.get("")
async def webhooks_page(request: Request, db: Session = Depends(get_db)):
    events = db.query(WebhookEvent).order_by(WebhookEvent.received_at.desc()).limit(20).all()
    return templates.TemplateResponse("admin/webhooks.html", {"request": request, "clients": [], "projects": [], "webhooks": events, "page": 1, "total_pages": 1})
