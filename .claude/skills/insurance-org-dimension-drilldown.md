---
name: insurance-org-dimension-drilldown
description: 三级机构渐进式下钻分析器 - 从能源类型到业务类型TOP3，再到险别/新转续组合
---

# insurance-org-dimension-drilldown

## 使用场景

对单个三级机构进行深度诊断，执行渐进式下钻分析，精准定位问题根因。

## 功能说明

本skill采用三层渐进式下钻架构：
1. **第1层**：按能源类型分组（新能源 vs 传统），判断哪个有问题
2. **第2层**：针对有问题的能源类型，按业务类型分组，找出TOP3问题业务类型
3. **第3层**：针对每个TOP3问题业务类型，双路径下钻：
   - 路径A：业务类型 + 险别组合（主全/交三/单交）
   - 路径B：业务类型 + 新转续（新保/续保/转保）

## 下钻终止条件

- 能源类型健康（赔付率<70% 且 边贡率>8%）→ 跳过第2层，只汇总数据
- 业务类型占比<1%  → 跳过第3层下钻

## 前置条件

- 必须先执行 `insurance-data-loader` 和 `insurance-kpi-calculator`

## 输入参数

- `year`: 年度（'2024' 或 '2025'）
- `third_org_name`: 三级机构名称（如 '高新'）
- `target_week`: 目标周次（如 44）
- `data_folder`: 数据文件夹路径（默认 `处理后/`）

## 执行步骤

### Step 1: 加载数据

```python
import pandas as pd
import pickle
from pathlib import Path
import numpy as np

# 参数
year = "2025"
third_org_name = "高新"
target_week = 44
data_folder = "."

# 读取缓存数据
cache_file = Path(data_folder) / f".cache_week_{target_week}.pkl"

if not cache_file.exists():
    raise FileNotFoundError(f"❌ 缓存文件不存在，请先执行 insurance-data-loader")

with open(cache_file, 'rb') as f:
    cache = pickle.load(f)

data_by_year = cache['data_by_year']

# 获取该机构数据
if year not in data_by_year or target_week not in data_by_year[year]:
    raise ValueError(f"❌ {year}保单第{target_week}周数据不存在")

df_org = data_by_year[year][target_week]
df_org = df_org[df_org['third_level_organization'] == third_org_name].copy()

if len(df_org) == 0:
    raise ValueError(f"❌ 机构 {third_org_name} 无数据")

print("="*60)
print(f"📊 【{third_org_name}】渐进式下钻分析")
print(f"    {year}保单 第{target_week}周")
print("="*60)
print(f"\n数据行数: {len(df_org):,}")
```

### Step 2: 定义KPI计算函数

```python
def calculate_kpis(df):
    """计算KPI"""
    epsilon = 1e-10

    signed_premium = max(df['signed_premium_yuan'].sum(), epsilon)
    matured_premium = max(df['matured_premium_yuan'].sum(), epsilon)
    policy_count = max(df['policy_count'].sum(), epsilon)
    claim_case_count = max(df['claim_case_count'].sum(), epsilon)
    reported_claim = df['reported_claim_payment_yuan'].sum()
    expense_amount = df['expense_amount_yuan'].sum()

    loss_ratio = (reported_claim / matured_premium) * 100
    expense_ratio = (expense_amount / signed_premium) * 100
    contrib_ratio = 100 - loss_ratio - expense_ratio

    avg_claim = reported_claim / claim_case_count if claim_case_count > 1 else 0
    claim_rate = (claim_case_count / policy_count) * 100 if policy_count > 1 else 0

    return {
        '签单保费': signed_premium / 10000,
        '满期保费': matured_premium / 10000,
        '保单件数': int(policy_count),
        '赔案件数': int(claim_case_count),
        '赔付率': round(loss_ratio, 2),
        '费用率': round(expense_ratio, 2),
        '边贡率': round(contrib_ratio, 2),
        '案均赔款': round(avg_claim, 0),
        '出险率': round(claim_rate, 2)
    }


def judge_health(kpis):
    """判断是否健康"""
    return kpis['赔付率'] < 70 and kpis['边贡率'] > 8


def judge_severity(kpis, total_premium):
    """
    计算问题严重度
    严重度 = (赔付率偏离 × 3 + 边贡率偏离 × 2.5) × 规模占比
    """
    loss_deviation = max(0, kpis['赔付率'] - 70)
    contrib_deviation = max(0, 6 - kpis['边贡率'])
    scale_ratio = kpis['满期保费'] / total_premium

    severity = (loss_deviation * 3 + contrib_deviation * 2.5) * scale_ratio * 100

    return severity
```

