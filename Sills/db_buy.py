import sqlite3
import uuid
from datetime import datetime
from Sills.base import get_db_connection

def get_buy_list(page=1, page_size=10, search_kw="", order_id=""):
    offset = (page - 1) * page_size
    
    base_query = """
    FROM uni_buy b
    LEFT JOIN uni_order ord ON b.order_id = ord.order_id
    LEFT JOIN uni_vendor v ON b.vendor_id = v.vendor_id
    WHERE (b.buy_id LIKE ? OR b.buy_mpn LIKE ? OR v.vendor_name LIKE ?)
    """
    params = [f"%{search_kw}%", f"%{search_kw}%", f"%{search_kw}%"]
    
    if order_id:
        base_query += " AND b.order_id = ?"
        params.append(order_id)
        
    query = f"""
    SELECT b.*, ord.order_id, v.vendor_name
    {base_query}
    ORDER BY b.created_at DESC
    LIMIT ? OFFSET ?
    """
    
    count_query = f"SELECT COUNT(*) {base_query}"
    
    with get_db_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        items = conn.execute(query, params + [page_size, offset]).fetchall()
        
        results = [
            {k: ("" if v is None else v) for k, v in dict(row).items()}
            for row in items
        ]
        return results, total

def add_buy(data):
    try:
        hex_str = str(uuid.uuid4().hex)
        buy_id = "PU" + datetime.now().strftime("%Y%m%d%H%M%S") + hex_str[:4]
        buy_date = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate total_amount: buy_price_rmb * buy_qty
        price = float(data.get('buy_price_rmb', 0.0))
        qty = int(data.get('buy_qty', 0))
        total_amount = round(price * qty, 2)
        
        sql = """
        INSERT INTO uni_buy (
            buy_id, buy_date, order_id, vendor_id, buy_mpn, buy_brand, buy_price_rmb, buy_qty,
            sales_price_rmb, total_amount, is_source_confirmed, is_ordered, is_instock, is_shipped, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            buy_id,
            buy_date,
            data.get('order_id'),
            data.get('vendor_id'),
            data.get('buy_mpn', ''),
            data.get('buy_brand', ''),
            price,
            qty,
            float(data.get('sales_price_rmb', 0.0)),
            total_amount,
            int(data.get('is_source_confirmed', 0)),
            int(data.get('is_ordered', 0)),
            int(data.get('is_instock', 0)),
            int(data.get('is_shipped', 0)),
            data.get('remark', '')
        )
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, f"采购单 {buy_id} 创建成功"
    except Exception as e:
        return False, str(e)

def update_buy_node(buy_id, field, value):
    try:
        nodes = ['is_source_confirmed', 'is_ordered', 'is_instock', 'is_shipped']
        if field not in nodes:
            return False, "非法节点字段"
        
        sql = f"UPDATE uni_buy SET {field} = ? WHERE buy_id = ?"
        with get_db_connection() as conn:
            conn.execute(sql, (int(value), buy_id))
            conn.commit()
            return True, "节点更新成功"
    except Exception as e:
        return False, str(e)

def update_buy(buy_id, data):
    try:
        # Re-calculate total_amount if price or qty changed
        if 'buy_price_rmb' in data or 'buy_qty' in data:
            with get_db_connection() as conn:
                current = conn.execute("SELECT buy_price_rmb, buy_qty FROM uni_buy WHERE buy_id = ?", (buy_id,)).fetchone()
                price = float(data.get('buy_price_rmb', current['buy_price_rmb']))
                qty = int(data.get('buy_qty', current['buy_qty']))
                data['total_amount'] = round(price * qty, 2)

        set_cols = []
        params = []
        for k, v in data.items():
            set_cols.append(f"{k} = ?")
            params.append(v)
        if not set_cols: return True, "No changes"
        
        sql = f"UPDATE uni_buy SET {', '.join(set_cols)} WHERE buy_id = ?"
        params.append(buy_id)
        
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, "更新成功"
    except Exception as e:
        return False, str(e)

def delete_buy(buy_id):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM uni_buy WHERE buy_id = ?", (buy_id,))
            conn.commit()
            return True, "删除成功"
    except Exception as e:
        return False, str(e)
