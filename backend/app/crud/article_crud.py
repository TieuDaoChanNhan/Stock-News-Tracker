from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib
import json

from app.models import article_model as models
from app.schemas import article_schema as schemas
from app.models import ai_analysis_model
from app.crud import watchlist_crud
from app.crud import ai_analysis_crud  # ← Thêm import
from app.schemas import ai_analysis_schema  # ← Thêm import
from app.services import notification_service
from app.services import gemini_service

def get_article_by_url(db: Session, url: str) -> Optional[models.Article]:
    """Lấy article theo URL"""
    return db.query(models.Article).filter(models.Article.url == url).first()

def get_article_by_content_hash(db: Session, content_hash: str) -> Optional[models.Article]:
    """Lấy article theo content hash"""
    return db.query(models.Article).filter(models.Article.content_hash == content_hash).first()

def create_article(db: Session, article: schemas.ArticleCreate) -> models.Article:
    """Tạo article mới hoặc trả về article đã tồn tại"""
    
    # Tính content hash
    content_to_hash = (article.title or "") + (article.summary or "")
    content_hash = hashlib.md5(content_to_hash.encode('utf-8')).hexdigest()
    
    # Kiểm tra trùng lặp theo URL
    existing_article_by_url = get_article_by_url(db, url=article.url)
    if existing_article_by_url:
        print(f"📄 Article đã tồn tại (URL): {article.title[:50]}...")
        return existing_article_by_url
    
    # Kiểm tra trùng lặp theo content hash
    existing_article_by_hash = get_article_by_content_hash(db, content_hash=content_hash)
    if existing_article_by_hash:
        print(f"📄 Article đã tồn tại (Content): {article.title[:50]}...")
        return existing_article_by_hash
    
    # Tạo article mới
    article_dict = article.dict()
    article_dict['content_hash'] = content_hash
    
    db_article = models.Article(**article_dict)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    print(f"✅ Tạo article mới: {article.title[:50]}...")
    
    # **PHÂN TÍCH AI VỚI GEMINI**
    try:
        # 1. Tóm tắt bằng Gemini
        print(f"🤖 Đang tóm tắt bài viết bằng Gemini...")
        try:
            ai_summary = gemini_service.summarize_article_with_gemini(
                title=db_article.title, 
                content=db_article.summary or ""
            )
            print(f"✅ Tóm tắt thành công: {ai_summary[:50] if ai_summary else 'None'}...")
        except Exception as e:
            print(f"❌ Lỗi tóm tắt: {e}")
            ai_summary = None
        
        # 2. Phân tích toàn diện bằng Gemini
        print(f"🤖 Đang phân tích bài viết bằng Gemini...")
        try:
            full_analysis = gemini_service.analyze_article_with_gemini(
                title=db_article.title,
                content=db_article.summary or ""
            )
            print(f"✅ Phân tích thành công: {full_analysis}")
        except Exception as e:
            print(f"❌ Lỗi phân tích: {e}")
            full_analysis = None
        
        # 3. Tạo record ArticleAIAnalysis (KHÔNG dùng schema để tránh lỗi)
        print(f"🤖 Đang tạo AI analysis record...")
        try:
            db_ai_analysis = ai_analysis_model.ArticleAIAnalysis(
                article_id=db_article.id,
                summary=ai_summary
            )
            
            # 4. Cập nhật kết quả phân tích nếu có
            if full_analysis:
                db_ai_analysis.category = full_analysis.get("category")
                # Chuyển đổi sentiment text sang score số
                sentiment_map = {"Tích cực": 1.0, "Trung tính": 0.0, "Tiêu cực": -1.0}
                db_ai_analysis.sentiment_score = sentiment_map.get(full_analysis.get("sentiment"), 0.0)
                # Chuyển đổi impact text sang score số
                impact_map = {"Cao": 1.0, "Trung bình": 0.5, "Thấp": 0.1}
                db_ai_analysis.impact_score = impact_map.get(full_analysis.get("impact_level"), 0.1)
                db_ai_analysis.keywords_extracted = json.dumps(full_analysis.get("key_entities", []), ensure_ascii=False)
                # Lưu toàn bộ JSON phân tích để tham khảo sau
                db_ai_analysis.analysis_metadata = json.dumps(full_analysis, ensure_ascii=False)
                
                print(f"📊 Phân tích hoàn tất: Category={full_analysis.get('category')}, Sentiment={full_analysis.get('sentiment')}, Impact={full_analysis.get('impact_level')}")
            
            # 5. Lưu kết quả AI vào database
            print(f"🤖 Đang lưu AI analysis vào database...")
            db.add(db_ai_analysis)
            db.commit()
            db.refresh(db_ai_analysis)
            print(f"✅ Đã lưu AI analysis với ID: {db_ai_analysis.id}")
            
            # 6. Kiểm tra watchlist và gửi thông báo nâng cao
            print(f"🤖 Đang kiểm tra watchlist...")
            check_and_notify_watchlist_with_ai(db, db_article, db_ai_analysis, full_analysis)
            
        except Exception as e:
            print(f"❌ Lỗi khi tạo/lưu AI analysis: {e}")
            print(f"❌ Chi tiết lỗi: {type(e).__name__}: {str(e)}")
            # Fallback về watchlist thông thường
            check_and_notify_watchlist(db, db_article)
            
    except Exception as e:
        print(f"⚠️ Lỗi tổng thể khi phân tích AI: {e}")
        print(f"⚠️ Chi tiết lỗi: {type(e).__name__}: {str(e)}")
        # Vẫn kiểm tra watchlist thông thường nếu AI lỗi
        check_and_notify_watchlist(db, db_article)
    
    return db_article

