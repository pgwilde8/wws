from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class PortfolioFile(Base):
    __tablename__ = "portfolio_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    url_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - simple debug helper
        return f"<PortfolioFile filename={self.filename}>"

