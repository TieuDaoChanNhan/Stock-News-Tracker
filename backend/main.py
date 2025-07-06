import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import database
from app.api.endpoints import article_endpoints, crawl_source_endpoints, watchlist_endpoints, ai_analysis_endpoints, company_endpoints
from app.scheduler_script import main as start_scheduler

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tạo FastAPI app
app = FastAPI(
    title="Stock News Tracker API",
    version="0.3.0",
    description="API để quản lý tin tức tài chính, nguồn crawler và watchlist"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, 
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

# Event startup
@app.on_event("startup")
async def startup_event():
    print("🚀 Khởi động Stock News Tracker API...")
    # Import tất cả models
    from app.models import article_model, crawl_source_model, watchlist_model, ai_analysis_model, company_model
    database.init_db()
    print("✅ Database đã được khởi tạo!")

# Include routers
app.include_router(article_endpoints.router)
app.include_router(crawl_source_endpoints.router)
app.include_router(watchlist_endpoints.router)  # ← MỚI
app.include_router(ai_analysis_endpoints.router)
app.include_router(company_endpoints.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Stock News Tracker API",
        "version": "0.3.0",
        "features": [
            "Articles Management", 
            "Crawl Sources Management", 
            "Watchlist Management",
            "Telegram Notifications",
            "Scheduled Crawling"
        ],
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Stock News Tracker API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    start_scheduler()

