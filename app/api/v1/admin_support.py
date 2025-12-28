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
    Contract: return support threads and total pages
    """
    q = f"%{search}%"

    # Get 12 most recent support threads (grouped by client email)
    result = await session.execute(
        "SELECT DISTINCT ON (client_email) id, client_email, plan_name, created_at "
        "FROM support_messages "
        "WHERE client_email ILIKE :q "
        "ORDER BY client_email, created_at DESC "
        "LIMIT 12 OFFSET :offset",
        {"q": q, "offset": (page - 1) * 12}
    )
    threads = result.fetchall()

    # Count pages
    count = await session.execute(
        "SELECT COUNT(DISTINCT client_email) FROM support_messages WHERE client_email ILIKE :q",
        {"q": q}
    )
    total = count.scalar() or 0
    total_pages = ceil(total / 12)

    return {
        "threads": threads,
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
