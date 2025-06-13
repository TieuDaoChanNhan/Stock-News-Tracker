from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from app.models import stock_metrics_model as models
from app.schemas import stock_metrics_schema as schemas

def create_or_update_stock_metrics(db: Session, symbol: str, metrics_data: Dict[str, Any]) -> models.StockMetrics:
    """Create or update stock metrics"""
    
    # Check if record exists
    existing = db.query(models.StockMetrics).filter(
        models.StockMetrics.symbol == symbol
    ).first()
    
    if existing:
        # Update existing record
        for key, value in metrics_data.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        
        existing.updated_at = datetime.utcnow()
        existing.raw_data = json.dumps(metrics_data, ensure_ascii=False)
        
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        db_metrics = models.StockMetrics(
            symbol=symbol,
            price=metrics_data.get('price'),
            pe=metrics_data.get('pe'),
            f_pe=metrics_data.get('f_pe'),
            pb=metrics_data.get('pb'),
            eps=metrics_data.get('eps'),
            bvps=metrics_data.get('bvps'),
            market_cap=metrics_data.get('market_cap'),
            volume=metrics_data.get('volume'),
            beta=metrics_data.get('beta'),
            dividend=metrics_data.get('dividend'),
            foreign_ownership=metrics_data.get('foreign_ownership'),
            roe=metrics_data.get('roe'),
            roa=metrics_data.get('roa'),
            detail_url=metrics_data.get('detail_url'),
            raw_data=json.dumps(metrics_data, ensure_ascii=False)
        )
        
        db.add(db_metrics)
        db.commit()
        db.refresh(db_metrics)
        return db_metrics

def get_latest_metrics(db: Session, symbol: str) -> Optional[models.StockMetrics]:
    """Get latest metrics for a symbol"""
    return db.query(models.StockMetrics).filter(
        models.StockMetrics.symbol == symbol
    ).order_by(models.StockMetrics.updated_at.desc()).first()

def get_all_latest_metrics(db: Session) -> List[models.StockMetrics]:
    """Get latest metrics for all symbols"""
    return db.query(models.StockMetrics).order_by(
        models.StockMetrics.updated_at.desc()
    ).all()
