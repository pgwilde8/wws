"""
Provisioning helpers for client agents (OpenAI assistant, Twilio voice).
Reads credentials from the `credentials` table and updates the `clients` table.
"""
from datetime import datetime
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def provision_openai_assistant(client_id: int, db: AsyncSession) -> None:
    """
    Create an OpenAI Assistant for the client and persist the assistant ID / status.
    """
    cred_res = await db.execute(
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
    cred = cred_res.mappings().first() or {}
    api_key = cred.get("openai_api_key")

    onboarding_res = await db.execute(
        text(
            """
            SELECT business_name, industry, site_description
            FROM client_onboarding
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    onboarding = onboarding_res.mappings().first() or {}

    assistant_id = None
    status = "pending"
    status_detail = None

    if not api_key:
        status = "failed"
        status_detail = "missing_openai_key"
    else:
        try:
            try:
                import openai  # type: ignore
            except ImportError:
                openai = None

            if not openai:
                status = "failed"
                status_detail = "openai_sdk_not_installed"
            else:
                openai.api_key = api_key
                name = onboarding.get("business_name") or f"Client {client_id} Assistant"
                instructions = (
                    f"You are the assistant for {onboarding.get('business_name') or 'our client'} "
                    f"in the {onboarding.get('industry') or 'business'} space. "
                    f"Project brief: {onboarding.get('site_description') or 'N/A'}"
                )
                resp = openai.beta.assistants.create(
                    model="gpt-4o-mini",
                    name=name,
                    instructions=instructions,
                    extra_headers={"OpenAI-Beta": "assistants=v2"},
                )
                assistant_id = resp.id if resp else None
                status = "created" if assistant_id else "failed"
                status_detail = None if assistant_id else "openai_create_failed"
        except Exception as exc:
            status = "failed"
            status_detail = f"error:{type(exc).__name__}"

    await db.execute(
        text(
            """
            UPDATE clients
            SET openai_assistant_id = :assistant_id,
                assistant_status = :status,
                assistant_status_detail = :status_detail,
                assistant_provisioned_at = :ts
            WHERE id = :cid
            """
        ),
        {
            "assistant_id": assistant_id,
            "status": status,
            "status_detail": status_detail,
            "ts": datetime.utcnow(),
            "cid": client_id,
        },
    )
    await db.commit()


async def provision_twilio_voice(client_id: int, db: AsyncSession) -> None:
    """
    Create/assign a Twilio voice workflow and persist the SID / status.
    """
    cred_res = await db.execute(
        text(
            """
            SELECT twilio_sid, twilio_token, twilio_from_number
            FROM credentials
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    cred = cred_res.mappings().first() or {}
    account_sid = cred.get("twilio_sid")
    auth_token = cred.get("twilio_token")
    from_number = cred.get("twilio_from_number")

    voice_sid = None
    status = "pending"
    status_detail = None

    if not account_sid or not auth_token:
        status = "failed"
        status_detail = "missing_twilio_creds"
    else:
        try:
            try:
                from twilio.rest import Client  # type: ignore
            except ImportError:
                Client = None

            if not Client:
                status = "failed"
                status_detail = "twilio_sdk_not_installed"
            else:
                client = Client(account_sid, auth_token)
                client.api.accounts(account_sid).fetch()

                incoming = client.incoming_phone_numbers.list(phone_number=from_number, limit=1) if from_number else []
                if not incoming:
                    status = "failed"
                    status_detail = "from_number_not_found"
                else:
                    # Create a simple Studio Flow that greets and hangs up
                    flow_def = {
                        "description": "Auto-created voice flow",
                        "states": [
                            {
                                "name": "Greeting",
                                "type": "say-play",
                                "properties": {
                                    "say": "Thanks for calling. Your voice agent has been provisioned.",
                                    "voice": "Polly.Joanna",
                                    "loop": 1,
                                },
                                "transitions": [],
                            }
                        ],
                        "initial_state": "Greeting",
                        "flags": {"allow_concurrent_calls": True},
                    }
                    flow = client.studio.v2.flows.create(
                        friendly_name=f"Client {client_id} Voice Agent",
                        status="published",
                        definition=json.dumps(flow_def),
                    )
                    flow_sid = flow.sid if flow else None
                    if not flow_sid:
                        status = "failed"
                        status_detail = "flow_create_failed"
                    else:
                        voice_sid = flow_sid
                        number_sid = incoming[0].sid
                        flow_url = f"https://webhooks.twilio.com/v1/Accounts/{account_sid}/Flows/{flow_sid}"
                        client.incoming_phone_numbers(number_sid).update(voice_url=flow_url, voice_method="POST")
                        status = "provisioned"
                        status_detail = None
        except Exception as exc:
            status = "failed"
            status_detail = f"error:{type(exc).__name__}"

    await db.execute(
        text(
            """
            UPDATE clients
            SET twilio_voice_agent_sid = :voice_sid,
                twilio_status = :status,
                twilio_status_detail = :status_detail,
                twilio_provisioned_at = :ts
            WHERE id = :cid
            """
        ),
        {
            "voice_sid": voice_sid,
            "status": status,
            "status_detail": status_detail,
            "ts": datetime.utcnow(),
            "cid": client_id,
        },
    )
    await db.commit()

