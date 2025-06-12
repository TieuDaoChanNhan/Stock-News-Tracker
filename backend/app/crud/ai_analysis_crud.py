# backend/app/crud/ai_analysis_crud.py
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models import ai_analysis_model as models
from app.schemas import ai_analysis_schema as schemas

def create_ai_analysis(db: Session, analysis: schemas.AIAnalysisCreate) -> models.ArticleAIAnalysis:
    """Tạo AI analysis mới"""
    db_analysis = models.ArticleAIAnalysis(**analysis.dict())
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

def get_ai_analysis_by_article_id(db: Session, article_id: int) -> Optional[models.ArticleAIAnalysis]:
    """Lấy AI analysis theo article ID"""
    return db.query(models.ArticleAIAnalysis).filter(
        models.ArticleAIAnalysis.article_id == article_id
    ).first()

def get_articles_with_ai_analysis(db: Session, skip: int = 0, limit: int = 20) -> List:
    """Lấy articles kèm AI analysis"""
    return db.query(models.Article).join(
        models.ArticleAIAnalysis, 
        models.Article.id == models.ArticleAIAnalysis.article_id
    ).offset(skip).limit(limit).all()

def get_articles_by_category(db: Session, category: str) -> List:
    """Lấy articles theo category AI"""
    return db.query(models.Article).join(
        models.ArticleAIAnalysis
    ).filter(
        models.ArticleAIAnalysis.category == category
    ).all()

def get_high_impact_articles(db: Session, min_impact: float = 0.7) -> List:
    """Lấy articles có impact cao"""
    return db.query(models.Article).join(
        models.ArticleAIAnalysis
    ).filter(
        models.ArticleAIAnalysis.impact_score >= min_impact
    ).all()
