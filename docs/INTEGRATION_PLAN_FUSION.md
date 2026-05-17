# MCN-AI 完整融合方案

> 将4份Manus提示词能力系统化融入MCN AI Replacement
> 
> 日期：2026-05-17
> 基于：现状分析 + 4份提示词资产 + 已有代码能力

---

## 一、现状诊断

### 1.1 系统覆盖度矩阵

按照原始设计文档的9大MCN模块：

| 模块 | MCN职能 | 覆盖率 | 问题 |
|------|---------|--------|------|
| M1 | 全平台热点监测 | **85%** | Hermes已采集，但热点评分未反馈给采集端 |
| M2 | 趋势预判与赛道分析 | **0%** | 完全缺失 |
| M3 | 平台规则与算法解读 | **15%** | 只有静态广告法词库，无动态规则监测 |
| M4 | 账号数据分析与诊断 | **0%** | 无平台API接入 |
| M6 | 粉丝运营与互动管理 | **0%** | 未涉及 |
| M7 | 选题策划与脚本共创 | **70%** | 脚本和选题未闭环（生成→审核→迭代） |
| M9 | 内容合规审核 | **40%** | 只有关键词匹配，无平台规则感知 |
| M10 | 数据驱动的内容迭代 | **0%** | 无发布后数据分析回路 |
| M19 | 对标创作者发掘与分析 | **30%** | 有分析能力但无数据源、无反馈回路 |

### 1.2 核心断点

```
当前流程：
  Hermes采集 → SOUL评分 → 脚本提示词 → (手动Claude Code执行) → 结束
                                    ↓
                          ❌ 审核没接上
                          ❌ 对标分析孤立
                          ❌ 平台规则缺失
                          ❌ 趋势预判空白
                          ❌ 发布后无追踪

目标流程：
  趋势预判 → 平台规则 → Hermes采集 → SOUL评分(+对标差异化) 
    → 脚本生成(+规则提醒) → 合规审核(+动态规则) → 发布 
    → 数据回收 → 迭代
```

---

## 二、4份文件的能力映射

### 2.1 文件→模块→系统能力

| 文件 | 核心产出 | 映射到的系统能力 | 对应新模块 |
|------|---------|----------------|-----------|
| `wideresearch-hot-topics.md` | 20-30条结构化热点 | **已覆盖**，Hermes每日执行 | — |
| `widesearch-creator-analysis.md` | 对标创作者档案+爆款拆解 | 选题差异化评分、脚本策略参考 | **CreatorPipeline** |
| `widesearch-platform-rules.md` | 平台规则变动清单 | 动态合规规则、脚本风险提示 | **RulesMonitor** |
| `deepresearch-trend-report.md` | 3-6月赛道趋势预判 | 内容战略规划、关键词库更新 | **TrendAnalyzer** |

### 2.2 各文件融合深度

#### `wideresearch-hot-topics.md` — 已融合，需要增强闭环

**现有**：Hermes执行 → 报告 → MCN读取 → SOUL评分

**缺少**：
- 评分结果没有反哺给Hermes（哪些热点最终被选用，调整采集策略）
- 没有从报告中提取「受众痛点库」（报告里有但MCN没解析）
- 没有利用报告中的「执行路径报告」（用于优化采集策略）

#### `widesearch-creator-analysis.md` — 需要全链路设计

**文件价值**：

这份文件定义的不是一个简单的搜索任务，而是一个**四层分析体系**：

```
第一层：创作者发掘
  ├── 多平台搜索（抖音/小红书/B站/视频号）
  ├── 两层级分类（成长对标层 / 学习标杆层）
  └── 产出：创作者发现表

第二层：深度拆解（Top 5）
  ├── 画像分析（人设、定位、受众、商业模式）
  ├── 内容策略（主题分布、格式、频率、爆款规律）
  ├── 增长路径（起号策略、关键转折、流量来源）
  └── 产出：单人深度分析报告

第三层：对比矩阵
  ├── 多维度横评（定位/受众/风格/商业模式）
  ├── 共性规律提取（赛道成功模式）
  └── 产出：竞争态势图

第四层：差异化机会
  ├── 内容空白识别
  ├── 受众重叠分析
  ├── 可迁移元素提取
  └── 产出：我的行动建议
```

