import requests
import json

API_BASE_URL = "https://stock-news-tracker-production.up.railway.app/api/v1"
USER_ID = "ong_x"

# Danh sách watchlist mẫu
sample_watchlist = [
    # # Mã cổ phiếu
    # {"item_type": "STOCK_SYMBOL", "item_value": "FPT"},
    # {"item_type": "STOCK_SYMBOL", "item_value": "HPG"},
    # {"item_type": "STOCK_SYMBOL", "item_value": "VIC"},
    # {"item_type": "STOCK_SYMBOL", "item_value": "VCB"},
    # {"item_type": "STOCK_SYMBOL", "item_value": "Vinamilk"},
    
    # Từ khóa quan trọng
    {"item_type": "KEYWORD", "item_value": "lãi suất"},
    {"item_type": "KEYWORD", "item_value": "bất động sản"},
    {"item_type": "KEYWORD", "item_value": "chứng khoán"},
    {"item_type": "KEYWORD", "item_value": "ngân hàng"},
    {"item_type": "KEYWORD", "item_value": "kinh tế"},
    {"item_type": "KEYWORD", "item_value": "Mỹ"},
]

def add_watchlist_item(item_data):
    """Thêm item vào watchlist"""
    try:
        response = requests.post(f"{API_BASE_URL}/users/{USER_ID}/watchlist/", json=item_data)
        response.raise_for_status()
        result = response.json()
        print(f"✅ Đã thêm: {item_data['item_value']} ({item_data['item_type']})")
        return result
    except Exception as e:
        print(f"❌ Lỗi khi thêm {item_data['item_value']}: {e}")
        return None

def main():
    print(f"🔧 Thiết lập watchlist cho user: {USER_ID}")
    
    for item in sample_watchlist:
        add_watchlist_item(item)
    
    print(f"\n✅ Đã thiết lập {len(sample_watchlist)} items cho watchlist")
    print("💡 Kiểm tra tại: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    main()
