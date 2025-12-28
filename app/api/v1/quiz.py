import smtplib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.core.config import settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()


class QuizSubmission(BaseModel):
    email: EmailStr
    businessDescription: str
    exists: str
    customization: str
    needsAI: str
    timeline: str
    budget: str


@router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmission, session: AsyncSession = Depends(get_session)):
    """
    Minimal quiz submission handler.
    Chooses a recommended package based primarily on budget and stores the submission.
    """
    budget = payload.budget or ""
    budget = budget.lower()

    if "6k" in budget or "plus" in budget or "6k-plus" in budget:
        recommended = "scale"
    elif "not" in budget and "sure" in budget:
        recommended = "growth"
    else:
        recommended = "growth"

    # Persist the submission (requires quiz_submissions table)
    try:
        await session.execute(
            text(
                """
                INSERT INTO quiz_submissions (email, recommended_package, payload, created_at)
                VALUES (:email, :pkg, :payload::jsonb, NOW())
                """
            ),
            {
                "email": payload.email,
                "pkg": recommended,
                "payload": payload.model_dump_json(),
            },
        )
        await session.commit()
    except Exception:
        # Don't fail the user flow if storage has an issue
        await session.rollback()

    # Send admin notification email (best-effort, non-blocking for user flow)
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = settings.CONTACT_EMAIL or settings.SMTP_FROM_EMAIL
        msg["Subject"] = f"New Quiz Submission - {recommended.title()}"

        body = (
            "New quiz submission received:\n\n"
            f"Email: {payload.email}\n"
            f"Recommended package: {recommended}\n"
            f"Business description: {payload.businessDescription}\n"
            f"Exists: {payload.exists}\n"
            f"Customization: {payload.customization}\n"
            f"Needs AI: {payload.needsAI}\n"
            f"Timeline: {payload.timeline}\n"
            f"Budget: {payload.budget}\n"
        )
        msg.attach(MIMEText(body, "plain"))

        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
                server.starttls()
            try:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            finally:
                try:
                    server.quit()
                except Exception:
                    server.close()
    except Exception:
        # swallow email errors; do not block user flow
        pass

    return {"recommended_package": recommended}

