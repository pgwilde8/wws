from datetime import datetime
import secrets
import hashlib
from pathlib import Path
import importlib.util
from importlib.machinery import SourceFileLoader
from typing import Optional
import os
import stripe
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import RedirectResponse      # add this import
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.config import settings
from app.api.v1.admin_clients import router as admin_clients_router
from app.api.v1.admin_projects import router as admin_projects_router
from app.api.v1.admin_webhooks import router as admin_webhooks_router
from app.api.v1.admin_support import router as admin_support_router
from app.api.v1.admin_calls import router as admin_calls_router
from app.api.v1.public_pages import router as public_pages_router
from app.api.v1.chat import router as chat_router
from app.api.v1.dashboard_projects import router as dashboard_projects_router
from app.api.v1.dashboard_orders import router as dashboard_orders_router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.admin_checkout import router as admin_checkout_router
from app.api.v1.domain import router as domain_router
from app.api.v1.lead_forwarding import router as lead_forwarding_router
from app.api.v1.admin_forwarding import router as admin_forwarding_router
from app.api.v1.credentials import router as credentials_router
from app.api.v1.provision import router as provision_router
from app.api.v1.dashboard_support import router as dashboard_support_router
from app.api.v1.dashboard_onboarding import router as dashboard_onboarding_router
from app.api.v1.support import router as support_router
from app.api.v1.admin_support_tickets import router as admin_support_tickets_router
from app.api.v1.admin_login import router as admin_login_router
from app.api.v1.admin_calls import router as admin_calls_router
from app.services.email import send_welcome_email
from app.db.session import SessionLocal
from app.models.order import Order
from app.db.session import get_session
from app.middleware.auth import load_user_middleware, signer



app = FastAPI(title="WebWise Solutions")

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["now"] = datetime.utcnow  # keep this; remove the stray line

# Serve static assets (CSS/JS/images)
static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

stripe.api_key = settings.STRIPE_SECRET_KEY

# Allow fallback to legacy env var names if the new ones are not set
PRICE_MAP = {
    "starter": settings.STRIPE_PRICE_STARTER_BUILD or os.getenv("STRIPE_PRICE_ID_STARTER", ""),
    "growth": settings.STRIPE_PRICE_GROWTH_BUILD or os.getenv("STRIPE_PRICE_ID_GROWTH", ""),
    "scale": settings.STRIPE_PRICE_SCALE_BUILD or os.getenv("STRIPE_PRICE_ID_SCALE", ""),
}

# Load admin personal file upload router from the hyphenated filename
admin_file_upload_path = (
    Path(__file__).resolve().parent / "api" / "v1" / "admin_pers-file-upload.py"
)
_admin_upload_spec = importlib.util.spec_from_loader(
    "admin_pers_file_upload",
    SourceFileLoader("admin_pers_file_upload", str(admin_file_upload_path)),
)
if _admin_upload_spec and _admin_upload_spec.loader:
    _admin_upload_module = importlib.util.module_from_spec(_admin_upload_spec)
    _admin_upload_spec.loader.exec_module(_admin_upload_module)  # type: ignore
    admin_pers_file_upload_router = getattr(_admin_upload_module, "router", None)
else:
    admin_pers_file_upload_router = None

# Load file storage upload API (hyphenated filename)
file_storage_upload_path = (
    Path(__file__).resolve().parent / "api" / "v1" / "file-storage-upload.py"
)
_file_upload_spec = importlib.util.spec_from_loader(
    "file_storage_upload",
    SourceFileLoader("file_storage_upload", str(file_storage_upload_path)),
)
if _file_upload_spec and _file_upload_spec.loader:
    _file_upload_module = importlib.util.module_from_spec(_file_upload_spec)
    _file_upload_spec.loader.exec_module(_file_upload_module)  # type: ignore
    file_storage_upload_router = getattr(_file_upload_module, "router", None)
else:
    file_storage_upload_router = None


class CheckoutRequest(BaseModel):
    plan: str
    tos_checked: Optional[bool] = False


@app.get("/")
def home_page(request: Request):
    return templates.TemplateResponse("public/home.html", {"request": request})

