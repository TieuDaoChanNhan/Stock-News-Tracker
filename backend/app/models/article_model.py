from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    published_date_str = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    content_hash = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source='{self.source_url}')>"
