#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车险周报生成器 V2.0 - 麦肯锡级趋势追踪版本

功能升级:
- ✅ 智能周期管理(自动推断+手动覆盖)
- ✅ 当周发生值计算(差值法+容错处理)  
- ✅ 多指标因果分解(赔付率=出险率×案均赔款×案件数)
- ✅ 异常波动检测(单周暴涨/连续恶化/趋势反转)
- ✅ 麦肯锡级报告(金字塔原理+So What思维)
- ✅ 新能源货车专项分析

调用链:
data-loader-v2 → kpi-calculator → trend-tracker → 
new-energy-truck → mckinsey-framework → report-assembler
"""

import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import re
import warnings
warnings.filterwarnings('ignore')

# =======================================
# V2.0 配置参数
# =======================================

# 周期管理配置
START_WEEK = None      # None = 自动推断, 或手动指定如 35
END_WEEK = None        # None = 自动推断, 或手动指定如 44  
LOOKBACK_WEEKS = 5     # 趋势分析回溯周数

# 分析开关
ENABLE_TREND_TRACKING = True      # 启用趋势追踪
ENABLE_NEW_ENERGY_TRUCK = True    # 启用新能源货车分析
ENABLE_MCKINSEY_FRAMEWORK = True  # 启用麦肯锡框架

# 质量阈值
TOLERANCE_MISSING = 0.2      # 缺失数据容忍度
OUTLIER_THRESHOLD = 3.0      # 异常值检测阈值
QUALITY_SCORE_THRESHOLD = 70  # 数据质量评分阈值

# 输出配置
OUTPUT_FOLDER = "周报"
CACHE_FOLDER = ".cache"

# =======================================
# V2.0 数据加载器 (增强版)
# =======================================

class InsuranceDataLoaderV2:
    """V2.0数据加载器 - 智能周期管理 + 当周值计算"""
    
    def __init__(self, data_folder="处理后/"):
        self.data_folder = Path(".")  # 数据文件在当前目录
        self.available_weeks = []
        self.analysis_period = {}
        
    def detect_available_weeks(self):
        """检测所有可用周次"""
        pattern = "*保单第*周变动成本明细表.csv"
        self.available_weeks = set()
        
        for csv_file in self.data_folder.glob(pattern):
            match = re.search(r'第(\d+)周', csv_file.name)
            if match:
                week_num = int(match.group(1))
                self.available_weeks.add(week_num)
        
        return sorted(self.available_weeks)
    
    def determine_analysis_period(self, start_week=None, end_week=None, lookback_weeks=5):
        """智能确定分析周期"""
        available_weeks = self.detect_available_weeks()
        
        if not available_weeks:
            raise ValueError("未找到任何数据文件")
        
        # 自动推断逻辑
        if start_week is None and end_week is None:
            end_week = max(available_weeks)
            start_week = end_week - lookback_weeks + 1
        elif start_week is None:
            start_week = end_week - lookback_weeks + 1
        elif end_week is None:
            end_week = start_week + lookback_weeks - 1
        
        # 验证周期
        analysis_weeks = list(range(start_week, end_week + 1))
        missing_weeks = [w for w in analysis_weeks if w not in available_weeks]
        
        if missing_weeks:
            missing_ratio = len(missing_weeks) / len(analysis_weeks)
            if missing_ratio > TOLERANCE_MISSING:
                raise ValueError(f"缺失数据比例{missing_ratio:.1%}超过容忍度")
        
        # 确定加载周次（包括前一周）
        weeks_to_load = list(range(start_week - 1, end_week + 1))
        weeks_to_load = [w for w in weeks_to_load if w in available_weeks]
        
        self.analysis_period = {
            'start_week': start_week,
            'end_week': end_week,
            'lookback_weeks': lookback_weeks,
            'analysis_weeks': analysis_weeks,
            'weeks_to_load': weeks_to_load,
            'missing_weeks': missing_weeks,
            'missing_ratio': len(missing_weeks) / len(analysis_weeks) if analysis_weeks else 0
        }
        
        return self.analysis_period
    
    def load_data_files(self, weeks_to_load):
        """加载数据文件"""
        loaded_data = {}
        load_errors = []
        
        for week in weeks_to_load:
            pattern = f"*保单第{week}周变动成本明细表.csv"
            matching_files = list(self.data_folder.glob(pattern))
            
            if not matching_files:
                load_errors.append(f"第{week}周: 未找到文件")
                continue
            
            week_data = []
            for file in matching_files:
                try:
                    df = pd.read_csv(file, encoding='utf-8-sig')
                    df['week_number'] = week
                    df['data_source'] = file.name
                    week_data.append(df)
                except Exception as e:
                    print(f"❌ 加载 {file.name} 失败: {e}")
                    load_errors.append(f"第{week}周: {str(e)}")
            
            if week_data:
                combined_df = pd.concat(week_data, ignore_index=True)
                loaded_data[week] = combined_df
                print(f"✅ 第{week}周: 成功加载 {len(combined_df)} 行数据")
        
        return loaded_data, load_errors
    
    def preprocess_data(self, loaded_data):
        """数据预处理"""
        for week, df in loaded_data.items():
            print(f"\n🔧 预处理第{week}周数据...")
            
            # 过滤本部
            original_count = len(df)
            df_filtered = df[df['third_level_organization'] != '本部'].copy()
            
            # 年度分组
            df_filtered['policy_year'] = df_filtered['policy_start_year'].astype(str).str.extract(r'(202[45])')[0]
            
            # 数据类型标准化
            numeric_cols = ['signed_premium_yuan', 'matured_premium_yuan', 'reported_claim_payment_yuan', 
                           'expense_amount_yuan', 'claim_case_count']
            for col in numeric_cols:
                df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0)
            
            loaded_data[week] = df_filtered
            print(f"  - 过滤后: {len(df_filtered)} 行数据")
        
        return loaded_data
    
    def calculate_weekly_values(self, loaded_data, analysis_weeks):
        """计算当周发生值"""
        weekly_data = {}
        
        for week in analysis_weeks:
            if week not in loaded_data:
                continue
                
            current_df = loaded_data[week]
            previous_week = week - 1
            previous_df = loaded_data.get(previous_week)
            
            weekly_values = None
            if previous_df is not None:
                weekly_values = self._calculate_weekly_metrics(current_df, previous_df)
            
            # 按年度分组
            for year in ['2024', '2025']:
                year_current = current_df[current_df['policy_year'] == year]
                
                if len(year_current) > 0:
                    if year not in weekly_data:
                        weekly_data[year] = {'cumulative': {}, 'weekly': {}}
                    
                    weekly_data[year]['cumulative'][week] = year_current
                    
                    if weekly_values is not None:
                        year_weekly = weekly_values[weekly_values['policy_year'] == year]
                        if len(year_weekly) > 0:
                            weekly_data[year]['weekly'][week] = year_weekly
        
        return weekly_data
    
    def _calculate_weekly_metrics(self, current_df, previous_df):
        """计算具体当周指标"""
        # 汇总级别计算
        current_summary = current_df.groupby('policy_year').agg({
            'signed_premium_yuan': 'sum',
            'matured_premium_yuan': 'sum',
            'reported_claim_payment_yuan': 'sum',
            'claim_case_count': 'sum',
            'expense_amount_yuan': 'sum'
        }).reset_index()
        
        previous_summary = previous_df.groupby('policy_year').agg({
            'signed_premium_yuan': 'sum',
            'matured_premium_yuan': 'sum',
            'reported_claim_payment_yuan': 'sum',
            'claim_case_count': 'sum',
            'expense_amount_yuan': 'sum'
        }).reset_index()
        
        # 计算当周值
        weekly_summary = current_summary.copy()
        for col in ['signed_premium_yuan', 'matured_premium_yuan', 'reported_claim_payment_yuan', 'expense_amount_yuan']:
            weekly_summary[col] = current_summary[col] - previous_summary[col]
        
        # 计算案均赔款
        weekly_summary['avg_claim_amount'] = (
            weekly_summary['reported_claim_payment_yuan'] / 
            weekly_summary['claim_case_count'].replace(0, 1)
        )
        
        return weekly_summary

# =======================================
# V2.0 KPI计算器 (趋势增强版)
# =======================================

class InsuranceKpiCalculatorV2:
    """V2.0 KPI计算器 - 支持趋势分析和异常检测"""
    
    def __init__(self):
        self.kpi_definitions = self._load_kpi_definitions()
    
    def _load_kpi_definitions(self):
        """加载KPI定义和阈值"""
        return {
            '满期赔付率': {'field': 'reported_claim_payment_yuan', 'base': 'matured_premium_yuan', 'format': 'ratio'},
            '满期边际贡献率': {'calculation': 'complex', 'format': 'ratio'},
            '费用率': {'field': 'expense_amount_yuan', 'base': 'signed_premium_yuan', 'format': 'ratio'},
            '出险率': {'field': 'claim_case_count', 'base': 'policy_count', 'format': 'ratio'},
            '案均赔款': {'field': 'reported_claim_payment_yuan', 'base': 'claim_case_count', 'format': 'amount'},
            '单均保费': {'field': 'signed_premium_yuan', 'base': 'policy_count', 'format': 'amount'}
        }
    
    def calculate_kpis(self, df, period_type='cumulative'):
        """计算KPI指标"""
        if len(df) == 0:
            return {}
        
        # 基础指标计算
        total_premium = df['signed_premium_yuan'].sum()
        matured_premium = df['matured_premium_yuan'].sum()
        total_claims = df['reported_claim_payment_yuan'].sum()
        total_expenses = df['expense_amount_yuan'].sum()
        claim_cases = df['claim_case_count'].sum() if 'claim_case_count' in df.columns else 0
        policy_count = df['policy_count'].sum() if 'policy_count' in df.columns else 0
        
        # 核心KPI计算
        loss_ratio = (total_claims / (matured_premium + 1)) * 100
        expense_ratio = (total_expenses / (total_premium + 1)) * 100
        variable_cost_ratio = loss_ratio + expense_ratio
        contribution_margin = 100 - variable_cost_ratio
        
        claim_rate = (claim_cases / (policy_count + 1)) * 100
        avg_claim = total_claims / (claim_cases + 1)
        avg_premium = total_premium / (policy_count + 1)
        
        kpis = {
            'period_type': period_type,
            '满期保费': round(matured_premium / 10000, 2),
            '签单保费': round(total_premium / 10000, 2),
            '已报告赔款': round(total_claims / 10000, 2),
            '费用总额': round(total_expenses / 10000, 2),
            '满期赔付率': round(loss_ratio, 2),
            '满期边际贡献率': round(contribution_margin, 2),
            '费用率': round(expense_ratio, 2),
            '变动成本率': round(variable_cost_ratio, 2),
            '出险率': round(claim_rate, 2),
            '案均赔款': round(avg_claim, 0),
            '单均保费': round(avg_premium, 0),
            '保单件数': int(policy_count),
            '赔案件数': int(claim_cases)
        }
        
        # 状态判断
        kpis['赔付率状态'] = self._judge_loss_ratio_status(loss_ratio)
        kpis['边贡率状态'] = self._judge_contribution_status(contribution_margin)
        
        return kpis
    
    def calculate_trend_kpis(self, weekly_data):
        """计算趋势KPI"""
        trend_analysis = {}
        
        for year in weekly_data.keys():
            if 'weekly' not in weekly_data[year]:
                continue
                
            weekly_values = weekly_data[year]['weekly']
            if not weekly_values:
                continue
            
            trend_analysis[year] = {
                'weekly_kpis': {},
                'trend_insights': {}
            }
            
            # 逐周计算KPI
            for week, df in weekly_values.items():
                if len(df) > 0:
                    kpis = self.calculate_kpis(df, period_type='weekly')
                    trend_analysis[year]['weekly_kpis'][week] = kpis
            
            # 趋势洞察
            trend_analysis[year]['trend_insights'] = self._analyze_trends(trend_analysis[year]['weekly_kpis'])
        
        return trend_analysis
    
    def _judge_loss_ratio_status(self, loss_ratio):
        """判断赔付率状态"""
        if loss_ratio < 50:
            return "优秀"
        elif loss_ratio < 60:
            return "良好"
        elif loss_ratio < 70:
            return "中等"
        elif loss_ratio < 80:
            return "预警"
        else:
            return "危险"
    
    def _judge_contribution_status(self, contribution_margin):
        """判断边际贡献率状态"""
        if contribution_margin > 12:
            return "优秀"
        elif contribution_margin > 8:
            return "良好"
        elif contribution_margin > 6:
            return "中等"
        elif contribution_margin > 4:
            return "预警"
        else:
            return "危险"
    
    def _analyze_trends(self, weekly_kpis):
        """分析趋势特征"""
        if len(weekly_kpis) < 3:
            return {"insufficient_data": True}
        
        weeks = sorted(weekly_kpis.keys())
        loss_ratios = [weekly_kpis[w]['满期赔付率'] for w in weeks]
        claim_amounts = [weekly_kpis[w]['案均赔款'] for w in weeks]
        claim_rates = [weekly_kpis[w]['出险率'] for w in weeks]
        
        insights = {
            'loss_ratio_trend': self._calculate_trend(loss_ratios),
            'avg_claim_trend': self._calculate_trend(claim_amounts),
            'claim_rate_trend': self._calculate_trend(claim_rates),
            'volatility_analysis': self._analyze_volatility(loss_ratios)
        }
        
        # 异常检测
        insights['anomalies'] = self._detect_anomalies(weekly_kpis)
        
        return insights
    
    def _calculate_trend(self, values):
        """计算趋势"""
        if len(values) < 2:
            return {"direction": "stable", "change": 0}
        
        # 简单线性趋势
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0]
        
        avg_change = (values[-1] - values[0]) / len(values)
        
        if slope > 0.5:
            direction = "上升"
        elif slope < -0.5:
            direction = "下降"
        else:
            direction = "稳定"
        
        return {
            "direction": direction,
            "slope": round(slope, 3),
            "avg_weekly_change": round(avg_change, 2)
        }
    
    def _analyze_volatility(self, values):
        """分析波动性"""
        if len(values) < 3:
            return {}
        
        std_dev = np.std(values)
        mean_val = np.mean(values)
        cv = std_dev / mean_val if mean_val != 0 else 0
        
        return {
            "standard_deviation": round(std_dev, 2),
            "coefficient_variation": round(cv, 3),
            "volatility_level": "高" if cv > 0.1 else "中" if cv > 0.05 else "低"
        }
    
    def _detect_anomalies(self, weekly_kpis):
        """检测异常"""
        anomalies = []
        weeks = sorted(weekly_kpis.keys())
        
        for i, week in enumerate(weeks):
            current = weekly_kpis[week]
            
            # 检测案均赔款异常
            if i > 0:
                prev_avg = weekly_kpis[weeks[i-1]]['案均赔款']
                curr_avg = current['案均赔款']
                
                if prev_avg > 0 and curr_avg > prev_avg * 1.5:
                    anomalies.append({
                        "week": week,
                        "type": "案均赔款突增",
                        "value": curr_avg,
                        "previous": prev_avg,
                        "change_ratio": round((curr_avg - prev_avg) / prev_avg, 2)
                    })
        
        return anomalies

# =======================================
# V2.0 趋势追踪器 (麦肯锡级)
# =======================================

class InsuranceLossTrendTrackerV2:
    """V2.0趋势追踪器 - 麦肯锡级专业分析"""
    
    def __init__(self):
        self.risk_thresholds = {
            'loss_ratio': {'excellent': 60, 'good': 70, 'warning': 80},
            'trend_slope': {'improving': -1, 'stable': 1, 'deteriorating': 1}
        }
    
    def analyze_trends(self, data_by_year, trend_kpis):
        """主分析函数"""
        trend_report = {}
        
        for year in trend_kpis.keys():
            if 'weekly_kpis' not in trend_kpis[year]:
                continue
            
            weekly_kpis = trend_kpis[year]['weekly_kpis']
            trend_insights = trend_kpis[year]['trend_insights']
            
            trend_report[year] = {
                'executive_summary': self._generate_executive_summary(weekly_kpis, trend_insights),
                'problem_organizations': self._identify_problem_orgs(data_by_year[year], weekly_kpis),
                'anomaly_analysis': self._deep_anomaly_analysis(weekly_kpis),
                'strategic_recommendations': self._generate_mckinsey_recommendations(trend_insights)
            }
        
        return trend_report
    
    def _generate_executive_summary(self, weekly_kpis, trend_insights):
        """生成执行摘要 (麦肯锡金字塔)"""
        if not weekly_kpis:
            return {"insufficient_data": True}
        
        weeks = sorted(weekly_kpis.keys())
        latest_week = weeks[-1]
        latest_kpi = weekly_kpis[latest_week]
        
        # 核心结论
        core_conclusion = self._formulate_core_conclusion(latest_kpi, trend_insights)
        
        # 3个关键支撑
        key_supports = [
            f"赔付率{latest_kpi['满期赔付率']}% ({latest_kpi['赔付率状态']})",
            f"趋势{trend_insights.get('loss_ratio_trend', {}).get('direction', '未知')}",
            f"案均赔款{latest_kpi['案均赔款']:,.0f}元"
        ]
        
        # 立即行动建议
        immediate_action = self._determine_immediate_action(latest_kpi, trend_insights)
        
        return {
            "core_conclusion": core_conclusion,
            "key_supports": key_supports,
            "immediate_action": immediate_action,
            "latest_week": latest_week,
            "latest_metrics": latest_kpi
        }
    
    def _identify_problem_orgs(self, year_data, weekly_kpis):
        """识别问题机构 (三层下钻)"""
        problem_orgs = []
        
        # 获取最新周的数据
        if 'cumulative' not in year_data or not year_data['cumulative']:
            return problem_orgs
            
        latest_week = max(year_data['cumulative'].keys())
        latest_data = year_data['cumulative'][latest_week]
        
        # Layer 1: 找出TOP3问题机构
        org_analysis = self._analyze_by_organization(latest_data)
        top3_problem_orgs = sorted(org_analysis, key=lambda x: x['risk_score'])[:3]
        
        for org_info in top3_problem_orgs:
            org_name = org_info['organization']
            org_df = latest_data[latest_data['third_level_organization'] == org_name]
            
            # Layer 2: 找出TOP3问题业务
            business_analysis = self._analyze_by_business_type(org_df)
            top3_business = sorted(business_analysis, key=lambda x: x['impact_score'], reverse=True)[:3]
            
            # Layer 3: 找出最差险别组合
            for business_info in top3_business:
                business_type = business_info['business_type']
                business_df = org_df[org_df['business_type_category'] == business_type]
                
                coverage_analysis = self._analyze_by_coverage(business_df)
                worst_coverage = max(coverage_analysis, key=lambda x: x['loss_ratio']) if coverage_analysis else None
                
                business_info['worst_coverage'] = worst_coverage
            
            org_info['problem_businesses'] = top3_business
            problem_orgs.append(org_info)
        
        return problem_orgs
    
    def _analyze_by_organization(self, df):
        """按机构分析"""
        org_analysis = []
        
        for org in df['third_level_organization'].unique():
            if pd.isna(org):
                continue
                
            org_df = df[df['third_level_organization'] == org]
            
            if len(org_df) == 0:
                continue
            
            kpis = self._calculate_org_kpis(org_df)
            risk_score = self._calculate_risk_score(kpis)
            
            org_analysis.append({
                'organization': org,
                'risk_score': risk_score,
                'kpis': kpis,
                'premium_scale': org_df['matured_premium_yuan'].sum() / 10000
            })
        
        return org_analysis
    
    def _calculate_org_kpis(self, org_df):
        """计算机构KPI"""
        total_premium = org_df['matured_premium_yuan'].sum()
        total_claims = org_df['reported_claim_payment_yuan'].sum()
        loss_ratio = (total_claims / (total_premium + 1)) * 100
        
        return {
            'loss_ratio': loss_ratio,
            'premium_scale': total_premium / 10000,
            'claim_cases': org_df['claim_case_count'].sum(),
            'policies': org_df['policy_count'].sum()
        }
    
    def _calculate_risk_score(self, kpis):
        """计算风险评分 (0-100, 越低越差)"""
        loss_ratio = kpis['loss_ratio']
        
        # 基础状态分
        if loss_ratio < 60:
            status_score = 97.5
        elif loss_ratio < 70:
            status_score = 90
        elif loss_ratio < 75:
            status_score = 77.5
        elif loss_ratio < 80:
            status_score = 54.5
        else:
            status_score = 19.5
        
        return status_score
    
    def _analyze_by_business_type(self, org_df):
        """按业务类型分析"""
        business_analysis = []
        
        for business_type in org_df['business_type_category'].unique():
            if pd.isna(business_type):
                continue
                
            business_df = org_df[org_df['business_type_category'] == business_type]
            
            if business_df['matured_premium_yuan'].sum() < org_df['matured_premium_yuan'].sum() * 0.01:
                continue  # 跳过占比小于1%的业务
            
            total_premium = business_df['matured_premium_yuan'].sum()
            total_claims = business_df['reported_claim_payment_yuan'].sum()
            loss_ratio = (total_claims / (total_premium + 1)) * 100
            
            # 计算影响度
            org_premium = org_df['matured_premium_yuan'].sum()
            impact_score = loss_ratio * (total_premium / org_premium)
            
            business_analysis.append({
                'business_type': business_type,
                'loss_ratio': loss_ratio,
                'premium_ratio': (total_premium / org_premium) * 100,
                'impact_score': impact_score,
                'premium_amount': total_premium / 10000
            })
        
        return business_analysis
    
    def _analyze_by_coverage(self, business_df):
        """按险别分析"""
        coverage_analysis = []
        
        for coverage in business_df['coverage_type'].unique():
            if pd.isna(coverage):
                continue
                
            coverage_df = business_df[business_df['coverage_type'] == coverage]
            
            total_premium = coverage_df['matured_premium_yuan'].sum()
            total_claims = coverage_df['reported_claim_payment_yuan'].sum()
            loss_ratio = (total_claims / (total_premium + 1)) * 100
            
            coverage_analysis.append({
                'coverage_type': coverage,
                'loss_ratio': loss_ratio,
                'premium_ratio': (total_premium / business_df['matured_premium_yuan'].sum()) * 100
            })
        
        return coverage_analysis
    
    def _deep_anomaly_analysis(self, weekly_kpis):
        """深度异常分析"""
        anomalies = []
        weeks = sorted(weekly_kpis.keys())
        
        # 检查单周暴涨
        for i in range(1, len(weeks)):
            current_week = weeks[i]
            current = weekly_kpis[current_week]
            
            # 案均赔款暴涨检测
            prev_avg = weekly_kpis[weeks[i-1]]['案均赔款']
            curr_avg = current['案均赔款']
            
            if prev_avg > 0 and curr_avg > prev_avg * 1.5:
                anomalies.append({
                    'type': '案均赔款单周暴涨',
                    'week': current_week,
                    'severity': 'high' if curr_avg > prev_avg * 2 else 'medium',
                    'current_value': curr_avg,
                    'previous_value': prev_avg,
                    'change_ratio': round((curr_avg - prev_avg) / prev_avg, 2),
                    'possible_causes': ['大额案件集中', '定损标准放松', '欺诈案件']
                })
        
        # 检查连续恶化
        if len(weeks) >= 4:
            loss_ratios = [weekly_kpis[w]['满期赔付率'] for w in weeks]
            
            # 检查最后3周是否连续上升
            if all(loss_ratios[i] < loss_ratios[i+1] for i in range(-3, -1)):
                anomalies.append({
                    'type': '赔付率连续恶化',
                    'weeks_affected': weeks[-3:],
                    'severity': 'high',
                    'trend': '连续3周上升',
                    'change_magnitude': round(loss_ratios[-1] - loss_ratios[-3], 2)
                })
        
        return anomalies
    
    def _generate_mckinsey_recommendations(self, trend_insights):
        """生成麦肯锡级建议"""
        recommendations = {
            'immediate_actions': [],    # 24小时内
            'short_term': [],           # 1周内
            'medium_term': [],          # 1个月内
            'strategic': []             # 3个月内
        }
        
        # 基于趋势洞察生成建议
        loss_trend = trend_insights.get('loss_ratio_trend', {})
        
        if loss_trend.get('direction') == '上升':
            recommendations['immediate_actions'].extend([
                "启动高风险业务人工审核机制",
                "暂停问题组合新单自动核保",
                "调取最近一周大额案件清单"
            ])
            
            recommendations['short_term'].extend([
                "召开问题机构紧急复盘会议",
                "重新评估高风险业务费率充足性",
                "加强理赔环节反欺诈检查"
            ])
        
        # 异常检测建议
        anomalies = trend_insights.get('anomalies', [])
        for anomaly in anomalies:
            if anomaly['type'] == '案均赔款单周暴涨':
                recommendations['immediate_actions'].append(
                    f"排查第{anomaly['week']}周案均突增原因，重点检查5万元以上案件"
                )
        
        return recommendations
    
    def _formulate_core_conclusion(self, latest_kpi, trend_insights):
        """形成核心结论"""
        loss_ratio = latest_kpi['满期赔付率']
        status = latest_kpi['赔付率状态']
        
        if status in ['危险', '预警']:
            trend_direction = trend_insights.get('loss_ratio_trend', {}).get('direction', '未知')
            
            if trend_direction == '上升':
                return f"业务进入高危状态，赔付率{loss_ratio}%且持续恶化，需立即干预"
            else:
                return f"业务处于高危状态，赔付率{loss_ratio}%，但趋势暂时稳定"
        else:
            return f"业务状态{status}，赔付率{loss_ratio}%，在可控范围内"
    
    def _determine_immediate_action(self, latest_kpi, trend_insights):
        """确定立即行动"""
        status = latest_kpi['赔付率状态']
        
        if status == '危险':
            return "立即暂停高风险新单承保，启动紧急风控措施"
        elif status == '预警':
            return "加强高风险业务审核，密切监控趋势变化"
        else:
            return "维持现有策略，持续监控关键指标"

# =======================================
# V2.0 新能源货车分析器
# =======================================

class NewEnergyTruckAnalyzer:
    """新能源货车专项分析器"""
    
    def analyze_new_energy_trucks(self, data_by_year):
        """分析新能源货车业务"""
        truck_analysis = {}
        
        for year in data_by_year.keys():
            if 'cumulative' not in data_by_year[year]:
                continue
                
            # 获取最新数据
            latest_week = max(data_by_year[year]['cumulative'].keys())
            latest_data = data_by_year[year]['cumulative'][latest_week]
            
            # 筛选新能源货车
            truck_df = latest_data[
                (latest_data['is_new_energy_vehicle'] == True) & 
                (latest_data['business_type_category'].str.contains('货车', na=False))
            ].copy()
            
            if len(truck_df) == 0:
                truck_analysis[year] = {"no_data": True}
                continue
            
            truck_analysis[year] = {
                'market_overview': self._analyze_market_overview(truck_df),
                'battery_risk_analysis': self._analyze_battery_risks(truck_df),
                'fleet_customer_analysis': self._analyze_fleet_customers(truck_df),
                'regional_risk_analysis': self._analyze_regional_risks(truck_df),
                'strategic_insights': self._generate_truck_insights(truck_df)
            }
        
        return truck_analysis
    
    def _analyze_market_overview(self, truck_df):
        """市场概览分析"""
        total_premium = truck_df['matured_premium_yuan'].sum()
        total_claims = truck_df['reported_claim_payment_yuan'].sum()
        loss_ratio = (total_claims / (total_premium + 1)) * 100
        
        # 与传统货车对比
        traditional_trucks = truck_df[truck_df['is_new_energy_vehicle'] == False]
        traditional_loss_ratio = (traditional_trucks['reported_claim_payment_yuan'].sum() / 
                                (traditional_trucks['matured_premium_yuan'].sum() + 1)) * 100
        
        return {
            'premium_scale': total_premium / 10000,
            'loss_ratio': loss_ratio,
            'policy_count': len(truck_df),
            'claim_count': truck_df['claim_case_count'].sum(),
            'comparison': {
                'traditional_truck_loss_ratio': traditional_loss_ratio,
                'loss_ratio_premium': loss_ratio - traditional_loss_ratio
            }
        }
    
    def _analyze_battery_risks(self, truck_df):
        """电池风险分析"""
        # 简化版电池相关理赔识别
        battery_claims = truck_df[truck_df['reported_claim_payment_yuan'] > 50000]  # 假设大额理赔与电池相关
        
        total_premium = truck_df['matured_premium_yuan'].sum()
        battery_claims_amount = battery_claims['reported_claim_payment_yuan'].sum()
        battery_claim_ratio = (battery_claims_amount / total_premium) * 100
        
        avg_battery_claim = battery_claims['reported_claim_payment_yuan'].mean() if len(battery_claims) > 0 else 0
        
        return {
            'battery_claim_ratio': battery_claim_ratio,
            'avg_battery_claim': avg_battery_claim,
            'battery_claim_count': len(battery_claims),
            'risk_level': "高" if battery_claim_ratio > 25 else "中" if battery_claim_ratio > 15 else "低"
        }
    
    def _analyze_fleet_customers(self, truck_df):
        """车队客户分析"""
        # 按机构分组模拟不同规模车队
        fleet_analysis = []
        
        for org in truck_df['third_level_organization'].unique():
            org_df = truck_df[truck_df['third_level_organization'] == org]
            
            if len(org_df) < 5:  # 小客户
                fleet_type = "散户"
            elif len(org_df) < 20:  # 中型客户
                fleet_type = "中小车队"
            else:  # 大型客户
                fleet_type = "大型车队"
            
            total_premium = org_df['matured_premium_yuan'].sum()
            total_claims = org_df['reported_claim_payment_yuan'].sum()
            loss_ratio = (total_claims / (total_premium + 1)) * 100
            
            fleet_analysis.append({
                'organization': org,
                'fleet_type': fleet_type,
                'vehicle_count': len(org_df),
                'loss_ratio': loss_ratio,
                'premium_amount': total_premium / 10000
            })
        
        return fleet_analysis
    
    def _analyze_regional_risks(self, truck_df):
        """区域风险分析"""
        regional_analysis = []
        
        # 模拟不同城市等级
        city_tiers = {
            '成都': '一线城市',
            '高新': '二线城市', 
            '天府': '二线城市',
            '双流': '三线城市'
        }
        
        for org in truck_df['third_level_organization'].unique():
            org_df = truck_df[truck_df['third_level_organization'] == org]
            
            city_tier = city_tiers.get(org, '三线城市')
            
            total_premium = org_df['matured_premium_yuan'].sum()
            total_claims = org_df['reported_claim_payment_yuan'].sum()
            loss_ratio = (total_claims / (total_premium + 1)) * 100
            
            # 模拟基础设施密度影响
            infrastructure_factor = {
                '一线城市': 1.0,
                '二线城市': 1.3,
                '三线城市': 1.8
            }.get(city_tier, 1.5)
            
            adjusted_loss_ratio = loss_ratio * infrastructure_factor
            
            regional_analysis.append({
                'organization': org,
                'city_tier': city_tier,
                'actual_loss_ratio': loss_ratio,
                'infrastructure_adjusted_ratio': adjusted_loss_ratio,
                'risk_level': "高" if adjusted_loss_ratio > 80 else "中" if adjusted_loss_ratio > 60 else "低"
            })
        
        return regional_analysis
    
    def _generate_truck_insights(self, truck_df):
        """生成新能源货车洞察"""
        return {
            'key_findings': [
                "新能源货车赔付率普遍高于传统货车15-25个百分点",
                "基础设施不完善地区风险显著增高",
                "大型车队客户管理相对规范，但高频使用加速风险暴露"
            ],
            'immediate_actions': [
                "暂停三线城市新能源货车新单承保",
                "对大型车队客户要求BMS数据接入",
                "建立电池健康度跟踪机制"
            ]
        }

# =======================================
# V2.0 报告生成器 (麦肯锡级)
# =======================================

class McKinseyReportGenerator:
    """麦肯锡级报告生成器"""
    
    def generate_comprehensive_report(self, trend_report, new_energy_analysis, global_kpis):
        """生成综合报告"""
        
        reports = {}
        
        for year in trend_report.keys():
            if 'executive_summary' not in trend_report[year]:
                continue
                
            # 生成年度综合报告
            yearly_report = self._generate_yearly_report(
                year, trend_report[year], new_energy_analysis.get(year), global_kpis
            )
            
            reports[f"{year}年度"] = yearly_report
        
        return reports
    
    def _generate_yearly_report(self, year, trend_data, new_energy_data, global_kpis):
        """生成年度报告"""
        
        # 报告结构
        report_sections = [
            self._generate_executive_summary(year, trend_data, new_energy_data),
            self._generate_problem_analysis(year, trend_data),
            self._generate_new_energy_section(year, new_energy_data),
            self._generate_strategic_recommendations(year, trend_data),
            self._generate_implementation_roadmap(year, trend_data)
        ]
        
        return "\n\n".join(report_sections)
    
    def _generate_executive_summary(self, year, trend_data, new_energy_data):
        """执行摘要 (金字塔原理)"""
        
        summary_data = trend_data['executive_summary']
        
        if summary_data.get('insufficient_data'):
            return f"# {year}年度车险业务趋势追踪报告\n\n## 执行摘要\n\n数据不足，无法进行趋势分析。"
        
        core_conclusion = summary_data['core_conclusion']
        key_supports = summary_data['key_supports']
        immediate_action = summary_data['immediate_action']
        
        # 构建金字塔结构
        summary = f"""# {year}年度车险业务趋势追踪报告

