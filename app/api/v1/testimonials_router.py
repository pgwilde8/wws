from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.core.security import require_admin  # dependency you can implement for admin-only pages
from app.models.testimonial import Testimonial
from datetime import datetime

router = APIRouter()

# Client submits testimonial (public or authenticated client)
@router.post("/submit", status_code=201)
async def submit_testimonial(payload: dict, db: AsyncSession = Depends(get_db)):
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
        stripe_reference=payload.get("stripe_reference"),
        received_at=datetime.utcnow(),
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": t.id, "status": "submitted"}

# Admin listing page (filtered to meaningful events)
@router.get("/", dependencies=[Depends(require_admin)])
async def list_testimonials(page: int = 1, page_size: int = 12, db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * page_size
    q = select(Testimonial).where(Testimonial.archived == False).order_by(Testimonial.received_at.desc()).offset(offset).limit(page_size)
    res = await db.execute(q)
    items = res.scalars().all()
    total = await db.scalar(select(Testimonial).where(Testimonial.archived == False).count())
    return {"items": items, "page": page, "total": total}

# Admin approves testimonial
@router.patch("/{tid}/approve", dependencies=[Depends(require_admin)])
async def approve_testimonial(tid: int, db: AsyncSession = Depends(get_db)):
    t = await db.get(Testimonial, tid)
    if not t:
        raise HTTPException(404, "Not found")
    t.is_approved = True
    await db.commit()
    return {"status": "approved"}

# Admin archives testimonial
@router.delete("/{tid}", dependencies=[Depends(require_admin)])
async def archive_testimonial(tid: int, db: AsyncSession = Depends(get_db)):
    t = await db.get(Testimonial, tid)
    if not t:
        raise HTTPException(404, "Not found")
    t.archived = True
    await db.commit()
    return {"status": "archived"}

# Admin marks featured
@router.patch("/{tid}/feature", dependencies=[Depends(require_admin)])
async def feature_testimonial(tid: int, featured: bool, db: AsyncSession = Depends(get_db)):
    t = await db.get(Testimonial, tid)
    if not t:
        raise HTTPException(404, "Not found")
    t.is_featured = featured
    await db.commit()
    return {"status": "updated", "featured": featured}
