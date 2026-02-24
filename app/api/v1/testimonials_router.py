from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_session
from app.core.security import require_admin_auth
from app.models.testimonial import Testimonial
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Client submits testimonial (public or authenticated client) - no admin auth required
@router.post("/submit", status_code=201)
async def submit_testimonial(payload: dict, db: AsyncSession = Depends(get_session)):
    text = payload.get("testimonial_text")
    name = payload.get("client_name")
    if not text or not name:
        raise HTTPException(400, "Missing required fields")

    t = Testimonial(
        client_id=payload.get("client_id"),
        client_name=name,
        client_location=payload.get("client_location"),
        event_type=payload.get("event_type"),
        testimonial_text=text,
        rating=payload.get("rating"),
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": t.id, "status": "submitted"}

# Admin testimonials management page
@router.get("/", dependencies=[Depends(require_admin_auth)])
async def testimonials_admin_page(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    # Get pending testimonials (not approved)
    pending_query = select(Testimonial).where(
        Testimonial.is_approved == False
    ).order_by(Testimonial.created_at.desc())
    pending_result = await db.execute(pending_query)
    pending_testimonials = pending_result.scalars().all()
    
    # Get approved testimonials
    approved_query = select(Testimonial).where(
        Testimonial.is_approved == True
    ).order_by(Testimonial.created_at.desc())
    approved_result = await db.execute(approved_query)
    approved_testimonials = approved_result.scalars().all()
    
    # Counts
    pending_count = len(pending_testimonials)
    approved_count = len(approved_testimonials)
    total_count = pending_count + approved_count
    
    return templates.TemplateResponse(
        "admin/testimonials.html",
        {
            "request": request,
            "pending_testimonials": pending_testimonials,
            "approved_testimonials": approved_testimonials[:20],  # Show last 20 approved
            "pending_count": pending_count,
            "approved_count": approved_count,
            "total_count": total_count,
        }
    )

# Admin approves testimonial (POST for form submission)
@router.post("/{tid}/approve", dependencies=[Depends(require_admin_auth)])
async def approve_testimonial(
    tid: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    t = await db.get(Testimonial, tid)
    if not t:
        raise HTTPException(404, "Not found")
    t.is_approved = True
    await db.commit()
    return RedirectResponse(url="/admin/testimonials", status_code=303)

# Admin deletes testimonial (POST for form submission)
@router.post("/{tid}/delete", dependencies=[Depends(require_admin_auth)])
async def delete_testimonial(
    tid: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    t = await db.get(Testimonial, tid)
    if not t:
        raise HTTPException(404, "Not found")
    await db.delete(t)
    await db.commit()
    return RedirectResponse(url="/admin/testimonials", status_code=303)

# Note: is_featured field doesn't exist in database, so feature endpoint removed
