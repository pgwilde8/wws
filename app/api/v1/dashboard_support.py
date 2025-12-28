from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/support")
async def support_page(request: Request):
    return templates.TemplateResponse(
        "dashboard/support.html",
        {
            "request": request,
            "client": None,  # prevent template error
        },
    )


@router.get("/support/new")
async def support_page_alias(request: Request):
    # Reuse the same support hub (form is on the page)
    return templates.TemplateResponse(
        "dashboard/support.html",
        {
            "request": request,
            "client": None,
        },
    )