import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import time
import re

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_vnexpress_page(
    page_url: str, 
    source_name: str = "vnexpress.net"
) -> List[Dict[str, str]]:
    """
    Crawler 1 bài viết mới nhất từ trang VnExpress
    """
    articles = []
    
    try:
        # Headers để giả lập trình duyệt thực
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Gửi request với timeout
        response = requests.get(page_url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Các selector cho VnExpress (thử nhiều pattern)
        article_selectors = [
            ".item-news",           # Selector chính cho bài viết
            ".item-news-common",    # Selector phụ
            ".title-news",          # Selector cho tiêu đề
            "article",              # Thẻ article
            ".story",               # Selector story
            ".item-news-wrap"       # Selector wrap
        ]
        
        article_found = None
        
        # Thử từng selector cho đến khi tìm được bài viết
        for selector in article_selectors:
            article_blocks = soup.select(selector)
            if article_blocks:
                article_found = article_blocks[0]  # Lấy bài viết đầu tiên (mới nhất)
                break
        
        if not article_found:
            # Nếu không tìm được bằng selector, thử tìm link đầu tiên có class title
            title_links = soup.select("h3 a, h2 a, h1 a, .title a, .title-news a")
            if title_links:
                article_found = title_links[0].parent
        
        if article_found:
            try:
                # Trích xuất tiêu đề
                title_selectors = ["h3 a", "h2 a", "h1 a", ".title a", ".title-news a", "a"]
                title = ""
                url = ""
                
                for title_sel in title_selectors:
                    title_element = article_found.select_one(title_sel)
                    if title_element:
                        title = title_element.get_text(strip=True)
                        url = title_element.get('href', '')
                        if title and url:
                            break
                
                # Nếu vẫn không có tiêu đề, thử tìm trực tiếp trong trang
                if not title:
                    title_element = soup.select_one("h1, .title-detail, .title-news")
                    if title_element:
                        title = title_element.get_text(strip=True)
                        url = page_url  # Sử dụng URL gốc
                
                # BỎ QUA nếu không có tiêu đề
                if not title or title.strip() == "":
                    logger.info(f"Bỏ qua: Không có tiêu đề từ {source_name}")
                    return articles
                
                # Xử lý URL
                if url.startswith('/'):
                    url = f"https://vnexpress.net{url}"
                elif not url.startswith('http'):
                    url = page_url
                
                # Trích xuất tóm tắt - CẢI THIỆN SELECTOR CHO VNEXPRESS
                summary = ""
                summary_selectors = [
                    ".description",         # Selector chính cho tóm tắt VnExpress
                    ".sapo",               # Selector sapo
                    ".lead",               # Lead paragraph
                    ".summary",            # Summary
                    ".item-news .description",  # Description trong item-news
                    ".excerpt",            # Excerpt
                    "p.description",       # Paragraph description
                    ".intro",              # Intro
                    ".abstract"            # Abstract
                ]
                
                for summary_sel in summary_selectors:
                    summary_element = article_found.select_one(summary_sel)
                    if summary_element:
                        summary = summary_element.get_text(strip=True)
                        if summary and len(summary) > 20:  # Chỉ lấy tóm tắt có ý nghĩa
                            break
                
                # Nếu vẫn không có summary, thử tìm paragraph đầu tiên
                if not summary:
                    paragraphs = article_found.select("p")
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 30 and not text.startswith("Theo"):
                            summary = text
                            break
                
                # Tạo dictionary cho bài viết
                article_data = {
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'source_page': source_name,
                    'collected_at_iso': datetime.now().isoformat()
                }
                
                articles.append(article_data)
                
                # PRINT ra bài viết tìm được
                print(f"\n📰 Bài viết từ {source_name}:")
                print(f"   Tiêu đề: {title}")
                print(f"   URL: {url}")
                if summary:
                    print(f"   Tóm tắt: {summary[:100]}...")
                else:
                    print(f"   Tóm tắt: Không có")
                print(f"   Thời gian: {article_data['collected_at_iso']}")
                print("-" * 80)
                
            except Exception as e:
                logger.error(f"Lỗi khi xử lý bài viết từ {source_name}: {str(e)}")
        
        else:
            logger.warning(f"Không tìm thấy bài viết nào từ {source_name}")
        
        # Delay để tránh bị block
        time.sleep(1)
        
    except requests.RequestException as e:
        logger.error(f"Lỗi kết nối khi crawler {source_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi crawler {source_name}: {str(e)}")
    
    return articles

def scrape_all_vnexpress_news() -> List[Dict[str, str]]:
    """
    Crawler 1 bài viết mới nhất từ mỗi nguồn VnExpress
    """
    all_articles = []
    
    # Danh sách các nguồn theo yêu cầu
    sources = [
        # 🏢 1. Tin tức doanh nghiệp
        {
            "url": "https://vnexpress.net/kinh-doanh/doanh-nghiep",
            "name": "VnExpress - Doanh nghiệp"
        },
        
        # 📊 2. Chỉ số tài chính và hướng dẫn đầu tư
        {
            "url": "https://vnexpress.net/chi-so-p-b-p-e-la-gi-4296226.html",
            "name": "VnExpress - Chỉ số P/B, P/E"
        },
        {
            "url": "https://vnexpress.net/chi-so-eps-la-gi-4461207.html",
            "name": "VnExpress - Chỉ số EPS"
        },
        {
            "url": "https://vnexpress.net/roa-roe-la-gi-4304366.html",
            "name": "VnExpress - ROA, ROE"
        },
        {
            "url": "https://vnexpress.net/meo-doc-bao-cao-tai-chinh-danh-cho-dau-tu-chung-khoan-4862943.html",
            "name": "VnExpress - Báo cáo tài chính"
        },
        
        # 🌐 3. Chính sách kinh tế và địa chính trị
        {
            "url": "https://vnexpress.net/chu-de/chinh-sach-kinh-te-1073",
            "name": "VnExpress - Chính sách kinh tế"
        },
        {
            "url": "https://vnexpress.net/chu-de/luat-doanh-nghiep-7163",
            "name": "VnExpress - Luật doanh nghiệp"
        },
        {
            "url": "https://vnexpress.net/kinh-doanh/quoc-te",
            "name": "VnExpress - Kinh doanh quốc tế"
        },
        
        # 💰 4. Giá vàng và tỷ giá USD
        {
            "url": "https://vnexpress.net/chu-de/gia-vang-1403",
            "name": "VnExpress - Giá vàng"
        },
        {
            "url": "https://vnexpress.net/tag/gia-usd-267904",
            "name": "VnExpress - Giá USD"
        },
        
        # 🔍 5. Các chuyên mục mở rộng khác
        {
            "url": "https://vnexpress.net/kinh-doanh",
            "name": "VnExpress - Kinh doanh"
        },
        {
            "url": "https://vnexpress.net/tag/chinh-sach-tien-te-1044604",
            "name": "VnExpress - Chính sách tiền tệ"
        }
    ]
    
    print(f"\n🔍 Bắt đầu crawler {len(sources)} nguồn từ VnExpress...")
    
    for idx, source in enumerate(sources, 1):
        print(f"\n⏳ [{idx}/{len(sources)}] Đang crawler: {source['name']}...")
        
        articles = scrape_vnexpress_page(source['url'], source['name'])
        all_articles.extend(articles)
        
        # Delay giữa các request
        time.sleep(2)
    
    print(f"\n🎉 TỔNG KẾT: Đã crawler {len(all_articles)} bài viết từ {len(sources)} nguồn VnExpress")
    return all_articles

def scrape_all_news() -> List[Dict[str, str]]:
    """
    Hàm chính để crawler tất cả tin tức
    """
    return scrape_all_vnexpress_news()

# Test function
if __name__ == "__main__":
    print("=" * 120)
    print("🚀 BẮT ĐẦU CRAWLER TIN TỨC VNEXPRESS (1 BÀI MỚI NHẤT MỖI NGUỒN)")
    print("=" * 120)
    
    # Test crawler tin tức
    articles = scrape_all_news()
    
    print(f"\n📊 KẾT QUẢ CUỐI CÙNG:")
    print(f"   Tổng số bài viết: {len(articles)}")
    
    # Thống kê theo nguồn
    sources = {}
    for article in articles:
        source = article['source_page']
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\n📋 THỐNG KÊ THEO NGUỒN:")
    for source, count in sources.items():
        print(f"   ✅ {source}: {count} bài viết")
    
    # **THÊM SUMMARY VÀO DANH SÁCH BÀI VIẾT**
    print(f"\n📝 DANH SÁCH TẤT CẢ BÀI VIẾT (CÓ SUMMARY):")
    for idx, article in enumerate(articles, 1):
        print(f"\n{idx}. {article['title']}")
        print(f"   🔗 URL: {article['url']}")
        print(f"   📰 Nguồn: {article['source_page']}")
        if article['summary']:
            print(f"   📄 Tóm tắt: {article['summary']}")
        else:
            print(f"   📄 Tóm tắt: Không có")
        print(f"   ⏰ Thời gian: {article['collected_at_iso']}")
        print("-" * 100)
