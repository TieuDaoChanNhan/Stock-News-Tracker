import asyncio
import logging
import threading
import os
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
    description="API để quản lý tin tức tài chính, nguồn crawler và watchlist",
    redirect_slashes=True,  # <- thêm dòng này
)

# ✅ SỬA: CORS Configuration chi tiết cho Flutter web
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080", 
        "https://localhost:3000",
        "https://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*"  # Cho phép tất cả cho development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization", 
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "User-Agent",
        "Cache-Control",
    ],
    expose_headers=["*"],
    max_age=86400,  # Cache preflight cho 24 hours
)

# ✅ THÊM: Explicit OPTIONS handler để fix Flutter web CORS
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle all preflight OPTIONS requests for Flutter web"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# ✅ THÊM: Custom middleware để ensure CORS headers
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    if request.method == "OPTIONS":
        # Handle preflight requests
        response = JSONResponse(content={})
        response.headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
            "Access-Control-Allow-Credentials": "true",
        })
        return response
    
    # Process normal request
    response = await call_next(request)
    
    # Add CORS headers to all responses
    response.headers.update({
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
    })
    
    return response

# ✅ CẢI THIỆN: Global exception handler với CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, 
        content={
            "detail": "Internal Server Error",
            "message": str(exc),
            "path": str(request.url)
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# ✅ CẢI THIỆN: Event startup
@app.on_event("startup")
async def startup_event():
    print("🚀 Khởi động Stock News Tracker API...")
    logger.info("Starting Stock News Tracker API...")
    
    try:
        # Import tất cả models
        from app.models import article_model, crawl_source_model, watchlist_model, ai_analysis_model, company_model
        database.init_db()
        print("✅ Database đã được khởi tạo!")
        logger.info("Database initialized successfully")
        
        # Start scheduler nếu không phải Railway environment
        threading.Thread(target=start_scheduler, daemon=True).start()
            
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise

# ✅ THÊM: Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Stock News Tracker API...")
    print("👋 Stock News Tracker API đã tắt")

# ✅ SỬA: Include routers với API prefix
app.include_router(article_endpoints.router, prefix="/api/v1")
app.include_router(crawl_source_endpoints.router, prefix="/api/v1")
app.include_router(watchlist_endpoints.router, prefix="/api/v1")
app.include_router(ai_analysis_endpoints.router, prefix="/api/v1")
app.include_router(company_endpoints.router, prefix="/api/v1")

# ✅ CẢI THIỆN: Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Stock News Tracker API",
        "version": "0.3.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "cors_enabled": True,
        "features": [
            "Articles Management", 
            "Crawl Sources Management", 
            "Watchlist Management",
            "AI Analysis",
            "Company Metrics",
            "Telegram Notifications",
            "Scheduled Crawling"
        ],
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api": "/api/v1"
        }
    }

# ✅ SỬA: Health check endpoint support cả GET và HEAD
@app.get("/health/")
@app.head("/health/")
async def health_check():
    return {
        "status": "ok", 
        "service": "Stock News Tracker API",
        "version": "0.3.0",
        "cors": "enabled"
    }

# ✅ THÊM: CORS test endpoint để debug
@app.get("/cors-test/")
async def cors_test():
    return {
        "message": "CORS is working perfectly!",
        "timestamp": "2025-07-06T21:30:00Z",
        "access_control": "enabled"
    }

if __name__ == "__main__":
    import uvicorn
    # ✅ SỬA: Dynamic port cho Railway
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
