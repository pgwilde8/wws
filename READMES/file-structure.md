# File Structure for /srv/projects/wws

This document describes the recommended file and folder structure for the `wws` project. Adjust as needed for your specific application requirements.

## Root Directory

- `main.py`                # Main FastAPI app entry point
- `requirements.txt`       # Python dependencies
- `README.md`              # Project documentation
- `.env.example`           # Example environment variables
- `alembic.ini`            # Alembic config (if using migrations)

## Application Code

- `app/`                   # Main application package
    - `__init__.py`
    - `main.py`            # FastAPI app instance
    - `api/`               # API route modules
    - `models/`            # SQLAlchemy models
    - `schemas/`           # Pydantic schemas
    - `db/`                # Database session, base, and utils
    - `services/`          # Business logic/services
    - `core/`              # Core utilities (config, security, etc.)
    - `templates/`         # Jinja2 templates (if using server-side rendering)
    - `static/`            # Static files (CSS, JS, images)

## Database & Migrations

- `alembic/`               # Alembic migration scripts
    - `versions/`          # Migration files

## Tests

- `tests/`                 # Unit and integration tests

## Infrastructure & Deployment

- `infra/`                 # Infrastructure as code, deployment scripts
- `scripts/`               # Utility scripts (DB seed, admin creation, etc.)

## Example Tree

```
wws/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── db/
│   ├── services/
│   ├── core/
│   ├── templates/
│   └── static/
├── alembic/
│   └── versions/
├── infra/
├── scripts/
├── tests/
├── main.py
├── requirements.txt
├── README.md
├── .env.example
└── alembic.ini
```

> **Tip:** Copy `.env.example` to `.env` and fill in your secrets for local development.
