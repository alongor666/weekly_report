#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车险分析项目需求设计演示脚本
"""

import json
from datetime import datetime
import os

class InsuranceRequirementsDesigner:
    """车险分析项目需求设计器演示版"""
    
    def __init__(self):
        self.project_data = {
            "project_name": "新能源货车保险业务分析平台",
            "analysis_period": "2025年保单第28-43周",
            "vehicle_count": 1310,
            "avg_loss_ratio": 160.5,
            "high_risk_count": 3,
            "total_premium": 8206,
            "data_sources": [
                "2025年保单第28-43周变动成本明细表",
                "理赔数据库",
                "机构组织架构",
                "产品配置信息"
            ]
        }
    
    def generate_html_requirements_report(self):
        """生成HTML格式的需求规格说明书"""
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新能源货车保险业务分析平台 - 需求规格说明书</title>
    <style>
        :root {{
            --primary-color: #2563eb;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --neutral-color: #6b7280;
            --background-color: #f9fafb;
            --text-color: #111827;
            --border-color: #e5e7eb;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--primary-color), #1d4ed8);
            color: white;
            padding: 3rem 2.5rem;
            text-align: center;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20"><defs><radialGradient id="a" cx="50%" cy="40%"><stop offset="0%" stop-color="white" stop-opacity="0.1"/><stop offset="100%" stop-color="white" stop-opacity="0"/></radialGradient></defs><rect width="100" height="20" fill="url(%23a)"/></svg>');
            opacity: 0.1;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.8rem;
            font-weight: 700;
            position: relative;
            z-index: 1;
        }}
        
        .header .subtitle {{
            margin: 1rem 0 0 0;
            font-size: 1.2rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }}
        
        .header .meta-info {{
            margin-top: 1.5rem;
            font-size: 0.9rem;
            opacity: 0.8;
            position: relative;
            z-index: 1;
        }}
        
        .content {{
            padding: 3rem 2.5rem;
        }}
        
        .section {{
            margin-bottom: 4rem;
            position: relative;
        }}
        
        .section::before {{
            content: '';
            position: absolute;
            left: -2.5rem;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--primary-color);
            border-radius: 2px;
        }}
        
        .section h2 {{
            color: var(--primary-color);
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .section h3 {{
            color: var(--neutral-color);
            font-size: 1.3rem;
            font-weight: 500;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}
        
        .kpi-dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }}
        
        .kpi-card {{
            background: linear-gradient(145deg, #ffffff, #f8fafc);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-color);
            opacity: 0.7;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .kpi-icon {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
            display: block;
        }}
        
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--primary-color), #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .kpi-label {{
            color: var(--neutral-color);
            font-size: 1rem;
            font-weight: 500;
        }}
        
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
            margin: 0.5rem 0;
        }}
        
        .status-danger {{
            background: linear-gradient(145deg, #fee2e2, #fecaca);
            color: var(--danger-color);
            border: 1px solid #f87171;
        }}
        
        .status-warning {{
            background: linear-gradient(145deg, #fef3c7, #fde68a);
            color: var(--warning-color);
            border: 1px solid #fbbf24;
        }}
        
        .status-success {{
            background: linear-gradient(145deg, #d1fae5, #dcfce7);
            color: var(--success-color);
            border: 1px solid #34d399;
        }}
        
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }}
        
        .feature-card {{
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .feature-card:hover {{
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }}
        
        .feature-card.priority-high {{
            border-left: 4px solid var(--danger-color);
            background: linear-gradient(145deg, #fef2f2, #fee2e2);
        }}
        
        .feature-card.priority-medium {{
            border-left: 4px solid var(--warning-color);
            background: linear-gradient(145deg, #fffbeb, #fef3c7);
        }}
        
        .feature-card.priority-low {{
            border-left: 4px solid var(--success-color);
            background: linear-gradient(145deg, #f0fdf4, #dcfce7);
        }}
        
        .code-block {{
            background: linear-gradient(145deg, #1f2937, #374151);
            color: #f9fafb;
            padding: 1.5rem;
            border-radius: 12px;
            overflow-x: auto;
            margin: 1.5rem 0;
            border: 1px solid #4b5563;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .code-block code {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        .alert-box {{
            padding: 1.25rem;
            border-radius: 12px;
            margin: 1.5rem 0;
            border: 1px solid;
            position: relative;
        }}
        
        .alert-box::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            border-radius: 2px;
        }}
        
        .alert-info {{
            background: linear-gradient(145deg, #dbeafe, #bfdbfe);
            border-color: #93c5fd;
            color: #1e40af;
        }}
        
        .alert-info::before {{
            background: #3b82f6;
        }}
        
        .alert-warning {{
            background: linear-gradient(145deg, #fef3c7, #fde68a);
            border-color: #fbbf24;
            color: #92400e;
        }}
        
        .alert-warning::before {{
            background: #f59e0b;
        }}
        
        .timeline {{
            position: relative;
            padding-left: 2rem;
        }}
        
        .timeline::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, var(--primary-color), #60a5fa);
            border-radius: 1px;
        }}
        
        .timeline-item {{
            position: relative;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: white;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }}
        
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -2.5rem;
            top: 2rem;
            width: 12px;
            height: 12px;
            background: var(--primary-color);
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: 0 0 0 4px white, 0 0 0 6px var(--primary-color);
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 8px;
            }}
            
            .header {{
                padding: 2rem 1.5rem;
            }}
            
            .header h1 {{
                font-size: 2.2rem;
            }}
            
            .content {{
                padding: 2rem 1.5rem;
            }}
            
            .kpi-dashboard {{
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }}
            
            .feature-grid {{
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 报告头部 -->
        <div class="header">
            <h1>🚛 新能源货车保险业务分析平台</h1>
            <div class="subtitle">需求规格说明书</div>
            <div class="meta-info">
                基于2025年保单第28-43周数据分析 | 生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
            </div>
        </div>
        
        <!-- 主要内容 -->
        <div class="content">
            <!-- 项目概览 -->
            <div class="section">
                <h2><span>🎯</span> 项目概述</h2>
                <p>基于{self.project_data['analysis_period']}的新能源货车保险业务数据，构建专业的业务分析平台，解决当前赔付率过高（{self.project_data['avg_loss_ratio']}%）的经营问题。</p>
                
                <div class="kpi-dashboard">
                    <div class="kpi-card">
                        <span class="kpi-icon">🚛</span>
                        <div class="kpi-value">{self.project_data['vehicle_count']}</div>
                        <div class="kpi-label">分析车辆数</div>
                    </div>
                    <div class="kpi-card">
                        <span class="kpi-icon">📊</span>
                        <div class="kpi-value">{self.project_data['avg_loss_ratio']}%</div>
                        <div class="kpi-label">平均赔付率</div>
                    </div>
                    <div class="kpi-card">
                        <span class="kpi-icon">⚠️</span>
                        <div class="kpi-value">{self.project_data['high_risk_count']}</div>
                        <div class="kpi-label">高风险机构</div>
                    </div>
                    <div class="kpi-card">
                        <span class="kpi-icon">💰</span>
                        <div class="kpi-value">{self.project_data['total_premium']:,}万</div>
                        <div class="kpi-label">保费规模</div>
                    </div>
                </div>
                
                <div class="status-indicator status-danger">
                    <span>🚨</span>
                    紧急项目：平均赔付率超行业标准130%，需立即实施
                </div>
            </div>
            
            <!-- 功能需求 -->
            <div class="section">
                <h2><span>⚙️</span> 功能需求</h2>
                
                <h3>核心分析模块</h3>
                <div class="feature-grid">
                    <div class="feature-card priority-high">
                        <h4>📈 多维度趋势分析</h4>
                        <p>支持时间、机构、业务类型三个维度的趋势分析，自动识别异常波动。</p>
                        <div class="code-block">
<code># 趋势分析算法
def analyze_trend(data, dimension='time'):
    # 线性回归趋势计算
    trend_slope = calculate_linear_trend(data)
    # 异常值检测
    anomalies = detect_anomalies(data, threshold=2.5)
    return trend_analysis_result</code>
                        </div>
                    </div>
                    
                    <div class="feature-card priority-high">
                        <h4>🎯 智能风险评级</h4>
                        <p>基于机器学习算法，自动评估机构和业务类型的风险等级。</p>
                        <ul>
                            <li>低风险：赔付率 < 70%</li>
                            <li>中风险：赔付率 70-80%</li>
                            <li>高风险：赔付率 80-100%</li>
                            <li>极高风险：赔付率 > 100%</li>
                        </ul>
                    </div>
                    
                    <div class="feature-card priority-medium">
                        <h4>🔮 预测建模</h4>
                        <p>基于历史数据建立预测模型，预测未来4周业务表现。</p>
                        <div class="code-block">
<code># 预测模型
def predict_future_performance(historical_data):
    model = XGBoostRegressor()
    model.fit(historical_data)
    predictions = model.predict(future_periods=4)
    return predictions_with_confidence_intervals</code>
                        </div>
                    </div>
                </div>
                
                <h3>数据可视化需求</h3>
                <div class="alert-box alert-info">
                    <strong>📊 图表组件要求：</strong>
                    <ul>
                        <li>交互式趋势图表（支持缩放、筛选）</li>
                        <li>风险热力图（机构×时间维度）</li>
                        <li>KPI仪表盘（实时数据更新）</li>
                        <li>地理分布图（机构风险地图）</li>
                    </ul>
                </div>
            </div>
            
            <!-- 技术要求 -->
            <div class="section">
                <h2><span>💻</span> 技术要求</h2>
                
                <h3>前端技术栈</h3>
                <div class="code-block">
<code>// 前端技术方案
{{
  "framework": "Vue.js 3.0",
  "charts": ["Chart.js", "D3.js", "ECharts"],
  "ui_library": "Element Plus",
  "responsive": "Bootstrap 5",
  "build_tool": "Vite",
  "browser_support": ["Chrome 90+", "Firefox 88+", "Safari 14+"]
}}</code>
                </div>
                
                <h3>后端技术栈</h3>
                <div class="code-block">
<code># 后端技术方案
{{
  "language": "Python 3.9+",
  "framework": "FastAPI",
  "database": "PostgreSQL 13+",
  "cache": "Redis",
  "ml_library": ["scikit-learn", "xgboost", "prophet"],
  "deployment": "Docker + Kubernetes"
}}</code>
                </div>
                
                <h3>性能要求</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <h4>⚡ 响应速度</h4>
                        <p>页面加载时间 &lt; 2秒</p>
                        <p>数据查询响应 &lt; 3秒</p>
                        <p>图表渲染完成 &lt; 1秒</p>
                    </div>
                    
                    <div class="feature-card">
                        <h4>📊 并发处理</h4>
                        <p>支持100个并发用户</p>
                        <p>数据处理能力：10万条记录/秒</p>
                        <p>内存使用优化：&lt; 2GB</p>
                    </div>
                </div>
            </div>
            
            <!-- 项目计划 -->
            <div class="section">
                <h2><span>📅</span> 项目实施计划</h2>
                
                <div class="timeline">
                    <div class="timeline-item">
                        <h4>第一阶段：需求分析与设计（2周）</h4>
                        <p>完成详细需求分析、技术方案设计、UI/UX设计</p>
                        <div class="status-indicator status-warning">
                            <span>⏰</span> 高优先级 - 立即启动
                        </div>
                    </div>
                    
                    <div class="timeline-item">
                        <h4>第二阶段：核心功能开发（4周）</h4>
                        <p>数据接入、分析算法开发、基础可视化功能</p>
                        <div class="status-indicator status-info">
                            <span>🔧</span> 技术实现阶段
                        </div>
                    </div>
                    
                    <div class="timeline-item">
                        <h4>第三阶段：高级功能与优化（3周）</h4>
                        <p>预测模型、交互优化、性能调优</p>
                        <div class="status-indicator status-info">
                            <span>⚡</span> 性能优化阶段
                        </div>
                    </div>
                    
                    <div class="timeline-item">
                        <h4>第四阶段：测试与部署（2周）</h4>
                        <p>系统测试、用户验收、生产部署</p>
                        <div class="status-indicator status-success">
                            <span>🚀</span> 上线准备阶段
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 预期成果 -->
            <div class="section">
                <h2><span>🎯</span> 预期成果与价值</h2>
                
                <div class="feature-grid">
                    <div class="feature-card status-success">
                        <h4>📊 量化指标</h4>
                        <ul>
                            <li>赔付率预测准确率 > 85%</li>
                            <li>高风险机构识别准确率 > 90%</li>
                            <li>分析效率提升 300%</li>
                            <li>决策响应时间缩短 50%</li>
                        </ul>
                    </div>
                    
                    <div class="feature-card status-success">
                        <h4>💰 业务价值</h4>
                        <ul>
                            <li>预计降低赔付率 15-25%</li>
                            <li>优化承保结构，提升优质业务占比</li>
                            <li>减少人工分析成本 60%</li>
                            <li>提升风险管控能力和合规水平</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 风险评估 -->
            <div class="section">
                <h2><span>⚠️</span> 风险评估与应对</h2>
                
                <div class="alert-box alert-warning">
                    <strong>🚨 高风险项目特征：</strong>
                    <ul>
                        <li>数据质量依赖性强，需要多部门数据协同</li>
                        <li>算法准确性要求极高，影响承保决策</li>
                        <li>业务用户接受度不确定，需要充分的培训和推广</li>
                    </ul>
                </div>
                
                <h3>风险应对措施</h3>
                <div class="feature-grid">
                    <div class="feature-card">
                        <h4>🛡️ 数据质量保障</h4>
                        <p>建立数据质量监控机制，实施多源数据验证，设置数据异常预警</p>
                    </div>
                    
                    <div class="feature-card">
                        <h4>🔍 模型验证机制</h4>
                        <p>A/B测试验证算法效果，历史数据回测，专家经验校验</p>
                    </div>
                    
                    <div class="feature-card">
                        <h4>👥 用户培训计划</h4>
                        <p>分批次用户培训，试点推广策略，持续技术支持服务</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 页脚 -->
        <div style="background: #f8fafc; padding: 2rem; text-align: center; border-top: 1px solid var(--border-color);">
            <p style="margin: 0; color: var(--neutral-color);">
                <strong>生成时间：</strong>{datetime.now().strftime('%Y年%m月%d日 %H:%M')} | 
                <strong>版本：</strong>v1.0 | 
                <strong>状态：</strong>待评审
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: var(--neutral-color);">
                本需求规格说明书基于{self.project_data['analysis_period']}数据分析结果编制
            </p>
        </div>
    </div>
</body>
</html>
    """
    
        return html_content
    
    def save_report(self, content, filename="需求规格说明书.html"):
        """保存HTML报告到文件"""
        output_path = "/Users/xuechenglong/Desktop/weekly_report/开发文档"
        os.makedirs(output_path, exist_ok=True)
        
        filepath = os.path.join(output_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 需求规格说明书已生成：{filepath}")
        return filepath
    
    def run_demo(self):
        """运行完整演示"""
        print("🚀 开始生成车险分析项目需求规格说明书...")
        print("=" * 60)
        
        # 生成HTML内容
        html_content = self.generate_html_requirements_report()
        
        # 保存文件
        filepath = self.save_report(html_content)
        
        # 输出总结
        print("\n" + "=" * 60)
        print("🎉 需求规格说明书生成完成！")
        print("=" * 60)
        print(f"📄 文件位置：{filepath}")
        print(f"📊 文件大小：{len(html_content):,} 字符")
        print(f"🎯 项目范围：新能源货车保险业务分析")
        print(f"📅 分析周期：{self.project_data['analysis_period']}")
        print(f"💰 保费规模：{self.project_data['total_premium']:,}万元")
        print(f"⚠️ 风险等级：极高（赔付率{self.project_data['avg_loss_ratio']}%）")
        
        return filepath

if __name__ == "__main__":
    designer = InsuranceRequirementsDesigner()
    designer.run_demo()