# -*- coding: utf-8 -*-
"""
重构验证测试脚本
用于测试重构后的系统各模块是否正常工作
"""

def test_constants():
    """测试常量模块"""
    print("测试常量模块...")
    from Sills.constants import (
        CURRENCY_USD, CURRENCY_KRW,
        DEFAULT_RATE_USD, DEFAULT_RATE_KRW,
        RULE_SALES, RULE_READ_ONLY, RULE_ADMIN, RULE_DISABLED,
        STATUS_QUOTE_INQUIRY, STATUS_QUOTE_QUOTED
    )

    assert CURRENCY_USD == 1, "USD 货币代码应为 1"
    assert CURRENCY_KRW == 2, "KRW 货币代码应为 2"
    assert DEFAULT_RATE_USD == 7.0, "默认美元汇率应为 7.0"
    assert DEFAULT_RATE_KRW == 180.0, "默认韩元汇率应为 180.0"
    print("  [PASS]")


def test_service_base():
    """测试服务基类"""
    print("测试服务基类...")
    from Sills.service_base import BaseService

    class TestService(BaseService):
        table_name = "uni_emp"
        primary_key = "emp_id"

    service = TestService()
    assert service.table_name == "uni_emp"
    assert service.primary_key == "emp_id"
    print("  [PASS]")


def test_exchange_rate_service():
    """测试汇率服务"""
    print("测试汇率服务...")
    from Sills.services.exchange_rate_service import ExchangeRateService
    from Sills.constants import CURRENCY_USD, CURRENCY_KRW

    # 测试获取汇率（优先使用数据库中的值，如果为空则使用默认值）
    rate_usd = ExchangeRateService.get_latest_rate(CURRENCY_USD)
    rate_krw = ExchangeRateService.get_latest_rate(CURRENCY_KRW)

    # 验证汇率值在合理范围内（数据库中的实际值或默认值）
    assert 6.0 <= rate_usd <= 8.0, f"美元汇率 {rate_usd} 不在合理范围内 (6.0-8.0)"
    assert 150.0 <= rate_krw <= 250.0, f"韩元汇率 {rate_krw} 不在合理范围内 (150.0-250.0)"

    # 测试价格计算（使用实际获取的汇率）
    price_krw = ExchangeRateService.calculate_price(100, CURRENCY_KRW)
    expected_krw = round(100 * rate_krw, 2)
    assert price_krw == expected_krw, f"韩币价格计算错误：期望 {expected_krw}, 得到 {price_krw}"

    print(f"  [PASS] (USD: {rate_usd}, KRW: {rate_krw})")


def test_routes_import():
    """测试路由模块导入"""
    print("测试路由模块导入...")
    # 路由模块暂未拆分，此测试跳过
    print("  [SKIP] 路由模块暂未拆分")


def test_main_app():
    """测试主应用"""
    print("测试主应用...")
    import main

    assert main.app is not None, "FastAPI 应用应为非空"
    assert main.templates is not None, "模板引擎应为非空"
    print("  [PASS]")


def test_database():
    """测试数据库连接"""
    print("测试数据库连接...")
    from Sills.base import get_db_connection, init_db

    # 初始化数据库
    init_db()

    # 测试连接
    with get_db_connection() as conn:
        # 检查表是否存在
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t['name'] for t in tables]

        expected_tables = ['uni_emp', 'uni_cli', 'uni_vendor', 'uni_quote',
                          'uni_offer', 'uni_order', 'uni_buy', 'uni_daily']

        for table in expected_tables:
            assert table in table_names, f"表 {table} 应存在"

    print("  [PASS]")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("UniUltra ERP 重构验证测试")
    print("=" * 50)

    tests = [
        test_constants,
        test_service_base,
        test_exchange_rate_service,
        test_routes_import,
        test_main_app,
        test_database
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            test()
            passed += 1
            print("  [PASS]")
        except AssertionError as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {test.__name__}: {e}")
            failed += 1

    print("=" * 50)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
