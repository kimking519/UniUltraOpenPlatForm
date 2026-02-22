---
name: sale-input-needs
description: 自动根据聊天记录提取电子零组件采购需求并录入到 UniUltra 平台的“需求管理”模块。
---

# Skill: sale-input-needs

这个 Skill 旨在协助销售人员快速从分散的聊天记录、邮件或口头描述中提取结构化的电子元组件需求，并利用系统的 API 自动将其录入到 `uni_quote`（需求管理）表中。

## 指令建议

当用户提供类似于“帮我把这些录进去：客户 C001 要 1000 个 STM32F103C8T6，品牌 st，目标价 5 块左右，备注急需”的信息时，你应该启动此 Skill。

## 处理流程

1. **信息提取**：从用户的原始输入中识别出以下关键字段：
   - `cli_id` (客户 ID，必填)
   - `inquiry_mpn` (询价型号，必填)
   - `inquiry_brand` (品牌)
   - `inquiry_qty` (数量)
   - `target_price_rmb` (客户目标单价)
   - `remark` (备注)

2. **数据标准化**：
   - 型号应转换为大写（如 `stm32` -> `STM32`）。
   - 数量应转换为整数。
   - 价格应转换为浮点数。

3. **执行录入**：
   - 你可以使用 `run_command` 调用 Python 脚本或直接利用 `curl` 请求平台的 `/quote/add` 接口（如果已知本地地址为 `http://127.0.0.1:8000`）。
   - 或者，更优雅的方式是通过 `batch_import_quote_text` 逻辑，构造 CSV 格式的文本进行批量导入。

## 系统映射参考 (uni_quote 表)

| 字段名 | 含义 | 类型 | 录入建议 |
| :--- | :--- | :--- | :--- |
| `cli_id` | 客户编号 | TEXT | 必须匹配 `uni_cli` 中的 ID |
| `inquiry_mpn` | 询价型号 | TEXT | 原始型号 |
| `inquiry_brand` | 品牌 | TEXT | 建议大写 |
| `inquiry_qty` | 数量 | INTEGER | 默认 0 |
| `target_price_rmb`| 目标价 | REAL | 默认 0.0 |
| `remark` | 备注 | TEXT | 来源或特殊要求 |

## 示例脚本 (scripts/auto_input.py)

你可以调用预置在 `scripts/` 下的脚本来执行动作。

```python
# 示例调用
python scripts/auto_input.py --cli_id "C001" --mpn "TPS54331DR" --qty 500
```

## 注意事项

- **多项录入**：如果对话中包含多个型号，应逐一提取并批量导入。
- **校验**：录入前应确认 `cli_id` 是否存在（可以通过搜索 `uni_cli` 表确认）。
- **反馈**：录入成功后，向用户反馈已生成的“需求编号”（格式如 Q20260223...）。
