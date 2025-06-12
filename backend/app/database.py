from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cấu hình database SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./local_news_tracker.db"

# Tạo engine với cấu hình tối ưu cho SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # Timeout 30 giây
    },
    echo=False  # Tắt SQL logging
)

# Cấu hình PRAGMA khi kết nối database
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Thiết lập PRAGMA cho SQLite khi tạo kết nối"""
    cursor = dbapi_connection.cursor()
    # Thiết lập busy timeout
    cursor.execute("PRAGMA busy_timeout = 30000")  # 30 giây
    # Thiết lập WAL mode cho hiệu suất tốt hơn với concurrent access
    cursor.execute("PRAGMA journal_mode = WAL")
    # Thiết lập synchronous mode
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.close()

# Tạo SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo Base class
Base = declarative_base()

# Dependency để lấy database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hàm khởi tạo database
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
