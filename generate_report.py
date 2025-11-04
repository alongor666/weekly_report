#!/usr/bin/env python3
"""
车险周报生成脚本
自动生成2024和2025保单的经营周报
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# ==================== 配置参数 ====================
TARGET_WEEK = 44
DATA_FOLDER = Path(".")
OUTPUT_FOLDER = Path("./周报")

# 创建输出目录
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# ==================== KPI计算函数 ====================
def calculate_kpis(df):
    """计算KPI指标"""
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

    return {
        '满期保费': round(matured_premium / 10000, 2),
        '保单件数': int(policy_count),
        '赔案件数': int(claim_case_count),
        '赔付率': round(loss_ratio, 2),
        '费用率': round(expense_ratio, 2),
        '边贡率': round(contrib_ratio, 2)
    }


def judge_status(kpi_name, value):
    """判断KPI状态"""
    if kpi_name == '赔付率':
        if value < 50: return '🟢 优秀'
        if value < 60: return '🟢 健康'
        if value < 70: return '🔵 中等'
        if value < 80: return '🟡 预警'
        return '🔴 危险'
    elif kpi_name == '边贡率':
        if value > 12: return '🟢 优秀'
        if value >= 8: return '🟢 健康'
        if value >= 6: return '🔵 中等'
        if value >= 4: return '🟡 预警'
        return '🔴 危险'
    elif kpi_name == '费用率':
        if value < 7.5: return '🟢 优秀'
        if value < 12.5: return '🟢 健康'
        if value < 17.5: return '🔵 中等'
        if value < 22.5: return '🟡 预警'
        return '🔴 危险'
    return '⚪ 中性'


# ==================== 渐进式下钻函数 ====================
def drilldown_org(df_org, org_name, total_premium):
    """对单个三级机构执行渐进式下钻分析"""

    result = {
        'org_name': org_name,
        'org_kpis': None,
        'energy_analysis': {}
    }

    # 机构整体KPI
    org_kpis = calculate_kpis(df_org)
    result['org_kpis'] = org_kpis

    # 第1层：能源类型分组
    for energy_flag in [True, False]:
        energy_name = "新能源车" if energy_flag else "传统车"
        df_energy = df_org[df_org['is_new_energy_vehicle'] == energy_flag]

        if len(df_energy) == 0:
            continue

        kpis_energy = calculate_kpis(df_energy)
        ratio = (kpis_energy['满期保费'] / org_kpis['满期保费']) * 100

        # 占比<1%跳过
        if ratio < 1.0:
            continue

        energy_healthy = kpis_energy['赔付率'] < 70 and kpis_energy['边贡率'] > 8

        result['energy_analysis'][energy_name] = {
            'kpis': kpis_energy,
            'ratio': ratio,
            'healthy': energy_healthy,
            'business_problems': []
        }

        # 如果健康，跳过第2层
        if energy_healthy:
            continue

        # 第2层：业务类型下钻
        business_groups = df_energy.groupby('business_type_category')
        business_problems = []

        for biz_type, df_biz in business_groups:
            kpis_biz = calculate_kpis(df_biz)
            biz_ratio = (kpis_biz['满期保费'] / kpis_energy['满期保费']) * 100

            # 占比<1%跳过
            if biz_ratio < 1.0:
                continue

            # 计算严重度
            loss_deviation = max(0, kpis_biz['赔付率'] - 70)
            contrib_deviation = max(0, 6 - kpis_biz['边贡率'])
            severity = (loss_deviation * 3 + contrib_deviation * 2.5) * biz_ratio

            business_problems.append({
                'business_type': biz_type,
                'kpis': kpis_biz,
                'ratio': biz_ratio,
                'severity': severity,
                'coverage_drilldown': [],
                'renewal_drilldown': []
            })

        # 排序取TOP3
        business_problems.sort(key=lambda x: x['severity'], reverse=True)
        top3_problems = business_problems[:3]

        # 第3层：对TOP3执行险别/新转续下钻
        for problem in top3_problems:
            biz_type = problem['business_type']
            df_biz = df_energy[df_energy['business_type_category'] == biz_type]
            biz_total = problem['kpis']['满期保费']

            # 路径A：险别
            for coverage in ['主全', '交三', '单交']:
                df_c = df_biz[df_biz['coverage_type'] == coverage]
                if len(df_c) == 0:
                    continue

                kpis_c = calculate_kpis(df_c)
                c_ratio = (kpis_c['满期保费'] / biz_total) * 100

                problem['coverage_drilldown'].append({
                    'coverage': coverage,
                    'kpis': kpis_c,
                    'ratio': c_ratio
                })

            # 按赔付率排序
            problem['coverage_drilldown'].sort(key=lambda x: x['kpis']['赔付率'], reverse=True)

            # 路径B：新转续
            for renewal in ['新保', '续保', '转保']:
                df_r = df_biz[df_biz['renewal_status'] == renewal]
                if len(df_r) == 0:
                    continue

                kpis_r = calculate_kpis(df_r)
                r_ratio = (kpis_r['满期保费'] / biz_total) * 100

                problem['renewal_drilldown'].append({
                    'renewal': renewal,
                    'kpis': kpis_r,
                    'ratio': r_ratio
                })

            # 按赔付率排序
            problem['renewal_drilldown'].sort(key=lambda x: x['kpis']['赔付率'], reverse=True)

        result['energy_analysis'][energy_name]['business_problems'] = top3_problems

    return result


# ==================== Markdown生成函数 ====================
def generate_markdown(year, week, global_kpis, org_results):
    """生成周报Markdown内容"""

    md = []

    # 标题
    md.append(f"# {year}保单第{week}周车险业务经营周报\n")
    md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"**数据来源**: {year}保单第{week}周变动成本明细表\n")
    md.append("---\n")

    # 一、全局核心指标
    md.append("## 一、全局核心指标驾驶舱\n")
    md.append("| 指标 | 数值 | 状态 |")
    md.append("|------|------|------|")
    md.append(f"| 满期保费 | {global_kpis['满期保费']:,.2f} 万元 | ⚪ 规模 |")
    md.append(f"| 保单件数 | {global_kpis['保单件数']:,} 件 | ⚪ 规模 |")
    md.append(f"| 满期赔付率 | {global_kpis['赔付率']:.2f}% | {judge_status('赔付率', global_kpis['赔付率'])} |")
    md.append(f"| 费用率 | {global_kpis['费用率']:.2f}% | {judge_status('费用率', global_kpis['费用率'])} |")
    md.append(f"| 满期边际贡献率 | {global_kpis['边贡率']:.2f}% | {judge_status('边贡率', global_kpis['边贡率'])} |")
    md.append("")

    # 二、三级机构快速索引
    md.append("## 二、三级机构快速索引\n")
    md.append("| 机构 | 满期保费(万) | 占比 | 赔付率 | 边贡率 | 状态 |")
    md.append("|------|-------------|------|--------|--------|------|")

    total_premium = global_kpis['满期保费']
    for result in org_results:
        org_kpis = result['org_kpis']
        ratio = (org_kpis['满期保费'] / total_premium) * 100
        status = "🟢 健康" if (org_kpis['赔付率'] < 70 and org_kpis['边贡率'] > 8) else "🔴 关注"

        md.append(f"| {result['org_name']} | {org_kpis['满期保费']:,.2f} | {ratio:.1f}% | "
                  f"{org_kpis['赔付率']:.2f}% | {org_kpis['边贡率']:.2f}% | {status} |")

    md.append("")

    # 三、三级机构深度诊断
    md.append("## 三、三级机构深度诊断\n")

    for idx, result in enumerate(org_results, 1):
        org_name = result['org_name']
        org_kpis = result['org_kpis']

        md.append(f"### {idx}. {org_name}\n")

        # 机构整体KPI
        md.append("#### 核心指标\n")
        md.append("| 指标 | 数值 |")
        md.append("|------|------|")
        md.append(f"| 满期保费 | {org_kpis['满期保费']:,.2f} 万元 |")
        md.append(f"| 保单件数 | {org_kpis['保单件数']:,} 件 |")
        md.append(f"| 赔案件数 | {org_kpis['赔案件数']:,} 件 |")
        md.append(f"| 赔付率 | {org_kpis['赔付率']:.2f}% {judge_status('赔付率', org_kpis['赔付率'])} |")
        md.append(f"| 费用率 | {org_kpis['费用率']:.2f}% {judge_status('费用率', org_kpis['费用率'])} |")
        md.append(f"| 边贡率 | {org_kpis['边贡率']:.2f}% {judge_status('边贡率', org_kpis['边贡率'])} |")
        md.append("")

        # 能源类型分析
        if result['energy_analysis']:
            md.append("#### 能源类型分析\n")

            for energy_name, energy_info in result['energy_analysis'].items():
                kpis = energy_info['kpis']
                ratio = energy_info['ratio']
                healthy = energy_info['healthy']

                status = "🟢 健康" if healthy else "🔴 有问题"
                md.append(f"**{energy_name}** ({ratio:.1f}%占比) - {status}\n")
                md.append(f"- 满期保费: {kpis['满期保费']:,.2f} 万元")
                md.append(f"- 赔付率: {kpis['赔付率']:.2f}%")
                md.append(f"- 边贡率: {kpis['边贡率']:.2f}%")
                md.append("")

                # 业务类型问题
                if energy_info['business_problems']:
                    md.append(f"**{energy_name}问题业务类型（TOP3）**:\n")

                    for rank, problem in enumerate(energy_info['business_problems'], 1):
                        biz_type = problem['business_type']
                        biz_kpis = problem['kpis']

                        md.append(f"{rank}. **{biz_type}**")
                        md.append(f"   - 满期保费: {biz_kpis['满期保费']:,.2f} 万 (占{energy_name}{problem['ratio']:.1f}%)")
                        md.append(f"   - 赔付率: {biz_kpis['赔付率']:.2f}% | 边贡率: {biz_kpis['边贡率']:.2f}%")

                        # 险别下钻
                        if problem['coverage_drilldown']:
                            coverage_strs = [f"{c['coverage']}({c['kpis']['赔付率']:.1f}%)"
                                           for c in problem['coverage_drilldown'][:3]]
                            md.append(f"   - **按险别**: {' | '.join(coverage_strs)}")

                        # 新转续下钻
                        if problem['renewal_drilldown']:
                            renewal_strs = [f"{r['renewal']}({r['kpis']['赔付率']:.1f}%)"
                                          for r in problem['renewal_drilldown'][:3]]
                            md.append(f"   - **按新转续**: {' | '.join(renewal_strs)}")

                        md.append("")

        md.append("---\n")

    return "\n".join(md)


# ==================== 主程序 ====================
def main():
    print("="*60)
    print(f"📊 开始生成第{TARGET_WEEK}周车险业务经营周报")
    print("="*60)

    for year in ['2024', '2025']:
        file_path = DATA_FOLDER / f"{year}保单第{TARGET_WEEK}周变动成本明细表.csv"

        if not file_path.exists():
            print(f"\n⚠️  {year}保单数据文件不存在: {file_path}")
            continue

        print(f"\n{'='*40}")
        print(f"  处理{year}保单")
        print(f"{'='*40}")

        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df = df[df['third_level_organization'] != '本部'].copy()
        print(f"✅ 数据加载: {len(df)}行")

        # 计算全局KPI
        global_kpis = calculate_kpis(df)
        print(f"✅ 全局KPI: 满期保费{global_kpis['满期保费']:,.2f}万, "
              f"赔付率{global_kpis['赔付率']:.2f}%, 边贡率{global_kpis['边贡率']:.2f}%")

        # 获取三级机构列表
        third_orgs = sorted(df['third_level_organization'].unique())
        print(f"✅ 三级机构: {len(third_orgs)}个")

        # 对每个三级机构执行下钻
        print(f"\n开始下钻分析...")
        org_results = []

        for org_name in third_orgs:
            df_org = df[df['third_level_organization'] == org_name]
            if len(df_org) == 0:
                continue

            result = drilldown_org(df_org, org_name, global_kpis['满期保费'])
            org_results.append(result)
            print(f"  ✓ {org_name}: 满期保费{result['org_kpis']['满期保费']:.2f}万")

        # 生成Markdown
        print(f"\n生成Markdown周报...")
        markdown_content = generate_markdown(year, TARGET_WEEK, global_kpis, org_results)

        # 保存文件
        output_file = OUTPUT_FOLDER / f"{year}保单第{TARGET_WEEK}周经营周报.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✅ 周报已生成: {output_file}")
        print(f"   文件大小: {len(markdown_content):,} 字符")

    print("\n" + "="*60)
    print("✅ 所有周报生成完成！")
    print("="*60)


if __name__ == "__main__":
    main()
