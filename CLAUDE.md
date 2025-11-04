# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**车险周报生成系统** - 一个自动化保险数据分析和周报生成工具，支持多维度钻取分析、风险识别和专业报告生成。

- **技术栈**: Python 3 + Pandas + NumPy
- **核心功能**: 数据加载、KPI计算、趋势分析、异常检测、周报生成
- **分析框架**: 基于麦肯锡商业分析方法论

## 快速开始

### 运行完整周报生成

```bash
# V2.0 完整版（含趋势追踪和新能源货车分析）
python3 generate_report_v2.py

# 新能源货车专项分析
python3 analyze_new_energy_trucks.py
```

### 数据文件要求

- **位置**: `{年份}年保单/` 目录（如 `2024年保单/`, `2025年保单/`）
- **命名格式**: `{年份}保单第{周次}周变动成本明细表.csv`
- **编码**: UTF-8-SIG
- **必需字段**: 26个字段（见 [参考文档/03_technical_design/data_architecture.md](参考文档/03_technical_design/data_architecture.md)）

## 核心架构

### Claude Skills 系统

项目采用模块化 Skills 协作架构，每个 Skill 负责特定分析任务：

1. **loading-insurance-data** (数据加载)
   - 智能周期检测和管理
   - 自动数据清洗和验证
   - 支持多年度数据整合

2. **analyzing-new-energy-trucks** (新能源货车分析)
   - 电池风险三维模型
   - 机构风险分级（6档）
   - 业务类型深度钻取
   - 异常波动自动检测

3. **insurance-kpi-calculator** (KPI计算)
   - 16个核心KPI自动计算
   - 智能状态判断（卓越/健康/预警/危险/高危）
   - 环比分析和趋势识别

4. **insurance-weekly-report-assembler** (周报组装)
   - 金字塔原理结构
   - MECE分析框架
   - 董事会级别专业度

### 数据分析流程

```
数据加载 → KPI计算 → 多维钻取 → 异常检测 → 报告生成
   ↓          ↓          ↓          ↓          ↓
loading  calculator  drilldown  trend      assembler
```

### 渐进式钻取逻辑

系统采用3层渐进式钻取，避免维度爆炸：

1. **Layer 1**: 能源类型（新能源 vs 传统车）
2. **Layer 2**: 业务类型 TOP3（按严重性评分）
3. **Layer 3**: 对每个TOP3，分两路钻取：
   - Path A: 业务类型 + 险别组合（主全/交三/单交）
   - Path B: 业务类型 + 续保状态（新保/续保/转保）

**终止条件**:
- 能源类型健康（赔付率<70% 且 边际贡献率>8%）
- 占比<1%（小规模数据停止钻取）

## 核心指标体系

### 16个核心KPI（4×4网格布局）

**第一行: 核心比率指标**
- 满期边际贡献率 = 100% - 变动成本率
- 保费时间进度达成率（50周工作制）
- 满期赔付率
- 费用率

**第二行: 核心金额指标**
- 满期边际贡献额
- 签单保费
- 已报告赔款
- 费用额

**第三行: 结构与效率指标**
- 变动成本率 = 满期赔付率 + 费用率
- 满期率
- 满期出险率
- 保单件数

**第四行: 单均质量指标**
- 赔案件数
- 单均保费
- 案均赔款
- 单均费用

详细计算公式见: [参考文档/03_technical_design/core_calculations.md](参考文档/03_technical_design/core_calculations.md)

### 风险评级标准

| 指标 | 卓越 | 健康 | 预警 | 危险 | 高危 |
|------|------|------|------|------|------|
| 赔付率 | <50% | 50-60% | 60-70% | 70-80% | >80% |
| 边际贡献率 | >12% | 8-12% | 6-8% | 4-6% | <4% |
| 费用率 | <7.5% | 7.6-12.5% | 12.6-17.5% | 17.6-22.5% | >22.5% |

## 关键技术特性

### 智能周期管理

```python
# 自动检测可用周次
weeks = detect_available_weeks("2025年保单")

# 智能推荐分析周期（默认最近5周）
START_WEEK = None  # 自动推断
END_WEEK = None    # 自动推断
LOOKBACK_WEEKS = 5 # 回溯周数
```

### 当周发生值计算

系统使用差值法计算累计数据中的当周值：
- 当周保费 = 本周累计 - 上周累计
- 自动容错处理缺失周次（最多向前查找5周）

### 异常波动检测

- **单周暴涨**: 单周上升>1.5倍均值
- **连续恶化**: 3周连续上升
- **趋势反转**: 方向改变且幅度>10%

## 数据架构关键点

### 26个必需字段

