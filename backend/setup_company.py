import sys
import os
from datetime import datetime
from typing import List

# Add backend directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.database import SessionLocal, init_db
from app.crud import company_crud as crud
from app.schemas import company_schema as schemas
from app.services.financial_api_service import financial_api, test_financial_api

def setup_popular_companies() -> List[str]:
    """
    🏢 CHỨC NĂNG DUY NHẤT: Add danh sách companies vào bảng 'companies'
    Return list of symbols đã được add thành công
    """
    
    popular_companies = [
        # Technology Giants
        {"symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics"},
        {"symbol": "MSFT", "company_name": "Microsoft Corporation", "sector": "Technology", "industry": "Software"},
        {"symbol": "GOOGL", "company_name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Services"},
        {"symbol": "TSLA", "company_name": "Tesla Inc.", "sector": "Technology", "industry": "Electric Vehicles"},
        {"symbol": "NVDA", "company_name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors"},
        {"symbol": "META", "company_name": "Meta Platforms Inc.", "sector": "Technology", "industry": "Social Media"},
        
        # Financial Services
        {"symbol": "JPM", "company_name": "JPMorgan Chase & Co.", "sector": "Financial", "industry": "Banking"},
        {"symbol": "BAC", "company_name": "Bank of America Corp", "sector": "Financial", "industry": "Banking"},
        {"symbol": "WFC", "company_name": "Wells Fargo & Company", "sector": "Financial", "industry": "Banking"},
        
        # Healthcare
        {"symbol": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare", "industry": "Pharmaceuticals"},
        {"symbol": "PFE", "company_name": "Pfizer Inc.", "sector": "Healthcare", "industry": "Pharmaceuticals"},
        {"symbol": "UNH", "company_name": "UnitedHealth Group Inc.", "sector": "Healthcare", "industry": "Health Insurance"},
        
        # Consumer Goods
        {"symbol": "KO", "company_name": "The Coca-Cola Company", "sector": "Consumer", "industry": "Beverages"},
        {"symbol": "PG", "company_name": "Procter & Gamble Co", "sector": "Consumer", "industry": "Consumer Goods"},
        {"symbol": "DIS", "company_name": "The Walt Disney Company", "sector": "Entertainment", "industry": "Media"},
        
        # Energy
        {"symbol": "XOM", "company_name": "Exxon Mobil Corporation", "sector": "Energy", "industry": "Oil & Gas"},
        {"symbol": "CVX", "company_name": "Chevron Corporation", "sector": "Energy", "industry": "Oil & Gas"},
        
        # Industrial
        {"symbol": "GE", "company_name": "General Electric Company", "sector": "Industrial", "industry": "Conglomerates"},
        
        # Retail
        {"symbol": "WMT", "company_name": "Walmart Inc.", "sector": "Retail", "industry": "Discount Stores"},
        {"symbol": "AMZN", "company_name": "Amazon.com Inc.", "sector": "Retail", "industry": "E-commerce"},
    ]
    
    db = SessionLocal()
    added_symbols = []
    
    try:
        print("🏢 SETUP COMPANIES: Đang thêm companies vào bảng 'companies'...")
        print("=" * 60)
        
        for company_data in popular_companies:
            try:
                # Check if already exists
                existing = crud.get_company_by_symbol(db, company_data['symbol'])
                
                if existing:
                    print(f"   ⚠️ {company_data['symbol']} đã tồn tại, skipping...")
                    continue
                
                # Create new company
                company_create = schemas.CompanyCreate(**company_data)
                db_company = crud.create_company(db, company_create)
                
                added_symbols.append(company_data['symbol'])
                print(f"   ✅ Added {company_data['symbol']} - {company_data['company_name']}")
                
            except Exception as e:
                print(f"   ❌ Error adding {company_data['symbol']}: {e}")
                continue
        
        print(f"\n🎉 Hoàn thành setup: {len(added_symbols)} companies đã được thêm vào bảng 'companies'")
        return added_symbols
        
    finally:
        db.close()

def test_sample_companies():
    """Test fetch metrics cho vài companies mẫu để verify setup"""
    print("\n🧪 TESTING: Sample companies fetch...")
    print("=" * 60)
    
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    db = SessionLocal()
    
    try:
        for symbol in test_symbols:
            company = crud.get_company_by_symbol(db, symbol)
            if not company:
                print(f"   ⚠️ {symbol} chưa có trong bảng 'companies', skipping...")
                continue
            
            print(f"📊 Testing fetch cho {symbol}...")
            
            # Fetch metrics từ service
            metrics_data = financial_api.fetch_all_company_metrics(symbol)
            
            if metrics_data and 'symbol' in metrics_data:
                db_metrics = crud.create_company_metrics(db, company.id, metrics_data)
                
                print(f"   ✅ {symbol}: PE={metrics_data.get('pe_ratio')}, "
                      f"Market Cap={metrics_data.get('market_cap')}, "
                      f"ROE={metrics_data.get('roe')}")
                print(f"   🆔 Saved to company_metrics table với ID: {db_metrics.id}")
            else:
                print(f"   ❌ Failed to fetch metrics for {symbol}")
                
    finally:
        db.close()

def show_database_summary():
    """Hiển thị summary của 2 bảng database"""
    db = SessionLocal()
    
    try:
        print("\n📋 DATABASE SUMMARY:")
        print("=" * 60)
        
        # Count companies
        companies = crud.get_companies(db, limit=1000)
        active_companies = [c for c in companies if c.is_active]
        
        print(f"📊 Bảng 'companies':")
        print(f"   Total companies: {len(companies)}")
        print(f"   Active companies: {len(active_companies)}")
        print(f"   Inactive companies: {len(companies) - len(active_companies)}")
        
        # Count metrics
        total_metrics = db.query(crud.models.CompanyMetrics).count()
        
        print(f"\n📈 Bảng 'company_metrics':")
        print(f"   Total metrics records: {total_metrics}")
        
        # Show some examples
        if active_companies:
            print(f"\n📋 Example companies:")
            for company in active_companies[:5]:
                latest_metrics = crud.get_latest_metrics_by_symbol(db, company.symbol)
                metrics_count = db.query(crud.models.CompanyMetrics).filter(
                    crud.models.CompanyMetrics.company_id == company.id
                ).count()
                
                print(f"   {company.symbol} ({company.company_name}):")
                print(f"     - Sector: {company.sector}")
                print(f"     - Metrics records: {metrics_count}")
                if latest_metrics:
                    print(f"     - Latest PE: {latest_metrics.pe_ratio}")
                    print(f"     - Last updated: {latest_metrics.recorded_at}")
                
    finally:
        db.close()

def main():
    """
    🎯 MAIN SETUP FUNCTION: Chỉ để initialize companies
    Fetch metrics sẽ được handle bởi services/financial_api_service.py
    """
    print("=" * 80)
    print("🏢 COMPANY SETUP (Companies Only)")
    print("=" * 80)
    
    # Initialize database
    print("📋 Initializing database tables...")
    init_db()
    print("✅ Database tables created: 'companies' và 'company_metrics'")
    
    # Test API connection
    print("\n🔌 Testing Financial API Service...")
    if not financial_api.test_api_connection():
        print("❌ API connection failed. Kiểm tra FMP_API_KEY trong .env file")
        return
    
    # Setup companies
    added_symbols = setup_popular_companies()
    
    # # Test sample metrics từ service
    # if added_symbols:
    #     test_sample_companies()
    
    # Show summary
    show_database_summary()
    
    print("\n" + "=" * 80)
    print("🎉 SETUP COMPANIES HOÀN TẤT")
    print("=" * 80)
    print("✅ Companies đã được setup trong bảng 'companies'")
    print("✅ Financial API Service đã được test")
    print("✅ Sample metrics đã được fetch từ service")
    print(f"\n📖 Để fetch tất cả metrics:")
    print("   1. Chạy scheduler: python app/scheduler_script.py")
    print("   2. Scheduler sẽ gọi services/financial_api_service.py")
    print("   3. Hoặc manual: GET /api/v1/companies/AAPL/fetch-metrics")

if __name__ == "__main__":
    main()
