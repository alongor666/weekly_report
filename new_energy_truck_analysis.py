#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新能源货车专项分析工具
分析2025保单第28周至43周新能源货车数据
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class NewEnergyTruckAnalyzer:
    """新能源货车专项分析器"""
    
    def __init__(self):
        self.start_week = 28
        self.end_week = 43
        self.data_folder = Path("/Users/xuechenglong/Desktop/weekly_report/2025年保单")
        self.output_folder = Path("新能源货车分析报告")
        self.output_folder.mkdir(exist_ok=True)
        
    def load_weekly_data(self):
        """加载第28周至43周数据"""
        print("📊 加载2025年保单第28-43周数据...")
        
        all_data = []
        for week in range(self.start_week, self.end_week + 1):
            # 跳过缺失的周次
            if week in [32, 38]:  # 假设这些周次缺失
                continue
                
            file_path = self.data_folder / f"2025保单第{week}周变动成本明细表.csv"
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    # 筛选新能源货车数据
                    new_energy_trucks = df[
                        (df['is_new_energy_vehicle'] == True) & 
                        (df['customer_category_3'] == '营业货车')
                    ].copy()
                    new_energy_trucks['week'] = week
                    all_data.append(new_energy_trucks)
                    print(f"  第{week}周: {len(new_energy_trucks)}条新能源货车记录")
                except Exception as e:
                    print(f"  第{week}周数据加载失败: {e}")
            else:
                print(f"  第{week}周文件不存在")
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            print(f"✅ 成功加载 {len(combined_data)} 条新能源货车记录")
            return combined_data
        else:
            print("❌ 没有找到新能源货车数据")
            return pd.DataFrame()
    
    def calculate_weekly_kpis(self, df):
        """计算周度KPI指标"""
        print("📈 计算周度KPI指标...")
        
        weekly_kpis = []
        
        for week in sorted(df['week'].unique()):
            week_df = df[df['week'] == week]
            
            if len(week_df) == 0:
                continue
            
            # 核心指标计算
            signed_premium = week_df['signed_premium_yuan'].sum()
            matured_premium = week_df['matured_premium_yuan'].sum()
            reported_claims = week_df['reported_claim_payment_yuan'].sum()
            expense_amount = week_df['expense_amount_yuan'].sum()
            policy_count = week_df['policy_count'].sum()
            claim_count = week_df['claim_case_count'].sum()
            
            # 率值指标
            loss_ratio = (reported_claims / matured_premium * 100) if matured_premium > 0 else 0
            expense_ratio = (expense_amount / signed_premium * 100) if signed_premium > 0 else 0
            contribution_margin = 100 - loss_ratio - expense_ratio
            
            # 单均指标
            avg_premium = signed_premium / policy_count if policy_count > 0 else 0
            avg_claim = reported_claims / claim_count if claim_count > 0 else 0
            claim_rate = (claim_count / policy_count * 100) if policy_count > 0 else 0
            
            weekly_kpis.append({
                'week': week,
                'signed_premium': signed_premium / 10000,  # 万元
                'matured_premium': matured_premium / 10000,  # 万元
                'reported_claims': reported_claims / 10000,  # 万元
                'expense_amount': expense_amount / 10000,  # 万元
                'policy_count': policy_count,
                'claim_count': claim_count,
                'loss_ratio': loss_ratio,
                'expense_ratio': expense_ratio,
                'contribution_margin': contribution_margin,
                'avg_premium': avg_premium,
                'avg_claim': avg_claim,
                'claim_rate': claim_rate,
                'vehicle_count': len(week_df)
            })
        
        return pd.DataFrame(weekly_kpis)
    
    def analyze_by_dimensions(self, df):
        """多维度分析"""
        print("🔍 多维度分析...")
        
        analyses = {}
        
        # 1. 分机构分析
        org_analysis = []
        for org in df['third_level_organization'].unique():
            org_df = df[df['third_level_organization'] == org]
            
            total_premium = org_df['matured_premium_yuan'].sum()
            total_claims = org_df['reported_claim_payment_yuan'].sum()
            loss_ratio = (total_claims / total_premium * 100) if total_premium > 0 else 0
            
            org_analysis.append({
                'organization': org,
                'vehicle_count': len(org_df),
                'premium_amount': total_premium / 10000,
                'loss_ratio': loss_ratio,
                'avg_weekly_vehicles': len(org_df) / len(org_df['week'].unique()) if len(org_df) > 0 else 0
            })
        
        analyses['by_organization'] = pd.DataFrame(org_analysis)
        
        # 2. 分业务类型分析
        biz_analysis = []
        for biz_type in df['business_type_category'].unique():
            biz_df = df[df['business_type_category'] == biz_type]
            
            total_premium = biz_df['matured_premium_yuan'].sum()
            total_claims = biz_df['reported_claim_payment_yuan'].sum()
            loss_ratio = (total_claims / total_premium * 100) if total_premium > 0 else 0
            
            biz_analysis.append({
                'business_type': biz_type,
                'vehicle_count': len(biz_df),
                'premium_amount': total_premium / 10000,
                'loss_ratio': loss_ratio
            })
        
        analyses['by_business_type'] = pd.DataFrame(biz_analysis)
        
        # 3. 分险别分析
        coverage_analysis = []
        for coverage in df['coverage_type'].unique():
            coverage_df = df[df['coverage_type'] == coverage]
            
            total_premium = coverage_df['matured_premium_yuan'].sum()
            total_claims = coverage_df['reported_claim_payment_yuan'].sum()
            loss_ratio = (total_claims / total_premium * 100) if total_premium > 0 else 0
            
            coverage_analysis.append({
                'coverage_type': coverage,
                'vehicle_count': len(coverage_df),
                'premium_amount': total_premium / 10000,
                'loss_ratio': loss_ratio
            })
        
        analyses['by_coverage'] = pd.DataFrame(coverage_analysis)
        
        return analyses
    
    def identify_problems_and_trends(self, weekly_kpis, dimensional_analyses):
        """识别问题和趋势"""
        print("⚠️ 识别问题和趋势...")
        
        problems = {}
        
        # 1. 整体趋势分析
        if len(weekly_kpis) > 3:
            # 赔付率趋势
            loss_trend = np.polyfit(weekly_kpis['week'], weekly_kpis['loss_ratio'], 1)[0]
            
            # 业务规模趋势
            premium_trend = np.polyfit(weekly_kpis['week'], weekly_kpis['signed_premium'], 1)[0]
            
            problems['overall_trends'] = {
                'loss_ratio_trend': '上升' if loss_trend > 0.5 else '下降' if loss_trend < -0.5 else '稳定',
                'loss_ratio_slope': loss_trend,
                'premium_trend': '增长' if premium_trend > 1 else '下滑' if premium_trend < -1 else '稳定',
                'premium_slope': premium_trend
            }
        
        # 2. 高风险机构识别
        org_df = dimensional_analyses['by_organization']
        high_risk_orgs = org_df[org_df['loss_ratio'] > 80].sort_values('loss_ratio', ascending=False)
        
        problems['high_risk_organizations'] = high_risk_orgs.to_dict('records')
        
        # 3. 高风险业务类型识别
        biz_df = dimensional_analyses['by_business_type']
        high_risk_biz = biz_df[biz_df['loss_ratio'] > 80].sort_values('loss_ratio', ascending=False)
        
        problems['high_risk_business_types'] = high_risk_biz.to_dict('records')
        
        # 4. 异常波动检测
        if len(weekly_kpis) > 3:
            recent_weeks = weekly_kpis.tail(3)
            avg_loss = recent_weeks['loss_ratio'].mean()
            
            # 检测最近一周是否异常
            latest_loss = weekly_kpis.iloc[-1]['loss_ratio']
            if latest_loss > avg_loss * 1.2:
                problems['abnormal_fluctuation'] = {
                    'type': '赔付率突增',
                    'latest_value': latest_loss,
                    'recent_average': avg_loss,
                    'deviation': (latest_loss - avg_loss) / avg_loss
                }
        
        return problems
    
    def generate_executive_summary(self, weekly_kpis, dimensional_analyses, problems):
        """生成执行摘要"""
        print("📝 生成执行摘要...")
        
        if len(weekly_kpis) == 0:
            return {"error": "无数据"}
        
        # 最新一周数据
        latest = weekly_kpis.iloc[-1]
        
        # 累计数据
        total_vehicles = weekly_kpis['vehicle_count'].sum()
        total_premium = weekly_kpis['signed_premium'].sum()
        avg_loss_ratio = weekly_kpis['loss_ratio'].mean()
        
        # 核心结论
        core_conclusion = f"""
        2025年保单第{self.start_week}-{self.end_week}周，新能源货车业务呈现以下特征：
        - 累计承保{total_vehicles}辆，签单保费{total_premium:.1f}万元
        - 平均赔付率{avg_loss_ratio:.1f}%，整体{'盈利' if avg_loss_ratio < 70 else '亏损'}
        - 最新一周（第{latest['week']}周）赔付率{latest['loss_ratio']:.1f}%
        """
        
        # 关键风险点
        risk_points = []
        
        if problems.get('high_risk_organizations'):
            risk_orgs = problems['high_risk_organizations'][:3]
            risk_points.append(f"高风险机构：{', '.join([org['organization'] for org in risk_orgs])}")
        
        if problems.get('overall_trends', {}).get('loss_ratio_trend') == '上升':
            risk_points.append("赔付率呈上升趋势，需要重点关注")
        
        return {
            'core_conclusion': core_conclusion.strip(),
            'key_metrics': {
                'total_vehicles': total_vehicles,
                'total_premium': total_premium,
                'avg_loss_ratio': avg_loss_ratio,
                'latest_week': latest['week'],
                'latest_loss_ratio': latest['loss_ratio']
            },
            'risk_points': risk_points,
            'recommendations': [
                '加强对高风险机构的监控和管理',
                '分析赔付率上升的具体原因',
                '优化业务结构，提高优质业务占比'
            ]
        }
    
    def create_visualizations(self, weekly_kpis, dimensional_analyses):
        """创建可视化图表"""
        print("📊 创建可视化图表...")
        
        if len(weekly_kpis) == 0:
            print("  无数据，跳过图表生成")
            return
        
        plt.style.use('seaborn-v0_8')
        fig_size = (12, 8)
        
        # 1. 周度趋势图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 赔付率趋势
        ax1.plot(weekly_kpis['week'], weekly_kpis['loss_ratio'], 'ro-', linewidth=2, markersize=6)
        ax1.axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='警戒线70%')
        ax1.set_title('新能源货车周度赔付率趋势', fontsize=14, fontweight='bold')
        ax1.set_xlabel('周次')
        ax1.set_ylabel('赔付率(%)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 保费规模趋势
        ax2.bar(weekly_kpis['week'], weekly_kpis['signed_premium'], color='steelblue', alpha=0.7)
        ax2.set_title('新能源货车周度签单保费', fontsize=14, fontweight='bold')
        ax2.set_xlabel('周次')
        ax2.set_ylabel('签单保费(万元)')
        ax2.grid(True, alpha=0.3)
        
        # 案均赔款趋势
        ax3.plot(weekly_kpis['week'], weekly_kpis['avg_claim'], 'go-', linewidth=2, markersize=6)
        ax3.set_title('新能源货车案均赔款趋势', fontsize=14, fontweight='bold')
        ax3.set_xlabel('周次')
        ax3.set_ylabel('案均赔款(元)')
        ax3.grid(True, alpha=0.3)
        
        # 出险率趋势
        ax4.plot(weekly_kpis['week'], weekly_kpis['claim_rate'], 'bo-', linewidth=2, markersize=6)
        ax4.set_title('新能源货车出险率趋势', fontsize=14, fontweight='bold')
        ax4.set_xlabel('周次')
        ax4.set_ylabel('出险率(%)')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_folder / '新能源货车周度趋势分析.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 机构分析图
        org_df = dimensional_analyses['by_organization']
        if len(org_df) > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            # 机构赔付率对比
            colors = ['red' if x > 80 else 'orange' if x > 70 else 'green' for x in org_df['loss_ratio']]
            ax1.bar(range(len(org_df)), org_df['loss_ratio'], color=colors, alpha=0.7)
            ax1.set_xticks(range(len(org_df)))
            ax1.set_xticklabels(org_df['organization'], rotation=45)
            ax1.axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='警戒线70%')
            ax1.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='高危线80%')
            ax1.set_title('各机构新能源货车赔付率对比', fontsize=14, fontweight='bold')
            ax1.set_ylabel('赔付率(%)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 机构业务规模对比
            ax2.bar(range(len(org_df)), org_df['premium_amount'], color='steelblue', alpha=0.7)
            ax2.set_xticks(range(len(org_df)))
            ax2.set_xticklabels(org_df['organization'], rotation=45)
            ax2.set_title('各机构新能源货车保费规模', fontsize=14, fontweight='bold')
            ax2.set_ylabel('保费规模(万元)')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(self.output_folder / '新能源货车机构分析.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print("  ✅ 图表生成完成")
    
    def generate_markdown_report(self, weekly_kpis, dimensional_analyses, problems, summary):
        """生成Markdown格式报告"""
        print("📝 生成Markdown报告...")
        
        report = f"""# 新能源货车专项分析报告

## 执行摘要

{summary['core_conclusion']}

### 关键指标
- **累计承保车辆**: {summary['key_metrics']['total_vehicles']}辆
- **累计签单保费**: {summary['key_metrics']['total_premium']:.1f}万元  
- **平均赔付率**: {summary['key_metrics']['avg_loss_ratio']:.1f}%
- **最新周次**: 第{summary['key_metrics']['latest_week']}周
- **最新赔付率**: {summary['key_metrics']['latest_loss_ratio']:.1f}%

### 风险关注点
"""
        
        for risk in summary['risk_points']:
            report += f"- {risk}\n"
        
        report += "\n### 管理建议\n"
        for rec in summary['recommendations']:
            report += f"- {rec}\n"
        
        # 周度趋势分析
        if len(weekly_kpis) > 0:
            report += f"""

## 周度趋势分析

| 周次 | 签单保费(万元) | 赔付率(%) | 出险率(%) | 案均赔款(元) | 承保车辆数 |
|------|---------------|-----------|-----------|-------------|------------|\n"""
            
            for _, row in weekly_kpis.iterrows():
                report += f"| {row['week']} | {row['signed_premium']:.1f} | {row['loss_ratio']:.1f} | {row['claim_rate']:.1f} | {row['avg_claim']:.0f} | {row['vehicle_count']} |\n"
        
        # 机构分析
        org_df = dimensional_analyses['by_organization']
        if len(org_df) > 0:
            report += """

## 机构分析

### 高风险机构（赔付率>80%）
"""
            
            high_risk = org_df[org_df['loss_ratio'] > 80].sort_values('loss_ratio', ascending=False)
            if len(high_risk) > 0:
                report += """
| 机构 | 赔付率(%) | 保费规模(万元) | 车辆数 | 周均车辆数 |
|------|-----------|---------------|--------|------------|\n"""
                for _, row in high_risk.iterrows():
                    report += f"| {row['organization']} | {row['loss_ratio']:.1f} | {row['premium_amount']:.1f} | {row['vehicle_count']} | {row['avg_weekly_vehicles']:.1f} |\n"
            else:
                report += "\n暂无高风险机构\n"
            
            report += """
### 所有机构明细

| 机构 | 赔付率(%) | 保费规模(万元) | 车辆数 |
|------|-----------|---------------|--------|\n"""
            
            for _, row in org_df.sort_values('loss_ratio', ascending=False).iterrows():
                report += f"| {row['organization']} | {row['loss_ratio']:.1f} | {row['premium_amount']:.1f} | {row['vehicle_count']} |\n"
        
        # 业务类型分析
        biz_df = dimensional_analyses['by_business_type']
        if len(biz_df) > 0:
            report += """

## 业务类型分析

| 业务类型 | 赔付率(%) | 保费规模(万元) | 车辆数 |
|----------|-----------|---------------|--------|\n"""
            
            for _, row in biz_df.sort_values('loss_ratio', ascending=False).iterrows():
                report += f"| {row['business_type']} | {row['loss_ratio']:.1f} | {row['premium_amount']:.1f} | {row['vehicle_count']} |\n"
        
        # 险别分析
        coverage_df = dimensional_analyses['by_coverage']
        if len(coverage_df) > 0:
            report += """

## 险别分析

| 险别 | 赔付率(%) | 保费规模(万元) | 车辆数 |
|------|-----------|---------------|--------|\n"""
            
            for _, row in coverage_df.sort_values('loss_ratio', ascending=False).iterrows():
                report += f"| {row['coverage_type']} | {row['loss_ratio']:.1f} | {row['premium_amount']:.1f} | {row['vehicle_count']} |\n"
        
        # 趋势和问题分析
        if problems:
            report += """

## 趋势与问题分析
"""
            
            if 'overall_trends' in problems:
                trends = problems['overall_trends']
                report += f"""
### 整体趋势
- **赔付率趋势**: {trends['loss_ratio_trend']}
- **保费趋势**: {trends['premium_trend']}
"""
            
            if 'abnormal_fluctuation' in problems:
                abnormal = problems['abnormal_fluctuation']
                report += f"""
### 异常波动
- **类型**: {abnormal['type']}
- **最新值**: {abnormal['latest_value']:.1f}
- **近期均值**: {abnormal['recent_average']:.1f}  
- **偏离度**: {abnormal['deviation']:.1%}
"""
        
        report += f"""

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析周期**: 2025年保单第{self.start_week}-{self.end_week}周
**数据范围**: 新能源货车（营业货车）
"""
        
        return report
    
    def run_analysis(self):
        """运行完整分析流程"""
        print("🚀 开始新能源货车专项分析...")
        print("=" * 60)
        
        # 1. 加载数据
        df = self.load_weekly_data()
        if len(df) == 0:
            print("❌ 没有新能源货车数据，分析终止")
            return False
        
        # 2. 计算周度KPI
        weekly_kpis = self.calculate_weekly_kpis(df)
        print(f"✅ 计算了 {len(weekly_kpis)} 周的KPI数据")
        
        # 3. 多维度分析
        dimensional_analyses = self.analyze_by_dimensions(df)
        print("✅ 完成多维度分析")
        
        # 4. 识别问题和趋势
        problems = self.identify_problems_and_trends(weekly_kpis, dimensional_analyses)
        print("✅ 完成问题识别")
        
        # 5. 生成执行摘要
        summary = self.generate_executive_summary(weekly_kpis, dimensional_analyses, problems)
        print("✅ 生成执行摘要")
        
        # 6. 创建可视化
        self.create_visualizations(weekly_kpis, dimensional_analyses)
        print("✅ 创建可视化图表")
        
        # 7. 生成Markdown报告
        markdown_report = self.generate_markdown_report(weekly_kpis, dimensional_analyses, problems, summary)
        
        # 保存报告
        report_path = self.output_folder / "新能源货车专项分析报告.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print("✅ 完成Markdown报告生成")
        
        # 保存数据文件
        weekly_kpis.to_csv(self.output_folder / "周度KPI数据.csv", index=False, encoding='utf-8')
        
        for analysis_name, analysis_df in dimensional_analyses.items():
            analysis_df.to_csv(self.output_folder / f"{analysis_name}.csv", index=False, encoding='utf-8')
        
        print("✅ 数据文件保存完成")
        
        # 最终总结
        print("\n" + "=" * 60)
        print("🎉 新能源货车专项分析完成！")
        print("=" * 60)
        print(f"📊 分析周期: 第{self.start_week}-{self.end_week}周")
        print(f"📈 数据记录: {len(df)}条")
        print(f"🚛 新能源货车: {len(df)}辆")
        print(f"💰 累计保费: {weekly_kpis['signed_premium'].sum():.1f}万元")
        print(f"📋 平均赔付率: {weekly_kpis['loss_ratio'].mean():.1f}%")
        print(f"📁 报告位置: {self.output_folder}")
        
        return True

if __name__ == "__main__":
    analyzer = NewEnergyTruckAnalyzer()
    success = analyzer.run_analysis()
    
    if not success:
        exit(1)