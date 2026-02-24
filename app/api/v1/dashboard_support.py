from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_session
from app.middleware.auth import _get_client_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/support")
async def support_page(request: Request):
    return templates.TemplateResponse(
        "dashboard/support.html",
        {
            "request": request,
            "client": None,
        },
    )


@router.get("/support/new")
async def support_page_alias(request: Request):
    return templates.TemplateResponse(
        "dashboard/support.html",
        {
            "request": request,
            "client": None,
        },
    )


@router.get("/support/inbox")
async def support_inbox(
    request: Request,
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    """Client support ticket inbox"""
    try:
        tickets = await db.execute(
            text(
                """
                SELECT st.id, st.subject, st.status, st.priority, st.created_at, st.updated_at,
                       COUNT(sm.id) as message_count
                FROM support_tickets st
                LEFT JOIN support_messages sm ON sm.ticket_id = st.id
                WHERE st.client_id = :cid
                GROUP BY st.id
                ORDER BY st.updated_at DESC
                """
            ),
            {"cid": client_id},
        )
        ticket_list = [dict(row) for row in tickets.mappings().all()]
        
        return templates.TemplateResponse(
            "dashboard/support-inbox.html",
            {
                "request": request,
                "tickets": ticket_list,
            },
        )
    except Exception as e:
        # Log error and return empty inbox
        print(f"Error loading support inbox: {e}")
        return templates.TemplateResponse(
            "dashboard/support-inbox.html",
            {
                "request": request,
                "tickets": [],
            },
        )