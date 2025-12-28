"""Chat lead qualification model."""
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum

class LeadStatus(str, enum.Enum):
	"""Lead status enum."""
	NEW = "new"
	CONTACTED = "contacted"
	QUALIFIED = "qualified"
	CONVERTED = "converted"
	DISQUALIFIED = "disqualified"

class ChatLead(BaseModel):
	"""Lead captured and qualified through chat."""
	__tablename__ = "chat_leads"
	session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, unique=True, index=True)
	name = Column(String(255), nullable=True)
	email = Column(String(255), nullable=True, index=True)
	phone = Column(String(50), nullable=True)
	company = Column(String(255), nullable=True)
	interested_in = Column(String(255), nullable=True)  # Which package/service
	budget = Column(String(100), nullable=True)
	timeline = Column(String(100), nullable=True)
	notes = Column(Text, nullable=True)  # Additional context from conversation
	status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True)
	# Relationships
	session = relationship("ChatSession", back_populates="lead")
	def __repr__(self):
		return f"<ChatLead(name='{self.name}', email='{self.email}', status='{self.status}')>"