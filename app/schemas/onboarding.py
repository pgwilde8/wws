from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, SecretStr


class ClientOnboardIn(BaseModel):
    full_name: str
    business_name: str
    industry: str
    site_description: str
    target_audience: Optional[str] = None
    phone: Optional[str] = None

    domain_name: str
    lead_forward_email: EmailStr

    calling_direction: Literal["none", "inbound", "outbound", "both"]
    wants_sms: bool = False

    wants_payments: bool = False
    uses_cloudflare: bool = False

    cloudflare_email: Optional[EmailStr] = None

    twilio_sid: Optional[str] = None
    twilio_token: Optional[SecretStr] = None
    twilio_from_number: Optional[str] = None

    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[SecretStr] = None

    openai_api_key: Optional[SecretStr] = None

    has_logo: bool = False
    brand_colors: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        anystr_strip_whitespace = True