def check_and_notify_watchlist_with_ai(db: Session, db_article: models.Article, db_ai_analysis, full_analysis):
    """Kiểm tra watchlist và gửi thông báo nâng cao với AI insights"""
    
    print(f"🔍 DEBUG: Checking watchlist for article: {db_article.title}")
    
    # Lấy danh sách watchlist của ông X
    watchlist_items = watchlist_crud.get_watchlist_items_by_user(db, user_id='ong_x')
    
    if not watchlist_items:
        print("🔍 DEBUG: No watchlist items found")
        return
    
    triggered_keywords = set()
    
    # Chuẩn bị text để kiểm tra
    article_title_lower = db_article.title.lower()
    article_summary_lower = (db_article.summary or "").lower()
    
    # Kiểm tra từng item trong watchlist
    for item in watchlist_items:
        keyword_to_check = item.item_value.lower()
        
        # Kiểm tra keyword có trong title hoặc summary không
        if (keyword_to_check in article_title_lower or 
            keyword_to_check in article_summary_lower):
            triggered_keywords.add(item.item_value)
    
    # Lấy thông tin AI analysis
    impact_score = db_ai_analysis.impact_score if db_ai_analysis else 0.0
    category = db_ai_analysis.category or "Tin tức" if db_ai_analysis else "Tin tức"
    sentiment_text = full_analysis.get("sentiment", "N/A") if full_analysis else "N/A"
    impact_text = full_analysis.get("impact_level", "N/A") if full_analysis else "N/A"
    analysis_summary = full_analysis.get("analysis_summary", "") if full_analysis else ""
    
    # **ĐIỀU KIỆN 1: CÓ TRIGGERED KEYWORDS**
    if triggered_keywords:
        matched_keywords_list = list(triggered_keywords)
        print(f"🔔 Tìm thấy match với watchlist: {matched_keywords_list}")
        
        # Format thông báo cho triggered keywords
        message = create_keyword_notification_message(
            db_article, category, sentiment_text, impact_text, 
            analysis_summary, matched_keywords_list
        )
        
        success = notification_service.send_telegram_message_sync(message=message)
        
        if success:
            print(f"✅ Đã gửi thông báo KEYWORD cho: {matched_keywords_list}")
        else:
            print(f"❌ Gửi thông báo KEYWORD thất bại")
    
    # **ĐIỀU KIỆN 2: IMPACT TỪ TRUNG BÌNH TRỞ LÊN (0.5+)**
    elif impact_score >= 0.5:
        print(f"📊 Tin tức có tác động cao: {impact_text} (score: {impact_score})")
        
        # Format thông báo cho high impact
        message = create_impact_notification_message(
            db_article, category, sentiment_text, impact_text, analysis_summary
        )
        
        success = notification_service.send_telegram_message_sync(message=message)
        
        if success:
            print(f"✅ Đã gửi thông báo HIGH IMPACT: {category} - {impact_text}")
        else:
            print(f"❌ Gửi thông báo HIGH IMPACT thất bại")
    
    else:
        print("🔍 DEBUG: Không đủ điều kiện thông báo (no keywords + low impact)")