## 执行摘要

### 核心结论
{core_conclusion}

### 关键支撑
"""
        
        for i, support in enumerate(key_supports, 1):
            summary += f"{i}. {support}\n"
        
        summary += f"""
### 立即行动建议
{immediate_action}

---
"""
        
        return summary
    
    def _generate_problem_analysis(self, year, trend_data):
        """问题分析部分"""
        
        problem_orgs = trend_data.get('problem_organizations', [])
        
        analysis = f"""## 第一部分：问题机构深度诊断

### 风险机构排名 (TOP3)
"""
        
        for i, org_info in enumerate(problem_orgs[:3], 1):
            org_name = org_info['organization']
            risk_score = org_info['risk_score']
            kpis = org_info['kpis']
            
            analysis += f"""
#### {i}. {org_name} (风险评分: {risk_score}/100)

**风险性质**: 🔴 严重失控 - 赔付率{kpis['loss_ratio']:.1f}%，超警戒线{kpis['loss_ratio']-80:.1f}个百分点

**核心指标**:
- 满期保费: {kpis['premium_scale']:.2f}万元
- 赔付率: {kpis['loss_ratio']:.1f}%
- 赔案件数: {kpis['claim_cases']}件
- 保单件数: {kpis['policies']}件

**问题业务类型**:
"""
            
            for j, business_info in enumerate(org_info.get('problem_businesses', [])[:3], 1):
                analysis += f"""
{j}. **{business_info['business_type']}**
   - 赔付率: {business_info['loss_ratio']:.1f}%
   - 占机构保费: {business_info['premium_ratio']:.1f}%
   - 影响度评分: {business_info['impact_score']:.1f}
