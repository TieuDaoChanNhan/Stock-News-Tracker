# app/scheduler_script.py
import requests
import json
import time
import schedule
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# Thêm thư mục backend vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Bây giờ có thể import bình thường
from app.services.generic_crawler import scrape_news_from_website
from setup_sample_sources import main as source_setup
from setup_watchlist import main as watchlist_setup
from setup_company import main as company_setup
from app.services.notification_service import test_telegram_connection
from app.services.financial_api_service import fetch_all_active_company_metrics

API_BASE_URL = "https://stock-news-tracker-production.up.railway.app/api/v1"

def post_article_to_api(article_data: dict) -> Optional[Dict]:
    """Gửi bài báo đã crawl lên API để lưu trữ."""
    payload = {
        "title": article_data.get("title"),
        "url": article_data.get("url"),
        "summary": article_data.get("summary"),
        "published_date_str": article_data.get("published_date_str") or article_data.get("collected_at_iso"),
        "source_url": article_data.get("source_page")
    }
    
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        response = requests.post(f"{API_BASE_URL}/articles/", json=payload)
        response.raise_for_status()
        
        created_article = response.json()
        print(f"✅ Posted article to DB: '{payload.get('title')[:50]}...' (ID: {created_article.get('id')})")
        return created_article
        
    except Exception as e:
        print(f"❌ Lỗi khi post bài báo: {e}")
        return None

def update_source_last_crawled(source_id: int) -> bool:
    """Cập nhật thời gian crawl cuối cho nguồn."""
    try:
        payload = {"last_crawled_at": datetime.now().isoformat()}
        response = requests.put(f"{API_BASE_URL}/crawl-sources/{source_id}/", json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật nguồn {source_id}: {e}")
        return False

def fetch_and_process_all_active_sources():
    """Lấy và xử lý tin tức từ các nguồn đang hoạt động."""
    print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Bắt đầu chu kỳ xử lý...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/crawl-sources/?is_active=true/")
        response.raise_for_status()
        sources = response.json()
        print(f"📊 Tìm thấy {len(sources)} nguồn đang hoạt động.")
        
        total_new_articles = 0
        
        for source in sources:
            print(f"\n🔍 Đang crawl: {source['name']}")
            
            # 1. CRAWL TIN TỨC
            scraped_articles = scrape_news_from_website(
                page_url=source['url'],
                article_container_selector=source['article_container_selector'],
                title_selector=source['title_selector'],
                link_selector=source['link_selector'],
                summary_selector=source.get('summary_selector'),
                date_selector=source.get('date_selector'),
                source_name=source['name'],
                max_articles=2
            )
            
            if not scraped_articles:
                print(f"   ⚠️ Không tìm thấy bài viết mới nào từ {source['name']}")
                update_source_last_crawled(source['id'])
                continue

            # 2. LƯU BÀI BÁO (AI sẽ được xử lý tự động trong article_crud.py)
            new_articles_count_for_source = 0
            for article in scraped_articles:
                created_article = post_article_to_api(article)
                
                if created_article:
                    new_articles_count_for_source += 1
                    print(f"   📝 Bài viết sẽ được phân tích AI tự động trong backend")
            
            total_new_articles += new_articles_count_for_source
            
            # 3. CẬP NHẬT THỜI GIAN CRAWL CUỐI
            update_source_last_crawled(source['id'])
            
            time.sleep(2)
        
        print(f"\n🎉 Hoàn thành chu kỳ: {total_new_articles} bài báo mới đã được xử lý.")
        
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng trong chu kỳ xử lý: {e}")

def check_api_connection():
    """Kiểm tra kết nối API."""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health/", timeout=5)
        response.raise_for_status()
        print("✅ API đang hoạt động")
        return True
    except Exception as e:
        print(f"❌ Không thể kết nối API: {e}")
        return False

def fetch_company_metrics():
    """
    🎯 Function được gọi bởi scheduler
    Gọi đến services/financial_api_service.py
    """
    print(f"\n📊 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - SCHEDULER: Gọi Financial API Service...")
    
    try:
        # 🔥 GỌI SERVICE THAY VÌ SETUP_COMPANY
        summary = fetch_all_active_company_metrics()
        
        if summary['success_count'] > 0:
            print(f"✅ SCHEDULER: Thành công fetch metrics cho {summary['success_count']} companies")
            
            # Gửi notification nếu muốn
            # if summary['success_count'] >= 5:
            #     notification_message = f"📊 Company Metrics Update\n✅ Successfully fetched metrics for {summary['success_count']} companies\n🔧 API usage: {summary['api_requests_used']}/{summary['api_limit']}"
                 # notification_service.send_telegram_message_sync(notification_message)
        
        if summary['error_count'] > 0:
            print(f"⚠️ SCHEDULER: {summary['error_count']} companies có lỗi")
            
    except Exception as e:
        print(f"❌ SCHEDULER: Lỗi khi gọi Financial API Service: {e}")

def gather_data():
    fetch_company_metrics()
    fetch_and_process_all_active_sources()


def main():

    print("=" * 80)
    print("🤖 STOCK NEWS TRACKER SCHEDULER (with Gemini AI)")
    print("=" * 80)

    source_setup()
    watchlist_setup()
    company_setup()
    test_telegram_connection()
    
    if not check_api_connection():
        return
        
    # Lập lịch
    schedule.every(1).hours.do(gather_data)
    
    print("⏰ Scheduler đã khởi động. Lịch: Mỗi 15 phút.")
    print("🤖 AI phân tích sẽ được thực hiện tự động trong backend.")
    
    # Chạy ngay lần đầu để test
    print("\n🚀 Chạy chu kỳ đầu tiên ngay bây giờ...")
    gather_data()
    
    # Vòng lặp chính
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Đã dừng scheduler.")

if __name__ == "__main__":
    main()
