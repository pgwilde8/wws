import os
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from app.core.security import require_admin_auth

router = APIRouter(
    tags=["Admin Checkout"],
    dependencies=[Depends(require_admin_auth)]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/checkout")
async def admin_checkout_page(request: Request):
    price_map = {
        "starter": {
            "product": os.getenv("STRIPE_PRODUCT_STARTER", ""),
            "price": os.getenv("STRIPE_PRICE_STARTER", ""),
        },
        "growth": {
            "product": os.getenv("STRIPE_PRODUCT_GROWTH", ""),
            "price": os.getenv("STRIPE_PRICE_GROWTH", ""),
        },
        "scale": {
            "product": os.getenv("STRIPE_PRODUCT_SCALE", ""),
            "price": os.getenv("STRIPE_PRICE_SCALE", ""),
        },
    }
    return templates.TemplateResponse(
        "admin/checkout.html",
        {"request": request, "price_map": price_map},
    )
