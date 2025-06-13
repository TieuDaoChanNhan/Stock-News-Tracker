from typing import List, Dict, Any, Optional
import json
from app.crud import stock_metrics_crud
from app.services import notification_service
from app.database import get_db

def check_significant_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[str]:
    """Check for significant changes in stock metrics"""
    
    changes = []
    
    # Define thresholds for significant changes
    thresholds = {
        'price': 0.05,      # 5% change
        'pe': 0.10,         # 10% change
        'pb': 0.10,         # 10% change
        'market_cap': 0.05, # 5% change
        'volume': 0.20      # 20% change
    }
    
    for metric, threshold in thresholds.items():
        old_val = old_data.get(metric)
        new_val = new_data.get(metric)
        
        if old_val and new_val:
            try:
                # Clean and convert to float
                old_num = float(old_val.replace(',', ''))
                new_num = float(new_val.replace(',', ''))
                
                # Calculate percentage change
                change_pct = abs(new_num - old_num) / old_num
                
                if change_pct >= threshold:
                    direction = "tăng" if new_num > old_num else "giảm"
                    changes.append(f"{metric.upper()}: {direction} {change_pct:.1%} ({old_val} → {new_val})")
                    
            except (ValueError, ZeroDivisionError):
                continue
    
    return changes

def send_stock_alert(symbol: str, changes: List[str]):
    """Send Telegram alert for stock changes"""
    
    if not changes:
        return
    
    escaped_symbol = notification_service.escape_markdown_v2(symbol)
    
    message_parts = [
        f"📈 *CẢNH BÁO CỔ PHIẾU {escaped_symbol}*",
        "",
        "*Thay đổi đáng chú ý:*"
    ]
    
    for change in changes:
        escaped_change = notification_service.escape_markdown_v2(change)
        message_parts.append(f"• {escaped_change}")
    
    message_parts.extend([
        "",
        f"🕐 Thời gian: {notification_service.escape_markdown_v2(datetime.now().strftime('%H:%M %d/%m/%Y'))}"
    ])
    
    message = "\n".join(message_parts)
    
    success = notification_service.send_telegram_message_sync(message)
    
    if success:
        print(f"✅ Đã gửi cảnh báo cho {symbol}")
    else:
        print(f"❌ Gửi cảnh báo {symbol} thất bại")

def process_vietstock_updates(new_metrics: List[Dict[str, Any]]):
    """Process new metrics and send alerts if needed"""
    
    db = next(get_db())
    
    try:
        for metrics in new_metrics:
            symbol = metrics.get('symbol')
            if not symbol:
                continue
            
            # Get old data
            old_record = stock_metrics_crud.get_latest_metrics(db, symbol)
            old_data = {}
            
            if old_record and old_record.raw_data:
                try:
                    old_data = json.loads(old_record.raw_data)
                except:
                    pass
            
            # Check for changes
            changes = check_significant_changes(old_data, metrics)
            
            # Save new data
            stock_metrics_crud.create_or_update_stock_metrics(db, symbol, metrics)
            
            # Send alert if there are significant changes
            if changes:
                send_stock_alert(symbol, changes)
                
    finally:
        db.close()
