---
name: 保险周报装配技能
description: 汇聚各模块分析结果（数据加载、KPI、趋势、组织下钻、新能源专题），装配为完整的中文周报内容。
author: 保险数据团队
tags:
  - 周报装配
  - 汇总
version: 2.0.0
---

# 技能规范（最佳实践版）

## 输入参数
- `modules`：各分析模块的结果字典，键包含 `data_loader`、`kpi`、`trend`、`org_drill`、`new_energy` 等。
- `week_no`：周次编号；`version`：报告版本号。

## 输出
- 完整中文周报Markdown文本：概览、指标、趋势、下钻、专题、建议与行动项。

## 流程
1. 校验模块结果的存在与结构。
2. 统一卡片化格式输出各模块要点。
3. 组装建议与行动项；附版本与口径说明。

## 代码模板（含函数级中文注释）

```python
def assemble_insurance_weekly_report(modules: dict, week_no: int, version: str = 'v1') -> str:
    """
    函数用途：将各分析模块结果装配为完整中文周报文本
    参数说明：
    - modules: 分析结果字典，包含多个模块的结构化输出
    - week_no: 周次编号
    - version: 报告版本号
    返回结果：Markdown格式的周报文本
    """
    parts = []
    parts.append(f"# 周报概览（周次：{week_no}，版本：{version}）\n")
    if 'kpi' in modules:
        parts.append("## 关键指标\n\n" + str(modules['kpi']))
    if 'trend' in modules:
        parts.append("## 损失趋势\n\n" + str(modules['trend']))
    if 'org_drill' in modules:
        parts.append("## 组织维度下钻\n\n" + str(modules['org_drill']))
    if 'new_energy' in modules:
        parts.append("## 新能源专题\n\n" + str(modules['new_energy']))
    parts.append("## 建议与行动项\n\n- [ ] 明确责任人与完成期限\n")
    parts.append("## 数据口径与版本\n\n- 统一字段定义与统计口径\n")
    return "\n\n".join(parts)
```

## 版本与维护
- v2.0.0：统一结构、中文注释与装配规范。