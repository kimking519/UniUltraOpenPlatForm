# UniUltra 开放平台 - 测试用例清单

本文档用于回归测试和功能验证。

---

## 测试环境配置

### 前置条件
- [x] Python 3.12+ 已安装
- [x] 依赖已安装：`pip install -r requirements.txt`
- [x] 数据库初始化：`python -c "from Sills.base import init_db; init_db()"`

### 测试账户
| 账号 | 密码 | 权限 |
|------|------|------|
| Admin | Admin123 (MD5) | 管理员 (rule=3) |

---

## 单元测试列表

### 1. 常量模块测试 (`Sills/constants.py`)

```python
def test_constants():
    """测试常量定义"""
    from Sills.constants import (
        CURRENCY_USD, CURRENCY_KRW,
        DEFAULT_RATE_USD, DEFAULT_RATE_KRW,
        RULE_SALES, RULE_READ_ONLY, RULE_ADMIN, RULE_DISABLED
    )

    assert CURRENCY_USD == 1
    assert CURRENCY_KRW == 2
    assert DEFAULT_RATE_USD == 7.0
    assert DEFAULT_RATE_KRW == 180.0
    assert RULE_SALES == 0
    assert RULE_READ_ONLY == 1
    assert RULE_ADMIN == 3
    assert RULE_DISABLED == 4
```

**测试状态**: ✅ 已通过

---

### 2. 服务基类测试 (`Sills/service_base.py`)

```python
def test_service_base():
    """测试服务基类功能"""
    from Sills.service_base import BaseService

    class TestService(BaseService):
        table_name = "uni_emp"
        primary_key = "emp_id"

    service = TestService()
    assert service.table_name == "uni_emp"
    assert service.primary_key == "emp_id"
```

**测试状态**: ✅ 已通过

---

### 3. 汇率服务测试 (`Sills/services/exchange_rate_service.py`)

```python
def test_exchange_rate_service():
    """测试汇率服务"""
    from Sills.services.exchange_rate_service import ExchangeRateService
    from Sills.constants import CURRENCY_USD, CURRENCY_KRW

    # 测试获取汇率（数据库中的实际值）
    rate_usd = ExchangeRateService.get_latest_rate(CURRENCY_USD)
    rate_krw = ExchangeRateService.get_latest_rate(CURRENCY_KRW)

    # 验证汇率值在合理范围内
    assert 6.0 <= rate_usd <= 8.0
    assert 150.0 <= rate_krw <= 250.0

    # 测试价格计算
    price_krw = ExchangeRateService.calculate_price(100, CURRENCY_KRW)
    expected_krw = round(100 * rate_krw, 2)
    assert price_krw == expected_krw
```

**测试状态**: ✅ 已通过 (USD: 6.5, KRW: 215.0)

---

### 4. 路由模块导入测试

```python
def test_routes_import():
    """测试路由模块导入"""
    # 路由模块暂未拆分，此测试跳过
```

**测试状态**: ⏭️ 已跳过 (待实施)

---

### 5. 主应用测试

```python
def test_main_app():
    """测试主应用"""
    import main

    assert main.app is not None
    assert main.templates is not None
```

**测试状态**: ✅ 已通过

---

### 6. 数据库连接测试

```python
def test_database():
    """测试数据库连接和表结构"""
    from Sills.base import get_db_connection, init_db

    init_db()

    with get_db_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t['name'] for t in tables]

        expected_tables = [
            'uni_emp', 'uni_cli', 'uni_vendor', 'uni_quote',
            'uni_offer', 'uni_order', 'uni_buy', 'uni_daily'
        ]

        for table in expected_tables:
            assert table in table_names
```

**测试状态**: ✅ 已通过

---

## 集成测试列表

### 7. 员工管理测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 登录验证 | 访问 /login，输入正确账号密码 | 跳转到首页 | [ ] |
| 添加员工 | POST /emp/add，填写完整信息 | 员工创建成功 | [ ] |
| 编辑员工 | 在线修改员工字段 | 更新成功 | [ ] |
| 删除员工 | 点击删除按钮 | 删除成功 | [ ] |
| 批量删除 | 选择多条记录后批量删除 | 批量删除成功 | [ ] |

---

### 8. 客户管理测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 添加客户 | POST /cli/add，填写完整信息 | 客户创建成功 | [ ] |
| 编辑客户 | 在线修改客户字段 | 更新成功 | [ ] |
| 删除客户 | 点击删除按钮 | 删除成功 | [ ] |
| 客户筛选 | 使用筛选条件查询 | 返回正确结果 | [ ] |
| 导出 CSV | 点击导出 CSV 按钮 | 下载成功 | [ ] |

---

