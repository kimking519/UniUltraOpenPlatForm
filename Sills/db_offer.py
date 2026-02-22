import sqlite3
import uuid
from datetime import datetime
from Sills.base import get_db_connection

def get_offer_list(page=1, page_size=10, search_kw=""):
    offset = (page - 1) * page_size
    query = """
    SELECT o.*, 
           v.vendor_name,
           e.emp_name
    FROM uni_offer o
    LEFT JOIN uni_vendor v ON o.vendor_id = v.vendor_id
    LEFT JOIN uni_emp e ON o.emp_id = e.emp_id
    WHERE o.inquiry_mpn LIKE ? OR o.offer_id LIKE ? OR v.vendor_name LIKE ? OR e.emp_name LIKE ?
    ORDER BY o.created_at DESC
    LIMIT ? OFFSET ?
    """
    count_query = """
    SELECT COUNT(*) 
    FROM uni_offer o
    LEFT JOIN uni_vendor v ON o.vendor_id = v.vendor_id
    LEFT JOIN uni_emp e ON o.emp_id = e.emp_id
    WHERE o.inquiry_mpn LIKE ? OR o.offer_id LIKE ? OR v.vendor_name LIKE ? OR e.emp_name LIKE ?
    """
    params = (f"%{search_kw}%", f"%{search_kw}%", f"%{search_kw}%", f"%{search_kw}%")
    
    with get_db_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        items = conn.execute(query, params + (page_size, offset)).fetchall()
        
        results = [
            {k: ("" if v is None else v) for k, v in dict(row).items()}
            for row in items
        ]
        return results, total

def add_offer(data, emp_id):
    try:
        hex_str = str(uuid.uuid4().hex)
        offer_id = "O" + datetime.now().strftime("%Y%m%d%H%M%S") + hex_str[:4]
        offer_date = datetime.now().strftime("%Y-%m-%d")
        
        sql = """
        INSERT INTO uni_offer (
            offer_id, offer_date, quote_id, inquiry_mpn, quoted_mpn, inquiry_brand, quoted_brand,
            inquiry_qty, actual_qty, quoted_qty, cost_price_rmb, offer_price_rmb, platform,
            vendor_id, date_code, delivery_date, emp_id, offer_statement, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            offer_id,
            offer_date,
            data.get('quote_id'),
            data.get('inquiry_mpn', ''),
            data.get('quoted_mpn', ''),
            data.get('inquiry_brand', ''),
            data.get('quoted_brand', ''),
            data.get('inquiry_qty', 0),
            data.get('actual_qty', 0),
            data.get('quoted_qty', 0),
            data.get('cost_price_rmb', 0.0),
            data.get('offer_price_rmb', 0.0),
            data.get('platform', ''),
            data.get('vendor_id', ''),
            data.get('date_code', ''),
            data.get('delivery_date', ''),
            emp_id,  # Set by the logged in user
            data.get('offer_statement', ''),
            data.get('remark', '')
        )
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, f"报价单 {offer_id} 创建成功"
    except Exception as e:
        return False, str(e)

def update_offer(offer_id, data):
    try:
        if 'emp_id' in data:
            del data['emp_id'] # Prevent changing owner post-creation
            
        set_cols = []
        params = []
        for k, v in data.items():
            set_cols.append(f"{k} = ?")
            params.append(v)
        if not set_cols: return True, "No changes"
        
        sql = f"UPDATE uni_offer SET {', '.join(set_cols)} WHERE offer_id = ?"
        params.append(offer_id)
        
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, "更新成功"
    except Exception as e:
        return False, str(e)

def delete_offer(offer_id):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM uni_offer WHERE offer_id = ?", (offer_id,))
            conn.commit()
            return True, "删除成功"
    except Exception as e:
        return False, str(e)

def batch_import_offer_text(text, emp_id):
    lines = text.strip().split('\n')
    success_count = 0
    errors = []
    for line in lines:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 1: continue
        
        try:
            data = {
                "quote_id": parts[0] if len(parts) > 0 else "",
                "inquiry_mpn": parts[1] if len(parts) > 1 else "",
                "quoted_mpn": parts[2] if len(parts) > 2 else "",
                "inquiry_brand": parts[3] if len(parts) > 3 else "",
                "quoted_brand": parts[4] if len(parts) > 4 else "",
                "inquiry_qty": int(parts[5]) if len(parts) > 5 and parts[5] else 0,
                "actual_qty": int(parts[6]) if len(parts) > 6 and parts[6] else 0,
                "quoted_qty": int(parts[7]) if len(parts) > 7 and parts[7] else 0,
                "cost_price_rmb": float(parts[8]) if len(parts) > 8 and parts[8] else 0.0,
                "offer_price_rmb": float(parts[9]) if len(parts) > 9 and parts[9] else 0.0,
                "platform": parts[10] if len(parts) > 10 else "",
                "vendor_id": parts[11] if len(parts) > 11 else "",
                "date_code": parts[12] if len(parts) > 12 else "",
                "delivery_date": parts[13] if len(parts) > 13 else "",
                "offer_statement": parts[14] if len(parts) > 14 else "",
                "remark": parts[15] if len(parts) > 15 else ""
            }
            if not data["inquiry_mpn"]:
                errors.append(f"{line}: 缺少询价型号")
                continue
                
            ok, msg = add_offer(data, emp_id)
            if ok: success_count += 1
            else: errors.append(f"{parts[1]}: {msg}")
        except Exception as e:
            errors.append(f"{line}: 数据格式解析失败 ({str(e)})")
            
    return success_count, errors
