# backend/app/api/endpoints/ai_analysis_endpoints.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.crud import ai_analysis_crud as crud
from app.schemas import ai_analysis_schema as schemas
from app.database import get_db

router = APIRouter(prefix="/api/v1/ai-analysis", tags=["ai-analysis"])

@router.get("/article/{article_id}", response_model=schemas.AIAnalysisResponse)
async def get_ai_analysis(article_id: int, db: Session = Depends(get_db)):
    """Lấy AI analysis của một bài báo"""
    analysis = crud.get_ai_analysis_by_article_id(db, article_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found")
    return analysis

@router.get("/category/{category}", response_model=List[schemas.ArticleWithAIResponse])
async def get_articles_by_category(category: str, db: Session = Depends(get_db)):
    """Lấy articles theo category"""
    return crud.get_articles_by_category(db, category)

@router.get("/high-impact", response_model=List[schemas.ArticleWithAIResponse])
async def get_high_impact_articles(min_impact: float = 0.7, db: Session = Depends(get_db)):
    """Lấy articles có impact cao"""
    return crud.get_high_impact_articles(db, min_impact)
