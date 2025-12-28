"""AI Chat routes using OpenAI Assistants API + DB history + Support Tickets."""
import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from app.db.session import get_session

router = APIRouter(prefix="/chat", tags=["Chat"])
templates = Jinja2Templates(directory="app/templates")

load_dotenv()

openai_client = None
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID", "")


def get_openai_client():
    """Lazy-load OpenAI client + assistant id from ENV."""
    global openai_client
    if openai_client is None:
        try:
            from openai import OpenAI  # type: ignore
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("Missing OpenAI API key in environment.")
            openai_client = OpenAI(
                api_key=api_key,
                default_headers={"OpenAI-Beta": "assistants=v2"},
            )
        except ImportError:
            raise HTTPException(status_code=500, detail="OpenAI library not installed.")
    return openai_client


def get_or_create_assistant(client):
    """Reuse existing assistant or create one with legacy instructions."""
    global ASSISTANT_ID
    if ASSISTANT_ID:
        return ASSISTANT_ID

    instructions = """
You are the AI assistant for WebWise Solutions, a done-for-you automation company that builds fully automated, AI-powered businesses from scratch. Be conversational and helpful. Guide visitors on packages (Starter $1,997; Growth $3,997; Scale $5,997), process (choose package -> onboarding -> setup -> build -> launch -> support), tech stack (FastAPI, Stripe, OpenAI, CRM, automations), and always offer to book a call if serious. If unsure which package, suggest the quick quiz at /client-quiz. Use relative paths (like /client-quiz, /pricing, /book-call). Avoid hard-selling; focus on clarity and value.

QUIZ ANSWERS:
- When asked about the quiz, always give a short, confident link in markdown: "👉 [Take quick quiz](/client-quiz)"
- Never say you can’t show the quiz; just give the link above.
"""
    try:
        assistant = client.beta.assistants.create(
            name="WebWise Solutions Assistant",
            instructions=instructions,
            model="gpt-4o-mini",
            temperature=0.7,
            extra_headers={"OpenAI-Beta": "assistants=v2"},
        )
        ASSISTANT_ID = assistant.id
        return ASSISTANT_ID
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create assistant: {e}")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[int] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    assistant_id: str
    thread_id: str


class LeadCaptureRequest(BaseModel):
    session_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    interested_in: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    notes: Optional[str] = None


class SupportTicketSchema(BaseModel):
    subject: str
    message: str
    priority: str = "normal"

@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session)
):
    """Create or reuse chat session, run assistant, store history, return AI response."""
    client = get_openai_client()
    assistant_id = get_or_create_assistant(client)
    thread = None
    session_id = payload.session_id or f"chat_{uuid.uuid4().hex[:8]}"

    # 1) Get or create chat session
    find_session = await session.execute(
        text("SELECT id, session_id, thread_id FROM chat_sessions WHERE session_id = :sid"),
        {"sid": session_id}
    )
    existing = find_session.mappings().first()

    if not existing:
        # create new thread at OpenAI
        thread = client.beta.threads.create(
            extra_headers={"OpenAI-Beta": "assistants=v2"},
        )
        await session.execute(
            text("INSERT INTO chat_sessions (session_id, user_id, thread_id, last_active_at) "
                 "VALUES (:sid, :uid, :tid, NOW())"),
            {"sid": session_id, "uid": payload.user_id, "tid": thread.id}
        )
        await session.commit()
        new_id = await session.execute(
            text("SELECT id FROM chat_sessions WHERE session_id = :sid"),
            {"sid": session_id}
        )
        existing = {"id": new_id.scalar(), "session_id": session_id, "thread_id": thread.id}
    else:
        # update activity
        await session.execute(
            text("UPDATE chat_sessions SET last_active_at = NOW() WHERE id = :id"),
            {"id": existing["id"]}
        )
        await session.commit()

    thread_id = existing["thread_id"]

    # 2) Store user message in DB
    await session.execute(
        text("INSERT INTO chat_messages (session_id, role, content, created_at) "
             "VALUES (:sid, 'user', :c, NOW())"),
        {"sid": existing["id"], "c": payload.message}
    )
    await session.commit()

    # 3) Add message to OpenAI thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=payload.message,
        extra_headers={"OpenAI-Beta": "assistants=v2"},
    )

    # 4) Run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        extra_headers={"OpenAI-Beta": "assistants=v2"},
    )

    # 5) Wait for completion (async-friendly)
    waited = 0
    while run.status in ["queued", "in_progress", "requires_action"] and waited < 25:
        await asyncio.sleep(1)
        waited += 1
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
            extra_headers={"OpenAI-Beta": "assistants=v2"},
        )

    if run.status != "completed":
        raise HTTPException(status_code=500, detail="Assistant did not complete.")

    # 6) Get last assistant message
    msgs = client.beta.threads.messages.list(
        thread_id=thread_id,
        order="desc",
        limit=1,
        extra_headers={"OpenAI-Beta": "assistants=v2"},
    )
    ai_message = msgs.data[0].content[0].text.value

    # 7) Store assistant message in DB
    await session.execute(
        text("INSERT INTO chat_messages (session_id, role, content, created_at) "
             "VALUES (:sid, 'assistant', :c, NOW())"),
        {"sid": existing["id"], "c": ai_message}
    )
    await session.commit()

    return {
        "message": ai_message,
        "response": ai_message,  # alias for frontend widget expecting 'response'
        "session_id": session_id,
        "assistant_id": assistant_id,
        "thread_id": thread_id
    }


# Convenience alias to match /api/chat posting without /message
@router.post("", response_model=ChatResponse)
async def chat_entrypoint(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session)
):
    return await send_message(payload, session)

@router.post("/lead")
async def capture_lead(
    lead: LeadCaptureRequest,
    session: AsyncSession = Depends(get_session)
):
    """Store lead details against chat session."""
    await session.execute(
        text("UPDATE chat_sessions SET user_id = :uid, last_active_at = NOW() WHERE id = :id"),
        {"uid": lead.user_id, "id": lead.session_id}
    )
    await session.commit()
    return JSONResponse({"success": True, "lead": True})

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str = Path(...),
    session: AsyncSession = Depends(get_session)
):
    """Return full chat history for UI display."""
    find_session = await session.execute(
        text("SELECT id, session_id FROM chat_sessions WHERE session_id = :sid"),
        {"sid": session_id}
    )
    sess = find_session.mappings().first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")

    msgs = await session.execute(
        text("SELECT role, content, created_at FROM chat_messages WHERE session_id = :id ORDER BY created_at ASC"),
        {"id": sess["id"]}
    )
    messages = msgs.mappings().all()

    return {
        "session_id": session_id,
        "messages": [
            {"role": m["role"], "content": m["content"], "timestamp": m["created_at"].isoformat()}
            for m in messages
        ]
    }

# Optional support ticket creation if you wire support UI later
@router.post("/support-ticket")
async def create_support_ticket(
    ticket: SupportTicketSchema,
    session: AsyncSession = Depends(get_session)
):
    """Create support ticket request from chat support UI."""
    await session.execute(
        text("INSERT INTO support_tickets (subject, priority, created_at, updated_at) "
             "VALUES (:s, :p, NOW(), NOW())"),
        {"s": ticket.subject, "p": ticket.priority}
    )
    await session.commit()
    return {"success": True, "ticket": True}
