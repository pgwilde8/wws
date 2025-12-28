from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func, Boolean

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan = Column(String(50), nullable=False)  # e.g. starter, growth, scale
    stripe_price_id = Column(String(100), nullable=True)
    stripe_product_id = Column(String(100), nullable=True)
    stripe_session_id = Column(String(120), nullable=True)
    stripe_payment_intent_id = Column(String(120), nullable=True)
    buyer_email = Column(String(255), nullable=True)
    status = Column(String(30), default="onboarding", nullable=False)
    welcome_sent = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