关键字段说明：
- `snapshot_date`: 快照日期 (YYYY-MM-DD)
- `policy_start_year`: 保单年度 (2024/2025)
- `week_number`: 周序号 (28-44)
- `is_new_energy_vehicle`: 是否新能源 (True/False)
- `business_type_category`: 业务类型（17种，包括"10吨以上-普货"、"网约车"等）
- `third_level_organization`: 三级机构（13种，如"本部"、"达州"、"德阳"等）
- `coverage_type`: 险别组合（主全/交三/单交）
- `renewal_status`: 新续转状态（新保/续保/转保）
- `signed_premium_yuan`: 签单保费
- `matured_premium_yuan`: 满期保费
- `reported_claim_payment_yuan`: 已报告赔款
- `expense_amount_yuan`: 费用金额
- `policy_count`: 保单件数
- `claim_case_count`: 赔案件数

完整字段定义见: [参考文档/03_technical_design/data_architecture.md](参考文档/03_technical_design/data_architecture.md)

### 数据验证规则

- **必填字段**: 除评级字段外，所有字段必须有值
- **数值范围**:
  - `policy_start_year`: 2024-2025
  - `week_number`: 28-44（根据实际数据调整）
  - 金额/数量字段 ≥ 0（`marginal_contribution_amount_yuan` 可为负）
- **编码**: 统一使用 UTF-8-SIG
- **布尔值**: `True`/`False`（首字母大写）

## 开发约定

### 报告生成规范

1. **年度隔离原则**: 2024保单和2025保单必须分别生成独立报告，不混合分析
2. **机构过滤**: 分析时排除"本部"数据
3. **麦肯锡标准**: 遵循金字塔原理、MECE框架、So What思维
4. **输出位置**: 所有报告输出到 `周报/` 目录

### 命名约定

- **报告文件**: `{年份}保单第{周次}周经营周报.md` 或 `{年份}保单{分析类型}报告_第{起始周}-{结束周}周.md`
- **数据文件**: `{年份}保单第{周次}周变动成本明细表.csv`
- **缓存文件**: 存放在 `.cache/` 目录

### 错误处理策略

- **缺失数据**: 容忍度≤20%，超过则报错
- **异常值**: 3σ原则自动检测并标记
- **编码错误**: 自动尝试 UTF-8-SIG → GBK → GB2312
- **文件不存在**: 提供明确的路径和命名规范提示

## 新能源货车专项分析

### 高风险识别规则

**立即警报条件**:
- 单机构赔付率>150%
- 单周赔付率环比上升>50%
- 案均赔款突增>10,000元
- 单交险别赔付率>300%

**重点关注名单**:
- 连续3周赔付率>100%
- 累计边际贡献率<-30%
- 规模占比>10%且赔付率>80%

### 电池风险三维模型

1. **电池质量风险**: 自燃、热失控、续航衰减
2. **充电基础设施**: 三四线城市基础设施不足
3. **车队运营风险**: 高强度使用、维护不当

## 常见任务

### 生成指定周期的报告

```bash
# 编辑 generate_report_v2.py 顶部配置
START_WEEK = 35  # 起始周
END_WEEK = 44    # 结束周

# 运行生成
python3 generate_report_v2.py
```

### 分析特定机构

```python
# 在数据加载后筛选特定机构
df = df[df['third_level_organization'].isin(['达州', '德阳'])]
```

### 调整风险阈值

编辑脚本中的阈值配置：
```python
LOSS_RATIO_DANGER = 70    # 赔付率预警线
MARGIN_RATE_MIN = 8       # 最低边际贡献率
OUTLIER_THRESHOLD = 3.0   # 异常值检测阈值
```

## 关键参考文档

- [数据架构](参考文档/03_technical_design/data_architecture.md) - 26字段详细说明
- [核心计算公式](参考文档/03_technical_design/core_calculations.md) - 16个KPI计算方法
- [技术栈说明](参考文档/03_technical_design/tech_stack.md) - 依赖和环境配置
- [麦肯锡分析方法论](docs/methodology/麦肯锡级业务分析方法论.md) - 报告写作标准
- [V2.0完成总结](V2.0_项目完成总结.md) - 项目架构和实现细节

## 故障排除

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `FileNotFoundError` | 数据文件不存在 | 检查文件路径和命名格式 |
| `UnicodeDecodeError` | 编码问题 | 使用 `encoding='utf-8-sig'` |
| `KeyError: column` | 缺少必需字段 | 检查CSV文件是否包含全部26个字段 |
| `缺失数据比例超过容忍度` | 周次数据不完整 | 调整 `START_WEEK`/`END_WEEK` 或补充数据 |

### 性能优化

- **大数据处理**: 对于>100,000行数据，考虑使用 Parquet 格式
- **内存限制**: 分批加载周次数据，避免一次性加载全部
- **计算加速**: 使用 `.cache/` 缓存中间结果

## 项目状态

- **版本**: V2.0
- **状态**: ✅ 生产就绪
- **最后更新**: 2025-11-04
- **维护**: 保险数据团队
