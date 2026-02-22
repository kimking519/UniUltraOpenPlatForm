import sqlite3
import uuid
from datetime import datetime
from Sills.base import get_db_connection

def get_quote_list(page=1, page_size=10, search_kw=""):
    offset = (page - 1) * page_size
    query = """
    SELECT q.*, c.cli_name, 
           (COALESCE(q.quoted_mpn, '') || ' | ' || 
            COALESCE(q.inquiry_brand, '') || ' | ' || 
            COALESCE(CAST(q.inquiry_qty AS TEXT), '') || ' | ' || 
            COALESCE(q.remark, '')) as combined_info
    FROM uni_quote q
    LEFT JOIN uni_cli c ON q.cli_id = c.cli_id
    WHERE q.inquiry_mpn LIKE ? OR q.quote_id LIKE ? OR c.cli_name LIKE ?
    ORDER BY q.created_at DESC
    LIMIT ? OFFSET ?
    """
    count_query = """
    SELECT COUNT(*) 
    FROM uni_quote q
    LEFT JOIN uni_cli c ON q.cli_id = c.cli_id
    WHERE q.inquiry_mpn LIKE ? OR q.quote_id LIKE ? OR c.cli_name LIKE ?
    """
    params = (f"%{search_kw}%", f"%{search_kw}%", f"%{search_kw}%")
    
    with get_db_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        items = conn.execute(query, params + (page_size, offset)).fetchall()
        
        results = [
            {k: ("" if v is None else v) for k, v in dict(row).items()}
            for row in items
        ]
        return results, total

def add_quote(data):
    try:
        quote_id = "Q" + datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:4]
        quote_date = datetime.now().strftime("%Y-%m-%d")
        
        sql = """
        INSERT INTO uni_quote (quote_id, quote_date, cli_id, inquiry_mpn, quoted_mpn, inquiry_brand, inquiry_qty, target_price_rmb, cost_price_rmb, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            quote_id,
            quote_date,
            data.get('cli_id'),
            data.get('inquiry_mpn'),
            data.get('quoted_mpn', ''),
            data.get('inquiry_brand', ''),
            data.get('inquiry_qty', 0),
            data.get('target_price_rmb', 0.0),
            data.get('cost_price_rmb', 0.0),
            data.get('remark', '')
        )
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, f"需求 {quote_id} 创建成功"
    except Exception as e:
        return False, str(e)

def update_quote(quote_id, data):
    try:
        set_cols = []
        params = []
        for k, v in data.items():
            set_cols.append(f"{k} = ?")
            params.append(v)
        if not set_cols: return True, "No changes"
        
        sql = f"UPDATE uni_quote SET {', '.join(set_cols)} WHERE quote_id = ?"
        params.append(quote_id)
        
        with get_db_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
            return True, "更新成功"
    except Exception as e:
        return False, str(e)

def delete_quote(quote_id):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM uni_quote WHERE quote_id = ?", (quote_id,))
            conn.commit()
            return True, "删除成功"
    except Exception as e:
        return False, str(e)
