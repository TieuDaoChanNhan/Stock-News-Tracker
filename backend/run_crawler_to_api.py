import requests
import json
import sys
import os

# Import scraper từ file web_scrapers.py của bạn
from backend.app.services.web_scrapers import scrape_all_vnexpress_news

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

def post_article_to_api(article_data: dict):
    """Gửi article lên API"""
    payload = {
        "title": article_data.get("title"),
        "url": article_data.get("url"),
        "summary": article_data.get("summary"),
        "published_date_str": article_data.get("collected_at_iso"),
        "source_url": article_data.get("source_page")  # Đây chính là source_name từ scraper
    }
    
    # Loại bỏ các key có giá trị None
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        response = requests.post(f"{API_BASE_URL}/articles/", json=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ SUCCESS: Posted article '{payload.get('title')[:50]}...' - Status: {response.status_code}")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to post article '{payload.get('title', 'Unknown')[:50]}...'")
        print(f"   Error: {e}")
        
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response status: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                print(f"   Response data: {error_detail}")
            except json.JSONDecodeError:
                print(f"   Response text: {e.response.text}")
        return None

def check_api_health():
    """Kiểm tra API có hoạt động không"""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        response.raise_for_status()
        print("✅ API đang hoạt động bình thường")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ API không hoạt động: {e}")
        print("💡 Hãy đảm bảo server FastAPI đang chạy: uvicorn main:app --reload")
        return False

def main():
    print("=" * 80)
    print("🚀 BẮT ĐẦU CRAWLER VÀ GỬI DỮ LIỆU LÊN API")
    print("=" * 80)
    
    # Kiểm tra API
    if not check_api_health():
        return
    
    # Chạy crawler
    print("\n📰 Đang crawler tin tức từ VnExpress...")
    try:
        # Gọi hàm từ file web_scrapers.py của bạn
        articles_from_vnexpress = scrape_all_vnexpress_news()
        
        if articles_from_vnexpress:
            print(f"\n📊 Tìm thấy {len(articles_from_vnexpress)} bài viết. Đang gửi lên API...")
            
            success_count = 0
            error_count = 0
            
            for idx, article in enumerate(articles_from_vnexpress, 1):
                print(f"\n[{idx}/{len(articles_from_vnexpress)}] Đang xử lý...")
                
                result = post_article_to_api(article)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            
            print(f"\n🎉 KẾT QUẢ:")
            print(f"   ✅ Thành công: {success_count}")
            print(f"   ❌ Lỗi: {error_count}")
            print(f"   📊 Tổng cộng: {len(articles_from_vnexpress)}")
            
        else:
            print("❌ Không tìm thấy bài viết nào từ crawler")
            
    except Exception as e:
        print(f"❌ Lỗi khi chạy crawler: {e}")

if __name__ == "__main__":
    main()
