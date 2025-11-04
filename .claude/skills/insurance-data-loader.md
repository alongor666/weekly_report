---
name: 保险数据加载技能（基础版）
description: 从指定来源加载保险业务数据并进行基本清洗，输出统一的结构化数据视图。
author: 保险数据团队
tags:
  - 数据加载
  - 清洗
  - 保险
version: 2.0.0
---

# 技能规范（最佳实践版）

## 输入参数
- `source_paths`：数据文件路径列表（CSV/Parquet）。
- `schema`：字段与类型定义（字典）。
- `keys`：主键列表用于去重（如 `claim_id`）。
- `date_col`：日期字段名，配合 `date_range` 过滤。

## 输出
- 清洗后的 `DataFrame`，字段标准化与重复剔除。
- 加载报告（日志）：行数、缺失字段、异常记录统计。

## 流程
1. 逐源加载（失败记录并跳过）。
2. 标准化字段与类型。
3. 去重与日期过滤。
4. 返回统一视图供下游分析使用。

## 错误处理与审计
- 加载失败、类型转换失败、缺失列，均记录并可重试。
- 输出最终视图质量统计（字段完整性、重复率）。

## 代码模板（含函数级中文注释）

```python
import pandas as pd
from typing import List, Dict

def load_insurance_data_basic(source_paths: List[str], schema: Dict[str, str], keys: List[str], date_col: str | None = None, date_range: tuple | None = None) -> pd.DataFrame:
    """
    函数用途：基础版保险数据加载与清洗，返回统一视图
    参数说明：
    - source_paths: 数据源路径列表
    - schema: 字段与类型定义
    - keys: 用于去重的主键列表
    - date_col: 可选日期字段名
    - date_range: 可选起止时间范围
    返回结果：清洗后的DataFrame
    """
    dfs = []
    for p in source_paths:
        try:
            dfs.append(pd.read_parquet(p) if p.endswith('.parquet') else pd.read_csv(p))
        except Exception as e:
            print(f"[加载失败] {p}: {e}")
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    # 标准化类型
    for col, typ in schema.items():
        if col not in df.columns:
            df[col] = None
        try:
            if typ == 'float':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif typ == 'int':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            elif typ == 'date':
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif typ == 'str':
                df[col] = df[col].astype(str)
        except Exception as e:
            print(f"[类型转换失败] {col}: {e}")
    # 日期过滤与去重
    if date_col and date_range:
        start, end = date_range
        df = df[(df[date_col] >= pd.to_datetime(start)) & (df[date_col] <= pd.to_datetime(end))]
    if keys:
        df = df.drop_duplicates(subset=keys, keep='last')
    return df
```

## 版本与维护
- v2.0.0：统一中文规范与错误处理，补充函数级中文注释。