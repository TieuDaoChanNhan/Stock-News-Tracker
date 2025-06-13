from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.database import Base

class StockMetrics(Base):
    __tablename__ = "stock_metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # Price data
    price = Column(String(20), nullable=True)
    close_price = Column(String(20), nullable=True)
    
    # Valuation metrics
    pe = Column(String(20), nullable=True)
    f_pe = Column(String(20), nullable=True)
    pb = Column(String(20), nullable=True)
    
    # Per-share metrics
    eps = Column(String(20), nullable=True)
    bvps = Column(String(20), nullable=True)
    
    # Market data
    market_cap = Column(String(30), nullable=True)
    volume = Column(String(30), nullable=True)
    beta = Column(String(10), nullable=True)
    
    # Ownership & dividends
    dividend = Column(String(20), nullable=True)
    foreign_ownership = Column(String(10), nullable=True)
    
    # Performance metrics
    roe = Column(String(10), nullable=True)
    roa = Column(String(10), nullable=True)
    
    # Additional data
    detail_url = Column(Text, nullable=True)
    raw_data = Column(Text, nullable=True)  # JSON string of all crawled data
    
    # Timestamps
    crawled_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<StockMetrics(symbol='{self.symbol}', price='{self.price}', pe='{self.pe}')>"