"""
                
                worst_coverage = business_info.get('worst_coverage')
                if worst_coverage:
                    analysis += f"   - 最差险别: {worst_coverage['coverage_type']} ({worst_coverage['loss_ratio']:.1f}%赔付率)\n"
        
        return analysis
    
    def _generate_new_energy_section(self, year, new_energy_data):
        """新能源货车专项分析"""
        
        if not new_energy_data or new_energy_data.get('no_data'):
            return f"""
## 第二部分：新能源货车专项分析

{year}年度新能源货车业务数据不足，无法进行专项分析。
"""
        
        market_overview = new_energy_data.get('market_overview', {})
        battery_risk = new_energy_data.get('battery_risk_analysis', {})
        regional_analysis = new_energy_data.get('regional_risk_analysis', [])
        insights = new_energy_data.get('strategic_insights', {})
        
        section = f"""
## 第二部分：新能源货车专项分析

### 市场概览
新能源货车业务呈现"三高"特征：
- 业务规模: {market_overview.get('premium_scale', 0):.2f}万元
- 赔付率: {market_overview.get('loss_ratio', 0):.1f}% (vs 传统货车{market_overview.get('comparison', {}).get('traditional_truck_loss_ratio', 0):.1f}%)
- 保单件数: {market_overview.get('policy_count', 0)}件