def create_keyword_notification_message(db_article, category, sentiment_text, impact_text, analysis_summary, matched_keywords_list):
    """Tạo message cho thông báo triggered keywords"""
    
    # Escape tất cả text
    escaped_category = notification_service.escape_markdown_v2(category.upper())
    escaped_impact = notification_service.escape_markdown_v2(impact_text)
    escaped_sentiment = notification_service.escape_markdown_v2(sentiment_text)
    escaped_keywords = notification_service.escape_markdown_v2(', '.join(matched_keywords_list))
    escaped_title = notification_service.escape_markdown_v2(db_article.title)
    escaped_analysis = notification_service.escape_markdown_v2(analysis_summary)
    escaped_url = notification_service.escape_markdown_v2(db_article.url)
    
    # Format cho triggered keywords
    message_parts = [
        f"🎯 *WATCHLIST ALERT*",
        f"📂 {escaped_category} \\| 📊 {escaped_impact} \\| 💭 {escaped_sentiment}",
        f"🔍 Từ khóa: *{escaped_keywords}*",
        "\\-\\-\\-",
        f"*{escaped_title}*",
        f"_{escaped_analysis}_",
        "",
        f"[Đọc ngay]({escaped_url})"
    ]
    
    return "\n".join(message_parts)

def create_impact_notification_message(db_article, category, sentiment_text, impact_text, analysis_summary):
    """Tạo message cho thông báo high impact"""
    
    # Escape tất cả text
    escaped_category = notification_service.escape_markdown_v2(category.upper())
    escaped_impact = notification_service.escape_markdown_v2(impact_text)
    escaped_sentiment = notification_service.escape_markdown_v2(sentiment_text)
    escaped_title = notification_service.escape_markdown_v2(db_article.title)
    escaped_analysis = notification_service.escape_markdown_v2(analysis_summary)
    escaped_url = notification_service.escape_markdown_v2(db_article.url)
    
    # Chọn emoji theo impact level
    impact_emoji = "🔥" if impact_text == "Cao" else "⚡"
    
    # Format cho high impact
    message_parts = [
        f"{impact_emoji} *TIN TỨC TÁC ĐỘNG {escaped_impact.upper()}*",
        f"📂 {escaped_category} \\| 💭 {escaped_sentiment}",
        "\\-\\-\\-",
        f"*{escaped_title}*",
        f"_{escaped_analysis}_",
        "",
        f"[Đọc ngay]({escaped_url})"
    ]
    
    return "\n".join(message_parts)

def check_and_notify_watchlist(db: Session, db_article: models.Article):
    """Kiểm tra watchlist thông thường (fallback khi AI lỗi)"""
    print(f"🔍 DEBUG: Checking watchlist for article (fallback): {db_article.title}")
    
    try:
        # Lấy danh sách watchlist của ông X
        watchlist_items = watchlist_crud.get_watchlist_items_by_user(db, user_id='ong_x')
        
        if not watchlist_items:
            print("🔍 DEBUG: No watchlist items found")
            return
        
        triggered_keywords = set()
        
        # Chuẩn bị text để kiểm tra
        article_title_lower = db_article.title.lower()
        article_summary_lower = (db_article.summary or "").lower()
        
        # Kiểm tra từng item trong watchlist
        for item in watchlist_items:
            keyword_to_check = item.item_value.lower()
            
            if (keyword_to_check in article_title_lower or 
                keyword_to_check in article_summary_lower):
                triggered_keywords.add(item.item_value)
        
        # Nếu có keyword match, gửi thông báo đơn giản
        if triggered_keywords:
            matched_keywords_list = list(triggered_keywords)
            print(f"🔔 Tìm thấy match với watchlist (fallback): {matched_keywords_list}")
            
            # Format thông báo đơn giản
            message = notification_service.format_news_notification(
                article_title=db_article.title,
                article_url=db_article.url,
                matched_keywords=matched_keywords_list
            )
            
            success = notification_service.send_telegram_message_sync(message=message)
            
            if success:
                print(f"✅ Đã gửi thông báo FALLBACK cho: {matched_keywords_list}")
            else:
                print(f"❌ Gửi thông báo FALLBACK thất bại")
    except Exception as e:
        print(f"❌ Lỗi trong fallback watchlist: {e}")

# Các hàm khác giữ nguyên...
def get_articles(db: Session, skip: int = 0, limit: int = 20) -> List[models.Article]:
    """Lấy danh sách articles với phân trang"""
    return db.query(models.Article)\
             .order_by(models.Article.created_at.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()

def get_articles_count(db: Session) -> int:
    """Đếm tổng số articles"""
    return db.query(models.Article).count()

def get_articles_with_ai_analysis(db: Session, skip: int = 0, limit: int = 20):
    """Lấy articles kèm AI analysis"""
    return ai_analysis_crud.get_articles_with_ai_analysis(db, skip, limit)

def get_articles_by_category(db: Session, category: str):
    """Lấy articles theo category AI"""
    return ai_analysis_crud.get_articles_by_category(db, category)

def get_high_impact_articles(db: Session, min_impact: float = 0.7):
    """Lấy articles có impact cao"""
    return ai_analysis_crud.get_high_impact_articles(db, min_impact)
