from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app.api.v1 import dashboard_projects
from app.api.v1.public_pages import router as public_pages_router


from app.api.v1 import (
    projects_router,
    admin_webhooks,
    admin_clients,
    testimonials_router,
    admin_calls,
    admin_projects,
    admin_projects_detail,
    admin_support,
    admin_webhook_detail,
    dashboard_projects,
)

app = FastAPI(title="WWS API")

# Template engine
templates = Jinja2Templates(directory="app/templates")

# Admin section wiring
app.include_router(admin_webhooks.router, prefix="/admin/webhooks", tags=["Admin Webhooks"])
app.include_router(admin_clients.router, prefix="/admin/clients", tags=["Admin Clients"])
app.include_router(admin_projects.router, prefix="/admin/projects", tags=["Admin Projects"])
app.include_router(admin_projects_detail.router, prefix="/admin/projects", tags=["Admin Project Detail"])
app.include_router(admin_calls.router, prefix="/admin/calls", tags=["Admin Calls"])
app.include_router(admin_support.router, prefix="/admin/support", tags=["Admin Support"])
app.include_router(admin_webhook_detail.router, prefix="/admin/webhooks", tags=["Webhook Detail"])
app.include_router(dashboard_projects.router, prefix="/dashboard", tags=["Client Projects"])
# Dashboard wiring
app.include_router(dashboard_projects.router, prefix="/dashboard/projects", tags=["Dashboard Projects"])
app.include_router(dashboard_projects.router, prefix="/dashboard", tags=["Dashboard Root"])
app.include_router(testimonials_router.router, prefix="/admin/testimonials", tags=["Admin Testimonials"])
app.include_router(dashboard_projects.router, prefix="/dashboard/projects", tags=["Dashboard Projects"])
#Public
app.include_router(public_pages_router)