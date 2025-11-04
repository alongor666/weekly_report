---
name: insurance-requirements-designer
description: 设计车险分析项目的需求草案，生成专业的HTML格式分析报告。在车险项目需求分析、功能设计、报告生成或制定分析方案时使用。
---

# 车险分析项目需求设计器

## 🎯 核心功能

专门用于设计车险分析项目的需求草案，提供：
- 需求收集和分析框架
- HTML格式专业报告生成
- 功能模块设计指导
- 技术方案建议
- 项目交付物规划

## ⚡ 立即开始

```python
# 设计完整需求方案
designer = InsuranceRequirementsDesigner()
requirements = designer.gather_requirements(project_type="新能源货车分析")
html_report = designer.generate_html_report(requirements)

# 快速生成特定模块
dashboard_req = designer.design_dashboard_requirements()
analysis_req = designer.design_analysis_requirements()
```

## 📋 需求设计框架

### 1. 项目背景分析

```markdown
## 项目背景

### 业务现状
- 【现状描述】当前新能源货车业务赔付率160.5%，严重亏损
- 【数据基础】基于2025年保单第28-43周数据，共1310辆新能源车
- 【分析范围】涵盖9个三级机构，14周连续数据

### 问题识别  
- 【核心问题】平均赔付率远超行业警戒线70%
- 【关键机构】青羊机构赔付率214.1%，风险极高
- 【业务痛点】单交险别赔付率657.8%，承保政策需调整
```

### 2. 功能需求设计

#### 数据层需求
```python
# 数据接口需求
data_requirements = {
    "sources": [
        "保单变动成本明细表",
        "理赔数据接口", 
        "机构组织架构",
        "产品配置信息"
    ],
    "frequency": "weekly",
    "format": "CSV/JSON",
    "validation": "自动数据质量检查"
}
```

#### 分析层需求
```python
# 核心分析功能
analysis_modules = {
    "trend_analysis": {
        "description": "多周趋势分析",
        "algorithms": ["线性回归", "季节性调整", "异常检测"],
        "output": "趋势图表+预警信息"
    },
    "risk_assessment": {
        "description": "风险评估评级",
        "models": ["赔付率模型", "风险评分卡", "机构评级"],
        "thresholds": "基于行业标准的动态阈值"
    }
}
```

#### 展示层需求
```html
<!-- 仪表盘组件 -->
<div class="dashboard-component">
  <kpi-card title="总体赔付率" value="160.5%" status="danger" trend="+5.2%" />
  <chart-component type="trend" data="weekly_loss_ratio" />
  <alert-panel alerts="high_risk_alerts" />
</div>
```

## 🎨 HTML报告生成器

