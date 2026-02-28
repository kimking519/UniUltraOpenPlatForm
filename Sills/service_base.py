# -*- coding: utf-8 -*-
"""
业务服务基类
提供通用的 CRUD 操作方法
"""

from Sills.base import get_db_connection


class BaseService:
    """服务基类，提供通用 CRUD 方法"""

    table_name = None
    primary_key = None

    def get_by_id(self, id_value, conn=None):
        """根据主键获取单条记录"""
        close = False
        if conn is None:
            conn = get_db_connection()
            close = True
        try:
            row = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = ?",
                (id_value,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            if close:
                conn.close()

    def create(self, data, conn=None):
        """创建记录"""
        close = False
        if conn is None:
            conn = get_db_connection()
            close = True
        try:
            columns = list(data.keys())
            placeholders = [f"? " for _ in columns]
            values = list(data.values())

            sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            conn.execute(sql, values)
            if close:
                conn.commit()
            return True, "创建成功"
        except Exception as e:
            if not close:
                raise
            return False, str(e)
        finally:
            if close:
                conn.close()

    def update(self, id_value, data, conn=None):
        """更新记录"""
        close = False
        if conn is None:
            conn = get_db_connection()
            close = True
        try:
            set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
            values = list(data.values()) + [id_value]

            sql = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.primary_key} = ?"
            conn.execute(sql, values)
            if close:
                conn.commit()
            return True, "更新成功"
        except Exception as e:
            if not close:
                raise
            return False, str(e)
        finally:
            if close:
                conn.close()

    def delete(self, id_value, conn=None):
        """删除记录"""
        close = False
        if conn is None:
            conn = get_db_connection()
            close = True
        try:
            sql = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = ?"
            conn.execute(sql, (id_value,))
            if close:
                conn.commit()
            return True, "删除成功"
        except Exception as e:
            if not close:
                raise
            return False, str(e)
        finally:
            if close:
                conn.close()
