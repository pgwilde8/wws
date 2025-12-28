"""Chat session model."""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class ChatSession(BaseModel):
	"""Chat session tracking model - links visitors to OpenAI threads."""
	__tablename__ = "chat_sessions"
	session_id = Column(String(255), nullable=False, unique=True, index=True)  # From cookie/localStorage
	user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # If logged in
	thread_id = Column(String(255), nullable=False, index=True)  # OpenAI thread ID
	last_active_at = Column(DateTime, nullable=False, index=True)
	is_active = Column(Boolean, default=True, nullable=False)
	# Relationships
	user = relationship("User", backref="chat_sessions")
	messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
	lead = relationship("ChatLead", back_populates="session", uselist=False, cascade="all, delete-orphan")
	def __repr__(self):
		return f"<ChatSession(session_id='{self.session_id}', thread_id='{self.thread_id}')>"