**现状**：`CreatorProfiler` 只有80行，`ViralContentAnalyzer` 只有120行，且无法自动获取数据。

**融合目标**：把这四层分析变成可持续运行的流水线。

#### `widesearch-platform-rules.md` — 空白→核心能力

**文件价值**：

```
监测维度：
  ├── 算法调整（推荐机制变化）
  ├── 社区规范（审核标准更新）
  ├── 扶持政策（流量激励/挑战赛）
  └── 跨平台趋势（收紧/放松）

输出：
  ├── 变动清单（平台|类型|内容|来源|可信度|影响）
  ├── 重点解读（影响≥中的变动展开分析）
  ├── 应对建议（短期调整+中期适应）
  └── 无变动确认（有价值的"无变化"信息）
```

**现状**：`ContentRiskScanner` 只有广告法禁用词库，完全不知道平台在发生什么。

**融合目标**：把平台规则从"静态词库"升级为"动态情报系统"。

#### `deepresearch-trend-report.md` — 战术→战略

**文件价值**：

```
研究维度：
  ├── 赛道宏观趋势（子赛道增长/衰退判断）
  ├── 内容形式演变（平台算法偏好变化）
  ├── 受众需求迁移（焦虑→理性，副业→意义）
  └── 竞争格局变化（新进入者、方向调整）

输出：
  ├── 趋势判断报告
  ├── 内容战略建议
  ├── 机会窗口识别
  └── 风险预警
```

**现状**：系统只能告诉你"今天什么热"，不能告诉你"半年后该做什么"。

**融合目标**：把趋势分析从"一次性报告"变成"持续演进的战略输入"。

---

## 三、完整融合架构

### 3.1 目标系统全景

```
                        ┌──────────────────────┐
                        │   deepresearch-trend  │ ← 月度
                        │   赛道趋势预判         │
                        └──────────┬───────────┘
                                   │ 战略输入
                                   ▼
              ┌──────────────────────────────────────┐
              │        战略层 (月度更新)               │
              │  TrendAnalyzer: 趋势→关键词库→权重    │
              └──────────────────┬───────────────────┘
                                 │
  ┌──────────────────────────────┼──────────────────────────────┐
  │                              │                              │
  ▼                              ▼                              ▼
┌──────────────┐    ┌──────────────────────┐    ┌──────────────┐
│ widesearch-  │    │  widesearch-creator  │    │ widesearch-  │
│ platform-    │    │  -analysis           │    │ hot-topics   │
│ rules        │    │  对标创作者发掘        │    │ 热点采集      │
│ 平台规则监测  │    │                      │    │              │
└──────┬───────┘    └──────────┬───────────┘    └──────┬───────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────────────┐    ┌──────────────┐
│ RulesMonitor │    │  CreatorPipeline     │    │   (已融合)    │
│ 规则情报→     │    │  对标分析→           │    │ Hermes报告   │
│ Compliance   │    │  Profiler+Analyzer  │    │ →Collector   │
└──────┬───────┘    └──────────┬───────────┘    └──────┬───────┘
       │                       │                       │
       │    差异化机会          │                       │
       │ ┌─────────────────────┘                       │
       │ │  反哺                                       │
       ▼ ▼  ◄────────────────────────────────────────  │
┌──────────────────────────────────────────────────────┐
│              战术层 (每日/每周)                        │
│                                                      │
│  SOULHotTopicMatcher                                 │
│  ├── 有限性三角 (30%)                                │
│  ├── 受众匹配 (25%)                                  │
│  ├── 三阶对话法 (25%)                                │
│  ├── 差异化空间 (15%) ← 对标分析输入                  │
│  └── 风险评分 (5%)    ← 平台规则输入                  │
│                                                      │
│  SOULScriptWriter                                    │
│  ├── 脚本生成                                        │
│  ├── 对标参考注入 ← 对标分析输入                      │
│  ├── 规则提醒注入 ← 平台规则输入                      │
│  └── 趋势方向注入 ← 趋势分析输入                      │
│                                                      │
│  ContentRiskScanner                                  │
│  ├── 广告法检查                                      │
│  ├── 平台规则检查 ← RulesMonitor输入                  │
│  └── 敏感词检查                                      │
└──────────────────────────────────────────────────────┘
```

