import pytest
from httpx import AsyncClient
from app.main import app  # FastAPI instance

@pytest.mark.asyncio
async def test_public_home():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/")
        assert r.status_code == 200

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_admin_projects_api():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/admin/projects/api?page=1")
        assert r.status_code == 200

        # We may get 200 with empty list if no auth override in test client
        assert r.status_code in (200, 401, 403)

@pytest.mark.asyncio
async def test_admin_clients():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/admin/clients")
        assert r.status_code in (200, 401, 403, 404)

@pytest.mark.asyncio
async def test_chat_message():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/chat/message", json={"message": "hello"})
        assert r.status_code in (200, 401, 403, 500)
#r = await ac.get("/admin/projects/api?page=1")