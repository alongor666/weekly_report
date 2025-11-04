---
name: 保险数据加载技能（简版入口）
description: 提供简洁入口加载保险数据并做最基础清洗，供快速分析与周报使用。
author: 保险数据团队
tags:
  - 数据加载
  - 简版
version: 2.0.0
---

# 技能规范（最佳实践版）

## 输入参数
- `path`：单一数据源路径（CSV/Parquet）。
- `schema`：字段与类型定义（字典）。

## 输出
- 清洗后的 `DataFrame`（小规模快速使用）。

## 代码模板（含函数级中文注释）

```python
import pandas as pd

def load_insurance_quick(path: str, schema: dict) -> pd.DataFrame:
    """
    函数用途：快速加载单一保险数据源并标准化字段类型
    参数说明：
    - path: 数据文件路径
    - schema: 字段与类型定义字典
    返回结果：清洗后的DataFrame，适用于快速分析
    """
    try:
        df = pd.read_parquet(path) if path.endswith('.parquet') else pd.read_csv(path)
    except Exception as e:
        print(f"[加载失败] {path}: {e}")
        return pd.DataFrame()
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
    return df
```

## 版本与维护
- v2.0.0：统一结构与中文注释，简化入口设计。