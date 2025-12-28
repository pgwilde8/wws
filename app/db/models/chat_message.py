"""Chat message model."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum

class MessageRole(str, enum.Enum):
	"""Chat message role enum."""
	USER = "user"
	ASSISTANT = "assistant"
	SYSTEM = "system"

class ChatMessage(BaseModel):
	"""Chat message storage for analytics and history."""
	__tablename__ = "chat_messages"
	session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
	role = Column(Enum(MessageRole), nullable=False)
	content = Column(Text, nullable=False)
	# Relationships
	session = relationship("ChatSession", back_populates="messages")
	def __repr__(self):
		return f"<ChatMessage(session_id={self.session_id}, role='{self.role}')>"