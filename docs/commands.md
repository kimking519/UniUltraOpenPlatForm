# UniUltra 开放平台 - API 端点和命令汇总

本文档记录系统所有 API 端点和命令。

---

## 认证相关

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /login | 登录页面 |
| POST | /login | 执行登录 |
| GET | /logout | 退出登录 |
| POST | /change-password | 修改密码 |

---

## 仪表板

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | / | 首页仪表板 |

---

## 动态参数 (汇率)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /daily | 汇率列表页面 |
| POST | /daily/add | 添加汇率记录 |
| POST | /api/daily/update | 更新汇率记录 |

---

## 员工管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /emp | 员工列表页面 |
| POST | /emp/add | 添加员工 |
| POST | /api/emp/update | 更新员工 |
| POST | /api/emp/delete | 删除员工 |
| POST | /api/emp/batch-delete | 批量删除员工 |
| POST | /api/emp/import | 批量导入员工 |

---

## 客户管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /cli | 客户列表页面 |
| POST | /cli/add | 添加客户 |
| POST | /api/cli/update | 更新客户 |
| POST | /api/cli/delete | 删除客户 |
| POST | /api/cli/batch-delete | 批量删除客户 |
| POST | /api/cli/import | 批量导入客户 |
| POST | /api/cli/export_csv | 导出客户 CSV |

---

## 供应商管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /vendor | 供应商列表页面 |
| POST | /vendor/add | 添加供应商 |
| POST | /api/vendor/update | 更新供应商 |
| POST | /api/vendor/delete | 删除供应商 |
| POST | /api/vendor/batch-delete | 批量删除供应商 |
| POST | /api/vendor/import | 批量导入供应商 |

---

## 需求管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /quote | 需求列表页面 |
| POST | /quote/add | 添加需求 |
| POST | /api/quote/update | 更新需求 |
| POST | /api/quote/delete | 删除需求 |
| POST | /api/quote/batch-delete | 批量删除需求 |
| POST | /api/quote/batch-copy | 批量复制需求 |
| POST | /api/quote/import | 批量导入需求 |
| POST | /api/quote/convert-to-offer | 需求转报价 |
| POST | /api/quote/export_offer_csv | 导出报价 CSV |

---

## 报价管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /offer | 报价列表页面 |
| POST | /offer/add | 添加报价 |
| POST | /api/offer/update | 更新报价 |
| POST | /api/offer/delete | 删除报价 |
| POST | /api/offer/batch-delete | 批量删除报价 |
| POST | /api/offer/import | 批量导入报价 |
| POST | /api/offer/convert-to-order | 报价转订单 |
| POST | /api/offer/export_excel | 导出 Excel |
| POST | /api/offer/batch_send_email | 批量发送邮件 |

---

## 销售订单

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /order | 订单列表页面 |
| POST | /order/add | 添加订单 |
| POST | /api/order/update | 更新订单 |
| POST | /api/order/update-node | 更新节点状态 |
| POST | /api/order/delete | 删除订单 |
| POST | /api/order/batch-delete | 批量删除订单 |
| POST | /api/order/import | 批量导入订单 |
| POST | /api/order/convert-from-offer | 报价转订单 |
| POST | /api/order/export_csv | 导出 CSV |
| POST | /api/order/batch_to_buy | 订单转采购 |

---

## 采购管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /buy | 采购列表页面 |
| POST | /buy/add | 添加采购 |
| POST | /api/buy/update | 更新采购 |
| POST | /api/buy/update-node | 更新节点状态 |
| POST | /api/buy/delete | 删除采购 |
| POST | /api/buy/batch-delete | 批量删除采购 |
| POST | /api/buy/import | 批量导入采购 |
| POST | /api/buy/export_csv | 导出 CSV |

---

## 系统设置

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /settings | 设置页面 |
| POST | /api/backup | 备份数据库 |

---

## 工作流

```
需求 (quote) → 报价 (offer) → 销售订单 (order) → 采购 (buy)
```

### 转单流程

1. **需求 → 报价**: 选择需求记录，点击"转报价"按钮
2. **报价 → 订单**: 选择报价记录，点击"转订单"按钮
3. **订单 → 采购**: 选择订单记录，点击"转采购"按钮

---

## 环境切换

系统支持开发环境和正式环境切换，通过 cookie `app_env` 控制：
- `dev`: 开发环境
- `prod`: 正式环境

---

## 权限等级

| 等级 | 代码 | 说明 |
|------|------|------|
| 销售 | 0 | 可编辑业务数据 |
| 只读 | 1 | 仅查看权限 |
| 管理 | 3 | 完全权限 |
| 禁用 | 4 | 禁止访问 |

---

## 数据导出格式

| 模块 | 格式 | 说明 |
|------|------|------|
| 客户 | CSV | 包含所有字段 |
| 供应商 | CSV | 包含所有字段 |
| 需求 | CSV/Excel | 可导出为报价格式 |
| 报价 | Excel | 包含价格详情 |
| 订单 | CSV | 包含状态信息 |
| 采购 | CSV | 包含节点状态 |
