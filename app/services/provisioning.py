"""
Provisioning stubs for client agents (OpenAI assistant, Twilio voice).

These functions are intentionally minimal and contain no credentials.
Wire actual API calls where indicated, then persist IDs/statuses on the clients row.
"""
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def provision_openai_assistant(client_id: int, db: AsyncSession) -> None:
    """
    Placeholder:
    - Fetch OpenAI API key from credentials table.
    - Create the assistant server-side.
    - Persist assistant ID + status on clients.
    """
    # Example: fetch credential
    res = await db.execute(
        text(
            """
            SELECT openai_api_key
            FROM credentials
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    cred = res.mappings().first()
    api_key = cred.get("openai_api_key") if cred else None

    # TODO: Call OpenAI Assistants API with api_key; store returned assistant_id.
    assistant_id = None  # replace with real ID

    await db.execute(
        text(
            """
            UPDATE clients
            SET openai_assistant_id = :assistant_id,
                assistant_status = :status,
                assistant_provisioned_at = :ts
            WHERE id = :cid
            """
        ),
        {
            "assistant_id": assistant_id,
            "status": "created" if assistant_id else "pending",
            "ts": datetime.utcnow(),
            "cid": client_id,
        },
    )
    await db.commit()


async def provision_twilio_voice(client_id: int, db: AsyncSession) -> None:
    """
    Placeholder:
    - Fetch Twilio creds from onboarding/credentials tables.
    - Create/assign a voice workflow (Studio/Voice).
    - Persist voice SID + status on clients.
    """
    res = await db.execute(
        text(
            """
            SELECT twilio_sid, twilio_token, twilio_from_number
            FROM client_onboarding
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    onboarding = res.mappings().first() or {}

    # TODO: Call Twilio API with creds; create voice agent/Studio flow; capture SID.
    voice_sid = None  # replace with real SID

    await db.execute(
        text(
            """
            UPDATE clients
            SET twilio_voice_agent_sid = :voice_sid,
                twilio_status = :status,
                twilio_provisioned_at = :ts
            WHERE id = :cid
            """
        ),
        {
            "voice_sid": voice_sid,
            "status": "provisioned" if voice_sid else "pending",
            "ts": datetime.utcnow(),
            "cid": client_id,
        },
    )
    await db.commit()

