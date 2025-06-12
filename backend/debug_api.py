import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoints():
    """Test các API endpoints"""
    
    print("🔍 Testing API endpoints...")
    
    # Test health check
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test root endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test articles endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/articles/")
        print(f"✅ Articles endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Articles endpoint failed: {e}")
    
    # Test crawl-sources endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/crawl-sources/")
        print(f"✅ Crawl sources endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Crawl sources endpoint failed: {e}")
    
    # Test POST crawl-sources với dữ liệu đơn giản
    try:
        test_data = {
            "name": "Test Source",
            "url": "https://example.com",
            "article_container_selector": ".test",
            "title_selector": "h1",
            "link_selector": "a",
            "is_active": True
        }
        
        response = requests.post(f"{API_BASE_URL}/api/v1/crawl-sources/", json=test_data)
        print(f"✅ POST crawl source: {response.status_code}")
        if response.status_code != 201:
            print(f"   Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ POST crawl source failed: {e}")

if __name__ == "__main__":
    test_api_endpoints()
