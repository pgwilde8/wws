wws: 134.199.242.254:8888
tree /srv/projects/wws/app/models
/srv/projects/wws/app/models

1: su - webadmin

2: cd /srv/projects/wws
source venv/bin/activate

master-famous-liked-joyful

uvicorn app.main:app --reload --host 0.0.0.0 --port 8888
uvicorn app.main:app --reload --host 0.0.0.0 --port 8888 --log-level debug

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db

SELECT id, email, hashed_password FROM users WHERE email='678@webwisesolutions.dev';
\d orders
\d users
fg %2

/admin/login
Email: admin@webwisesolutions.dev
Password: YourStrongPwd

1997: prod_TdQijJms4jaRRc, price_1Sg9rHRzRv6CTjxR69nkwXrx
3997: prod_TdQkXuk1BBULCb, price_1Sg9t0RzRv6CTjxRDJZdEq5y
5997: prod_TdQm4ocyVXU2A5, price_1Sg9uTRzRv6CTjxR0It8rVkC

starter: prod_TdQijJms4jaRRc, price_1Sg9rHRzRv6CTjxR69nkwXrx
build; prod_TdQkXuk1BBULCb, price_1Sg9t0RzRv6CTjxRDJZdEq5y
scale' prod_TdQm4ocyVXU2A5, price_1Sg9uTRzRv6CTjxR0It8rVkC



=======================================================================
Add lead capture endpoint and ticket creation only if you plan to use them.
Add a route to render the chat widget/template if the UI expects on




app/templates/
├── home.html                   ← public marketing home
├── contact.html
├── faq.html
├── login.html
├── services.html
├── testimonials.html
├── testimonials/ (optional future folder if you expand)
│
├── layout/
│   └── base.html               ← global layout shell
│
├── admin/                      ← internal staff UI
│   ├── clients.html            ← admin client cards listing
│   ├── client_detail.html      ← admin client detail view
│   ├── projects.html           ← admin projects listing
│   ├── project_detail.html     ← admin project detail view
│   ├── calls.html              ← admin calls listing
│   ├── call_detail.html        ← admin call detail view
│   ├── support_inbox.html      ← admin support ticket listing
│   ├── support_detail.html     ← single support ticket view
│   ├── support_thread.html     ← thread view (if used)
│   ├── webhooks.html           ← webhook listing
│   ├── webhook_detail.html     ← single webhook event view
│   └── webhook_events.html     ← optional (if splitting events)
│
└── dashboard/                  ← client UI after login
    ├── dashboard.html          ← client main dashboard  ✔ keep name
    ├── credentials.html        ← client API keys form
    ├── domain.html             ← domain submit UI
    ├── project_overview.html   ← client purchased project overview
    ├── support.html            ← client support inbox (tickets)
    └── orders.html             ← optional future (client purchases)

    app/api/v1/
├── public_pages.py          → serves public templates
├── dashboard_projects.py    → serves client dashboard pages
├── dashboard_orders.py      → serves orders.html
├── admin_clients.py         → serves clients + client cards
├── admin_projects.py        → serves admin project listings
├── admin_webhooks.py        → serves admin webhook UI
└── admin_support.py         → serves support inbox/thread UI

/srv/projects/wws/app/api/v1
├── admin_calls.py
├── admin_calls_detail.py
├── admin_clients.py
├── admin_projects.py
├── admin_projects_detail.py
├── admin_support.py
├── admin_webhook_detail.py
├── admin_webhook_events.py
├── admin_webhooks.py
├── clients_router.py
├── dashboard_orders.py
├── dashboard_projects.py
├── projects_router.py
├── public_pages.py
├── testimonials_router.py
└── webhooks.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL=postgresql://webadmin:Securepass9@localhost:5432/wwsdev_db

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session




app.include_router(public_pages_router)

twillio: Account SID, Auth Token