### Step 3: 机构整体KPI

```python
org_kpis = calculate_kpis(df_org)
total_premium = org_kpis['满期保费']

print(f"\n【机构整体KPI】")
print(f"  满期保费: {org_kpis['满期保费']:,.2f} 万元")
print(f"  保单件数: {org_kpis['保单件数']:,} 件")
print(f"  赔付率: {org_kpis['赔付率']:.2f}%")
print(f"  费用率: {org_kpis['费用率']:.2f}%")
print(f"  边贡率: {org_kpis['边贡率']:.2f}%")

# 判断整体健康度
org_healthy = judge_health(org_kpis)
if org_healthy:
    print(f"  状态: 🟢 健康 (无需深度下钻)")
else:
    print(f"  状态: 🔴 有问题 (需要深度下钻)")
```

### Step 4: 第1层 - 能源类型分组

```python
print(f"\n{'='*60}")
print(f"【第1层】能源类型分组")
print(f"{'='*60}")

energy_analysis = {}

for energy_flag in [True, False]:
    energy_name = "新能源车" if energy_flag else "传统车"
    df_energy = df_org[df_org['is_new_energy_vehicle'] == energy_flag]

    if len(df_energy) == 0:
        print(f"\n❌ {energy_name}: 无数据")
        continue

    kpis_energy = calculate_kpis(df_energy)
    is_healthy = judge_health(kpis_energy)
    ratio = (kpis_energy['满期保费'] / total_premium) * 100

    # 判断是否占比过小
    if ratio < 1.0:
        print(f"\n⚪ {energy_name}: 占比{ratio:.1f}%<1%，跳过分析")
        continue

    print(f"\n【{energy_name}】")
    print(f"  满期保费: {kpis_energy['满期保费']:,.2f} 万元 (占比 {ratio:.1f}%)")
    print(f"  赔付率: {kpis_energy['赔付率']:.2f}%")
    print(f"  边贡率: {kpis_energy['边贡率']:.2f}%")
    print(f"  状态: {'🟢 健康' if is_healthy else '🔴 有问题'}")

    energy_analysis[energy_name] = {
        'data': df_energy,
        'kpis': kpis_energy,
        'healthy': is_healthy,
        'ratio': ratio,
        'business_problems': []  # 用于存储第2层分析结果
    }

    # 只对有问题的能源类型进行第2层下钻
    if not is_healthy:
        print(f"  → 需要进入第2层下钻")
```

### Step 5: 第2层 - 业务类型下钻（仅针对有问题的能源类型）

