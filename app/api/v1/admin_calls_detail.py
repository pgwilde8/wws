from fastapi import APIRouter, Depends, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.security import require_admin_auth
from app.models.call_booking import CallBooking

router = APIRouter(
    prefix="/admin/calls",
    tags=["Admin Call Detail"],
    dependencies=[Depends(require_admin_auth)]
)

@router.get("/{call_id}")
async def view_call_booking(
    request: Request,
    call_id: str = Path(..., min_length=5, max_length=120),
    session: AsyncSession = Depends(get_session)
):
    """
    Contract: Load 1 call booking from DB and render detail page
    """
    call = await session.get(CallBooking, call_id)
    if not call:
        return {"error": "Call booking not found"}

    return {"call": call}
