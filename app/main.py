from datetime import datetime
import secrets
import hashlib
from pathlib import Path
import importlib.util
from importlib.machinery import SourceFileLoader
from typing import Optional
import os
import stripe
import logging
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import RedirectResponse      # add this import
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.testimonial import Testimonial
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
from app.api.v1.dashboard_password import router as dashboard_password_router
from app.api.v1.support import router as support_router
from app.api.v1.admin_support_tickets import router as admin_support_tickets_router
from app.api.v1.admin_login import router as admin_login_router
from app.api.v1.admin_calls import router as admin_calls_router
from app.api.v1.testimonials_router import router as testimonials_router
from app.api.v1.admin_marketer import router as admin_marketer_router
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

logger = logging.getLogger(__name__)

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



class CheckoutRequest(BaseModel):
    plan: str
    tos_checked: Optional[bool] = False


def _get_checkout_domain(request: Request) -> str:
    if settings.DOMAIN_URL:
        return settings.DOMAIN_URL.rstrip("/")
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    proto = forwarded_proto or request.url.scheme
    host = forwarded_host or request.headers.get("host") or request.url.netloc
    if proto == "http" and host and "localhost" not in host and "127.0.0.1" not in host:
        proto = "https"
    return f"{proto}://{host}".rstrip("/")


@app.get("/")
async def home_page(request: Request, db: AsyncSession = Depends(get_session)):
    # Fetch approved testimonials for the homepage hero/footer section
    testimonials_query = (
        select(Testimonial)
        .where(Testimonial.is_approved.is_(True))
        .order_by(Testimonial.created_at.desc())
        .limit(6)
    )
    testimonials_result = await db.execute(testimonials_query)
    testimonials = testimonials_result.scalars().all()

    return templates.TemplateResponse(
        "public/home.html", {"request": request, "testimonials": testimonials}
    )

