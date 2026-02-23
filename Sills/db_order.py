import sqlite3
import uuid
from datetime import datetime
from Sills.base import get_db_connection

def get_order_list(page=1, page_size=10, search_kw="", cli_id="", start_date="", end_date="", is_finished=""):
    offset = (page - 1) * page_size
    query = """
    FROM uni_order o
    JOIN uni_cli c ON o.cli_id = c.cli_id
    LEFT JOIN uni_offer off ON o.offer_id = off.offer_id
    WHERE (o.inquiry_mpn LIKE ? OR o.order_id LIKE ? OR c.cli_name LIKE ?)
    """
    params = [f"%{search_kw}%", f"%{search_kw}%", f"%{search_kw}%"]
    
    if cli_id:
        query += " AND o.cli_id = ?"
        params.append(cli_id)
    if start_date:
        query += " AND o.order_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND o.order_date <= ?"
        params.append(end_date)
    if is_finished in ('0', '1'):
        query += " AND o.is_finished = ?"
        params.append(int(is_finished))

    count_sql = "SELECT COUNT(*) " + query
    data_sql = "SELECT o.*, c.cli_name, c.margin_rate, off.quoted_mpn, off.offer_price_rmb " + query + " ORDER BY o.order_date DESC, o.created_at DESC LIMIT ? OFFSET ?"
    params_with_limit = params + [page_size, offset]

    with get_db_connection() as conn:
        total = conn.execute(count_sql, params).fetchone()[0]
        rows = conn.execute(data_sql, params_with_limit).fetchall()
        
        results = [dict(r) for r in rows]
        
        try:
            rate_krw = conn.execute("SELECT exchange_rate FROM uni_daily WHERE currency_code=2 ORDER BY record_date DESC LIMIT 1").fetchone()
            rate_usd = conn.execute("SELECT exchange_rate FROM uni_daily WHERE currency_code=1 ORDER BY record_date DESC LIMIT 1").fetchone()
            krw_val = float(rate_krw[0]) if rate_krw else 180.0
            usd_val = float(rate_usd[0]) if rate_usd else 7.0
            
            for r in results:
                price = r.get('offer_price_rmb') or r.get('sales_price_rmb') or 0.0
                margin = float(r.get('margin_rate') or 0.0)
                final_price = float(price) * (1 + margin / 100.0)
                
                if krw_val > 10: r['price_kwr'] = round(final_price * krw_val, 2)
                else: r['price_kwr'] = round(final_price / krw_val, 2) if krw_val else 0.0
                    
                if usd_val > 10: r['price_usd'] = round(final_price * usd_val, 2)
                else: r['price_usd'] = round(final_price / usd_val, 2) if usd_val else 0.0
        except Exception as e:
            for r in results:
                r['price_kwr'] = 0.0
                r['price_usd'] = 0.0

    return results, total

