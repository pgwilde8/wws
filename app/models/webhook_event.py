from sqlalchemy import Column, String, JSON, DateTime
from app.db.base import Base
from sqlalchemy.sql import func

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, index=True)
    event_type = Column(String, index=True)
    status = Column(String, index=True)
    raw_payload = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