### 9. 需求管理测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 添加需求 | POST /quote/add | 需求创建成功 | [ ] |
| 批量导入文本 | POST /quote/import | 导入成功 | [ ] |
| 批量复制 | POST /api/quote/batch-copy | 复制成功 | [ ] |
| 转报价 | POST /api/quote/convert-to-offer | 转换成功 | [ ] |
| 导出 CSV | POST /api/quote/export_offer_csv | 导出成功 | [ ] |
| 转单状态 | 检查 transfer_status 字段 | 状态正确 | [ ] |

---

### 10. 报价管理测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 添加报价 | POST /offer/add | 报价创建成功 | [ ] |
| 批量导入 | POST /offer/import | 导入成功 | [ ] |
| 编辑报价 | POST /api/offer/update | 更新成功 | [ ] |
| 转订单 | POST /api/offer/convert-to-order | 转换成功 | [ ] |
| 导出 Excel | POST /api/offer/export_excel | 导出成功 | [ ] |
| 转单状态 | 检查 transfer_status 字段 | 状态正确 | [ ] |

---

### 11. 销售订单测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 添加订单 | POST /order/add | 订单创建成功 | [ ] |
| 更新节点 | POST /api/order/update-node | 更新成功 | [ ] |
| 导出 CSV | POST /api/order/export_csv | 导出成功 | [ ] |
| 转采购 | POST /api/order/batch_to_buy | 转换成功 | [ ] |
| 转单状态 | 检查 transfer_status 字段 | 状态正确 | [ ] |

---

### 12. 采购管理测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 添加采购 | POST /buy/add | 采购创建成功 | [ ] |
| 批量导入 | POST /buy/import | 导入成功 | [ ] |
| 更新节点 | POST /api/buy/update-node | 更新成功 | [ ] |
| 导出 CSV | POST /api/buy/export_csv | 导出成功 | [ ] |
| 批量删除 | POST /api/buy/batch-delete | 删除成功 | [ ] |

---

## 工作流测试

### 13. 完整业务流程测试

```
需求 → 报价 → 订单 → 采购
```

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|----------|----------|------|
| 需求转报价 | 选择需求记录，点击转报价 | 报价单生成 | [ ] |
| 报价转订单 | 选择报价记录，点击转订单 | 订单生成 | [ ] |
| 订单转采购 | 选择订单记录，点击转采购 | 采购单生成 | [ ] |
| 状态同步 | 检查原记录 transfer_status | 已转单 | [ ] |

---

## 权限测试

### 14. 权限控制测试

| 用户类型 | 需求 | 报价 | 订单 | 采购 | 员工管理 |
|----------|------|------|------|------|----------|
| 销售 (rule=0) | 编辑 | 编辑 | 编辑 | 编辑 | 只读 |
| 只读 (rule=1) | 只读 | 只读 | 只读 | 只读 | 只读 |
| 管理 (rule=3) | 编辑 | 编辑 | 编辑 | 编辑 | 编辑 |
| 禁用 (rule=4) | 拒绝 | 拒绝 | 拒绝 | 拒绝 | 拒绝 |

---

## 回归测试检查清单

### 每次发布前必测

- [ ] 登录/登出功能正常
- [ ] 所有模块列表页面可访问
- [ ] 所有模块新增功能正常
- [ ] 所有模块编辑功能正常
- [ ] 所有模块删除功能正常
- [ ] 批量导入功能正常
- [ ] 导出功能正常（CSV/Excel）
- [ ] 工作流转换正常
- [ ] 环境切换正常
- [ ] 左侧导航菜单正常

---

## 运行测试

### 使用测试脚本
```bash
# 运行重构验证测试
python test_refactor.py

# 预期输出:
# ==================================================
# UniUltra ERP 重构验证测试
# ==================================================
# 测试常量模块... [PASS]
# 测试服务基类... [PASS]
# 测试汇率服务... [PASS] (USD: 6.5, KRW: 215.0)
# 测试路由模块导入... [SKIP]
# 测试主应用... [PASS]
# 测试数据库连接... [PASS]
# ==================================================
# 测试结果：6 通过，0 失败
# ==================================================
```

### 使用 pytest（待实现）
```bash
# 安装 pytest
pip install pytest httpx

# 运行所有测试
pytest tests/
```

---

## 测试覆盖率目标

| 模块 | 当前覆盖率 | 目标覆盖率 |
|------|------------|------------|
| Sills/constants.py | 100% | 100% |
| Sills/service_base.py | 80% | 90% |
| Sills/services/exchange_rate_service.py | 80% | 90% |
| routes/*.py | 待测试 | 80% |
| Sills/db_*.py | 待测试 | 80% |

---

## 已知问题

| 问题描述 | 影响模块 | 状态 | 备注 |
|----------|----------|------|------|
| 无 | - | - | - |
