from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.webhook_event import WebhookEvent

router = APIRouter(prefix="/api/admin/stripe/webhooks", tags=["Stripe Webhooks"])

@router.get("")
async def list_webhooks(
    page: int = 1,
    limit: int = 12,
    client_id: int | None = None,
    project_id: int | None = None,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    account: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(WebhookEvent)

    # apply filters only if provided
    if client_id:
        q = q.filter(WebhookEvent.client_id == client_id)
    if project_id:
        q = q.filter(WebhookEvent.project_id == project_id)
    if category:
        q = q.filter(WebhookEvent.category == category)
    if status:
        q = q.filter(WebhookEvent.status == status)
    if search:
        q = q.filter(WebhookEvent.event_type.ilike(f"%{search}%"))
    if account:
        q = q.filter(WebhookEvent.stripe_account.ilike(f"%{account}%"))

    total = q.count()
    total_pages = max(1, (total + limit - 1) // limit)
    page = min(page, total_pages)

    events = (
        q.order_by(WebhookEvent.received_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "page": page,
        "total_pages": total_pages,
        "total_events": total,
        "events": events,
    }
