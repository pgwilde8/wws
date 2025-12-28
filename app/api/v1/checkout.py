import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from app.db.session import get_session
from app.core.security import get_current_user_optional

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/api/checkout", tags=["Checkout"])

@router.post("/create-session")
async def create_checkout_session(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_optional)
):
    data = await request.json()
    plan = data.get("plan")

    # Map plan names to your Stripe price IDs from .env
    prices = {
        "starter": os.getenv("STRIPE_PRICE_STARTER_BUILD"),
        "growth": os.getenv("STRIPE_PRICE_GROWTH_BUILD"),
        "scale": os.getenv("STRIPE_PRICE_SCALE_BUILD"),
        "1997": "price_1Sg9rHRzRv6CTjxR69nkwXrx",
        "3997": "price_1Sg9t0RzRv6CTjxRDJZdEq5y",
        "5997": "price_1Sg9uTRzRv6CTjxR0It8rVkC"
    }

    if plan not in prices:
        raise HTTPException(status_code=400, detail="Invalid plan")

    price_id = prices[plan]
    if not price_id:
        raise HTTPException(status_code=500, detail="Price ID missing in env")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url="/client/dashboard?checkout=success",
            cancel_url="/pricing?checkout=cancelled",
            metadata={
                "user_id": user.id if user else "guest",
                "plan": plan
            }
        )
        return JSONResponse({"id": checkout_session.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
