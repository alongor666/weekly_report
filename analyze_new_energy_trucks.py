#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025保单第28-43周新能源货车专项分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 分析配置
START_WEEK = 28
END_WEEK = 43
DATA_FOLDER = "2025年保单"
OUTPUT_FOLDER = "周报"

class NewEnergyTruckAnalyzer:
    """新能源货车专项分析器"""

    def __init__(self, data_folder, start_week, end_week):
        self.data_folder = Path(data_folder)
        self.start_week = start_week
        self.end_week = end_week
        self.weekly_data = {}
        self.cumulative_data = {}

    def load_data(self):
        """加载指定周次的数据"""
        print(f"\n📊 加载第{self.start_week}-{self.end_week}周数据...")

        available_weeks = []
        missing_weeks = []

        for week in range(self.start_week, self.end_week + 1):
            file_pattern = f"2025保单第{week}周变动成本明细表.csv"
            file_path = self.data_folder / file_pattern

            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')

                    # 筛选新能源货车数据
                    # is_new_energy_vehicle = True 且 business_type_category 包含"货车"
                    truck_df = df[
                        (df['is_new_energy_vehicle'] == True) &
                        (df['business_type_category'].str.contains('货车', na=False))
                    ].copy()

                    if len(truck_df) > 0:
                        self.cumulative_data[week] = truck_df
                        available_weeks.append(week)
                        print(f"  ✅ 第{week}周: {len(truck_df):,}条新能源货车记录")
                    else:
                        print(f"  ⚠️  第{week}周: 无新能源货车数据")
                        missing_weeks.append(week)

                except Exception as e:
                    print(f"  ❌ 第{week}周: 加载失败 - {e}")
                    missing_weeks.append(week)
            else:
                print(f"  ❌ 第{week}周: 文件不存在")
                missing_weeks.append(week)

        print(f"\n✅ 数据加载完成:")
        print(f"  - 成功加载: {len(available_weeks)}周")
        print(f"  - 缺失周次: {missing_weeks}")

        return available_weeks, missing_weeks

    def calculate_weekly_kpis(self):
        """计算各周核心KPI"""
        print("\n📈 计算各周核心指标...")

        weekly_kpis = {}

        for week in sorted(self.cumulative_data.keys()):
            df = self.cumulative_data[week]

            # 基础指标
            signed_premium = df['signed_premium_yuan'].sum()
            matured_premium = df['matured_premium_yuan'].sum()
            total_claims = df['reported_claim_payment_yuan'].sum()
            total_expenses = df['expense_amount_yuan'].sum()
            policy_count = df['policy_count'].sum()
            claim_cases = df['claim_case_count'].sum()

            # 计算率值
            loss_ratio = (total_claims / matured_premium * 100) if matured_premium > 0 else 0
            expense_ratio = (total_expenses / signed_premium * 100) if signed_premium > 0 else 0
            claim_frequency = (claim_cases / policy_count * 100) if policy_count > 0 else 0
            avg_claim_amount = (total_claims / claim_cases) if claim_cases > 0 else 0
            avg_premium = (signed_premium / policy_count) if policy_count > 0 else 0

            # 边际贡献率
            contribution_margin = 100 - loss_ratio - expense_ratio

            weekly_kpis[week] = {
                '周次': week,
                '签单保费(万元)': round(signed_premium / 10000, 2),
                '满期保费(万元)': round(matured_premium / 10000, 2),
                '已报告赔款(万元)': round(total_claims / 10000, 2),
                '费用总额(万元)': round(total_expenses / 10000, 2),
                '保单件数': int(policy_count),
                '赔案件数': int(claim_cases),
                '赔付率(%)': round(loss_ratio, 2),
                '费用率(%)': round(expense_ratio, 2),
                '边际贡献率(%)': round(contribution_margin, 2),
                '出险率(%)': round(claim_frequency, 2),
                '案均赔款(元)': round(avg_claim_amount, 0),
                '单均保费(元)': round(avg_premium, 0)
            }

            print(f"  第{week}周: 赔付率 {loss_ratio:.1f}%, 保费 {signed_premium/10000:.2f}万元, 保单 {policy_count}件")

        return weekly_kpis

    def analyze_regional_performance(self):
        """分析区域表现"""
        print("\n🗺️  区域表现分析...")

        # 使用最新周的数据
        latest_week = max(self.cumulative_data.keys())
        latest_df = self.cumulative_data[latest_week]

        regional_analysis = []

        for org in latest_df['third_level_organization'].unique():
            if pd.isna(org) or org == '本部':
                continue

            org_df = latest_df[latest_df['third_level_organization'] == org]

            signed_premium = org_df['signed_premium_yuan'].sum()
            matured_premium = org_df['matured_premium_yuan'].sum()
            total_claims = org_df['reported_claim_payment_yuan'].sum()
            policy_count = org_df['policy_count'].sum()
            claim_cases = org_df['claim_case_count'].sum()

            # 只保留有一定业务规模的机构
            if signed_premium < 10000:  # 小于1万元的忽略
                continue

            loss_ratio = (total_claims / matured_premium * 100) if matured_premium > 0 else 0
            claim_frequency = (claim_cases / policy_count * 100) if policy_count > 0 else 0
            avg_claim = (total_claims / claim_cases) if claim_cases > 0 else 0

            # 判断风险等级
            if loss_ratio >= 80:
                risk_level = "🔴 高危"
            elif loss_ratio >= 70:
                risk_level = "🟠 预警"
            elif loss_ratio >= 60:
                risk_level = "🟡 关注"
            else:
                risk_level = "🟢 良好"

            regional_analysis.append({
                '机构': org,
                '签单保费(万元)': round(signed_premium / 10000, 2),
                '满期保费(万元)': round(matured_premium / 10000, 2),
                '保单件数': int(policy_count),
                '赔付率(%)': round(loss_ratio, 2),
                '出险率(%)': round(claim_frequency, 2),
                '案均赔款(元)': round(avg_claim, 0),
                '风险等级': risk_level
            })

        # 按赔付率降序排序
        regional_analysis = sorted(regional_analysis, key=lambda x: x['赔付率(%)'], reverse=True)

        return regional_analysis

    def analyze_business_types(self):
        """分析不同货车类型"""
        print("\n🚛 货车类型分析...")

        latest_week = max(self.cumulative_data.keys())
        latest_df = self.cumulative_data[latest_week]

        business_analysis = []

        for business_type in latest_df['business_type_category'].unique():
            if pd.isna(business_type):
                continue

            biz_df = latest_df[latest_df['business_type_category'] == business_type]

            signed_premium = biz_df['signed_premium_yuan'].sum()
            matured_premium = biz_df['matured_premium_yuan'].sum()
            total_claims = biz_df['reported_claim_payment_yuan'].sum()
            policy_count = biz_df['policy_count'].sum()

            if signed_premium < 10000:
                continue

            loss_ratio = (total_claims / matured_premium * 100) if matured_premium > 0 else 0

            business_analysis.append({
                '业务类型': business_type,
                '签单保费(万元)': round(signed_premium / 10000, 2),
                '保单件数': int(policy_count),
                '赔付率(%)': round(loss_ratio, 2)
            })

        business_analysis = sorted(business_analysis, key=lambda x: x['签单保费(万元)'], reverse=True)

        return business_analysis

    def analyze_trend(self, weekly_kpis):
        """趋势分析"""
        print("\n📊 趋势分析...")

        weeks = sorted(weekly_kpis.keys())

        if len(weeks) < 2:
            return {
                'trend': '数据不足',
                'insights': []
            }

        # 提取关键指标趋势
        loss_ratios = [weekly_kpis[w]['赔付率(%)'] for w in weeks]
        premiums = [weekly_kpis[w]['签单保费(万元)'] for w in weeks]
        avg_claims = [weekly_kpis[w]['案均赔款(元)'] for w in weeks]
        claim_frequencies = [weekly_kpis[w]['出险率(%)'] for w in weeks]

        insights = []

        # 赔付率趋势
        loss_ratio_change = loss_ratios[-1] - loss_ratios[0]
        loss_ratio_avg = np.mean(loss_ratios)
        loss_ratio_std = np.std(loss_ratios)

        if loss_ratio_change > 10:
            insights.append(f"⚠️ 赔付率从第{weeks[0]}周的{loss_ratios[0]:.1f}%上升至第{weeks[-1]}周的{loss_ratios[-1]:.1f}%，累计上升{loss_ratio_change:.1f}个百分点")
        elif loss_ratio_change < -10:
            insights.append(f"✅ 赔付率从第{weeks[0]}周的{loss_ratios[0]:.1f}%下降至第{weeks[-1]}周的{loss_ratios[-1]:.1f}%，累计下降{abs(loss_ratio_change):.1f}个百分点")
        else:
            insights.append(f"📊 赔付率相对稳定，在{loss_ratios[0]:.1f}%-{loss_ratios[-1]:.1f}%之间波动")

        # 保费规模趋势
        premium_change = premiums[-1] - premiums[0]
        premium_growth_rate = (premium_change / premiums[0] * 100) if premiums[0] > 0 else 0

        if premium_growth_rate > 20:
            insights.append(f"📈 业务规模快速增长，保费从{premiums[0]:.2f}万元增至{premiums[-1]:.2f}万元，增长{premium_growth_rate:.1f}%")
        elif premium_growth_rate > 0:
            insights.append(f"📈 业务规模稳步增长，保费增长{premium_growth_rate:.1f}%")
        else:
            insights.append(f"📉 业务规模下降{abs(premium_growth_rate):.1f}%")

        # 案均赔款趋势
        avg_claim_change = avg_claims[-1] - avg_claims[0]
        if avg_claim_change > 5000:
            insights.append(f"⚠️ 案均赔款显著上升，从{avg_claims[0]:,.0f}元增至{avg_claims[-1]:,.0f}元，增加{avg_claim_change:,.0f}元")
        elif avg_claim_change < -5000:
            insights.append(f"✅ 案均赔款有所下降，减少{abs(avg_claim_change):,.0f}元")

        # 出险率趋势
        claim_freq_change = claim_frequencies[-1] - claim_frequencies[0]
        if claim_freq_change > 5:
            insights.append(f"⚠️ 出险率上升{claim_freq_change:.1f}个百分点，风险暴露增加")

        # 波动性分析
        if loss_ratio_std > 10:
            insights.append(f"⚠️ 赔付率波动较大（标准差{loss_ratio_std:.1f}），业务稳定性不足")

        return {
            'loss_ratio_avg': round(loss_ratio_avg, 2),
            'loss_ratio_std': round(loss_ratio_std, 2),
            'loss_ratio_change': round(loss_ratio_change, 2),
            'premium_growth_rate': round(premium_growth_rate, 2),
            'insights': insights
        }

    def identify_problem_weeks(self, weekly_kpis):
        """识别问题周次"""
        print("\n🔍 识别异常周次...")

        weeks = sorted(weekly_kpis.keys())
        problem_weeks = []

        # 计算平均值
        avg_loss_ratio = np.mean([weekly_kpis[w]['赔付率(%)'] for w in weeks])
        avg_claim = np.mean([weekly_kpis[w]['案均赔款(元)'] for w in weeks])

        for i, week in enumerate(weeks):
            kpi = weekly_kpis[week]
            issues = []

            # 检查赔付率异常
            if kpi['赔付率(%)'] > 80:
                issues.append("赔付率过高(>80%)")
            elif kpi['赔付率(%)'] > avg_loss_ratio * 1.3:
                issues.append(f"赔付率显著高于均值({kpi['赔付率(%)']:.1f}% vs {avg_loss_ratio:.1f}%)")

            # 检查案均赔款异常
            if kpi['案均赔款(元)'] > avg_claim * 1.5:
                issues.append(f"案均赔款异常({kpi['案均赔款(元)']:,.0f}元 vs 均值{avg_claim:,.0f}元)")

            # 检查出险率异常
            if kpi['出险率(%)'] > 30:
                issues.append(f"出险率过高({kpi['出险率(%)']:.1f}%)")

            # 检查周环比异常
            if i > 0:
                prev_week = weeks[i-1]
                prev_kpi = weekly_kpis[prev_week]

                loss_ratio_change = kpi['赔付率(%)'] - prev_kpi['赔付率(%)']
                if loss_ratio_change > 15:
                    issues.append(f"赔付率单周暴涨{loss_ratio_change:.1f}个百分点")

            if issues:
                problem_weeks.append({
                    '周次': week,
                    '问题': ', '.join(issues),
                    '赔付率': kpi['赔付率(%)'],
                    '案均赔款': kpi['案均赔款(元)']
                })

        return problem_weeks

    def generate_report(self, weekly_kpis, regional_analysis, business_analysis, trend_analysis, problem_weeks):
        """生成分析报告"""
        print("\n📝 生成分析报告...")

        weeks = sorted(weekly_kpis.keys())
        latest_week = weeks[-1]
        latest_kpi = weekly_kpis[latest_week]

        report = f"""# 2025保单新能源货车专项分析报告
## 分析周期：第{self.start_week}周 至 第{self.end_week}周

---

## 一、执行摘要

### 核心结论
"""

        # 生成核心结论
        if latest_kpi['赔付率(%)'] > 80:
            report += f"新能源货车业务处于**高风险状态**，最新周次（第{latest_week}周）赔付率达到**{latest_kpi['赔付率(%)']}%**，"
        elif latest_kpi['赔付率(%)'] > 70:
            report += f"新能源货车业务处于**风险预警状态**，最新周次（第{latest_week}周）赔付率为**{latest_kpi['赔付率(%)']}%**，"
        else:
            report += f"新能源货车业务表现**相对稳定**，最新周次（第{latest_week}周）赔付率为**{latest_kpi['赔付率(%)']}%**，"

        report += f"业务规模为**{latest_kpi['签单保费(万元)']}万元**，累计承保**{latest_kpi['保单件数']}件**保单。\n\n"

        # 关键指标
        report += f"""### 关键指标（第{latest_week}周累计值）

| 指标 | 数值 | 状态 |
|------|------|------|
| 签单保费 | {latest_kpi['签单保费(万元)']:.2f}万元 | - |
| 满期保费 | {latest_kpi['满期保费(万元)']:.2f}万元 | - |
| 保单件数 | {latest_kpi['保单件数']:,}件 | - |
| 赔付率 | {latest_kpi['赔付率(%)']}% | {"🔴 高危" if latest_kpi['赔付率(%)'] > 80 else "🟠 预警" if latest_kpi['赔付率(%)'] > 70 else "🟡 关注" if latest_kpi['赔付率(%)'] > 60 else "🟢 良好"} |
| 费用率 | {latest_kpi['费用率(%)']}% | - |
| 边际贡献率 | {latest_kpi['边际贡献率(%)']}% | {"🔴 亏损" if latest_kpi['边际贡献率(%)'] < 0 else "🟠 微利" if latest_kpi['边际贡献率(%)'] < 5 else "🟢 健康"} |
| 出险率 | {latest_kpi['出险率(%)']}% | {"⚠️ 过高" if latest_kpi['出险率(%)'] > 25 else "正常"} |
| 案均赔款 | {latest_kpi['案均赔款(元)']:,.0f}元 | - |
| 单均保费 | {latest_kpi['单均保费(元)']:,.0f}元 | - |

---

## 二、趋势分析

### 分析周期表现
分析周期：第{self.start_week}周 - 第{self.end_week}周，共{len(weeks)}周

"""

        # 趋势洞察
        if trend_analysis['insights']:
            report += "### 核心发现\n\n"
            for insight in trend_analysis['insights']:
                report += f"- {insight}\n"
            report += "\n"

        # 统计指标
        report += f"""### 统计指标

- 平均赔付率: {trend_analysis['loss_ratio_avg']}%
- 赔付率标准差: {trend_analysis['loss_ratio_std']}
- 赔付率变化: {trend_analysis['loss_ratio_change']:+.2f}个百分点
- 保费增长率: {trend_analysis['premium_growth_rate']:+.2f}%

"""

        # 各周详细数据
        report += "### 各周详细指标\n\n"
        report += "| 周次 | 签单保费(万) | 保单件数 | 赔付率(%) | 出险率(%) | 案均赔款(元) | 边际贡献率(%) |\n"
        report += "|------|-------------|----------|-----------|-----------|-------------|---------------|\n"

        for week in weeks:
            kpi = weekly_kpis[week]
            report += f"| 第{kpi['周次']}周 | {kpi['签单保费(万元)']:.2f} | {kpi['保单件数']:,} | {kpi['赔付率(%)']} | {kpi['出险率(%)']} | {kpi['案均赔款(元)']:,.0f} | {kpi['边际贡献率(%)']} |\n"

        report += "\n---\n\n"

        # 问题周次
        if problem_weeks:
            report += "## 三、异常周次识别\n\n"
            report += "以下周次存在异常指标，需要重点关注：\n\n"

            for problem in problem_weeks:
                report += f"### 第{problem['周次']}周\n"
                report += f"- **问题**: {problem['问题']}\n"
                report += f"- 赔付率: {problem['赔付率']}%\n"
                report += f"- 案均赔款: {problem['案均赔款']:,.0f}元\n\n"
        else:
            report += "## 三、异常周次识别\n\n✅ 未发现明显异常周次\n\n"

        report += "---\n\n"

        # 区域分析
        report += "## 四、区域表现分析\n\n"
        report += "### 各机构业务表现（按赔付率降序）\n\n"
        report += "| 机构 | 签单保费(万) | 保单件数 | 赔付率(%) | 出险率(%) | 案均赔款(元) | 风险等级 |\n"
        report += "|------|-------------|----------|-----------|-----------|-------------|----------|\n"

        for region in regional_analysis[:10]:  # 只显示前10个
            report += f"| {region['机构']} | {region['签单保费(万元)']:.2f} | {region['保单件数']:,} | {region['赔付率(%)']} | {region['出险率(%)']} | {region['案均赔款(元)']:,.0f} | {region['风险等级']} |\n"

        report += "\n"

        # 高风险机构
        high_risk_orgs = [r for r in regional_analysis if r['赔付率(%)'] > 80]
        if high_risk_orgs:
            report += f"### ⚠️ 高风险机构（赔付率>80%）\n\n"
            report += f"共有**{len(high_risk_orgs)}个机构**需要重点关注：\n\n"
            for org in high_risk_orgs:
                report += f"- **{org['机构']}**: 赔付率{org['赔付率(%)']}%, 保费规模{org['签单保费(万元)']:.2f}万元\n"
            report += "\n"

        report += "---\n\n"

        # 业务类型分析
        if business_analysis:
            report += "## 五、货车类型分析\n\n"
            report += "| 业务类型 | 签单保费(万) | 保单件数 | 赔付率(%) |\n"
            report += "|----------|-------------|----------|----------|\n"

            for biz in business_analysis:
                report += f"| {biz['业务类型']} | {biz['签单保费(万元)']:.2f} | {biz['保单件数']:,} | {biz['赔付率(%)']} |\n"

            report += "\n---\n\n"

        # 战略建议
        report += "## 六、战略建议与行动计划\n\n"
        report += "### 🚨 立即行动（24小时内）\n\n"

        if latest_kpi['赔付率(%)'] > 80:
            report += "1. **暂停高风险机构新单承保**：对赔付率超过80%的机构立即暂停新单自动核保\n"
            report += "2. **启动大案调查**：调取最近4周案均赔款超过5万元的所有案件进行复核\n"
            report += "3. **紧急风险评估**：召集风控、核保、理赔部门紧急会议，评估业务持续性\n"
        elif latest_kpi['赔付率(%)'] > 70:
            report += "1. **加强核保审核**：提高高风险机构的人工审核比例至100%\n"
            report += "2. **理赔审核升级**：5000元以上案件需二次核定\n"
            report += "3. **客户资质复查**：对车队客户进行运营资质和车况复查\n"
        else:
            report += "1. **持续监控**：保持现有风控策略，密切监控关键指标变化\n"
            report += "2. **数据跟踪**：每周更新趋势分析，及时发现异常\n"

        report += "\n### ⏰ 本周内完成（7天）\n\n"
        report += "1. **问题机构专项复盘**：对高赔付率机构进行业务质量专项调查\n"
        report += "2. **费率充足性评估**：重新评估新能源货车费率水平，考虑调整\n"
        report += "3. **客户分层管理**：建立客户风险分级体系，差异化承保策略\n"
        report += "4. **理赔数据分析**：分析高赔付案件特征，识别共性风险因素\n"

        report += "\n### 📊 中期优化（1个月内）\n\n"
        report += "1. **定价模型优化**：基于累计数据优化新能源货车定价模型\n"
        report += "2. **风控规则升级**：建立新能源货车专项风控规则库\n"
        report += "3. **客户筛选机制**：完善客户准入标准，提高业务质量\n"
        report += "4. **区域策略调整**：根据各地表现制定差异化区域策略\n"

        report += "\n### 🎯 长期战略（3个月内）\n\n"
        report += "1. **数据能力建设**：接入车辆运行数据（BMS、GPS等），实现动态定价\n"
        report += "2. **合作伙伴开发**：寻找优质车队客户，建立长期合作关系\n"
        report += "3. **产品创新**：开发适配新能源货车特点的创新保险产品\n"
        report += "4. **服务生态构建**：打造充电、维修、救援一体化服务生态\n"

        report += "\n---\n\n"

        # 附录
        report += f"""## 附录：分析说明

### 数据来源
- 数据源：2025年保单变动成本明细表
- 分析周期：第{self.start_week}周 - 第{self.end_week}周
- 筛选条件：is_new_energy_vehicle = True 且 business_type_category 包含"货车"
- 统计口径：累计值（非当周发生值）

### 关键指标定义
- **赔付率** = 已报告赔款 / 满期保费 × 100%
- **费用率** = 费用总额 / 签单保费 × 100%
- **边际贡献率** = 100% - 赔付率 - 费用率
- **出险率** = 赔案件数 / 保单件数 × 100%
- **案均赔款** = 已报告赔款 / 赔案件数
- **单均保费** = 签单保费 / 保单件数

### 风险等级标准
- 🟢 良好：赔付率 < 60%
- 🟡 关注：60% ≤ 赔付率 < 70%
- 🟠 预警：70% ≤ 赔付率 < 80%
- 🔴 高危：赔付率 ≥ 80%

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*分析工具：新能源货车专项分析器 v1.0*
"""

        return report