### 专业报告模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>车险分析项目需求规格说明书</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --neutral-color: #6b7280;
            --background-color: #f9fafb;
            --text-color: #111827;
            --border-color: #e5e7eb;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary-color), #1d4ed8);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .header .subtitle {
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .content {
            padding: 2rem;
        }
        
        .section {
            margin-bottom: 3rem;
        }
        
        .section h2 {
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        .section h3 {
            color: var(--neutral-color);
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .kpi-card {
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.2s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .kpi-label {
            color: var(--neutral-color);
            font-size: 0.9rem;
        }
        
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-danger {
            background-color: #fee2e2;
            color: var(--danger-color);
        }
        
        .status-warning {
            background-color: #fef3c7;
            color: var(--warning-color);
        }
        
        .status-success {
            background-color: #d1fae5;
            color: var(--success-color);
        }
        
        .feature-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
        }
        
        .feature-table th,
        .feature-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        .feature-table th {
            background-color: #f3f4f6;
            font-weight: 600;
            color: var(--neutral-color);
        }
        
        .priority-high {
            border-left: 4px solid var(--danger-color);
        }
        
        .priority-medium {
            border-left: 4px solid var(--warning-color);
        }
        
        .priority-low {
            border-left: 4px solid var(--success-color);
        }
        
        .code-block {
            background: #1f2937;
            color: #f9fafb;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin: 1rem 0;
        }
        
        .alert-box {
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        }
        
        .alert-info {
            background-color: #dbeafe;
            border: 1px solid #93c5fd;
            color: #1e40af;
        }
        
        .alert-warning {
            background-color: #fef3c7;
            border: 1px solid #fbbf24;
            color: #92400e;
        }
        
        .timeline {
            position: relative;
            padding-left: 2rem;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--primary-color);
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 2rem;
        }
        
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -2rem;
            top: 0.5rem;
            width: 12px;
            height: 12px;
            background: var(--primary-color);
            border-radius: 50%;
            transform: translateX(-50%);
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
            }
            
            .header {
                padding: 1.5rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .content {
                padding: 1.5rem;
            }
            
            .kpi-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
```

### 动态内容生成

```python
# 需求报告生成器
def generate_requirements_report(project_data):
    """生成完整的需求规格说明书"""
    
    html_template = """
    <div class="section">
        <h2><span>🎯</span> 项目概述</h2>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value" style="color: var(--primary-color)">{total_vehicles}</div>
                <div class="kpi-label">分析车辆数</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color: var(--danger-color)">{avg_loss_ratio}%</div>
                <div class="kpi-label">平均赔付率</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color: var(--warning-color)">{high_risk_orgs}</div>
                <div class="kpi-label">高风险机构数</div>
            </div>
        </div>
    </div>
    """
    
    return html_template.format(
        total_vehicles=project_data['vehicle_count'],
        avg_loss_ratio=project_data['avg_loss_ratio'],
        high_risk_orgs=project_data['high_risk_count']
    )
```

## 🔧 专业工具集

### 需求收集工具

```bash
# 交互式需求收集
python scripts/collect_requirements.py --type=insurance --format=structured

# 需求验证和完整性检查
python scripts/validate_requirements.py --file=draft_requirements.md
```

### HTML报告生成器

```bash
# 生成完整HTML报告
python scripts/generate_html_report.py --data=project_data.json --template=professional

# 导出PDF版本
python scripts/export_to_pdf.py --html=report.html --output=requirements_spec.pdf
```

### 需求模板库

```python
# 标准需求模板库
templates = {
    "dashboard_requirements": {
        "sections": ["数据展示", "交互功能", "导出能力", "权限控制"],
        "technologies": ["HTML5", "CSS3", "JavaScript", "Chart.js"],
        "responsive": True,
        "accessibility": "WCAG 2.1"
    },
    "analysis_requirements": {
        "algorithms": ["趋势分析", "异常检测", "预测建模"],
        "accuracy": ">95%",
        "performance": "<3秒响应",
        "scalability": "10万+记录"
    }
}
```

## 📋 需求设计检查清单

### 功能性需求
- [ ] 数据源识别和接口定义
- [ ] 核心算法和计算方法
- [ ] 用户界面和交互设计
- [ ] 报告生成和导出功能
- [ ] 权限管理和安全控制

### 非功能性需求
- [ ] 性能指标（响应时间、并发量）
- [ ] 可靠性要求（可用性、容错性）
- [ ] 可维护性（模块化、文档化）
- [ ] 可扩展性（数据量、功能扩展）
- [ ] 兼容性（浏览器、设备）

### 项目约束
- [ ] 时间计划和里程碑
- [ ] 资源预算和人员配置
- [ ] 技术栈和开发环境
- [ ] 质量标准和验收条件
- [ ] 风险识别和应对措施

## 🎨 报告美化功能

### 自动生成图表
```html
<!-- 动态图表嵌入 -->
<div class="chart-container">
    <canvas id="trendChart" data-chart-type="line" data-data-source="loss_ratio_trend"></canvas>
    <div class="chart-controls">
        <button onclick="toggleChartType()">切换图表类型</button>
        <button onclick="exportChart()">导出图表</button>
    </div>
</div>
```

### 响应式设计
```css
/* 移动优先的响应式设计 */
@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    
    .chart-container {
        height: 300px;
    }
}
```

### 交互动效
```javascript
// 平滑滚动和动画效果
document.addEventListener('DOMContentLoaded', function() {
    // KPI卡片动画
    animateKPIValues();
    
    // 图表渐进式加载
    loadChartsSequentially();
    
    // 导航平滑滚动
    enableSmoothScrolling();
});
```

## 🚀 高级功能

### AI辅助需求优化
```python
# 需求智能分析和建议
def optimize_requirements(requirements_text):
    """AI驱动的需求优化建议"""
    suggestions = []
    
    # 完整性检查
    if not check_completeness(requirements_text):
        suggestions.append("建议补充非功能性需求描述")
    
    # 可行性评估
    feasibility_score = assess_feasibility(requirements_text)
    if feasibility_score < 0.7:
        suggestions.append("需求可行性较低，建议调整技术方案")
    
    # 成本估算
    cost_estimate = estimate_development_cost(requirements_text)
    suggestions.append(f"预估开发成本：{cost_estimate}")
    
    return suggestions
```

### 版本控制和协作
```bash
# 需求版本管理
python scripts/version_control.py --action=create --version=v1.0 --description="初始版本"

# 团队协作和评论
python scripts/collaboration_tools.py --action=add_comment --section="功能需求" --comment="建议增加导出功能"
```

### 自动化测试用例生成
```python
# 基于需求自动生成测试用例
def generate_test_cases(requirements):
    """自动生成测试用例"""
    test_cases = []
    
    for functional_req in requirements['functional']:
        test_case = {
            'id': generate_test_id(),
            'description': functional_req['description'],
            'steps': generate_test_steps(functional_req),
            'expected_result': functional_req['expected_result'],
            'priority': determine_priority(functional_req)
        }
        test_cases.append(test_case)
    
    return test_cases
```

这个需求设计器skill将帮助您系统化地设计车险分析项目的需求，生成专业的HTML格式文档，确保项目需求的完整性和专业性。