### 3.2 数据流设计

```
月度：deepresearch-trend → TrendAnalyzer
  ├── 更新 keywords.yaml
  ├── 调整 SOUL评分权重
  └── 生成月度内容策略

双周：widesearch-platform-rules → RulesMonitor
  ├── 更新平台规则库
  ├── 生成风险提醒
  └── 注入 ContentRiskScanner

每周：Hermes热点采集 (已融合)
  ├── 读取报告
  ├── 提取痛点库
  └── → SOULHotTopicMatcher

每月：widesearch-creator-analysis → CreatorPipeline
  ├── 更新对标创作者库
  ├── 拆解爆款内容
  ├── 识别差异化机会
  └── → 反哺评分 + 脚本
```

---

## 四、新模块设计

### 4.1 RulesMonitor — 平台规则情报系统

**输入**：`widesearch-platform-rules` 提示词执行结果（定期在Manus/Claude Code中执行）

**处理**：
```python
class RulesMonitor:
    """
    平台规则情报系统
    
    功能：
    1. 解析平台规则变动报告
    2. 维护动态规则库（替代/补充静态广告法词库）
    3. 生成各平台风险提醒
    4. 向脚本生成注入规则上下文
    """
    
    # 规则库结构
    rules_db = {
        "douyin": {
            "algorithm_changes": [],    # 算法变化
            "content_policies": [],     # 内容政策
            "restricted_topics": [],    # 限制话题
            "promotions": [],           # 扶持活动
            "last_updated": None,
            "overall_stance": "neutral" # tightening/relaxing/neutral
        },
        "xiaohongshu": {...},
        "bilibili": {...},
    }
    
    def import_report(self, report_md: str):
        """导入规则变动报告，更新规则库"""
    
    def check_content(self, script: dict, platform: str) -> list:
        """检查脚本是否违反最新平台规则，返回风险点"""
    
    def get_rule_context(self, platform: str) -> str:
        """获取当前平台规则摘要，注入脚本生成提示词"""
```

### 4.2 CreatorPipeline — 对标分析流水线

**输入**：`widesearch-creator-analysis` 提示词执行结果

**处理**：
```python
class CreatorPipeline:
    """
    对标分析流水线
    
    四层分析：
    1. 发掘 → CreatorProfiler 建档
    2. 拆解 → ViralContentAnalyzer 分析
    3. 对比 → 构建差异化矩阵
    4. 反哺 → 注入评分和脚本生成
    
    功能：
    1. 解析创作者分析报告
    2. 更新对标创作者库
    3. 提取可迁移元素
    4. 生成差异化建议
    """
    
    def import_report(self, report_md: str):
        """导入创作者分析报告"""
    
    def update_profiles(self):
        """更新 CreatorProfiler 数据库"""
    
    def analyze_viral_patterns(self) -> list:
        """提取爆款规律模式"""
    
    def get_differentiation_signals(self) -> dict:
        """获取差异化信号，注入 SOULHotTopicMatcher"""
    
    def get_script_references(self, topic: str) -> list:
        """根据选题查找对标创作者的参考内容"""
```

### 4.3 TrendAnalyzer — 趋势分析引擎

**输入**：`deepresearch-trend-report` 提示词执行结果

**处理**：
```python
class TrendAnalyzer:
    """
    赛道趋势分析引擎
    
    功能：
    1. 解析趋势报告
    2. 更新关键词库权重
    3. 调整SOUL评分参数
    4. 生成月度内容策略
    """
    
    def import_report(self, report_md: str):
        """导入趋势报告"""
    
    def update_keywords(self):
        """更新 config/keywords.yaml 的子赛道权重"""
    
    def update_scoring_weights(self):
        """根据趋势调整SOUL评分的维度权重"""
    
    def generate_monthly_strategy(self) -> dict:
        """生成月度内容策略建议"""
```

---

## 五、模块间的连接点

### 5.1 注入点设计

将三个新模块的能力注入到已有的核心流程中：

