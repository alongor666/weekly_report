---
name: insurance-kpi-calculator
description: 车险KPI计算引擎 - 计算16个核心KPI、环比对比、5周趋势、状态判断
---

# insurance-kpi-calculator

## 使用场景

在数据加载后立即执行，计算所有核心KPI指标并进行趋势分析。

## 功能说明

本skill负责：
1. 计算16个核心KPI（基于 `core_calculations.md`）
2. 计算环比变化（本周 vs 上周）
3. 计算5周趋势（移动平均、趋势方向）
4. 应用阈值判断状态（基于 `率值指标区间状态值配置.md`）
5. 支持多个聚合级别（全局、二级机构、三级机构）

## 前置条件

- 必须先执行 `insurance-data-loader` 加载数据
- 数据缓存文件存在：`.cache_week_XX.pkl`

## 输入参数

- `target_week`: 目标周次（如 44）
- `data_folder`: 数据文件夹路径（默认 `处理后/`）
- `aggregation_levels`: 聚合级别列表（默认 `['global', 'second_org', 'third_org']`）

## 核心KPI定义（16个）

### 核心比率指标（4个）
1. **满期边际贡献率** = 100% - 变动成本率
2. **保费时间进度达成率** = (实际累计保费 / 年度目标) / (已过天数 / 365)
3. **满期赔付率** = 满期赔付 / 满期保费
4. **费用率** = 总费用 / 签单保费

### 核心金额指标（4个）
5. **满期边际贡献额** = 满期保费 × 满期边际贡献率
6. **签单保费** = SUM(签单保费)
7. **已报告赔款** = SUM(已报告赔款)
8. **费用额** = SUM(总费用)

### 结构与效率指标（4个）
9. **变动成本率** = 满期赔付率 + 费用率
10. **满期率** = 满期保费 / 签单保费
11. **满期出险率** = (赔案件数/保单件数) / (满期保费/签单保费)
12. **保单件数** = SUM(保单件数)

### 单均质量指标（4个）
13. **赔案件数** = SUM(赔案件数)
14. **单均保费** = 签单保费 / 保单件数
15. **案均赔款** = 已报告赔款 / 赔案件数
16. **单均费用** = 费用金额 / 保单件数

## 状态判断阈值

基于 `率值指标区间状态值配置.md`：

| 指标 | 优秀 | 健康 | 预警 | 危险 |
|------|------|------|------|------|
| 满期边际贡献率 | >12% | 8-12% | 6-8% | 4-6% |
| 保费进度达成率 | ≥110% | 100-110% | 90-100% | <90% |
| 满期赔付率 | <50% | 50-60% | 60-70% | >70% |
| 费用率 | <7.5% | 7.5-12.5% | 12.5-17.5% | >17.5% |
| 变动成本率 | <60% | 60-70% | 70-80% | >80% |

## 执行步骤

### Step 1: 加载缓存数据

```python
import pandas as pd
import pickle
from pathlib import Path
import numpy as np

# 参数
target_week = 44  # 从用户输入或上一个skill获取
data_folder = "."
aggregation_levels = ['global', 'second_org', 'third_org']

# 读取缓存
cache_file = Path(data_folder) / f".cache_week_{target_week}.pkl"

if not cache_file.exists():
    raise FileNotFoundError(f"❌ 缓存文件不存在: {cache_file}\n请先执行 insurance-data-loader")

with open(cache_file, 'rb') as f:
    cache = pickle.load(f)

data_by_year = cache['data_by_year']
metadata = cache['metadata']

print("✅ 数据加载成功")
print(f"  - 目标周: 第{target_week}周")
print(f"  - 可用年度: {list(data_by_year.keys())}")
```

### Step 2: 定义KPI计算函数

```python
def calculate_kpis(df):
    """
    计算单个DataFrame的16个KPI

    参数:
        df: pandas DataFrame，包含27个字段

    返回:
        dict: 包含16个KPI的字典
    """
    # 避免除零错误
    epsilon = 1e-10

    # 基础聚合
    signed_premium = df['signed_premium_yuan'].sum()
    matured_premium = df['matured_premium_yuan'].sum()
    policy_count = df['policy_count'].sum()
    claim_case_count = df['claim_case_count'].sum()
    reported_claim = df['reported_claim_payment_yuan'].sum()
    expense_amount = df['expense_amount_yuan'].sum()

    # 避免除零
    signed_premium = max(signed_premium, epsilon)
    matured_premium = max(matured_premium, epsilon)
    policy_count = max(policy_count, epsilon)
    claim_case_count = max(claim_case_count, epsilon)

    # 核心比率指标
    loss_ratio = (reported_claim / matured_premium) * 100  # 满期赔付率
    expense_ratio = (expense_amount / signed_premium) * 100  # 费用率
    variable_cost_ratio = loss_ratio + expense_ratio  # 变动成本率
    contribution_margin_ratio = 100 - variable_cost_ratio  # 满期边际贡献率

    # 核心金额指标（单位：万元）
    contribution_margin_amount = (matured_premium * contribution_margin_ratio / 100) / 10000
    signed_premium_wan = signed_premium / 10000
    matured_premium_wan = matured_premium / 10000
    reported_claim_wan = reported_claim / 10000
    expense_amount_wan = expense_amount / 10000

    # 结构与效率指标
    maturity_ratio = (matured_premium / signed_premium) * 100  # 满期率
    matured_claim_ratio = ((claim_case_count / policy_count) / (maturity_ratio / 100)) * 100  # 满期出险率

    # 单均质量指标
    avg_premium = signed_premium / policy_count  # 单均保费
    avg_claim = reported_claim / claim_case_count if claim_case_count > 1 else 0  # 案均赔款
    avg_expense = expense_amount / policy_count  # 单均费用

    # 保费时间进度达成率（暂时使用简化计算，后续可接入年度目标）
    # 简化版：假设50周工作制，每周应完成 100% / 50 = 2%
    week_number = df['week_number'].iloc[0] if len(df) > 0 else target_week
    expected_progress = (week_number / 50) * 100
    actual_progress = 100  # 需要累计数据，暂时占位
    progress_achievement = 100  # 暂时占位，需要年度目标数据

    return {
        # 核心比率指标
        '满期边际贡献率': round(contribution_margin_ratio, 2),
        '保费时间进度达成率': round(progress_achievement, 2),  # 占位
        '满期赔付率': round(loss_ratio, 2),
        '费用率': round(expense_ratio, 2),

        # 核心金额指标（万元）
        '满期边际贡献额': round(contribution_margin_amount, 2),
        '签单保费': round(signed_premium_wan, 2),
        '满期保费': round(matured_premium_wan, 2),
        '已报告赔款': round(reported_claim_wan, 2),
        '费用额': round(expense_amount_wan, 2),

        # 结构与效率指标
        '变动成本率': round(variable_cost_ratio, 2),
        '满期率': round(maturity_ratio, 2),
        '满期出险率': round(matured_claim_ratio, 2),
        '保单件数': int(policy_count),

        # 单均质量指标（元）
        '赔案件数': int(claim_case_count),
        '单均保费': round(avg_premium, 0),
        '案均赔款': round(avg_claim, 0),
        '单均费用': round(avg_expense, 0),
    }


def judge_status(kpi_name, value):
    """
    根据KPI值判断状态

    参数:
        kpi_name: KPI名称
        value: KPI值

    返回:
        str: 状态标签（优秀/健康/预警/危险）
    """
    thresholds = {
        '满期边际贡献率': {
            '优秀': lambda x: x > 12,
            '健康': lambda x: 8 <= x <= 12,
            '中等': lambda x: 6 <= x < 8,
            '预警': lambda x: 4 <= x < 6,
            '危险': lambda x: x < 4
        },
        '保费时间进度达成率': {
            '优秀': lambda x: x >= 110,
            '健康': lambda x: 100 <= x < 110,
            '预警': lambda x: 90 <= x < 100,
            '危险': lambda x: x < 90
        },
        '满期赔付率': {
            '优秀': lambda x: x < 50,
            '健康': lambda x: 50 <= x < 60,
            '中等': lambda x: 60 <= x < 70,
            '预警': lambda x: 70 <= x < 80,
            '危险': lambda x: x >= 80
        },
        '费用率': {
            '优秀': lambda x: x < 7.5,
            '健康': lambda x: 7.5 <= x < 12.5,
            '中等': lambda x: 12.5 <= x < 17.5,
            '预警': lambda x: 17.5 <= x < 22.5,
            '危险': lambda x: x >= 22.5
        },
        '变动成本率': {
            '优秀': lambda x: x < 60,
            '健康': lambda x: 60 <= x < 70,
            '中等': lambda x: 70 <= x < 80,
            '预警': lambda x: 80 <= x < 90,
            '危险': lambda x: x >= 90
        }
    }

    if kpi_name not in thresholds:
        return '中性'

    for status, condition in thresholds[kpi_name].items():
        if condition(value):
            # 映射到图标
            status_icons = {
                '优秀': '🟢',
                '健康': '🟢',
                '中等': '🔵',
                '预警': '🟡',
                '危险': '🔴'
            }
            return f"{status_icons.get(status, '⚪')} {status}"

    return '⚪ 未知'
```

### Step 3: 计算全局KPI

```python
print("\n" + "="*60)
print("📊 开始计算全局KPI")
print("="*60)

results = {}

for year in ['2024', '2025']:
    if year not in data_by_year or not data_by_year[year]:
        print(f"\n⚠️  {year}保单数据不存在，跳过")
        continue

    print(f"\n{'='*40}")
    print(f"  {year}保单数据")
    print(f"{'='*40}")

    results[year] = {
        'global': {},
        'second_org': {},
        'third_org': {}
    }

    # 全局KPI（本周）
    if target_week in data_by_year[year]:
        df_current = data_by_year[year][target_week]
        kpis_current = calculate_kpis(df_current)

        print(f"\n第{target_week}周全局KPI:")
        print(f"  满期保费: {kpis_current['满期保费']:.2f}万元")
        print(f"  满期赔付率: {kpis_current['满期赔付率']:.2f}% {judge_status('满期赔付率', kpis_current['满期赔付率'])}")
        print(f"  费用率: {kpis_current['费用率']:.2f}% {judge_status('费用率', kpis_current['费用率'])}")
        print(f"  满期边际贡献率: {kpis_current['满期边际贡献率']:.2f}% {judge_status('满期边际贡献率', kpis_current['满期边际贡献率'])}")

        results[year]['global'][target_week] = kpis_current

    # 全局KPI（上周，用于环比）
    last_week = target_week - 1
    if last_week in data_by_year[year]:
        df_last = data_by_year[year][last_week]
        kpis_last = calculate_kpis(df_last)
        results[year]['global'][last_week] = kpis_last

        # 计算环比
        print(f"\n环比变化（vs 第{last_week}周）:")
        for kpi_name in ['满期赔付率', '费用率', '满期边际贡献率']:
            current_val = kpis_current[kpi_name]
            last_val = kpis_last[kpi_name]
            change = current_val - last_val
            direction = "↗️" if change > 0 else "↘️" if change < 0 else "→"
            print(f"  {kpi_name}: {last_val:.2f}% → {current_val:.2f}% ({change:+.2f}pp {direction})")
```

### Step 4: 计算三级机构KPI

```python
if 'third_org' in aggregation_levels:
    print(f"\n{'='*40}")
    print(f"  三级机构KPI计算")
    print(f"{'='*40}")

    third_orgs = metadata['organizations']['third_level']

    for org_name in third_orgs:
        print(f"\n【{org_name}】")

        # 筛选该机构数据
        if target_week in data_by_year[year]:
            df_org = data_by_year[year][target_week]
            df_org = df_org[df_org['third_level_organization'] == org_name]

            if len(df_org) > 0:
                kpis_org = calculate_kpis(df_org)
                results[year]['third_org'][org_name] = {target_week: kpis_org}

                print(f"  满期保费: {kpis_org['满期保费']:.2f}万元")
                print(f"  赔付率: {kpis_org['满期赔付率']:.2f}% {judge_status('满期赔付率', kpis_org['满期赔付率'])}")
                print(f"  边贡率: {kpis_org['满期边际贡献率']:.2f}% {judge_status('满期边际贡献率', kpis_org['满期边际贡献率'])}")
            else:
                print(f"  ⚠️  无数据")
```

### Step 5: 计算5周趋势

```python
print(f"\n{'='*40}")
print(f"  5周趋势分析")
print(f"{'='*40}")

# 全局5周趋势
weeks = sorted([w for w in data_by_year[year].keys() if w <= target_week])[-5:]
print(f"\n分析周次: {weeks}")

trend_data = {
    '满期保费': [],
    '满期赔付率': [],
    '费用率': [],
    '满期边际贡献率': []
}

for week in weeks:
    if week in data_by_year[year]:
        kpis = calculate_kpis(data_by_year[year][week])
        trend_data['满期保费'].append(kpis['满期保费'])
        trend_data['满期赔付率'].append(kpis['满期赔付率'])
        trend_data['费用率'].append(kpis['费用率'])
        trend_data['满期边际贡献率'].append(kpis['满期边际贡献率'])

# 输出趋势
for kpi_name, values in trend_data.items():
    if len(values) >= 2:
        trend_direction = "上升" if values[-1] > values[0] else "下降" if values[-1] < values[0] else "持平"
        print(f"\n{kpi_name} 趋势: {trend_direction}")
        print(f"  数据: {' → '.join([f'{v:.1f}' for v in values])}")

results[year]['trend_5weeks'] = trend_data
```

### Step 6: 保存结果

```python
# 保存计算结果到缓存
output_file = Path(data_folder) / f".cache_kpi_week_{target_week}.pkl"
with open(output_file, 'wb') as f:
    pickle.dump(results, f)

print(f"\n💾 KPI计算结果已保存: {output_file}")
print(f"   后续skill可通过读取此文件获取KPI数据")

# 输出汇总
print("\n" + "="*60)
print("✅ KPI计算完成")
print("="*60)
for year in results.keys():
    print(f"\n{year}保单:")
    if 'global' in results[year] and target_week in results[year]['global']:
        kpis = results[year]['global'][target_week]
        print(f"  满期保费: {kpis['满期保费']:.2f}万元")
        print(f"  满期边际贡献率: {kpis['满期边际贡献率']:.2f}%")
    if 'third_org' in results[year]:
        print(f"  三级机构数量: {len(results[year]['third_org'])}个")
```

## 使用示例

```python
# 示例1: 计算第44周全局和三级机构KPI
insurance-kpi-calculator(
    target_week=44,
    data_folder="处理后/",
    aggregation_levels=['global', 'third_org']
)

# 示例2: 只计算全局KPI（快速模式）
insurance-kpi-calculator(
    target_week=44,
    aggregation_levels=['global']
)
```

## 输出文件

- `.cache_kpi_week_XX.pkl`: KPI计算结果缓存

## 下一步

KPI计算完成后，调用：
- `insurance-anomaly-detector`: 识别异常指标
- `insurance-org-dimension-drilldown`: 进行维度下钻分析
