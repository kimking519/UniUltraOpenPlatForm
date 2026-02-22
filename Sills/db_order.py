import sqlite3
import uuid
from datetime import datetime
from Sills.base import get_db_connection

def get_order_list(page=1, page_size=10, search_kw="", cli_id=""):
    offset = (page - 1) * page_size
    
    base_query = """
    FROM uni_order ord
    LEFT JOIN uni_cli c ON ord.cli_id = c.cli_id
    LEFT JOIN uni_offer o ON ord.offer_id = o.offer_id
    WHERE (ord.order_id LIKE ? OR c.cli_name LIKE ? OR o.inquiry_mpn LIKE ?)
    """
    params = [f"%{search_kw}%", f"%{search_kw}%", f"%{search_kw}%"]
    
    if cli_id:
        base_query += " AND ord.cli_id = ?"
        params.append(cli_id)
        
    query = f"""
    SELECT ord.*, c.cli_name, o.inquiry_mpn, o.quote_id
    {base_query}
    ORDER BY ord.created_at DESC
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

def add_order(data):
    try:
        hex_str = str(uuid.uuid4().hex)
        order_id = "SO" + datetime.now().strftime("%Y%m%d%H%M%S") + hex_str[:4]
        order_date = datetime.now().strftime("%Y-%m-%d")
        
        sql = """
        INSERT INTO uni_order (
            order_id, order_date, cli_id, offer_id, is_finished, is_paid, paid_amount, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            order_id,
            order_date,
            data.get('cli_id'),
            data.get('offer_id'),
            int(data.get('is_finished', 0)),
            int(data.get('is_paid', 0)),
            float(data.get('paid_amount', 0.0)),
            data.get('remark', '')
        )
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, f"销售订单 {order_id} 创建成功"
    except Exception as e:
        return False, str(e)

def update_order_status(order_id, field, value):
    try:
        if field not in ['is_finished', 'is_paid']:
            return False, "非法字段"
        
        sql = f"UPDATE uni_order SET {field} = ? WHERE order_id = ?"
        with get_db_connection() as conn:
            conn.execute(sql, (int(value), order_id))
            conn.commit()
            return True, "状态更新成功"
    except Exception as e:
        return False, str(e)

def update_order(order_id, data):
    try:
        set_cols = []
        params = []
        for k, v in data.items():
            set_cols.append(f"{k} = ?")
            params.append(v)
        if not set_cols: return True, "No changes"
        
        sql = f"UPDATE uni_order SET {', '.join(set_cols)} WHERE order_id = ?"
        params.append(order_id)
        
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, "更新成功"
    except Exception as e:
        return False, str(e)

def delete_order(order_id):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM uni_order WHERE order_id = ?", (order_id,))
            conn.commit()
            return True, "删除成功"
    except Exception as e:
        return False, str(e)
