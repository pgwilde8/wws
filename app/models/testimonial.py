from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean
from datetime import datetime
from app.db.base import BaseModel

class Testimonial(BaseModel):
    __tablename__ = "testimonials"

    client_id = Column(Integer, nullable=True, index=True)
    client_name = Column(String(120), nullable=False)
    client_location = Column(String(120), nullable=True)
    event_type = Column(String(80), nullable=True)
    testimonial_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    stripe_reference = Column(String(80), nullable=True, index=True)
    is_approved = Column(Boolean, default=False, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    archived = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Testimonial(client_name='{self.client_name}', rating={self.rating})>"