```python
print(f"\n{'='*60}")
print(f"【第2层】业务类型下钻（TOP3问题业务）")
print(f"{'='*60}")

for energy_name, energy_info in energy_analysis.items():
    if energy_info['healthy']:
        print(f"\n✅ {energy_name}: 健康，跳过业务类型下钻")
        continue

    print(f"\n" + "-"*40)
    print(f"  {energy_name} 业务类型分析")
    print("-"*40)

    df_energy = energy_info['data']

    # 按业务类型分组
    business_groups = df_energy.groupby('business_type_category')

    business_problems = []
    for biz_type, df_biz in business_groups:
        kpis_biz = calculate_kpis(df_biz)
        severity = judge_severity(kpis_biz, total_premium)
        ratio = (kpis_biz['满期保费'] / energy_info['kpis']['满期保费']) * 100

        # 只分析占比>=1%的业务类型
        if ratio < 1.0:
            continue

        business_problems.append({
            'business_type': biz_type,
            'kpis': kpis_biz,
            'severity': severity,
            'ratio': ratio
        })

    # 按严重度排序，取TOP3
    business_problems.sort(key=lambda x: x['severity'], reverse=True)
    top3_problems = business_problems[:3]

    if not top3_problems:
        print(f"  ✅ 未发现严重问题业务类型")
        continue

    print(f"\n  发现 {len(business_problems)} 个业务类型，以下是TOP3问题:")

    for rank, problem in enumerate(top3_problems, 1):
        biz_type = problem['business_type']
        kpis = problem['kpis']
        print(f"\n  🥇 #{rank} {biz_type}")
        print(f"     满期保费: {kpis['满期保费']:,.2f} 万元 (占{energy_name} {problem['ratio']:.1f}%)")
        print(f"     赔付率: {kpis['赔付率']:.2f}%")
        print(f"     边贡率: {kpis['边贡率']:.2f}%")
        print(f"     严重度评分: {problem['severity']:.1f}")

    energy_info['business_problems'] = top3_problems
```

### Step 6: 第3层 - 险别/新转续组合下钻（针对TOP3问题业务）

```python
print(f"\n{'='*60}")
print(f"【第3层】险别/新转续组合下钻")
print(f"{'='*60}")

for energy_name, energy_info in energy_analysis.items():
    if not energy_info['business_problems']:
        continue

    print(f"\n" + "="*40)
    print(f"  {energy_name}")
    print("="*40)

    df_energy = energy_info['data']

    for rank, problem in enumerate(energy_info['business_problems'], 1):
        biz_type = problem['business_type']
        print(f"\n{'-'*40}")
        print(f"🥇 #{rank} 问题业务: {biz_type}")
        print(f"{'-'*40}")

        # 筛选该业务类型数据
        df_biz = df_energy[df_energy['business_type_category'] == biz_type]
        biz_total_premium = problem['kpis']['满期保费']

        # 路径A: 险别组合下钻
        print(f"\n【路径A】按险别组合下钻")
        print(f"{'  ' + '-'*36}")

        coverage_results = []
        for coverage in ['主全', '交三', '单交']:
            df_coverage = df_biz[df_biz['coverage_type'] == coverage]
            if len(df_coverage) == 0:
                continue

            kpis_coverage = calculate_kpis(df_coverage)
            ratio = (kpis_coverage['满期保费'] / biz_total_premium) * 100

            coverage_results.append({
                'combination': f"{biz_type} + {coverage}",
                'kpis': kpis_coverage,
                'ratio': ratio
            })

        # 按赔付率排序，找最严重的
        coverage_results.sort(key=lambda x: x['kpis']['赔付率'], reverse=True)

        for i, result in enumerate(coverage_results):
            symbol = "  🔴" if i == 0 else ("  🟡" if i == 1 else "  🟢")
            kpis = result['kpis']
            print(f"{symbol} {result['combination']}")
            print(f"     满期保费: {kpis['满期保费']:,.2f} 万 (占比{result['ratio']:.1f}%)")
            print(f"     赔付率: {kpis['赔付率']:.2f}% | 边贡率: {kpis['边贡率']:.2f}%")
            print(f"     案均赔款: {kpis['案均赔款']:,.0f} 元 | 出险率: {kpis['出险率']:.1f}%")

        # 路径B: 新转续下钻
        print(f"\n【路径B】按新转续下钻")
        print(f"{'  ' + '-'*36}")

        renewal_results = []
        for renewal in ['新保', '续保', '转保']:
            df_renewal = df_biz[df_biz['renewal_status'] == renewal]
            if len(df_renewal) == 0:
                continue

            kpis_renewal = calculate_kpis(df_renewal)
            ratio = (kpis_renewal['满期保费'] / biz_total_premium) * 100

            renewal_results.append({
                'combination': f"{biz_type} + {renewal}",
                'kpis': kpis_renewal,
                'ratio': ratio
            })

        # 按赔付率排序
        renewal_results.sort(key=lambda x: x['kpis']['赔付率'], reverse=True)

        for i, result in enumerate(renewal_results):
            symbol = "  🔴" if i == 0 else ("  🟡" if i == 1 else "  🟢")
            kpis = result['kpis']
            print(f"{symbol} {result['combination']}")
            print(f"     满期保费: {kpis['满期保费']:,.2f} 万 (占比{result['ratio']:.1f}%)")
            print(f"     赔付率: {kpis['赔付率']:.2f}% | 边贡率: {kpis['边贡率']:.2f}%")
            print(f"     案均赔款: {kpis['案均赔款']:,.0f} 元 | 出险率: {kpis['出险率']:.1f}%")

        # 根因分析
        print(f"\n【问题根因分析】")
        worst_coverage = coverage_results[0] if coverage_results else None
        worst_renewal = renewal_results[0] if renewal_results else None

        if worst_coverage:
            print(f"  🎯 最严重险别组合: {worst_coverage['combination']}")
            print(f"     赔付率: {worst_coverage['kpis']['赔付率']:.2f}%")

        if worst_renewal:
            print(f"  🎯 最严重新转续组合: {worst_renewal['combination']}")
            print(f"     赔付率: {worst_renewal['kpis']['赔付率']:.2f}%")

        # 智能建议
        print(f"\n【改进建议】")
        if worst_coverage and worst_coverage['kpis']['赔付率'] > 80:
            print(f"  🚨 立即停止: {worst_coverage['combination']} 承保")
        elif worst_coverage and worst_coverage['kpis']['赔付率'] > 70:
            print(f"  ⚠️  提高费率: {worst_coverage['combination']} 费率+15-20%")

        if worst_renewal and worst_renewal['kpis']['赔付率'] > 80:
            if '续保' in worst_renewal['combination']:
                print(f"  🚨 建立黑名单: 历史赔付>2次的续保客户拒保")
            elif '转保' in worst_renewal['combination']:
                print(f"  🚨 强化核保: 转保车辆必须验车，提高准入标准")
```

