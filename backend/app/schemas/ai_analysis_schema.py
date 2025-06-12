# backend/app/schemas/ai_analysis_schema.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class AIAnalysisBase(BaseModel):
    article_id: int
    summary: Optional[str] = None
    category: Optional[str] = None
    sentiment_score: Optional[float] = None
    impact_score: Optional[float] = None
    keywords_extracted: Optional[List[str]] = None

class AIAnalysisCreate(AIAnalysisBase):
    pass

class AIAnalysisResponse(AIAnalysisBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ArticleWithAIResponse(BaseModel):
    # Article fields
    id: int
    title: str
    url: str
    summary: Optional[str]
    
    # AI Analysis
    ai_analysis: Optional[AIAnalysisResponse] = None
    
    model_config = ConfigDict(from_attributes=True)
