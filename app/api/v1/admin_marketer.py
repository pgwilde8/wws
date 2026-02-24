"""
Admin Marketing Assistant
Uses OPENAI_ASSISTANT_ID_MARKETER for marketing strategy & campaign help
"""
import os
import uuid
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.config import settings
from app.core.security import require_admin_auth

router = APIRouter(dependencies=[Depends(require_admin_auth)])
templates = Jinja2Templates(directory="app/templates")

# Initialize OpenAI client with v2 API
openai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

# Load marketer assistant ID from environment
ASSISTANT_ID_MARKETER = os.getenv("OPENAI_ASSISTANT_ID_MARKETER", settings.OPENAI_ASSISTANT_ID_MARKETER or "")

if not ASSISTANT_ID_MARKETER:
    raise ValueError("OPENAI_ASSISTANT_ID_MARKETER must be set in environment")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# In-memory session store (use Redis in production)
chat_threads = {}


@router.get("/admin/marketer")
async def marketer_page(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """Render the marketing assistant chat interface"""
    return templates.TemplateResponse(
        "admin/marketer.html",
        {"request": request}
    )


@router.get("/admin/teleprompter")
async def teleprompter_page(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """Render the teleprompter interface"""
    return templates.TemplateResponse(
        "admin/teleprompter.html",
        {"request": request}
    )


@router.post("/api/admin/marketer/chat")
async def marketer_chat(
    chat_request: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """Handle chat messages with the marketing assistant"""
    try:
        # Get or create thread
        session_id = chat_request.session_id
        if not session_id or session_id not in chat_threads:
            # Create new thread
            thread = openai_client.beta.threads.create(
                extra_headers={"OpenAI-Beta": "assistants=v2"}
            )
            session_id = thread.id
            chat_threads[session_id] = thread.id
        
        thread_id = chat_threads[session_id]
        
        # Add user message to thread
        openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=chat_request.message,
            extra_headers={"OpenAI-Beta": "assistants=v2"}
        )
        
        # Run the assistant
        run = openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID_MARKETER,
            extra_headers={"OpenAI-Beta": "assistants=v2"}
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress"]:
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
                extra_headers={"OpenAI-Beta": "assistants=v2"}
            )
            if run.status == "completed":
                break
            elif run.status in ["failed", "cancelled", "expired"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Assistant run failed: {run.status}"
                )
        
        # Get the assistant's response
        messages = openai_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=1,
            extra_headers={"OpenAI-Beta": "assistants=v2"}
        )
        
        assistant_message = messages.data[0]
        response_text = assistant_message.content[0].text.value
        
        return {
            "session_id": session_id,
            "response": response_text
        }
        
    except Exception as e:
        print(f"Marketer chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )
