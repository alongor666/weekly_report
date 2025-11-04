---
name: insurance-data-loader
description: 车险周报数据加载器 - 加载目标周及历史周数据，按年度分组，过滤本部机构
---

# insurance-data-loader

## 使用场景

每次生成车险周报的第一步，用于加载和预处理数据。

## 功能说明

本skill负责：
1. 加载目标周及前N周的CSV文件
2. 验证数据完整性（必须包含27个字段）
3. 按保险起期年度分组（2024保单 / 2025保单）
4. 过滤掉"本部"机构（三级机构 = '本部'）
5. 提取所有唯一的二级机构和三级机构名称列表

## 输入参数

- `target_week`: 目标周次（如 44）
- `data_folder`: 数据文件夹路径（默认 `处理后/`）
- `lookback_weeks`: 回溯周数（默认 5，用于趋势分析）

## 输出格式

输出一个JSON结构，包含：
- 按年度分组的DataFrame字典
- 机构列表
- 数据质量元信息

## 执行步骤

### Step 1: 验证输入参数

```python
# 必须提供的参数
if not target_week:
    raise ValueError("必须指定target_week参数")

# 设置默认值
data_folder = data_folder or "处理后/"
lookback_weeks = lookback_weeks or 5
```

### Step 2: 查找并加载CSV文件

```python
import pandas as pd
from pathlib import Path
import os

# 计算需要加载的周次列表
weeks_to_load = list(range(target_week - lookback_weeks + 1, target_week + 1))
# 示例：target_week=44, lookback_weeks=5 → [40, 41, 42, 43, 44]

# 查找文件
data_path = Path(data_folder)
loaded_files = {}
missing_weeks = []

for week in weeks_to_load:
    # 支持两种命名格式：
    # - 2024保单第XX周变动成本明细表.csv
    # - 2025保单第XX周变动成本明细表.csv

    # 先尝试查找所有匹配的文件
    pattern = f"*保单第{week}周变动成本明细表.csv"
    matching_files = list(data_path.glob(pattern))

    if matching_files:
        for file in matching_files:
            print(f"✅ 找到文件: {file.name}")
            try:
                df = pd.read_csv(file, encoding='utf-8-sig')
                loaded_files[week] = loaded_files.get(week, []) + [df]
            except Exception as e:
                print(f"❌ 读取文件失败 {file.name}: {e}")
    else:
        print(f"⚠️  未找到第{week}周的数据文件")
        missing_weeks.append(week)

# 汇总加载情况
print(f"\n📊 数据加载汇总:")
print(f"  - 目标周: 第{target_week}周")
print(f"  - 回溯周数: {lookback_weeks}周")
print(f"  - 成功加载: {len(loaded_files)}个周次")
if missing_weeks:
    print(f"  - 缺失周次: {missing_weeks}")
```

### Step 3: 验证数据完整性

```python
# 必须的27个字段
REQUIRED_FIELDS = [
    # 18个筛选维度字段
    'snapshot_date',
    'policy_start_year',
    'business_type_category',
    'chengdu_branch',
    'second_level_organization',
    'third_level_organization',
    'customer_category_3',
    'insurance_type',
    'is_new_energy_vehicle',
    'coverage_type',
    'is_transferred_vehicle',
    'renewal_status',
    'vehicle_insurance_grade',
    'highway_risk_grade',
    'large_truck_score',
    'small_truck_score',
    'terminal_source',
    # 9个绝对值字段
    'signed_premium_yuan',
    'matured_premium_yuan',
    'policy_count',
    'claim_case_count',
    'reported_claim_payment_yuan',
    'expense_amount_yuan',
    'commercial_premium_before_discount_yuan',
    'premium_plan_yuan',
    'marginal_contribution_amount_yuan',
    'week_number'
]

# 验证每个加载的文件
for week, dfs in loaded_files.items():
    for df in dfs:
        missing_fields = set(REQUIRED_FIELDS) - set(df.columns)
        if missing_fields:
            print(f"❌ 第{week}周数据缺少字段: {missing_fields}")
        else:
            print(f"✅ 第{week}周数据字段完整")
```

### Step 4: 过滤本部机构

```python
# 过滤掉三级机构为"本部"的数据
for week, dfs in loaded_files.items():
    for i, df in enumerate(dfs):
        original_count = len(df)
        df_filtered = df[df['third_level_organization'] != '本部'].copy()
        filtered_count = len(df_filtered)

        print(f"第{week}周: 过滤前{original_count}行，过滤后{filtered_count}行，剔除{original_count - filtered_count}行本部数据")

        loaded_files[week][i] = df_filtered
```

### Step 5: 按年度分组

```python
# 按保险起期年度分组
data_by_year = {
    '2024': {},
    '2025': {}
}

for week, dfs in loaded_files.items():
    for df in dfs:
        # 从policy_start_year字段提取年份
        # 可能的格式：2024, 2025, "2024", "2025"
        df['year'] = df['policy_start_year'].astype(str).str.extract(r'(202[45])')[0]

        # 分组
        for year in ['2024', '2025']:
            year_data = df[df['year'] == year].copy()
            if len(year_data) > 0:
                if week not in data_by_year[year]:
                    data_by_year[year][week] = []
                data_by_year[year][week].append(year_data)
                print(f"📋 {year}保单第{week}周: {len(year_data)}行数据")

# 合并同一周的多个文件（如果有的话）
for year in ['2024', '2025']:
    for week in data_by_year[year].keys():
        if len(data_by_year[year][week]) > 1:
            print(f"⚠️  {year}保单第{week}周有多个文件，正在合并...")
            data_by_year[year][week] = pd.concat(data_by_year[year][week], ignore_index=True)
        else:
            data_by_year[year][week] = data_by_year[year][week][0]
```

### Step 6: 提取机构列表

```python
# 收集所有机构名称（去重）
all_second_orgs = set()
all_third_orgs = set()

for year in ['2024', '2025']:
    for week, df in data_by_year[year].items():
        all_second_orgs.update(df['second_level_organization'].unique())
        all_third_orgs.update(df['third_level_organization'].unique())

# 移除空值和本部
all_second_orgs = sorted([org for org in all_second_orgs if pd.notna(org) and org != '本部'])
all_third_orgs = sorted([org for org in all_third_orgs if pd.notna(org) and org != '本部'])

print(f"\n🏢 机构列表:")
print(f"  - 二级机构数量: {len(all_second_orgs)}")
print(f"  - 三级机构数量: {len(all_third_orgs)}")
print(f"  - 三级机构: {', '.join(all_third_orgs)}")
```

### Step 7: 生成输出报告

```python
# 生成数据质量报告
print("\n" + "="*60)
print("📊 数据加载完成报告")
print("="*60)

print(f"\n✅ 成功加载 {len(weeks_to_load) - len(missing_weeks)}/{len(weeks_to_load)} 个周次")

for year in ['2024', '2025']:
    if data_by_year[year]:
        print(f"\n{year}保单数据:")
        for week in sorted(data_by_year[year].keys()):
            df = data_by_year[year][week]
            print(f"  - 第{week}周: {len(df):,}行数据")
            print(f"    满期保费合计: {df['matured_premium_yuan'].sum() / 10000:.2f}万元")
    else:
        print(f"\n{year}保单数据: 无")

print(f"\n🏢 机构统计:")
print(f"  - 二级机构: {len(all_second_orgs)}个")
print(f"  - 三级机构: {len(all_third_orgs)}个（已排除本部）")

if missing_weeks:
    print(f"\n⚠️  缺失周次: {missing_weeks}")
    print(f"   说明: 这些周次的数据将无法进行环比分析")

print("\n" + "="*60)
```

### Step 8: 输出数据结构

```python
# 将数据保存到全局变量，供后续skill使用
# 注意：Claude Code的skill之间通过输出文本和文件共享数据

# 输出一个JSON格式的数据路径映射
import json

output = {
    "target_week": target_week,
    "lookback_weeks": lookback_weeks,
    "data_quality": "完整" if not missing_weeks else "部分缺失",
    "missing_weeks": missing_weeks,
    "organizations": {
        "second_level": all_second_orgs,
        "third_level": all_third_orgs
    },
    "loaded_years": list(data_by_year.keys()),
    "data_summary": {
        year: {
            "weeks": list(data_by_year[year].keys()),
            "total_rows": sum(len(df) for df in data_by_year[year].values())
        }
        for year in ['2024', '2025'] if data_by_year[year]
    }
}

print("\n📦 数据加载器输出 (JSON):")
print(json.dumps(output, ensure_ascii=False, indent=2))

# 保存数据到临时文件，供后续skill读取
import pickle
cache_file = Path(data_folder) / f".cache_week_{target_week}.pkl"
with open(cache_file, 'wb') as f:
    pickle.dump({
        'data_by_year': data_by_year,
        'metadata': output
    }, f)

print(f"\n💾 数据已缓存到: {cache_file}")
print("   后续skill可通过读取此文件获取数据")
```

## 使用示例

```python
# 示例1: 加载第44周及前5周数据
insurance-data-loader(
    target_week=44,
    data_folder="处理后/",
    lookback_weeks=5
)

# 示例2: 只加载目标周及前2周（快速模式）
insurance-data-loader(
    target_week=44,
    lookback_weeks=2
)
```

## 错误处理

- 如果目标周数据缺失，报错并终止
- 如果历史周数据部分缺失，给出警告但继续执行
- 如果数据字段不完整，报错并列出缺失字段
- 如果文件读取失败，报错并显示错误信息

## 下一步

数据加载完成后，调用：
- `insurance-kpi-calculator`: 计算KPI指标
- `insurance-org-profiler`: 生成机构画像