```
SOULHotTopicMatcher.execute()
  ├── [现有] 有限性三角评分
  ├── [现有] 受众匹配评分
  ├── [现有] 三阶对话法评分
  ├── [新增] 差异化评分 ← CreatorPipeline.get_differentiation_signals()
  ├── [新增] 趋势加权     ← TrendAnalyzer.get_topic_weights()
  └── [现有] 风险评分     ← RulesMonitor.get_platform_risk()

SOULScriptWriter._build_script_prompt()
  ├── [现有] SOUL画像上下文
  ├── [现有] 三阶对话法框架
  ├── [新增] 对标参考     ← CreatorPipeline.get_script_references(topic)
  ├── [新增] 规则提醒     ← RulesMonitor.get_rule_context(platform)
  └── [新增] 趋势方向     ← TrendAnalyzer.get_content_direction()

ContentRiskScanner.execute()
  ├── [现有] 广告法检查
  ├── [新增] 平台规则检查 ← RulesMonitor.check_content(script, platform)
  └── [现有] 敏感词检查
```

### 5.2 CLI命令新增

```bash
# 平台规则
python scripts/run_workflow.py rules-import report.md     # 导入规则报告
python scripts/run_workflow.py rules-check -p douyin       # 查看平台当前规则
python scripts/run_workflow.py rules-status                # 各平台规则状态

# 对标分析
python scripts/run_workflow.py creator-import report.md    # 导入分析报告
python scripts/run_workflow.py creator-list                # 列对标创作者
python scripts/run_workflow.py creator-insight "选题"      # 查对标参考

# 趋势分析
python scripts/run_workflow.py trend-import report.md      # 导入趋势报告
python scripts/run_workflow.py trend-strategy              # 生成本月策略
```

### 5.3 统一工作流

```bash
# 月度战略工作流
python scripts/run_workflow.py trend-strategy              # ① 趋势→调整方向
python scripts/run_workflow.py rules-status                # ② 确认规则现状
python scripts/run_workflow.py creator-insight "选题"      # ③ 查对标参考

# 每日战术工作流（保持不变）
python scripts/run_workflow.py soul-rank --top 5           # ① SOUL选题
python scripts/run_workflow.py soul-script -t ".." -a ".." # ② 生成脚本

# 完整内容创作（新）：一站式命令
python scripts/run_workflow.py create-full \
  --topic "选题" --platform douyin --with-rules --with-creator-ref
```

---

## 六、实施计划

### Phase A：RulesMonitor（3-4天）

| Day | 任务 |
|-----|------|
| 1 | 报告解析器（变动清单表格→规则库） |
| 2 | ContentRiskScanner 增强（注入动态规则） |
| 3 | script生成规则上下文注入 |
| 4 | CLI命令 + 测试 |

### Phase B：CreatorPipeline（4-5天）

| Day | 任务 |
|-----|------|
| 1-2 | 报告解析器（四层结构提取） |
| 3 | CreatorProfiler + ViralContentAnalyzer 增强 |
| 4 | 差异化信号注入 SOULHotTopicMatcher |
| 5 | CLI命令 + 测试 |

### Phase C：TrendAnalyzer（3-4天）

| Day | 任务 |
|-----|------|
| 1 | 报告解析器（趋势判断+权重提取） |
| 2 | keywords.yaml 动态更新 |
| 3 | SOUL评分权重调整机制 |
| 4 | 月度策略生成 + 测试 |

### Phase D：集成与串联（2-3天）

| Day | 任务 |
|-----|------|
| 1 | 注入点全部串联 |
| 2 | 统一工作流测试 |
| 3 | 文档更新 |

**总计**：12-16天

---

## 七、融合前后对比

| 维度 | 融合前 | 融合后 |
|------|--------|--------|
| **MCN模块覆盖** | 4/9 (44%) | 7/9 (78%) |
| **合规审核** | 静态词库 | 动态规则+静态词库 |
| **对标分析** | 孤立模块 | 反馈到评分+脚本 |
| **趋势分析** | 无 | 月度战略输入 |
| **关键词库** | 手动维护 | 趋势驱动自动更新 |
| **评分权重** | 固定权重 | 趋势驱动自适应 |
| **脚本质量** | 纯SOUL框架 | SOUL+对标参考+规则提醒 |
| **战略能力** | 无 | 月度内容策略报告 |

---

**文档版本**：v1.0  
**状态**：待审核

DOCEND
