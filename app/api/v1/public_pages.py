# app/api/v1/public_pages.py
from datetime import datetime
from types import SimpleNamespace
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.services.email import (
    send_call_booking_confirmation,
    send_call_booking_email,
)


router = APIRouter(tags=["Public Pages"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["now"] = datetime.utcnow

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("public/home.html", {"request": request})
# ...rest unchanged ...

@router.get("/faq")
async def faq(request: Request):
    return templates.TemplateResponse("public/faq.html", {"request": request})

@router.get("/contact")
async def contact(request: Request):
    return templates.TemplateResponse("public/contact.html", {"request": request})

@router.get("/services")
async def services(request: Request):
    return templates.TemplateResponse("public/services.html", {"request": request})

@router.get("/testimonials")
async def testimonials(request: Request):
    return templates.TemplateResponse("public/testimonials.html", {"request": request})

@router.get("/tos")
async def tos(request: Request):
    return templates.TemplateResponse("public/tos.html", {"request": request})

@router.get("/privacy_policy")
async def privacy_policy(request: Request):
    return templates.TemplateResponse("public/privacy_policy.html", {"request": request})

@router.get("/how-it-works")
async def how_it_works(request: Request):
    return templates.TemplateResponse("public/how-it-works.html", {"request": request})

@router.get("/the-shift")
async def the_shift(request: Request):
    return templates.TemplateResponse("public/the-shift.html", {"request": request})

def _stripe_context():
    return {
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "stripe_price_starter": settings.STRIPE_PRICE_STARTER_BUILD,
        "stripe_price_growth": settings.STRIPE_PRICE_GROWTH_BUILD,
        "stripe_price_scale": settings.STRIPE_PRICE_SCALE_BUILD,
    }


@router.get("/choose-your-build")
async def choose_your_build(request: Request):
    ctx = {"request": request}
    ctx.update(_stripe_context())
    return templates.TemplateResponse("public/choose-your-build.html", ctx)

@router.get("/book-call")
async def book_call(request: Request):
    return templates.TemplateResponse("public/book-call.html", {"request": request})

@router.post("/book-call/submit")
async def book_call_submit(request: Request):
    form = await request.form()
    cb = SimpleNamespace(
        name=form.get("name"),
        email=form.get("email"),
        phone=form.get("phone"),
        preferred_date=form.get("preferred_date"),
        preferred_time=form.get("preferred_time"),
        timezone=form.get("timezone") or "EST",
        message=form.get("message") or "",
        created_at=datetime.utcnow(),
    )

    try:
        await send_call_booking_confirmation(cb)  # to the submitter (BCC devs if configured)
        await send_call_booking_email(cb)         # to internal team
    except Exception as e:
        print(f"Call booking email error: {e}")

    ctx = {
        "request": request,
        "success": True,
        "message": "Thanks! We got your request and will confirm your call shortly.",
    }
    ctx.update({k: v for k, v in form.items()})
    return templates.TemplateResponse("public/book-call.html", ctx)

@router.get("/automate-or-die")
async def automate_or_die(request: Request):
    return templates.TemplateResponse("public/automate-or-die.html", {"request": request})    

@router.get("/start-build-process")
async def star_build_process(request: Request):
    return templates.TemplateResponse("public/start-build-process.html", {"request": request})

@router.get("/start-your-project")
async def start_your_project(request: Request):
    return templates.TemplateResponse("public/start-your-project.html", {"request": request})    
    
@router.get("/pricing")
async def pricing(request: Request):
    ctx = {"request": request}
    ctx.update(_stripe_context())
    return templates.TemplateResponse("public/pricing.html", ctx)


@router.get("/success")
async def checkout_success(request: Request):
    return templates.TemplateResponse("public/success.html", {"request": request})

@router.get("/portfolio")
async def portfolio(request: Request):
    return templates.TemplateResponse("public/portfolio.html", {"request": request})  

@router.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("public/about.html", {"request": request})

@router.get("/client-quiz")
async def client_quiz(request: Request):
    return templates.TemplateResponse("public/client-quiz.html", {"request": request})

@router.get("/client-results")
async def client_results(request: Request):
    return templates.TemplateResponse("public/client-results.html", {"request": request})    

@router.get("/meet-the-team")
async def meet_the_team(request: Request):
    return templates.TemplateResponse("public/meet-the-team.html", {"request": request}) 

@router.get("/quiz-results")
async def quiz_results(request: Request, package: str | None = None):
    return templates.TemplateResponse(
        "public/quiz-results.html",
        {"request": request, "package": package or "growth"},
    )

@router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("public/login.html", {"request": request})     






   




      

          