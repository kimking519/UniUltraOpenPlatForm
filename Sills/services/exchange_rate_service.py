# -*- coding: utf-8 -*-
"""
汇率服务
提供汇率查询和价格计算功能
"""

from Sills.base import get_db_connection
from Sills.constants import CURRENCY_USD, CURRENCY_KRW, DEFAULT_RATE_USD, DEFAULT_RATE_KRW


class ExchangeRateService:
    """汇率服务类"""

    @staticmethod
    def get_latest_rate(currency_code, conn=None):
        """
        获取最新汇率

        Args:
            currency_code: 货币代码（1=USD, 2=KRW）
            conn: 数据库连接（可选，用于事务控制）

        Returns:
            最新汇率值（数据库为空时返回默认值）
        """
        close = False
        if conn is None:
            conn = get_db_connection()
            close = True
        try:
            row = conn.execute(
                "SELECT exchange_rate FROM uni_daily WHERE currency_code=? ORDER BY record_date DESC LIMIT 1",
                (currency_code,)
            ).fetchone()
            if row:
                return float(row[0])
            # 数据库为空时返回默认值
            return DEFAULT_RATE_USD if currency_code == CURRENCY_USD else DEFAULT_RATE_KRW
        finally:
            if close:
                conn.close()

    @staticmethod
    def calculate_price(rmb_amount, currency_code, conn=None):
        """
        根据汇率计算外币价格

        Args:
            rmb_amount: 人民币金额
            currency_code: 货币代码
            conn: 数据库连接（可选）

        Returns:
            外币价格（保留 2 位小数）
        """
        rate = ExchangeRateService.get_latest_rate(currency_code, conn)
        return round(rmb_amount * rate, 2)
