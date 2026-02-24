from fastapi import APIRouter, Depends, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.security import require_admin_auth
from math import ceil

router = APIRouter(prefix="/admin/support", tags=["Admin Support"], dependencies=[Depends(require_admin_auth)])

@router.get("")
async def support_inbox(
    request: Request,
    page: int = 1,
    search: str = Query("", max_length=120),
    session: AsyncSession = Depends(get_session)
):
    """
    Contract: return support tickets grouped by client
    """
    q = f"%{search}%"

    # Get support tickets ordered by most recent
    result = await session.execute(
        "SELECT st.id, st.client_id, st.subject, st.status, st.priority, st.created_at, st.updated_at, "
        "       COUNT(sm.id) as message_count "
        "FROM support_tickets st "
        "LEFT JOIN support_messages sm ON sm.ticket_id = st.id "
        "WHERE st.subject ILIKE :q "
        "GROUP BY st.id "
        "ORDER BY st.updated_at DESC "
        "LIMIT 20 OFFSET :offset",
        {"q": q, "offset": (page - 1) * 20}
    )
    tickets = [dict(row) for row in result.mappings().all()]

    # Count pages
    count = await session.execute(
        "SELECT COUNT(*) FROM support_tickets WHERE subject ILIKE :q",
        {"q": q}
    )
    total = count.scalar() or 0
    total_pages = ceil(total / 20)

    return {
        "tickets": tickets,
        "page": page,
        "search": search,
        "total_pages": total_pages
    }

@router.get("/{client_email}")
async def support_thread(
    request: Request,
    client_email: str = Path(...),
    page: int = 1,
    session: AsyncSession = Depends(get_session)
):
    """
    Contract: load support messages for 1 client
    """
    result = await session.execute(
        "SELECT * FROM support_messages "
        "WHERE client_email = :email "
        "ORDER BY created_at DESC "
        "LIMIT 20 OFFSET :offset",
        {"email": client_email, "offset": (page - 1) * 20}
    )
    messages = result.scalars().all()

    return {"messages": messages, "client_email": client_email}