def main():
    """主函数"""

    print("=" * 70)
    print("🚛 2025保单新能源货车专项分析")
    print("=" * 70)

    try:
        # 初始化分析器
        analyzer = NewEnergyTruckAnalyzer(DATA_FOLDER, START_WEEK, END_WEEK)

        # 加载数据
        available_weeks, missing_weeks = analyzer.load_data()

        if len(available_weeks) == 0:
            print("\n❌ 错误：未找到任何新能源货车数据")
            return False

        # 计算各周KPI
        weekly_kpis = analyzer.calculate_weekly_kpis()

        # 区域分析
        regional_analysis = analyzer.analyze_regional_performance()

        # 业务类型分析
        business_analysis = analyzer.analyze_business_types()

        # 趋势分析
        trend_analysis = analyzer.analyze_trend(weekly_kpis)

        # 识别问题周次
        problem_weeks = analyzer.identify_problem_weeks(weekly_kpis)

        # 生成报告
        report = analyzer.generate_report(
            weekly_kpis,
            regional_analysis,
            business_analysis,
            trend_analysis,
            problem_weeks
        )

        # 保存报告
        output_path = Path(OUTPUT_FOLDER)
        output_path.mkdir(exist_ok=True)

        report_filename = f"2025保单新能源货车分析报告_第{START_WEEK}-{END_WEEK}周.md"
        report_filepath = output_path / report_filename

        with open(report_filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ 报告生成成功: {report_filename}")
        print(f"📁 保存位置: {report_filepath.absolute()}")

        # 输出关键摘要
        latest_week = max(weekly_kpis.keys())
        latest_kpi = weekly_kpis[latest_week]

        print("\n" + "=" * 70)
        print("📊 核心指标摘要")
        print("=" * 70)
        print(f"分析周期: 第{START_WEEK}-{END_WEEK}周")
        print(f"最新周次: 第{latest_week}周")
        print(f"  - 签单保费: {latest_kpi['签单保费(万元)']:.2f}万元")
        print(f"  - 保单件数: {latest_kpi['保单件数']:,}件")
        print(f"  - 赔付率: {latest_kpi['赔付率(%)']}%")
        print(f"  - 边际贡献率: {latest_kpi['边际贡献率(%)']}%")
        print(f"  - 出险率: {latest_kpi['出险率(%)']}%")
        print(f"  - 案均赔款: {latest_kpi['案均赔款(元)']:,.0f}元")

        if trend_analysis['insights']:
            print("\n📈 核心发现:")
            for i, insight in enumerate(trend_analysis['insights'][:3], 1):
                print(f"  {i}. {insight}")

        if problem_weeks:
            print(f"\n⚠️  发现{len(problem_weeks)}个异常周次")

        print("\n" + "=" * 70)
        print("🎉 分析完成！")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
