# UniUltra 开放平台 - 数据库表结构

本文档记录系统所有数据库表结构。

---

## 员工表 (uni_emp)

| 字段 | 类型 | 说明 |
|------|------|------|
| emp_id | TEXT | 员工编号 (主键) |
| emp_name | TEXT | 员工姓名 |
| emp_email | TEXT | 邮箱 |
| emp_phone | TEXT | 电话 |
| emp_role | TEXT | 角色 |
| rule | INTEGER | 权限等级 (0=销售，1=只读，3=管理，4=禁用) |
| created_at | DATETIME | 创建时间 |

---

## 客户表 (uni_cli)

| 字段 | 类型 | 说明 |
|------|------|------|
| cli_id | TEXT | 客户编号 (主键) |
| cli_name | TEXT | 客户名称 |
| cli_contact | TEXT | 联系人 |
| cli_phone | TEXT | 联系电话 |
| cli_email | TEXT | 联系邮箱 |
| cli_address | TEXT | 地址 |
| created_at | DATETIME | 创建时间 |

---

## 供应商表 (uni_vendor)

| 字段 | 类型 | 说明 |
|------|------|------|
| vendor_id | TEXT | 供应商编号 (主键) |
| vendor_name | TEXT | 供应商名称 |
| vendor_contact | TEXT | 联系人 |
| vendor_phone | TEXT | 联系电话 |
| vendor_email | TEXT | 联系邮箱 |
| vendor_address | TEXT | 地址 |
| created_at | DATETIME | 创建时间 |

---

## 需求表 (uni_quote)

| 字段 | 类型 | 说明 |
|------|------|------|
| quote_id | TEXT | 需求编号 (主键) |
| cli_id | TEXT | 客户编号 |
| part_number | TEXT | 型号 |
| quantity | INTEGER | 数量 |
| price_usd | DECIMAL | 美元价格 |
| price_krw | DECIMAL | 韩元价格 |
| currency | INTEGER | 货币代码 (1=USD, 2=KRW) |
| status | TEXT | 状态 (询价中/缺货/已报价) |
| emp_id | TEXT | 负责人 |
| remark | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| transfer_status | INTEGER | 转单状态 (0=未转，1=处理中，2=已转) |

---

## 报价表 (uni_offer)

| 字段 | 类型 | 说明 |
|------|------|------|
| offer_id | TEXT | 报价编号 (主键) |
| quote_id | TEXT | 原需求编号 |
| cli_id | TEXT | 客户编号 |
| part_number | TEXT | 型号 |
| quantity | INTEGER | 数量 |
| price_usd | DECIMAL | 美元价格 |
| price_krw | DECIMAL | 韩元价格 |
| currency | INTEGER | 货币代码 |
| status | TEXT | 状态 |
| emp_id | TEXT | 负责人 |
| remark | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| transfer_status | INTEGER | 转单状态 |

---

## 销售订单表 (uni_order)

| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | TEXT | 订单编号 (主键) |
| offer_id | TEXT | 原报价编号 |
| cli_id | TEXT | 客户编号 |
| part_number | TEXT | 型号 |
| quantity | INTEGER | 数量 |
| paid_amount | DECIMAL | 已付金额 |
| status | TEXT | 订单状态 |
| node1 | INTEGER | 节点 1 状态 |
| node2 | INTEGER | 节点 2 状态 |
| node3 | INTEGER | 节点 3 状态 |
| node4 | INTEGER | 节点 4 状态 |
| node5 | INTEGER | 节点 5 状态 |
| emp_id | TEXT | 负责人 |
| remark | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| transfer_status | INTEGER | 转单状态 |

---

## 采购表 (uni_buy)

| 字段 | 类型 | 说明 |
|------|------|------|
| buy_id | TEXT | 采购编号 (主键) |
| order_id | TEXT | 原订单编号 |
| vendor_id | TEXT | 供应商编号 |
| part_number | TEXT | 型号 |
| quantity | INTEGER | 数量 |
| price | DECIMAL | 采购价格 |
| node1 | INTEGER | 节点 1 状态 |
| node2 | INTEGER | 节点 2 状态 |
| node3 | INTEGER | 节点 3 状态 |
| node4 | INTEGER | 节点 4 状态 |
| node5 | INTEGER | 节点 5 状态 |
| emp_id | TEXT | 负责人 |
| remark | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |

---

## 动态参数表 (uni_daily)

| 字段 | 类型 | 说明 |
|------|------|------|
| record_id | TEXT | 记录编号 (主键) |
| currency_code | INTEGER | 货币代码 (1=USD, 2=KRW) |
| exchange_rate | DECIMAL | 汇率 |
| record_date | DATE | 记录日期 |
| remark | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |

---

## 索引

| 表名 | 索引字段 | 说明 |
|------|----------|------|
| uni_daily | currency_code, record_date | 汇率查询优化 |
| uni_quote | cli_id, emp_id | 客户/负责人查询优化 |
| uni_offer | quote_id, cli_id | 联表查询优化 |
| uni_order | offer_id, cli_id | 联表查询优化 |
| uni_buy | order_id, vendor_id | 联表查询优化 |

---

## 数据流程

```
uni_cli (客户)
    ↓
uni_quote (需求) → transfer_status → uni_offer (报价)
                                       ↓
                                    transfer_status → uni_order (订单)
                                                         ↓
                                                      transfer_status → uni_buy (采购)
```

---

## 备注

- 所有表使用 `created_at` 记录创建时间
- 主键使用 TEXT 类型，便于自定义编号
- `transfer_status` 字段用于追踪转单状态
- 汇率表 `uni_daily` 支持多记录，按日期 DESC 取最新
