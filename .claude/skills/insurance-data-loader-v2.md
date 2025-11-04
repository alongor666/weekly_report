---
name: 保险数据加载技能 V2（更强鲁棒性）
description: 加载并清洗保险业务相关的多源数据（赔付、承保、车队、地区），提供统一的数据视图，支持统计与分析。
author: 保险数据团队
tags:
  - 数据加载
  - 清洗
  - 保险
version: 2.0.0
---

# 技能规范（最佳实践版）

## 适用场景
- 需要将多来源（CSV/Parquet/SQL）的保险业务数据统一加载并清洗。
- 为后续KPI计算、损失趋势分析、周报生成提供可靠输入。

## 输入参数
- `file_paths`：路径或连接信息的列表（支持本地与远程）。
- `schema`：期望的字段结构与类型定义（字典）。
- `dedup_keys`：去重主键集合，如 `claim_id`。
- `date_range`：时间范围过滤（起止日期）。
- `fallbacks`：字段缺失时的默认值或估算规则。

## 前置条件
- 数据源可访问，权限与网络正常。
- 目标字段与类型已在 `schema` 中定义。

## 输出
- 统一 `DataFrame`：字段标准化、类型正确、范围过滤、重复清理。
- 加载报告：记录数据量、缺失率、异常行数、字段修复情况。

## 核心流程
1. 逐源加载：自动识别格式（CSV/Parquet），失败则重试与告警。
2. 合并与标准化：按 `schema` 对齐字段并进行类型转换。
3. 去重与过滤：根据主键与时间范围剔除无效记录。
4. 缺失修复：按 `fallbacks` 补齐或估算，记录修复日志。
5. 产出数据视图：用于下游分析的统一表。

## 错误处理
- 加载失败：记录具体源与错误信息，跳过并继续其他源。
- 字段缺失：使用 `fallbacks` 修复或标记为缺失并提示。
- 类型不匹配：转换失败则降级处理或剔除异常行。

## 日志与审计
- 对每个源记录加载时间、行数、字段修复统计与失败详情。
- 输出最终视图的行数与字段完整性报告。

## 质量检查清单
- 所有必需字段存在且类型正确；重复记录率低于阈值。
- 缺失修复率与异常行比例在可接受范围内。
- 函数级中文注释完备；示例可运行（伪数据）。

## 代码模板（含函数级中文注释）

```python
import pandas as pd
from typing import List, Dict

def load_sources(file_paths: List[str]) -> List[pd.DataFrame]:
    """
    函数用途：批量加载多个数据源为DataFrame列表
    参数说明：
    - file_paths: 文件路径列表，支持CSV/Parquet
    返回结果：成功加载的数据帧列表，失败源将记录日志并跳过
    """
    dfs = []
    for p in file_paths:
        try:
            if p.endswith('.parquet'):
                dfs.append(pd.read_parquet(p))
            else:
                dfs.append(pd.read_csv(p))
        except Exception as e:
            print(f"[加载失败] {p}: {e}")
    return dfs

def standardize_schema(df: pd.DataFrame, schema: Dict[str, str]) -> pd.DataFrame:
    """
    函数用途：按给定schema标准化字段并进行类型转换
    参数说明：
    - df: 原始数据帧
    - schema: 字段名到类型的映射（如 'claim_amount': 'float'）
    返回结果：标准化后的数据帧
    """
    for col, typ in schema.items():
        if col not in df.columns:
            df[col] = None
        try:
            if typ == 'float':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif typ == 'int':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            elif typ == 'str':
                df[col] = df[col].astype(str)
            elif typ == 'date':
                df[col] = pd.to_datetime(df[col], errors='coerce')
        except Exception as e:
            print(f"[类型转换失败] {col}: {e}")
    return df

def merge_and_clean(dfs: List[pd.DataFrame], dedup_keys: List[str], date_col: str, date_range: tuple | None) -> pd.DataFrame:
    """
    函数用途：合并多个数据帧并进行去重与日期范围过滤
    参数说明：
    - dfs: 数据帧列表
    - dedup_keys: 去重主键列表
    - date_col: 日期字段名
    - date_range: (start, end) 起止时间，None表示不限制
    返回结果：清洗后的统一数据帧
    """
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    if date_range and date_col in df.columns:
        start, end = date_range
        df = df[(df[date_col] >= pd.to_datetime(start)) & (df[date_col] <= pd.to_datetime(end))]
    if dedup_keys:
        df = df.drop_duplicates(subset=dedup_keys, keep='last')
    return df

def apply_fallbacks(df: pd.DataFrame, fallbacks: Dict[str, object]) -> pd.DataFrame:
    """
    函数用途：按给定fallbacks对缺失字段进行补齐或估算
    参数说明：
    - df: 清洗后的数据帧
    - fallbacks: 字段到默认值或估算函数的映射
    返回结果：补齐后的数据帧，并打印修复统计
    """
    fix_count = 0
    for col, rule in fallbacks.items():
        if col in df.columns:
            missing_mask = df[col].isna()
            if callable(rule):
                df.loc[missing_mask, col] = df.loc[missing_mask].apply(rule, axis=1)
            else:
                df.loc[missing_mask, col] = rule
            fix_count += int(missing_mask.sum())
    print(f"[缺失修复] 总计修复 {fix_count} 项")
    return df

def load_insurance_data_v2(file_paths: List[str], schema: Dict[str, str], dedup_keys: List[str], date_col: str, date_range: tuple | None, fallbacks: Dict[str, object]) -> pd.DataFrame:
    """
    函数用途：端到端加载并清洗保险数据，返回统一视图
    参数说明：
    - file_paths: 多源路径列表
    - schema: 字段标准化定义
    - dedup_keys: 去重主键
    - date_col: 日期字段名
    - date_range: 时间范围过滤
    - fallbacks: 缺失修复规则
    返回结果：清洗合并后的统一数据帧
    """
    dfs = load_sources(file_paths)
    dfs = [standardize_schema(d, schema) for d in dfs]
    df = merge_and_clean(dfs, dedup_keys, date_col, date_range)
    df = apply_fallbacks(df, fallbacks)
    return df
```

## 版本与维护
- v2.0.0：引入统一最佳实践结构、增强错误处理与日志、中文注释。