@app.get("/dashboard")
async def dashboard_home(request: Request, db: AsyncSession = Depends(get_session)):
    latest_order = (
        await db.execute(select(Order).order_by(Order.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    user_email = None
    user = getattr(request.state, "user", None)

    # If logged in client has not completed onboarding, send them to the intake first.
    if user and getattr(user, "id", None):
        try:
            exists = await db.execute(
                text("SELECT 1 FROM client_onboarding WHERE client_id = :cid LIMIT 1"),
                {"cid": user.id},
            )
            has_onboarding = exists.scalar_one_or_none() is not None
            if not has_onboarding:
                return RedirectResponse(url="/dashboard/onboarding", status_code=303)
            res = await db.execute(
                text("SELECT email FROM users WHERE id = :uid LIMIT 1"),
                {"uid": user.id},
            )
            user_email = res.scalar_one_or_none()
        except Exception:
            user_email = None

    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {"request": request, "latest_order": latest_order, "user_email": user_email},
    )


async def _create_user_if_needed(email: str, name: str | None) -> tuple[bool, str | None]:
    """
    Upsert a minimal user record with a fresh temp password.
    Returns (True, temp_password) on success; (False, None) on failure.
    """
    temp_password = secrets.token_urlsafe(10)
    password_hash = hashlib.sha256(temp_password.encode()).hexdigest()

    try:
        async with SessionLocal() as db:
            await db.execute(
                text(
                    """
                    INSERT INTO users (email, hashed_password, role, created_at)
                    VALUES (:email, :password_hash, 'client', NOW())
                    ON CONFLICT (email) DO UPDATE SET
                        hashed_password = EXCLUDED.hashed_password
                    """
                ),
                {"email": email, "password_hash": password_hash},
            )
            await db.commit()

            # Check if user now exists
            res = await db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email},
            )
            user_id = res.scalar_one_or_none()
            if user_id:
                return True, temp_password
    except Exception as exc:  # noqa: BLE001
        # Log the root cause so self-heal can be debugged quickly
        print(f"Create user failed for {email}: {exc}")
        return False, None

    return False, None

