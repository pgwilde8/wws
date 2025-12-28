# WWS FastAPI Project
wws: 134.199.242.254:8888
port: 8888

Here’s a polished **README.md** tailored for your fresh rebuild (no trading, no Facebook, clear admin + client dashboard focus, FastAPI + Uvicorn + Nginx + Postgres):

```markdown
# WebWise Solutions — Business System Builder

A full-stack automated business system built with **FastAPI**, **Jinja**, **Tailwind (mobile-first UI)**, **PostgreSQL**, **Uvicorn**, and **Nginx**.

This project is a clean rewrite designed to be:
- **Maintainable**
- **Mobile-friendly**
- **Secure**
- **Scalable**
- **Free of legacy features that are no longer needed**

---

## Overview

WebWise Solutions provides an authenticated platform where:

### **Clients can**
- Onboard a **Stripe Connect** account
- Submit a **domain name** for DNS setup
- Input API credentials (**OpenAI**, **Twilio**)
- View project build progress
- Schedule setup calls

### **Admins can**
- Manage clients and projects behind secure authentication
- Review relevant **Stripe webhook events**
- View and mask API credentials for deployment
- Update project status across multiple admin pages
- Access structured onboarding state for support and DNS setup
- Prepare deployment environments by exporting credentials into `.env`

---

## Tech Stack

| Component | Technology |
|---|---|
| API Backend | FastAPI |
| ASGI Server | Uvicorn |
| Database | PostgreSQL + SQLAlchemy |
| Templating | Jinja2 |
| Styling | TailwindCSS (mobile-first UI) |
| Reverse Proxy | Nginx |
| Deployment | systemd + Gunicorn optional |

---

## Project Structure

```

myproject/
├── app/
│   ├── main.py                # FastAPI app entrypoint
│   ├── core/                  # config, auth, logging
│   ├── db/                    # database sessions & base models
│   ├── models/                # SQLAlchemy models (User, Client, Project, Credentials)
│   ├── schemas/               # Pydantic schemas for API responses & inputs
│   ├── crud/                  # database interaction logic
│   ├── api/v1/                # API routers (users, clients, projects, webhook logs, connect status)
│   ├── services/              # email, payment, deployment helpers
│   ├── templates/             # Jinja pages (dashboard + admin)
│   ├── static/                # css, js, media
│   └── middleware/            # JWT middleware
├── alembic/                   # database migrations
├── tests/                     # endpoint & polling validation (future stage)
├── scripts/                   # seed data, admin creation
├── nginx/
│   └── wws.conf               # nginx configuration
├── systemd/
│   └── wws.service            # service management
├── .env                       # deployment credentials (admin-managed)
└── requirements.txt

````

---

## Core Features

- **JWT authentication** for both admin and client dashboards
- **Stripe Connect onboarding** with async state handling
- **Webhook event logging and normalization**
- **Masked credential storage** for secure deployment use
- **Domain submission & DNS onboarding state**
- **Project status and progress tracking**
- **Mobile-ready UI using TailwindCSS**
- **Admin multi-page navigation for complex client and project data**

---

## Setup (Local Development)

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
````

3. Start the ASGI server:

   ```bash
   uvicorn app.main:app --reload
   ```
4. Ensure PostgreSQL is running and `.env` is configured
5. Nginx and systemd configs are provided for production deployment

---

## Deployment Notes

* API keys are **never stored in code**, only in DB and exported into `.env` by admin
* Clients own and control their external accounts (Stripe, Cloudflare, Twilio, OpenAI)
* Admins prepare deployment environments using masked keys securely
* System is intended to run behind **Nginx reverse proxy with auth enforced**

---

## Roadmap

* Improve admin UI into clear multi-page dashboards
* Add webhook event filtering for relevant Stripe events only
* Fix plan tier sync between DB → client dashboard
* Add Connect status polling and auto-update checklist
* Prepare automated `.env` deployment exports for clients and admins
* Add dashboard async verification state for Stripe Connect delays

---

## License

Private internal project — All rights reserved.

---

## Author

**Paul G Wilde**
Self-taught FastAPI web developer building automated business systems at scale.

```

---

If you want, I can also generate:
- A **shorter minimal version**
- A **feature-heavy version**
- Or a **public vs internal contributor version**

But this one is a strong starting point for your new build. Let me know if you want me to save it into the actual path too.
```