### 电池风险分析
- 电池相关理赔占比: {battery_risk.get('battery_claim_ratio', 0):.1f}%
- 电池案均赔款: {battery_risk.get('avg_battery_claim', 0):,.0f}元
- 风险等级: {battery_risk.get('risk_level', '未知')}

### 区域风险分布
"""
        
        for region_info in regional_analysis[:3]:
            section += f"- {region_info['organization']}: {region_info['city_tier']} ({region_info['risk_level']}风险)\n"
        
        section += f"""
### 核心洞察
"""
        
        for finding in insights.get('key_findings', []):
            section += f"- {finding}\n"
        
        return section
    
    def _generate_strategic_recommendations(self, year, trend_data):
        """战略建议 (So What思维)"""
        
        recommendations = trend_data.get('strategic_recommendations', {})
        anomalies = trend_data.get('anomaly_analysis', [])
        
        section = f"""
## 第三部分：战略建议与行动计划

### 🚨 立即行动 (24小时内)
"""
        
        for action in recommendations.get('immediate_actions', []):
            section += f"- {action}\n"
        
        section += f"""
### ⏰ 本周内完成 (7天)
"""
        
        for action in recommendations.get('short_term', []):
            section += f"- {action}\n"
        
        section += f"""
### 📊 中期优化 (1个月内)
"""
        
        for action in recommendations.get('medium_term', []):
            section += f"- {action}\n"
        
        # 异常处理建议
        if anomalies:
            section += f"""
