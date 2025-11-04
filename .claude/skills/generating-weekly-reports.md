---
name: 周报生成技能（保险业务）
description: 汇总每周的业务数据与洞察，生成结构化中文周报，支持卡片、图表、建议与后续行动项。
author: 保险数据团队
tags:
  - 周报
  - 汇总
  - 保险
version: 2.0.0
---

# 技能规范（最佳实践版）

## 适用场景
- 每周定期输出中文周报：业务指标、损失趋势、车队画像、策略建议。
- 面向管理层与操作团队的统一汇总与决策支持文档。

## 输入参数
- `weekly_data`：结构化周度数据，含关键KPI与明细。
- `insights`：本周重点观察与结论（文本）。
- `recommendations`：建议与行动项（文本列表）。
- 可选：`figures` 图表路径与说明、`risks` 风险事项、`next_week_plan` 下周计划。

## 前置条件
- 数据来源一致且已完成清洗；指标口径与上周一致。
- 有周度快照（版本号或周次编号），方便比对与回溯。

## 输出
- 中文周报Markdown文本：卡片化结构、图表引用、行动项清单。
- 可附加导出HTML/PDF（外部流程实现）。

## 核心流程
1. 验证输入完整性与指标口径。
2. 组装周报结构：概览/本周洞察/各模块/行动项。
3. 生成对比与趋势说明，突出异常与风险。
4. 输出可发布文本，并保存版本快照。

## 错误处理
- 输入缺失：提供模板与默认卡片，占位提示待补充。
- 指标不一致：记录差异并在周报“数据口径”节标注。
- 文件输出失败：告警并提示重试路径与权限检查。

## 日志与审计
- 记录生成时间、周次编号、数据版本与生成参数。
- 保存关键段落字数与图表引用数量，便于质量检查。

## 质量检查清单
- 中文表达清晰简洁；关键指标有对比与上下文。
- 风险与建议具体可执行；行动项有责任人与截止时间。
- 全文无空段落/无敏感信息泄露。

## 代码模板（含函数级中文注释）

```python
def build_weekly_report(weekly_data: dict, insights: str, recommendations: list, figures: list | None = None) -> str:
    """
    函数用途：将周度数据与洞察组装为结构化中文周报文本
    参数说明：
    - weekly_data: 周度KPI与明细数据的字典
    - insights: 本周重点洞察的文本
    - recommendations: 建议与行动项（字符串列表）
    - figures: 可选的图表引用信息（路径与说明）
    返回结果：完整的Markdown格式中文周报文本
    """
    sections = []
    sections.append("# 本周概览\n\n" + insights.strip())
    sections.append("# 关键指标\n\n" + _format_kpi_block(weekly_data))
    if figures:
        sections.append("# 图表与可视化\n\n" + _format_figures(figures))
    if recommendations:
        sections.append("# 建议与行动项\n\n" + _format_actions(recommendations))
    sections.append("# 数据口径与版本\n\n- 周次：" + str(weekly_data.get('week_no','N/A')))
    return "\n\n".join(sections)

def _format_kpi_block(weekly_data: dict) -> str:
    """
    函数用途：格式化关键指标模块为Markdown文本
    参数说明：
    - weekly_data: 周度KPI字典，包含数值与同比环比信息
    返回结果：KPI模块的Markdown字符串
    """
    lines = []
    for k, v in weekly_data.get('kpi', {}).items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines) if lines else "- 暂无关键指标"

def _format_figures(figures: list) -> str:
    """
    函数用途：格式化图表引用为Markdown文本块
    参数说明：
    - figures: 图表列表，元素包含路径与说明
    返回结果：图表引用的Markdown字符串
    """
    lines = []
    for fig in figures:
        lines.append(f"![{fig.get('title','figure')}]({fig.get('path','')})\n\n{fig.get('desc','')}\n")
    return "\n".join(lines) if lines else "- 本周暂无图表"

def _format_actions(actions: list) -> str:
    """
    函数用途：格式化建议与行动项列表
    参数说明：
    - actions: 字符串列表，每项为一条建议或行动
    返回结果：行动项的Markdown字符串
    """
    return "\n".join([f"- [ ] {a}" for a in actions])
```

## 版本与维护
- v2.0.0：结构重构，完善错误处理与质检清单，统一中文输出。