import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import re
from playwright.async_api import async_playwright, Page, Browser
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VietstockCrawler:
    """Crawler for Vietstock top 10 stocks and financial metrics"""
    
    def __init__(self):
        self.base_url = "https://finance.vietstock.vn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def crawl_top10_stocks(self) -> List[Dict[str, str]]:
        """
        Crawl top 10 stocks from Vietstock homepage
        Returns: List of dicts with symbol and detail_url
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Set headers
                await page.set_extra_http_headers(self.headers)
                
                # Navigate to Vietstock
                await page.goto(self.base_url, wait_until='networkidle', timeout=30000)
                logger.info("✅ Đã truy cập Vietstock homepage")
                
                # Wait for table to load
                await page.wait_for_selector('#top10fin-content', timeout=10000)
                
                # Get all rows in the table
                rows = await page.locator('#top10fin-content tr').all()
                logger.info(f"🔍 Tìm thấy {len(rows)} dòng trong bảng top 10")
                
                result = []
                
                for i, row in enumerate(rows):
                    try:
                        # Get all cells in this row
                        cells = await row.locator('td').all()
                        
                        if len(cells) < 2:
                            continue
                        
                        # Get symbol from column 2 (index 1)
                        symbol_cell = cells[1]
                        symbol = await symbol_cell.inner_text()
                        symbol = symbol.strip()
                        
                        # Get link from <a> tag in column 2
                        link_element = await symbol_cell.locator('a').first
                        if not link_element:
                            logger.warning(f"⚠️ Không tìm thấy link cho {symbol}")
                            continue
                        
                        href = await link_element.get_attribute('href')
                        if not href:
                            continue
                        
                        # Build full URL
                        if href.startswith('/'):
                            detail_url = f"{self.base_url}{href}"
                        else:
                            detail_url = href
                        
                        stock_data = {
                            'symbol': symbol,
                            'detail_url': detail_url
                        }
                        
                        result.append(stock_data)
                        logger.info(f"✅ Crawled: {symbol} -> {detail_url}")
                        
                    except Exception as e:
                        logger.error(f"❌ Lỗi khi xử lý dòng {i+1}: {e}")
                        continue
                
                logger.info(f"🎉 Hoàn thành crawl top 10: {len(result)} cổ phiếu")
                return result
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi crawl top 10: {e}")
                return []
            finally:
                await browser.close()
    
    async def crawl_stock_detail(self, symbol: str, detail_url: str) -> Dict[str, Any]:
        """
        Crawl financial metrics from stock detail page
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Set headers
                await page.set_extra_http_headers(self.headers)
                
                # Navigate to detail page
                await page.goto(detail_url, wait_until='networkidle', timeout=30000)
                logger.info(f"🔍 Đang crawl chi tiết: {symbol}")
                
                # Wait for content to load
                await page.wait_for_timeout(2000)
                
                # Initialize result
                data = {
                    'symbol': symbol,
                    'detail_url': detail_url,
                    'crawled_at': datetime.now().isoformat()
                }
                
                # Method 1: Try to get current price from main price display
                try:
                    price_element = await page.locator('.price, .current-price, .last-price').first
                    if price_element:
                        price = await price_element.inner_text()
                        data['price'] = self._clean_number(price)
                except:
                    pass
                
                # Method 2: Crawl financial metrics from info panels
                # Look for div.col-ce.bg-50 containing financial metrics
                try:
                    metric_panels = await page.locator('div.col-ce.bg-50').all()
                    
                    for panel in metric_panels:
                        # Get all p.p8 elements in this panel
                        metric_rows = await panel.locator('p.p8').all()
                        
                        for row in metric_rows:
                            try:
                                # Get the metric name (text before colon)
                                row_text = await row.inner_text()
                                
                                # Get the value from b.pull-right
                                value_element = await row.locator('b.pull-right').first
                                if not value_element:
                                    continue
                                
                                value = await value_element.inner_text()
                                value = value.strip()
                                
                                # Extract metric name
                                metric_name = row_text.split(':')[0].strip() if ':' in row_text else row_text.strip()
                                
                                # Map to standard names
                                mapped_key = self._map_metric_name(metric_name)
                                if mapped_key:
                                    data[mapped_key] = self._clean_number(value)
                                
                            except Exception as e:
                                continue
                
                except Exception as e:
                    logger.warning(f"⚠️ Không thể crawl metrics từ panels cho {symbol}: {e}")
                
                # Method 3: Try alternative selectors for common metrics
                await self._crawl_additional_metrics(page, data)
                
                logger.info(f"✅ Hoàn thành crawl {symbol}: {len(data)} chỉ số")
                return data
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi crawl chi tiết {symbol}: {e}")
                return {
                    'symbol': symbol,
                    'detail_url': detail_url,
                    'error': str(e),
                    'crawled_at': datetime.now().isoformat()
                }
            finally:
                await browser.close()
    
    async def _crawl_additional_metrics(self, page: Page, data: Dict[str, Any]):
        """Try to crawl metrics from alternative locations"""
        
        # Common selectors for financial metrics
        selectors_to_try = [
            '.financial-info .metric',
            '.stock-info .info-item',
            '.overview-info .item',
            'table.financial-table td',
            '.key-metrics .metric-item'
        ]
        
        for selector in selectors_to_try:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    text = await element.inner_text()
                    # Process text to extract metric name and value
                    # This would need to be customized based on actual HTML structure
                    pass
            except:
                continue
    
    def _map_metric_name(self, metric_name: str) -> Optional[str]:
        """Map Vietnamese metric names to English keys"""
        
        mapping = {
            'P/E': 'pe',
            'F P/E': 'f_pe',
            'P/B': 'pb',
            'EPS': 'eps',
            'BVPS': 'bvps',
            'Vốn hóa': 'market_cap',
            'Von hoa': 'market_cap',
            'Khối lượng': 'volume',
            'Khoi luong': 'volume',
            'Beta': 'beta',
            'Cổ tức': 'dividend',
            'Co tuc': 'dividend',
            'Tỷ lệ NN': 'foreign_ownership',
            'Ty le NN': 'foreign_ownership',
            'NN sở hữu': 'foreign_ownership',
            'Giá': 'price',
            'Gia': 'price',
            'Đóng cửa': 'close_price',
            'Dong cua': 'close_price',
            'ROE': 'roe',
            'ROA': 'roa',
            'Doanh thu': 'revenue',
            'Lợi nhuận': 'profit',
            'Loi nhuan': 'profit'
        }
        
        # Try exact match first
        if metric_name in mapping:
            return mapping[metric_name]
        
        # Try partial match
        for key, value in mapping.items():
            if key.lower() in metric_name.lower():
                return value
        
        return None
    
    def _clean_number(self, value: str) -> str:
        """Clean and standardize number format"""
        if not value or value == '-' or value.lower() == 'n/a':
            return None
        
        # Remove common prefixes/suffixes
        value = value.strip()
        value = re.sub(r'[^\d,.-]', '', value)  # Keep only digits, commas, dots, minus
        
        return value
    
    async def crawl_all_top10_with_details(self) -> List[Dict[str, Any]]:
        """
        Main function: Crawl top 10 stocks and their detailed metrics
        """
        logger.info("🚀 Bắt đầu crawl Top 10 Vietstock...")
        
        # Step 1: Get top 10 stocks
        top10_stocks = await self.crawl_top10_stocks()
        
        if not top10_stocks:
            logger.error("❌ Không thể lấy danh sách top 10")
            return []
        
        # Step 2: Crawl details for each stock
        all_data = []
        
        for i, stock in enumerate(top10_stocks, 1):
            logger.info(f"📊 [{i}/{len(top10_stocks)}] Crawling {stock['symbol']}...")
            
            try:
                detail_data = await self.crawl_stock_detail(
                    stock['symbol'], 
                    stock['detail_url']
                )
                all_data.append(detail_data)
                
                # Delay between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Lỗi khi crawl {stock['symbol']}: {e}")
                # Add error record
                all_data.append({
                    'symbol': stock['symbol'],
                    'detail_url': stock['detail_url'],
                    'error': str(e),
                    'crawled_at': datetime.now().isoformat()
                })
        
        logger.info(f"🎉 Hoàn thành crawl: {len(all_data)} cổ phiếu")
        return all_data

# Sync wrapper for integration with existing system
def crawl_vietstock_top10_sync() -> List[Dict[str, Any]]:
    """Sync wrapper for async crawler"""
    try:
        crawler = VietstockCrawler()
        return asyncio.run(crawler.crawl_all_top10_with_details())
    except Exception as e:
        logger.error(f"❌ Lỗi trong sync wrapper: {e}")
        return []

# Test function
async def test_crawler():
    """Test the crawler"""
    crawler = VietstockCrawler()
    
    print("=" * 80)
    print("🧪 TESTING VIETSTOCK CRAWLER")
    print("=" * 80)
    
    # Test crawling top 10
    print("\n📊 Testing top 10 crawl...")
    top10 = await crawler.crawl_top10_stocks()
    
    for stock in top10[:3]:  # Test first 3 stocks
        print(f"\n🔍 Testing detail crawl for {stock['symbol']}...")
        detail = await crawler.crawl_stock_detail(stock['symbol'], stock['detail_url'])
        
        print(f"📈 {stock['symbol']} metrics:")
        for key, value in detail.items():
            if value and key not in ['detail_url', 'crawled_at']:
                print(f"   {key}: {value}")
        
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_crawler())