async def _self_heal_user(email: str) -> bool:
    """
    Recreate a user from an existing paid order if the user row is missing.
    Generates a fresh temp password and re-sends the welcome email.
    """
    try:
        async with SessionLocal() as db:
            res = await db.execute(
                text(
                    """
                    SELECT plan
                    FROM orders
                    WHERE buyer_email = :email
                      AND welcome_sent = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"email": email},
            )
            order_row = res.mappings().first()
    except Exception as exc:  # noqa: BLE001
        print(f"Self-heal lookup failed for {email}: {exc}")
        return False

    if not order_row:
        return False

    created, temp_password = await _create_user_if_needed(email, email)
    if not created or not temp_password:
        print(f"Self-heal could not recreate user for {email}")
        return False

    try:
        dashboard_link = (settings.DOMAIN_URL or "").rstrip("/") + "/login"
        await send_welcome_email(
            customer_email=email,
            customer_name=email,
            plan_name=order_row.get("plan") or "Your plan",
            dashboard_link=dashboard_link,
            temp_password=temp_password,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Self-heal email send failed for {email}: {exc}")

    return True


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("public/login.html", {"request": request})

@app.post("/login")
async def login_post(
    email: str = Form(...),
    password: str = Form(...),
):
    # Validate against stored hashed_password
    try:
        async with SessionLocal() as db:
            res = await db.execute(
                text(
                    """
                    SELECT id, hashed_password
                    FROM users
                    WHERE email = :email
                    LIMIT 1
                    """
                ),
                {"email": email},
            )
            row = res.mappings().first()
    except Exception:
        row = None

    if not row:
        healed = await _self_heal_user(email)
        if healed:
            return RedirectResponse("/login?error=reset", status_code=303)
        return RedirectResponse("/login?error=invalid", status_code=303)

    incoming_hash = hashlib.sha256(password.encode()).hexdigest()
    if row["hashed_password"] != incoming_hash:
        healed = await _self_heal_user(email)
        if healed:
            return RedirectResponse("/login?error=reset", status_code=303)
        return RedirectResponse("/login?error=invalid", status_code=303)

    # Set signed session cookie and redirect to dashboard
    token = signer.sign(str(row["id"])).decode()
    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie(
        "session",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return resp

app.include_router(admin_clients_router, tags=["Admin Clients"])
app.include_router(admin_projects_router, tags=["Admin Projects"])
app.include_router(admin_webhooks_router, prefix="/admin/webhooks", tags=["Admin Webhooks"])
app.include_router(admin_support_router, prefix="/admin/support", tags=["Admin Support"])
app.include_router(admin_calls_router, prefix="/admin/calls", tags=["Admin Calls"])
app.include_router(public_pages_router, tags=["Public Pages"])
app.include_router(dashboard_projects_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(dashboard_orders_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat_router, prefix="/api")
app.include_router(quiz_router, prefix="/api", tags=["Quiz"])
app.include_router(admin_checkout_router, prefix="", tags=["Admin Checkout"])
app.include_router(domain_router, prefix="/api", tags=["Domain"])
app.include_router(lead_forwarding_router, prefix="/api", tags=["Lead Forwarding"])
app.include_router(credentials_router, prefix="/api", tags=["Credentials"])
app.include_router(support_router, prefix="/api", tags=["Support"])
app.include_router(dashboard_support_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(dashboard_onboarding_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(admin_support_tickets_router, tags=["Admin Support"])
app.include_router(admin_login_router, tags=["Admin"])
app.include_router(admin_calls_router, tags=["Admin Calls"])
app.include_router(admin_forwarding_router, tags=["Admin Forwarding"])
if admin_pers_file_upload_router:
    app.include_router(admin_pers_file_upload_router, tags=["Admin File Upload"])
if file_storage_upload_router:
    app.include_router(file_storage_upload_router, tags=["File Upload"])
app.include_router(provision_router)
app.middleware("http")(load_user_middleware)


@app.post("/api/login/resend")
async def resend_login(email: str = Form(...)):
    healed = await _self_heal_user(email)
    if healed:
        return {"detail": "A new temporary password has been emailed."}
    raise HTTPException(status_code=404, detail="No matching order found for this email.")


@app.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutRequest, request: Request):
    plan = payload.plan
    tos_checked = bool(payload.tos_checked)

    if not tos_checked:
        raise HTTPException(status_code=400, detail="Terms of Service must be accepted.")

    price_id = PRICE_MAP.get(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan selected.")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    domain = settings.DOMAIN_URL or str(request.base_url).rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{domain}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain}/pricing",
            metadata={
                "plan": plan,
                "tos_checked": str(tos_checked).lower(),
                "source": "web_checkout",
            },
            payment_intent_data={
                "metadata": {
                    "plan": plan,
                    "tos_checked": str(tos_checked).lower(),
                    "source": "web_checkout",
                }
            },
        )
        return {"id": session.id}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Unable to create checkout session.") from exc


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks; send welcome email on completed checkout."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured.")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid webhook signature.") from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = (session.get("customer_details") or {}).get("email") or session.get("customer_email")
        customer_name = (session.get("customer_details") or {}).get("name")
        plan = (session.get("metadata") or {}).get("plan")
        dashboard_link = f"{(settings.DOMAIN_URL or str(request.base_url).rstrip('/'))}/login"
        session_id = session.get("id")
        payment_intent_id = session.get("payment_intent")

        # Idempotency: skip if we've already processed this session_id
        if session_id:
            try:
                async with SessionLocal() as db:
                    res = await db.execute(
                        text("SELECT id FROM orders WHERE stripe_session_id = :sid LIMIT 1"),
                        {"sid": session_id},
                    )
                    if res.scalar_one_or_none():
                        return {"received": True}
            except Exception:
                pass

        # Fetch line item to capture price/product for the order record
        price_id = None
        product_id = None
        try:
            items = stripe.checkout.Session.list_line_items(session["id"], limit=1)
            if items.data:
                price_id = items.data[0].price.id if items.data[0].price else None
                product_id = items.data[0].price.product if items.data[0].price else None
        except Exception:
            price_id = None
            product_id = None

        # Store order record
        try:
            async with SessionLocal() as db:
                order = Order(
                    plan=plan or "unknown",
                    stripe_price_id=price_id or "",
                    stripe_product_id=product_id or "",
                    stripe_session_id=session_id or "",
                    stripe_payment_intent_id=payment_intent_id or "",
                    buyer_email=email or "",
                    status="onboarding",
                )
                db.add(order)
                await db.commit()
        except Exception:
            pass  # do not block webhook

        # Create/update user and send welcome email (guarded by welcome_sent)
        if email:
            temp_password = None
            try:
                _, temp_password = await _create_user_if_needed(email, customer_name)
            except Exception as exc:
                print(f"Error creating/updating user for {email}: {exc}")
                temp_password = None

            # Fallback: if we still don't have a temp password, generate one and update the user record.
            if not temp_password:
                try:
                    temp_password = secrets.token_urlsafe(10)
                    password_hash = hashlib.sha256(temp_password.encode()).hexdigest()
                    async with SessionLocal() as db:
                        await db.execute(
                            text(
                                """
                                UPDATE users
                                SET hashed_password = :password_hash
                                WHERE email = :email
                                """
                            ),
                            {"password_hash": password_hash, "email": email},
                        )
                        await db.commit()
                    print(f"Fallback temp password generated for {email}")
                except Exception as exc:
                    print(f"Error setting fallback temp password for {email}: {exc}")
                    temp_password = None

            can_send = True
            try:
                async with SessionLocal() as db:
                    res = await db.execute(
                        text(
                            """
                            UPDATE orders
                            SET welcome_sent = TRUE, updated_at = NOW()
                            WHERE stripe_session_id = :sid
                              AND (welcome_sent IS NULL OR welcome_sent = FALSE)
                            RETURNING id
                            """
                        ),
                        {"sid": session_id},
                    )
                    row = res.scalar_one_or_none()
                    await db.commit()
                    if row is None:
                        can_send = False
            except Exception:
                can_send = True  # fail open to avoid missing email

            if can_send:
                try:
                    await send_welcome_email(
                        customer_email=email,
                        customer_name=customer_name,
                        plan_name=plan or "Your plan",
                        dashboard_link=dashboard_link,
                        temp_password=temp_password,
                    )
                except Exception:
                    # Do not fail webhook delivery because of email issues
                    pass

    return {"received": True}