### Step 7: 输出汇总报告

```python
print(f"\n" + "="*60)
print(f"✅ 【{third_org_name}】下钻分析完成")
print("="*60)

print(f"\n【核心发现】")
for energy_name, energy_info in energy_analysis.items():
    if energy_info['business_problems']:
        top_problem = energy_info['business_problems'][0]
        print(f"  🔴 {energy_name}: {top_problem['business_type']} 是最严重问题")
        print(f"     赔付率 {top_problem['kpis']['赔付率']:.2f}%, 边贡率 {top_problem['kpis']['边贡率']:.2f}%")
    elif not energy_info['healthy']:
        print(f"  🟡 {energy_name}: 整体有问题但无单一突出业务类型")
    else:
        print(f"  🟢 {energy_name}: 健康")

print(f"\n" + "="*60)
```

## 使用示例

```python
# 示例1: 分析高新机构2025保单第44周
insurance-org-dimension-drilldown(
    year="2025",
    third_org_name="高新",
    target_week=44,
    data_folder="处理后/"
)

# 示例2: 分析天府机构2024保单第44周
insurance-org-dimension-drilldown(
    year="2024",
    third_org_name="天府",
    target_week=44
)
```

## 输出内容

完整的三层下钻分析报告，包括：
1. 机构整体KPI
2. 能源类型分组分析
3. TOP3问题业务类型
4. 每个问题业务类型的险别/新转续组合明细
5. 问题根因分析和改进建议

## 下一步

下钻分析完成后，调用：
- `insurance-weekly-report-assembler`: 将所有机构的下钻结果整合成周报