@app.get("/dashboard")
async def dashboard_home(request: Request, db: AsyncSession = Depends(get_session)):
    # Latest order (optional)
    latest_order = (
        await db.execute(select(Order).order_by(Order.created_at.desc()).limit(1))
    ).scalar_one_or_none()

    user = getattr(request.state, "user", None)
    
    # Check if user is authenticated and has completed onboarding
    if user and getattr(user, "id", None):
        # Require onboarding before showing dashboard - redirect to welcome page first
        try:
            exists = await db.execute(
                text("SELECT 1 FROM client_onboarding WHERE client_id = :cid LIMIT 1"),
                {"cid": user.id},
            )
            has_onboarding = exists.scalar_one_or_none() is not None
            if not has_onboarding:
                return RedirectResponse(url="/dashboard/welcome-instructions", status_code=303)
        except Exception:
            # If there's any error checking, redirect to welcome page to be safe
            return RedirectResponse(url="/dashboard/welcome-instructions", status_code=303)
    
    user_email = None
    onboarding_row = None
    client_status = None

    if user and getattr(user, "id", None):
        try:

            # Basic user email
            res = await db.execute(
                text("SELECT email FROM users WHERE id = :uid LIMIT 1"),
                {"uid": user.id},
            )
            user_email = res.scalar_one_or_none()

            # Onboarding summary
            res = await db.execute(
                text(
                    """
                    SELECT business_name, domain_name, lead_forward_email,
                           industry, created_at
                    FROM client_onboarding
                    WHERE client_id = :cid
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"cid": user.id},
            )
            onboarding_row = res.mappings().first()

            # Provisioning/status summary
            res = await db.execute(
                text(
                    """
                    SELECT assistant_status, assistant_status_detail, openai_assistant_id,
                           twilio_status, twilio_status_detail, twilio_voice_agent_sid
                    FROM clients
                    WHERE id = :cid
                    LIMIT 1
                    """
                ),
                {"cid": user.id},
            )
            client_status = res.mappings().first()
        except Exception:
            user_email = None
            onboarding_row = None
            client_status = None

    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "latest_order": latest_order,
            "user_email": user_email,
            "onboarding": onboarding_row,
            "client_status": client_status,
        },
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

@app.get("/dashboard/login")
async def dashboard_login(request: Request):
    """Client dashboard login page."""
    return templates.TemplateResponse("dashboard/client-login.html", {"request": request})

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
        # Password is incorrect - don't reset it, just return invalid
        return RedirectResponse("/login?error=invalid", status_code=303)

    # Set signed session cookie and redirect to welcome-instructions for new users
    token = signer.sign(str(row["id"])).decode()
    
    # Check if user has completed onboarding
    try:
        async with SessionLocal() as db:
            exists = await db.execute(
                text("SELECT 1 FROM client_onboarding WHERE client_id = :cid LIMIT 1"),
                {"cid": row["id"]},
            )
            has_onboarding = exists.scalar_one_or_none() is not None
            redirect_url = "/dashboard" if has_onboarding else "/dashboard/welcome-instructions"
    except Exception:
        # On error, default to welcome-instructions to be safe
        redirect_url = "/dashboard/welcome-instructions"
    
    resp = RedirectResponse(redirect_url, status_code=303)
    resp.set_cookie(
        "session",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return resp

@app.get("/logout")
async def logout():
    """Clear session cookie and redirect to login."""
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session", httponly=True, secure=True, samesite="lax")
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
app.include_router(dashboard_password_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(admin_support_tickets_router, tags=["Admin Support"])
app.include_router(admin_login_router, tags=["Admin"])
app.include_router(admin_calls_router, tags=["Admin Calls"])
app.include_router(admin_forwarding_router, tags=["Admin Forwarding"])
app.include_router(testimonials_router, prefix="/admin/testimonials", tags=["Admin Testimonials"])
app.include_router(admin_marketer_router, tags=["Admin Marketer"])
if admin_pers_file_upload_router:
    app.include_router(admin_pers_file_upload_router, tags=["Admin Personal"])
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

    domain = _get_checkout_domain(request)
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{domain}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain}/pricing",
            metadata={
                "project": "webwisesolutions",
                "app_name": "WebWise Solutions",
                "plan": plan,
                "tos_checked": str(tos_checked).lower(),
                "source": "web_checkout",
            },
            payment_intent_data={
                "metadata": {
                    "project": "webwisesolutions",
                    "app_name": "WebWise Solutions",
                    "plan": plan,
                    "tos_checked": str(tos_checked).lower(),
                    "source": "web_checkout",
                }
            },
        )
        return {"id": session.id}
    except stripe.error.StripeError as exc:
        logger.exception("Stripe checkout session creation failed", extra={"plan": plan})
        detail = "Unable to create checkout session."
        error_code = getattr(exc, "code", None)
        error_type = exc.__class__.__name__
        if settings.DEBUG:
            message = exc.user_message or str(exc)
            code_suffix = f" ({error_type}/{error_code})" if error_code else f" ({error_type})"
            detail = f"Stripe error{code_suffix}: {message}"
        elif error_code:
            detail = f"Stripe error ({error_code})."
        raise HTTPException(status_code=500, detail=detail) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Checkout session creation failed", extra={"plan": plan})
        detail = "Unable to create checkout session."
        if settings.DEBUG:
            detail = f"Server error: {str(exc)}"
        raise HTTPException(status_code=500, detail=detail) from exc


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
        metadata = session.get("metadata") or {}
        plan = metadata.get("plan")
        project = metadata.get("project")
        app_name = metadata.get("app_name")
        if project and project != "webwisesolutions":
            print("Stripe webhook ignored: foreign_project")
            return {"received": True, "ignored": True}
        if app_name and app_name != "WebWise Solutions":
            print("Stripe webhook ignored: foreign_app")
            return {"received": True, "ignored": True}
        if plan in {"free", "pro"}:
            print("Stripe webhook ignored: clickmeter_plan")
            return {"received": True, "ignored": True}
        email = (session.get("customer_details") or {}).get("email") or session.get("customer_email")
        customer_name = (session.get("customer_details") or {}).get("name")
        plan = metadata.get("plan")
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