def add_order(data, conn=None):
    try:
        order_id = data.get('order_id')
        if not order_id:
            hex_str = str(uuid.uuid4().hex)
            order_id = "SO" + datetime.now().strftime("%Y%m%d%H%M%S") + hex_str[:4]
        
        # Validation Logic
        must_close = False
        if conn is None:
            conn = get_db_connection()
            must_close = True

        try:
            # Check uniqueness
            existing = conn.execute("SELECT order_id FROM uni_order WHERE order_id = ?", (order_id,)).fetchone()
            if existing:
                return False, f"订单编号 {order_id} 已存在"

            cli_id = data.get('cli_id')
            if not cli_id or str(cli_id).strip() == "":
                return False, "缺少客户编号"
            
            # Check Cli
            cli = conn.execute("SELECT cli_id FROM uni_cli WHERE cli_id = ?", (cli_id,)).fetchone()
            if not cli:
                return False, f"客户编号 {cli_id} 在数据库中不存在"

            offer_id = data.get('offer_id')
            if not offer_id or str(offer_id).strip() == "":
                offer_id = None
            
            # Check Offer
            if offer_id:
                off = conn.execute("SELECT offer_id FROM uni_offer WHERE offer_id = ?", (offer_id,)).fetchone()
                if not off:
                    return False, f"关联报价单 {offer_id} 不存在"

            order_date = data.get('order_date') or datetime.now().strftime("%Y-%m-%d")
            
            paid_amount = 0.0
            try: paid_amount = float(data.get('paid_amount') or 0.0)
            except: pass

            sql = """
            INSERT INTO uni_order (
                order_id, order_date, cli_id, offer_id, inquiry_mpn, inquiry_brand, is_finished, is_paid, paid_amount, remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                order_id, order_date, cli_id, offer_id,
                data.get('inquiry_mpn'), data.get('inquiry_brand'),
                int(data.get('is_finished', 0)),
                int(data.get('is_paid', 0)),
                paid_amount,
                data.get('remark', '')
            )
            conn.execute(sql, params)
            if must_close:
                conn.commit()
            return True, f"销售订单 {order_id} 创建成功"
        finally:
            if must_close:
                conn.close()
    except Exception as e:
        return False, f"数据库错误: {str(e)}"

def batch_import_order(text, cli_id):
    import io, csv
    f = io.StringIO(text.strip())
    reader = csv.reader(f)
    success_count = 0
    errors = []
    
    try:
        rows = list(reader)
        if not rows: return 0, []
        start_idx = 0
        if len(rows[0]) > 0 and ("报价编号" in rows[0][0] or "型号" in str(rows[0])):
            start_idx = 1
            
        with get_db_connection() as conn:
            for row in rows[start_idx:]:
                if not row or len(row) < 1: continue
                try:
                    offer_id = row[0] if len(row) > 0 and str(row[0]).strip() != "" else None
                    if offer_id and not str(offer_id).startswith('O'):
                        offer_id = None
                    
                    data = {
                        "cli_id": cli_id,
                        "offer_id": offer_id,
                        "inquiry_mpn": row[4] if len(row) > 4 and row[4] else (row[3] if len(row) > 3 else ""),
                        "inquiry_brand": row[6] if len(row) > 6 and row[6] else (row[5] if len(row) > 5 else ""),
                        "remark": row[17] if len(row) > 17 else ""
                    }
                    if not data["offer_id"] and not data["inquiry_mpn"]:
                        continue
                        
                    ok, msg = add_order(data, conn=conn)
                    if ok: success_count += 1
                    else: errors.append(msg)
                except Exception as e:
                    errors.append(f"行解析失败: {str(e)}")
            
            if success_count > 0:
                conn.commit()
    except Exception as e:
        errors.append(f"导入失败: {str(e)}")
            
    return success_count, errors

def batch_convert_from_offer(offer_ids, cli_id=None):
    if not offer_ids: return False, "未选中记录"
    try:
        success_count = 0
        errors = []
        with get_db_connection() as conn:
            placeholders = ','.join(['?'] * len(offer_ids))
            rows = conn.execute(f"SELECT * FROM uni_offer WHERE offer_id IN ({placeholders})", offer_ids).fetchall()
            
            for row in rows:
                offer_data = dict(row)
                existing = conn.execute("SELECT order_id FROM uni_order WHERE offer_id = ?", (offer_data['offer_id'],)).fetchone()
                if existing:
                    errors.append(f"{offer_data['offer_id']}: 已存在销售订单")
                    continue
                
                final_cli_id = cli_id
                if not final_cli_id:
                    quote_info = conn.execute("SELECT cli_id FROM uni_quote WHERE quote_id = ?", (offer_data['quote_id'],)).fetchone()
                    if quote_info:
                        final_cli_id = quote_info['cli_id']
                
                if not final_cli_id:
                    errors.append(f"{offer_data['offer_id']}: 无法确定客户ID")
                    continue

                data = {
                    "cli_id": final_cli_id,
                    "offer_id": offer_data['offer_id'],
                    "inquiry_mpn": offer_data['quoted_mpn'] or offer_data['inquiry_mpn'],
                    "inquiry_brand": offer_data['quoted_brand'] or offer_data['inquiry_brand'],
                    "remark": offer_data['remark']
                }
                
                ok, msg = add_order(data, conn=conn)
                if ok: success_count += 1
                else: errors.append(msg)
            
            if success_count > 0:
                conn.commit()
                
        if success_count == 0 and errors:
            return False, errors[0]
        return True, f"成功转换 {success_count} 条记录" + (f" (失败 {len(errors)} 条)" if errors else "")
    except Exception as e:
        return False, str(e)

def batch_delete_order(order_ids):
    if not order_ids: return True, "无选中记录"
    try:
        with get_db_connection() as conn:
            placeholders = ','.join(['?'] * len(order_ids))
            conn.execute(f"DELETE FROM uni_order WHERE order_id IN ({placeholders})", order_ids)
            conn.commit()
            return True, "批量删除成功"
    except Exception as e:
        if "FOREIGN KEY constraint failed" in str(e):
            return False, "删除失败：部分记录已被[采购记录]引用，无法直接删除。"
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
        if "FOREIGN KEY constraint failed" in str(e):
            return False, "删除失败：记录已被[采购记录]引用，无法直接删除。"
        return False, str(e)
