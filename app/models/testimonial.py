from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, func
from datetime import datetime
from app.db.base import Base

class Testimonial(Base):
    __tablename__ = "testimonials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, nullable=True, index=True)
    client_name = Column(String(255), nullable=True)
    client_location = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    event_type = Column(String(255), nullable=True)
    testimonial_text = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)
    is_approved = Column("approved", Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Testimonial(client_name='{self.client_name}', rating={self.rating})>"
