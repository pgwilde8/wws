"""Coupon service utilities."""
import random
import string
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.coupon import Coupon, CouponRedemption


def generate_coupon_code(length: Optional[int] = None) -> str:
    """Generate a random coupon code."""
    if length is None:
        length = settings.COUPON_CODE_LENGTH
    
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choices(characters, k=length))


def validate_coupon_code(db: Session, code: str) -> Optional[Coupon]:
    """Validate a coupon code and return the coupon if valid."""
    coupon = db.query(Coupon).filter(Coupon.code == code.upper()).first()
    
    if coupon and coupon.is_valid():
        return coupon
    
    return None


def apply_coupon(db: Session, coupon_id: int, email: str, ip_address: Optional[str] = None) -> CouponRedemption:
    """Apply a coupon and create redemption record."""
    
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise ValueError("Coupon not found")
    
    if not coupon.is_valid():
        raise ValueError("Coupon is not valid")
    
    # Check if already redeemed by this email
    existing = db.query(CouponRedemption).filter(
        CouponRedemption.coupon_id == coupon_id,
        CouponRedemption.email == email
    ).first()
    
    if existing:
        raise ValueError("Coupon already redeemed by this email")
    
    # Create redemption
    redemption = CouponRedemption(
        coupon_id=coupon_id,
        email=email,
        ip_address=ip_address
    )
    
    db.add(redemption)
    coupon.current_uses += 1
    db.commit()
    db.refresh(redemption)
    
    return redemption


def get_coupon_stats(db: Session, coupon_id: int) -> dict:
    """Get statistics for a coupon."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        return {}
    
    total_redemptions = db.query(CouponRedemption).filter(
        CouponRedemption.coupon_id == coupon_id
    ).count()
    
    return {
        "code": coupon.code,
        "current_uses": coupon.current_uses,
        "max_uses": coupon.max_uses,
        "total_redemptions": total_redemptions,
        "is_active": coupon.is_active,
        "expires_at": coupon.expires_at.isoformat() if coupon.expires_at else None,
    }

