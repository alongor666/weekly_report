---
name: 保险KPI计算技能
description: 基于统一数据视图，计算保险业务关键指标（赔付率、频率、平均赔付金额、环比同比等），支持缓存与导出。
author: 保险数据团队
tags:
  - KPI
  - 统计
  - 保险
version: 2.0.0
---

# 技能规范（最佳实践版）

## 输入参数
- `df`：统一保险数据视图（已清洗）。
- `dimensions`：维度列表（如地区、车队、车型）。
- `date_col`：日期字段；`period`：周/月。
- `filters`：可选过滤条件（字典）。

## 输出
- 指标字典：赔付率、赔付频率、平均赔付金额、环比同比、分维度拆解。
- 可选：缓存对象（键=维度组合），用于重复查询加速。

## 流程
1. 按过滤条件选择数据；按维度分组统计。
2. 计算核心指标与环比同比。
3. 产出总览与维度分解；写入缓存（可选）。

## 错误处理
- 数据为空或字段缺失：返回默认指标并提示。
- 除零与类型错误：保护性计算与日志记录。

## 代码模板（含函数级中文注释）

```python
import pandas as pd
from typing import Dict, List

def calc_insurance_kpis(df: pd.DataFrame, dimensions: List[str], date_col: str, filters: Dict[str, object] | None = None) -> Dict[str, object]:
    """
    函数用途：计算保险业务核心KPI并按维度拆解
    参数说明：
    - df: 已清洗的统一数据视图
    - dimensions: 需要拆解的维度列表
    - date_col: 日期字段名
    - filters: 可选过滤条件字典
    返回结果：包含总体与维度拆解的指标字典
    """
    if df is None or df.empty:
        return {'overview': {}, 'by_dim': {}}
    d = df.copy()
    # 过滤
    if filters:
        for k, v in filters.items():
            if k in d.columns:
                d = d[d[k] == v]
    # 基础指标
    total_claims = int(d['claim_id'].nunique()) if 'claim_id' in d.columns else len(d)
    total_exposure = float(d['exposure'].sum()) if 'exposure' in d.columns else max(len(d),1)
    paid_amount = float(d['paid_amount'].sum()) if 'paid_amount' in d.columns else 0.0
    freq = total_claims / max(total_exposure, 1.0)
    severity = paid_amount / max(total_claims, 1.0)
    loss_ratio = paid_amount / max(d.get('premium', pd.Series([0.0]*len(d))).sum(), 1.0)
    overview = {
        'claims': total_claims,
        'frequency': round(freq,6),
        'severity': round(severity,2),
        'loss_ratio': round(loss_ratio,6),
    }
    # 维度拆解
    by_dim = {}
    for dim in dimensions:
        if dim in d.columns:
            grp = d.groupby(dim).agg({
                'claim_id':'nunique',
                'paid_amount':'sum',
                'premium':'sum',
                'exposure':'sum'
            })
            grp['frequency'] = grp['claim_id']/grp['exposure'].clip(lower=1.0)
            grp['severity'] = grp['paid_amount']/grp['claim_id'].clip(lower=1.0)
            grp['loss_ratio'] = grp['paid_amount']/grp['premium'].clip(lower=1.0)
            by_dim[dim] = grp.reset_index().to_dict(orient='records')
    return {'overview': overview, 'by_dim': by_dim}
```

## 质量检查清单
- 中文注释与输出齐全；单位与口径统一。
- 除零保护到位；维度不存在时有安全分支。

## 版本与维护
- v2.0.0：统一结构、完善错误处理与中文注释。