from fastapi import APIRouter, Depends, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.security import require_admin_auth
from fastapi.templating import Jinja2Templates
from app.models.webhook_event import WebhookEvent as WebhookEventModel


# Serve templates from /app/templates
templates = Jinja2Templates(directory="app/templates")

# This router is mounted under /admin/stripe/webhooks and protected by admin auth
router = APIRouter(
    prefix="/admin/stripe/webhooks",
    dependencies=[Depends(require_admin_auth)]
)

@router.get("/{event_id}")
async def webhook_detail_page(
    request: Request,
    event_id: int = Path(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Contract: Fetch a single webhook event and render detail UI.
    """
    event = await session.get(WebhookEvent, event_id)
    if not event:
        return templates.TemplateResponse(
            "admin/webhook_detail.html",
            {"request": request, "event": None, "error": "Webhook event not found"}
        )

    return templates.TemplateResponse(
        "admin/webhook_detail.html",
        {"request": request, "event": event, "raw_payload": event.raw_payload}
    )