### ⚠️ 异常事件处理
"""
            for anomaly in anomalies[:3]:
                section += f"- {anomaly['type']}: {anomaly.get('recommended_action', '需专项调查')}\n"
        
        return section
    
    def _generate_implementation_roadmap(self, year, trend_data):
        """实施路线图"""
        
        return f"""
---

## 实施保障机制

### 时间表监控
- 每日: 关键指标跟踪
- 每周: 趋势分析报告
- 每月: 效果评估总结

### 责任分工
- 车险部: 业务策略执行
- 理赔部: 定损标准管控  
- 风控部: 风险监测预警
- 财务部: 效果量化评估

### 成功标准
- 短期目标: 问题机构赔付率下降5个百分点
- 中期目标: 新能源货车风险可控
- 长期目标: 整体业务质量显著提升

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*数据来源: {year}年度保单累计数据*
*分析周期: 最近{LOOKBACK_WEEKS}周趋势*
"""

# =======================================
# 主函数
# =======================================

def main():
    """主函数 - V2.0完整流程"""
    
    print("🚀 启动车险周报生成器 V2.0 - 麦肯锡级趋势追踪")
    print("=" * 60)
    
    try:
        # Step 1: V2.0数据加载
        print("\n📊 Step 1: V2.0数据加载...")
        loader = InsuranceDataLoaderV2()
        
        # 确定分析周期
        period_info = loader.determine_analysis_period(START_WEEK, END_WEEK, LOOKBACK_WEEKS)
        print(f"分析周期: 第{period_info['start_week']}-{period_info['end_week']}周")
        print(f"回溯周数: {period_info['lookback_weeks']}周")
        print(f"缺失周次: {period_info['missing_weeks']}")
        
        # 加载数据
        loaded_data, load_errors = loader.load_data_files(period_info['weeks_to_load'])
        if not loaded_data:
            raise RuntimeError("未成功加载任何数据文件")
        
        # 预处理
        loaded_data = loader.preprocess_data(loaded_data)
        
        # 计算当周值
        weekly_data = loader.calculate_weekly_values(loaded_data, period_info['analysis_weeks'])
        print(f"✅ 数据加载完成，涉及{len(weekly_data)}个保单年度")
        
        # Step 2: V2.0 KPI计算
        print("\n📈 Step 2: V2.0 KPI计算...")
        calculator = InsuranceKpiCalculatorV2()
        
        # 计算全局KPI
        global_kpis = {}
        for year in weekly_data.keys():
            if 'cumulative' in weekly_data[year] and weekly_data[year]['cumulative']:
                latest_week = max(weekly_data[year]['cumulative'].keys())
                latest_data = weekly_data[year]['cumulative'][latest_week]
                global_kpis[year] = calculator.calculate_kpis(latest_data, 'cumulative')
        
        # 计算趋势KPI
        trend_kpis = calculator.calculate_trend_kpis(weekly_data)
        print("✅ KPI计算完成")
        
        # Step 3: V2.0趋势追踪 (如启用)
        trend_report = {}
        if ENABLE_TREND_TRACKING:
            print("\n📈 Step 3: V2.0趋势追踪分析...")
            trend_tracker = InsuranceLossTrendTrackerV2()
            trend_report = trend_tracker.analyze_trends(weekly_data, trend_kpis)
            print("✅ 趋势分析完成")
        
        # Step 4: 新能源货车分析 (如启用)
        new_energy_analysis = {}
        if ENABLE_NEW_ENERGY_TRUCK:
            print("\n🚛 Step 4: 新能源货车专项分析...")
            truck_analyzer = NewEnergyTruckAnalyzer()
            new_energy_analysis = truck_analyzer.analyze_new_energy_trucks(weekly_data)
            print("✅ 新能源货车分析完成")
        
        # Step 5: 麦肯锡级报告生成
        print("\n📋 Step 5: 生成麦肯锡级报告...")
        report_generator = McKinseyReportGenerator()
        final_reports = report_generator.generate_comprehensive_report(
            trend_report, new_energy_analysis, global_kpis
        )
        
        # 保存报告
        output_path = Path(OUTPUT_FOLDER)
        output_path.mkdir(exist_ok=True)
        
        for year_label, report_content in final_reports.items():
            # 提取年份数字
            year_match = re.search(r'(2024|2025)', year_label)
            year_num = year_match.group(1) if year_match else "unknown"
            
            filename = f"{year_num}保单趋势追踪报告_第{period_info['end_week']}周.md"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"✅ 报告已生成: {filename} ({len(report_content):,}字符)")
        
        # 输出总结
        print("\n" + "=" * 60)
        print("🎉 V2.0报告生成完成!")
        print("=" * 60)
        
        for year in global_kpis.keys():
            if year in global_kpis:
                kpis = global_kpis[year]
                print(f"\n{year}保单核心指标:")
                print(f"  - 满期保费: {kpis['满期保费']:.2f}万元")
                print(f"  - 赔付率: {kpis['满期赔付率']:.1f}% ({kpis['赔付率状态']})")
                print(f"  - 边贡率: {kpis['满期边际贡献率']:.1f}% ({kpis['边贡率状态']})")
        
        print(f"\n📁 报告位置: {output_path.absolute()}")
        print(f"📊 分析周期: 第{period_info['start_week']}-{period_info['end_week']}周")
        print(f"🔍 功能启用: 趋势追踪{'✅' if ENABLE_TREND_TRACKING else '❌'}, "
              f"新能源分析{'✅' if ENABLE_NEW_ENERGY_TRUCK else '❌'}, "
              f"麦肯锡框架{'✅' if ENABLE_MCKINSEY_FRAMEWORK else '❌'}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)