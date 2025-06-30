import requests
import json

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

# Danh sách nguồn crawl mẫu
sample_sources = [
    {
        "name": "VnExpress - Doanh nghiệp",
        "url": "https://vnexpress.net/kinh-doanh/doanh-nghiep",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Chính trị",
        "url": "https://vnexpress.net/thoi-su/chinh-tri",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Luật doanh nghiệp",
        "url": "https://vnexpress.net/chu-de/luat-doanh-nghiep-7163",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Kinh doanh",
        "url": "https://vnexpress.net/kinh-doanh",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Giá vàng",
        "url": "https://vnexpress.net/chu-de/gia-vang-1403",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Giá USD",
        "url": "https://vnexpress.net/tag/gia-usd-267904",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Kinh doanh",
        "url": "https://vnexpress.net/kinh-doanh",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Khoa học công nghệ",
        "url": "https://vnexpress.net/khoa-hoc-cong-nghe",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    {
        "name": "VnExpress - Trang chủ",
        "url": "https://vnexpress.net/",
        "article_container_selector": ".item-news",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "summary_selector": ".description",
        "date_selector": ".time",
        "is_active": True
    },
    # {
    #     "name": "CafeF - Trang chủ",
    #     "url": "https://cafef.vn/",
    #     "article_container_selector": "div.tlitem, div.top_noibat_row1, .top5_news .tlitem, .box-nha-dau-tu-content .item",
    #     "title_selector": "h2 a, h3 a, a.title", # Thử nhiều loại thẻ chứa tiêu đề
    #     "link_selector": "h2 a, h3 a, a.title",   # Thường giống title_selector
    #     "summary_selector": "p.sapo, .sapo, .box-category-sapo, .knsw-sapo", # Nhiều class có thể là sapo
    #     "date_selector": ".time, .time_cate .time, .knswli-meta .time", # Selector cho thời gian
    #     "is_active": True
    # },
    # {
    #     "name": "Asian Banking and Finance - Vietnam",
    #     "url": "https://asianbankingandfinance.net/market/vietnam",
    #     # Selector này là phỏng đoán, cần kiểm tra kỹ với Playwright
    #     "article_container_selector": "div.views-row, article.node--type-article, div.article-listing__item", 
    #     "title_selector": "h2 a, h3 a, .node__title a", # Tiêu đề
    #     "link_selector": "h2 a, h3 a, .node__title a",   # Link
    #     "summary_selector": "div.field--name-body p, div.content p, .article-listing__summary p", # Tóm tắt
    #     "date_selector": ".node__submitted .field--name-created, span.date-display-single, .article-listing__date", # Thời gian
    #     "is_active": True
    # },
    # {
    #     "name": "VnEconomy - Chứng khoán",
    #     "url": "https://vneconomy.vn/chung-khoan.htm",
    #     "article_container_selector": ".story",
    #     "title_selector": ".story__title a",
    #     "link_selector": ".story__title a",
    #     "summary_selector": ".story__summary",
    #     "date_selector": ".story__meta > time",
    #     "is_active": True
    # }
]

def add_crawl_source(source_data):
    """Thêm nguồn crawl"""
    try:
        response = requests.post(f"{API_BASE_URL}/crawl-sources/", json=source_data)
        response.raise_for_status()
        result = response.json()
        print(f"✅ Đã thêm: {source_data['name']}")
        return result
    except Exception as e:
        print(f"❌ Lỗi khi thêm {source_data['name']}: {e}")
        return None

def main():
    print("🔧 Thiết lập nguồn crawl mẫu...")
    
    for source in sample_sources:
        add_crawl_source(source)
    
    print(f"\n✅ Đã thiết lập {len(sample_sources)} nguồn crawl")
    print("💡 Kiểm tra tại: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    main()
