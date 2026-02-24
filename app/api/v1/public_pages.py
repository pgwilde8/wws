# app/api/v1/public_pages.py
from datetime import datetime
from types import SimpleNamespace
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from app.core.config import settings
from app.db.session import get_session
from app.models.testimonial import Testimonial
from app.services.email import (
    send_call_booking_confirmation,
    send_call_booking_email,
)


router = APIRouter(tags=["Public Pages"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["now"] = datetime.utcnow

BLOG_POSTS = [
    {
        "slug": "automate-lead-generation",
        "title": "Automated Lead Generation Systems That Work 24/7",
        "excerpt": "How to build inbound engines that capture and qualify leads on autopilot.",
        "category": "Automation",
        "template": "automate_lead_generation.html",
        "published_at": datetime(2025, 12, 1),
    },
    {
        "slug": "automated-booking-system-for-business",
        "title": "Automated Booking Systems for Business",
        "excerpt": "Reduce no-shows and manual scheduling with smart booking flows.",
        "category": "Operations",
        "template": "automated_booking_system_for_business.html",
        "published_at": datetime(2025, 11, 20),
    },
    {
        "slug": "automated-business-systems",
        "title": "Automated Business Systems",
        "excerpt": "Design the backbone that keeps sales, service, and fulfillment synchronized.",
        "category": "Systems",
        "template": "automated_business_systems.html",
        "published_at": datetime(2025, 11, 5),
    },
    {
        "slug": "custom-business-automation",
        "title": "Custom Business Automation",
        "excerpt": "Tailored workflows that match your real-world operations, not templates.",
        "category": "Automation",
        "template": "custom_business_automation.html",
        "published_at": datetime(2025, 10, 18),
    },
    {
        "slug": "website-automation-services",
        "title": "Website Automation Services",
        "excerpt": "Turn your site into a self-service, conversion-focused engine.",
        "category": "Web",
        "template": "website_automation_services.html",
        "published_at": datetime(2025, 10, 2),
    },
]

@router.get("/")
async def home(request: Request, db: AsyncSession = Depends(get_session)):
    # Fetch 3 approved testimonials for homepage
    testimonials_query = (
        select(Testimonial)
        .where(Testimonial.is_approved.is_(True))
        .order_by(Testimonial.created_at.desc())
        .limit(6)
    )
    testimonials_result = await db.execute(testimonials_query)
    testimonials = testimonials_result.scalars().all()
    
    return templates.TemplateResponse(
        "public/home.html",
        {"request": request, "testimonials": testimonials}
    )
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
async def testimonials(request: Request, db: AsyncSession = Depends(get_session)):
    # Fetch approved testimonials
    query = select(Testimonial).where(
        Testimonial.is_approved == True
    ).order_by(Testimonial.created_at.desc())
    result = await db.execute(query)
    testimonials_list = result.scalars().all()
    
    return templates.TemplateResponse(
        "public/testimonials.html",
        {"request": request, "testimonials": testimonials_list}
    )

@router.get("/testimonials/submit")
async def testimonial_submit_page(request: Request):
    return templates.TemplateResponse(
        "public/testimonial_submit.html",
        {"request": request}
    )

@router.post("/testimonials/submit")
async def testimonial_submit(
    request: Request,
    db: AsyncSession = Depends(get_session),
    client_name: str = Form(...),
    testimonial_text: str = Form(...),
    email: str = Form(None),
    client_location: str = Form(None),
    website_url: str = Form(None),
    event_type: str = Form(None),
    rating: str = Form(None),

):
    try:
        # Convert rating to int if provided
        rating_int = int(rating) if rating and rating.isdigit() else None
        
        # Create testimonial (defaults to not approved, needs admin approval)
        testimonial = Testimonial(
            client_name=client_name,
            testimonial_text=testimonial_text,
            client_location=client_location,
            website_url=website_url,
            event_type=event_type,
            rating=rating_int,
            is_approved=False,  # Requires admin approval
        )
        
        db.add(testimonial)
        await db.commit()
        await db.refresh(testimonial)
        
        return templates.TemplateResponse(
            "public/testimonial_submit.html",
            {
                "request": request,
                "success": True,
                "message": "Thank you for your testimonial! We'll review it and publish it on our website soon.",
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "public/testimonial_submit.html",
            {
                "request": request,
                "error": True,
                "message": f"Sorry, there was an error submitting your testimonial. Please try again. Error: {str(e)}",
            }
        )

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
async def choose_your_build(request: Request, db: AsyncSession = Depends(get_session)):
    # Fetch approved testimonials for carousel
    testimonials_query = (
        select(Testimonial)
        .where(Testimonial.is_approved.is_(True))
        .order_by(Testimonial.created_at.desc())
    )
    testimonials_result = await db.execute(testimonials_query)
    testimonials = testimonials_result.scalars().all()
    
    # Convert to dict for JSON serialization
    testimonials_data = [
        {
            "client_name": t.client_name,
            "client_location": t.client_location,
            "event_type": t.event_type,
            "testimonial_text": t.testimonial_text,
            "rating": t.rating or 5,
            "website_url": t.website_url,
        }
        for t in testimonials
    ]
    
    ctx = {"request": request, "testimonials": testimonials_data}
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
async def pricing(request: Request, db: AsyncSession = Depends(get_session)):
    # Fetch approved testimonials for carousel
    testimonials_query = (
        select(Testimonial)
        .where(Testimonial.is_approved.is_(True))
        .order_by(Testimonial.created_at.desc())
    )
    testimonials_result = await db.execute(testimonials_query)
    testimonials = testimonials_result.scalars().all()
    
    # Convert to dict for JSON serialization
    testimonials_data = [
        {
            "client_name": t.client_name,
            "client_location": t.client_location,
            "event_type": t.event_type,
            "testimonial_text": t.testimonial_text,
            "rating": t.rating or 5,
            "website_url": t.website_url,
        }
        for t in testimonials
    ]
    
    ctx = {"request": request, "testimonials": testimonials_data}
    ctx.update(_stripe_context())
    return templates.TemplateResponse("public/pricing.html", ctx)


@router.get("/success")
async def checkout_success(request: Request):
    return templates.TemplateResponse("public/success.html", {"request": request})

@router.get("/portfolio")
async def portfolio(request: Request):
    return templates.TemplateResponse("public/portfolio.html", {"request": request})  

@router.get("/blog")
async def blog_index(request: Request):
    return templates.TemplateResponse("blog/our_blog.html", {"request": request, "blog_posts": BLOG_POSTS})

@router.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("public/about.html", {"request": request})

@router.get("/blog/{slug}")
async def blog_detail(slug: str, request: Request):
    # Map slug to template file
    post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    template_name = post.get("template")
    template_path = Path("app/templates/blog") / template_name
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse(
        f"blog/{template_name}",
        {
            "request": request,
            "post": post,
        },
    )

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






   




      

          