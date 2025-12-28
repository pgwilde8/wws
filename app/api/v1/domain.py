from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import smtplib
from email.mime.text import MIMEText

from app.db.session import get_session
from app.services.cloudflare import CloudflareService, CloudflareAPIError
from app.core.config import settings
from app.middleware.auth import _get_client_id  # now provided by middleware


router = APIRouter()


class DomainSubmission(BaseModel):
    domain_name: str
    cloudflare_email: Optional[EmailStr] = None
    nameservers_updated: Optional[bool] = False


@router.post("/domain")
async def submit_domain(
    payload: DomainSubmission,
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    """
    Accept a domain, create/get the Cloudflare zone, and add standard DNS records.
    """
    domain = payload.domain_name.strip().lower()
    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="Please provide a valid domain.")

    # Cloudflare setup
    try:
        cf = CloudflareService()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Cloudflare is not configured.") from exc

    try:
        zone = await cf.get_or_create_zone(domain)
        zone_id = zone.get("id")
    except CloudflareAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Cloudflare error: {exc}") from exc

    nameservers = zone.get("name_servers", [])

    # Add standard records (best effort)
    target_ip = settings.CLOUDFLARE_SERVER_IP
    try:
        if target_ip:
            await cf.create_dns_record(zone_id, "A", domain, target_ip)
            await cf.create_dns_record(zone_id, "A", f"api.{domain}", target_ip)
        await cf.create_dns_record(zone_id, "CNAME", f"www.{domain}", domain)
    except CloudflareAPIError as exc:
        # Ignore duplicate record errors; surface others
        if "identical record already exists" not in str(exc).lower():
            raise HTTPException(status_code=502, detail=f"Cloudflare DNS error: {exc}") from exc
    except Exception as exc:
        # Do not fail the request if record creation has issues
        print(f"DNS record creation warning: {exc}")

    # Persist submission
    try:
        await db.execute(
            text(
                """
                INSERT INTO domains (client_id, domain, cloudflare_email, nameservers_updated, zone_id, status, created_at, updated_at)
                VALUES (:client_id, :domain, :cf_email, :ns_updated, :zone_id, 'pending', NOW(), NOW())
                ON CONFLICT (domain) DO UPDATE SET
                    cloudflare_email = EXCLUDED.cloudflare_email,
                    nameservers_updated = EXCLUDED.nameservers_updated,
                    zone_id = EXCLUDED.zone_id,
                    client_id = EXCLUDED.client_id,
                    updated_at = NOW()
                """
            ),
            {
                "client_id": client_id,
                "domain": domain,
                "cf_email": payload.cloudflare_email,
                "ns_updated": bool(payload.nameservers_updated),
                "zone_id": zone_id,
            },
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save domain.") from exc

    # Try to email the client their nameservers (best effort)
    try:
        res = await db.execute(
            text("SELECT email FROM users WHERE id = :cid LIMIT 1"), {"cid": client_id}
        )
        row = res.mappings().first()
        if row and row.get("email") and nameservers:
            _send_nameserver_email(row["email"], domain, nameservers)
    except Exception as exc:
        print(f"Nameserver email warning: {exc}")

    return {"domain": domain, "zone_id": zone_id, "status": "pending", "nameservers": nameservers}


@router.get("/domain")
async def get_domain(
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    """
    Return the most recent domain submission.
    """
    res = await db.execute(
        text(
            """
            SELECT domain, cloudflare_email, nameservers_updated, zone_id, status, created_at, updated_at
            FROM domains
            WHERE client_id = :client_id
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {"client_id": client_id},
    )
    row = res.mappings().first()
    if not row:
        return {}
    return dict(row)


def _send_nameserver_email(to_email: str, domain: str, nameservers: list[str]):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("Nameserver email skipped: SMTP not configured")
        return
    body = (
        f"Your domain submission for {domain} was received.\n\n"
        f"Please update your registrar to use these Cloudflare nameservers:\n"
        + "\n".join(f"- {ns}" for ns in nameservers)
        + "\n\nOnce updated, DNS may take up to 24 hours to propagate."
    )
    msg = MIMEText(body)
    msg["Subject"] = f"Cloudflare nameservers for {domain}"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email

    server = None
    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
    except Exception as exc:
        print(f"Nameserver email send failed: {exc}")
    finally:
        try:
            if server:
                server.quit()
        except Exception:
            pass

