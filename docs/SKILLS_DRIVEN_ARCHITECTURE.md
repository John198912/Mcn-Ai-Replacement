# MCN AI Replacement — Skills 驱动架构方案

> 从 Python 脚本驱动 → Claude Code Skill 驱动
> 
> 核心理念：LLM 做分析，Python 做管道
> 
> 设计日期：2026-05-17

---

## 一、架构重塑

### 1.1 原则

```
❌ 之前的错误：
   Python 做分析（regex解析、规则引擎、关键词匹配）
   LLM 被当成外挂（手动复制粘贴提示词）

✅ 正确的分工：
   Skill（LLM + WebSearch）→ 采集 + 分析 + 评分 + 策略
   Python → 调度触发 + 数据验证 + 入库 + 同步
```

### 1.2 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  Skills 层（LLM + WebSearch）                                │
│                                                             │
│  mcn-hotspot-research    mcn-platform-rules                 │
│  mcn-creator-analysis    mcn-trend-research                 │
│                                                             │
│  运行在 Claude Code / Hermes Agent 中                       │
│  产出：结构化 JSON → data/skill_outputs/                    │
└─────────────────────────────────────────────────────────────┘
                          ↓ JSON
┌─────────────────────────────────────────────────────────────┐
│  管道层（Python — 只做I/O和调度）                            │
│                                                             │
│  SkillOutputReader    读取JSON → 验证 → 入库                │
│  DataQualityValidator 数据质量检查                           │
│  FeishuBaseAdapter    写入飞书Base                           │
│  TwoLayerManager      本地 + GitHub 同步                    │
│  BackupManager        备份管理                               │
│  MCNScheduler         定时触发 Skill                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  存储层                                                     │
│                                                             │
│  飞书Base（结构化数据 + 可视化）                             │
│  本地 SQLite + Markdown（离线主存储）                        │
│  GitHub（版本控制 + 备份）                                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Python 瘦身清单

| 模块 | 之前角色 | 之后角色 | 变动 |
|------|---------|---------|------|
| `HermesHotspotAdapter` | 解析Hermes Markdown报告 | **删除** — Skill直接产出JSON | ✂️ |
| `SOULHotTopicMatcher` | Python关键词评分 | **删除** — LLM语义评分更准 | ✂️ |
| `SOULScriptWriter` | 生成提示词模板 | **保留重写** — 改为Skill内逻辑 | 🔄 |
| `ManualHotspotImporter` | CSV/JSON解析 | **保留** — 手动导入兜底 | ✅ |
| `HotspotCollector` | 协调多数据源 | **简化** — 只读Skill JSON输出 | 🔄 |
| `RulesMonitor` | Markdown报告解析 | **删除** — Skill直接产出规则JSON | ✂️ |
| `CreatorPipeline` | Markdown报告解析 | **删除** — Skill直接产出创作者JSON | ✂️ |
| `TrendAnalyzer` | Markdown报告解析 | **删除** — Skill直接产出趋势JSON | ✂️ |
| `FeishuBaseAdapter` | 飞书Base读写 | **保留** — 纯粹的API调用 | ✅ |
| `FeishuWikiKB` | 飞书Wiki管理 | **保留** | ✅ |
| `TwoLayerKnowledgeManager` | 本地+GitHub同步 | **保留** | ✅ |
| `BackupManager` | 备份恢复 | **保留** | ✅ |
| `MCNScheduler` | 定时任务 | **增强** — 触发Skill而非调用Python函数 | 🔄 |
| `DataQualityValidator` | 数据验证 | **保留** — JSON入库前的检查 | ✅ |
| `ContentRiskScanner` | 广告法检查 | **保留** — 安全兜底 | ✅ |

---

## 二、Skill 定义

### 2.1 Skill 存放位置

```
~/.hermes/skills/mcn-hotspot-research/SKILL.md
~/.hermes/skills/mcn-platform-rules/SKILL.md
~/.hermes/skills/mcn-creator-analysis/SKILL.md
~/.hermes/skills/mcn-trend-research/SKILL.md
```

放在 Hermes skills 目录下，Hermes cron 和 Claude Code 都能发现和触发。

### 2.2 Skill 1：mcn-hotspot-research（热点采集+SOUL评分）

**触发**：
- Hermes cron：每日 08:00
- 手动：`/skill mcn-hotspot-research` 或 Claude Code 中直接调用

**输入**（可选）：
- `keywords`：手动指定搜索关键词
- `days`：搜索最近N天，默认7
- `sources`：指定来源（hermes_reports / websearch / both），默认 both

**处理**（LLM 执行）：
1. 如果 `sources` 含 hermes_reports，读取 `~/hermes_workspace/reports/hotspot/` 最近报告
2. 如果 `sources` 含 websearch，用 WebSearch 搜索各平台AI×超级个体赛道热点
3. 基于 SOUL 框架对每条热点进行5维度语义评分（不是关键词匹配，是语义理解）
4. 推荐切入角度和内容形式
5. 去重、排序

**输出**（写入 `data/skill_outputs/mcn-hotspot-research/{timestamp}.json`）：

```json
{
  "skill": "mcn-hotspot-research",
  "executed_at": "2026-05-17T08:00:00Z",
  "sources_used": ["hermes_reports", "websearch"],
  "total_collected": 45,
  "after_quality_filter": 38,
  "hotspots": [
    {
      "rank": 1,
      "title": "Anthropic发布Founder's Playbook：AI可能提高创业失败率",
      "platform": "douyin",
      "heat": "rising",
      "tags": ["AI", "超级个体", "创业"],
      "soul_scoring": {
        "total": 8.5,
        "finitude_alignment": {"direction": "direction3", "name": "协议层协作", "score": 8.0},
        "audience_match": {"primary": "Marcus", "label": "转型者(30-38岁)", "score": 9.0},
        "dialogue_feasibility": {"rupture": 8, "illuminate": 9, "rebuild": 8},
        "differentiation_potential": 8.5,
        "risk_assessment": 9.0
      },
      "recommended_angle": "AI在创业中'帮倒忙'——这恰好说明人的判断力不可替代",
      "content_form": "口播视频",
      "publish_window": "3天内"
    }
  ],
  "top_picks": [...5个]
}
```

### 2.3 Skill 2：mcn-platform-rules（平台规则扫描）

**触发**：
- Hermes cron：每周一 09:00
- 手动：`/skill mcn-platform-rules --platforms douyin,xiaohongshu`

**输入**：
- `platforms`：目标平台列表，默认全部

**处理**（LLM 执行）：
1. WebSearch 搜索各平台近30天规则/算法变动
2. 判断可信度（官方公告 > 行业解读 > 创作者反馈）
3. 分析对创作者的具体影响
4. 提取限制关键词
5. 判断平台整体收紧/放松趋势

**输出**（`data/skill_outputs/mcn-platform-rules/{timestamp}.json`）：

```json
{
  "skill": "mcn-platform-rules",
  "executed_at": "2026-05-17T09:00:00Z",
  "scan_period": "2026-04-17 ~ 2026-05-17",
  "platforms": {
    "douyin": {
      "overall_stance": "tightening",
      "changes": [
        {
          "type": "算法调整",
          "summary": "知识类内容推荐权重上调，短剧类限流",
          "source": "官方公告",
          "confidence": "confirmed",
          "impact_level": "high",
          "impact_detail": "知识口播类内容将获得更多推荐，利好本赛道",
          "action_required": "增加知识密度，减少娱乐化表达"
        }
      ],
      "restricted_keywords": ["最", "第一", "国家级", " guaranteed"],
      "promotions": [
        {"name": "知识创作激励计划", "deadline": "2026-06-30", "worth_participating": true}
      ]
    },
    "xiaohongshu": {...},
    "bilibili": {...}
  },
  "cross_platform_signals": "各平台整体在鼓励知识类内容，限制低质娱乐"
}
```

### 2.4 Skill 3：mcn-creator-analysis（对标创作者分析）

**触发**：
- Hermes cron：每月1日 10:00
- 手动：`/skill mcn-creator-analysis --niche "AI+超级个体"`

**输入**：
- `niche`：赛道关键词
- `platforms`：搜索平台
- `analysis_depth`：quick / standard / deep

**处理**（LLM 执行）：
1. WebSearch 搜索赛道内新晋+头部创作者
2. 分层：学习标杆层（头部） + 成长对标层（同量级）
3. 对Top 5进行深度拆解（人设/内容策略/增长路径/商业模式）
4. 构建对比矩阵（定位/受众/风格/变现）
5. 识别差异化机会和可迁移元素

**输出**（`data/skill_outputs/mcn-creator-analysis/{timestamp}.json`）：

```json
{
  "skill": "mcn-creator-analysis",
  "executed_at": "2026-05-17T10:00:00Z",
  "discovered": [
    {
      "account_name": "AI小明",
      "platform": "douyin",
      "followers": "50万",
      "tier": "学习标杆",
      "positioning": "AI工具教程博主，轻松幽默风格",
      "update_frequency": "日更",
      "top_content_example": "《10个AI工具提升效率》50万赞",
      "learnable_points": ["标题公式：数字+反常识", "每期一个可操作技巧"],
      "differentiation_from_me": "偏工具实操，缺少哲学视角"
    }
  ],
  "deep_analysis": [
    {
      "account_name": "AI小明",
      "persona": "幽默的技术翻译官",
      "content_strategy": "日更短教程+周更深度对比",
      "viral_formula": "反常识开头(5s)→工具演示(30s)→效果对比(15s)→CTA",
      "monetization": "课程+工具分销",
      "growth_path": "从单一工具测评→系统性方法论"
    }
  ],
  "comparison_matrix": [
    {"dimension": "定位", "them": "工具推荐者", "me": "思维引导者", "gap": "我提供why+how而不只是what"},
    {"dimension": "受众", "them": "想省时间的打工人", "me": "想转型的觉醒者", "gap": "我的受众付费意愿更强"}
  ],
  "differentiation_opportunities": [
    "工具+哲学交叉话题尚未被覆盖",
    "前PM视角拆解AI产品策略是独特优势",
    "可用三阶对话法做深度内容（对标都是浅层教程）"
  ],
  "migratable_elements": [
    {"type": "hook_formula", "content": "数字+反常识：'7个工具你可能用错了5个'"},
    {"type": "structure", "content": "场景痛点→工具方案→效果对比→行动建议"}
  ]
}
```

### 2.5 Skill 4：mcn-trend-research（赛道趋势预判）

**触发**：
- Hermes cron：每月1日 11:00
- 手动：`/skill mcn-trend-research`

**输入**：
- `horizon`：预测周期，默认 3-6个月

**处理**（LLM 执行）：
1. WebSearch 搜索赛道宏观趋势
2. 分析各子赛道增长/衰退信号
3. 识别受众需求迁移方向
4. 研判内容形式演变
5. 竞争格局判断
6. 给出内容配比建议和评分权重调整

**输出**（`data/skill_outputs/mcn-trend-research/{timestamp}.json`）：

```json
{
  "skill": "mcn-trend-research",
  "executed_at": "2026-05-17T11:00:00Z",
  "horizon": "2026 Q3-Q4",
  "sub_track_weights": {
    "AI工具教程": {"weight": 0.6, "trend": "stable", "note": "大路货饱和，细分工具教程有机会"},
    "超级个体方法论": {"weight": 0.9, "trend": "rising", "note": "平台扶持，受众需求强烈"},
    "AI哲学思考": {"weight": 0.85, "trend": "rising", "note": "赛道蓝海，差异化空间大"},
    "AI副业赚钱": {"weight": 0.3, "trend": "declining", "note": "同质化严重，信任透支"}
  },
  "audience_shifts": {
    "anxiety_to_rational": "受众从AI焦虑转向理性工具需求",
    "meaning_seeking_rising": "职场转型者更关注意义而非技巧",
    "emerging_pain_points": ["AI工具选择困难", "一人企业法律/财务盲区", "超级个体孤独感"]
  },
  "content_form_trends": {
    "douyin": {"short_video": 0.7, "mid_video": 0.5, "text": 0.3},
    "xiaohongshu": {"short_video": 0.6, "text": 0.7, "live": 0.4},
    "bilibili": {"long_video": 0.8, "mid_video": 0.6}
  },
  "monthly_strategy": {
    "content_mix": {
      "methodology": 0.30,
      "philosophy_insight": 0.25,
      "tool_tutorial": 0.25,
      "trend_commentary": 0.20
    },
    "scoring_weight_adjustments": {
      "finitude_alignment": 0.30,
      "audience_match": 0.25,
      "dialogue_feasibility": 0.20,
      "differentiation": 0.20,
      "risk": 0.05
    },
    "key_recommendations": [
      "增加AI哲学类内容比例至25%",
      "减少纯工具教程，改为'工具+思维'融合形式",
      "B站布局中长视频（8-15分钟深度内容）",
      "小红书增加图文笔记频率"
    ]
  }
}
```

---

## 三、管道层设计

### 3.1 SkillOutputReader（核心新增模块）

```python
# src/pipeline/skill_output_reader.py

class SkillOutputReader:
    """
    读取 Skill 产出的 JSON，验证后入库。
    
    工作流：
    1. 监听 data/skill_outputs/ 目录
    2. 发现新文件 → 读取 JSON
    3. DataQualityValidator 验证
    4. 按 skill 类型分发给对应的入库函数
    5. 标记为已处理
    """
    
    def watch_and_process(self):
        """持续监听新输出文件（daemon模式）"""
    
    def process_file(self, filepath: Path):
        """处理单个输出文件"""
        skill_name = self._detect_skill(filepath)
        data = json.loads(filepath.read_text())
        
        if skill_name == "mcn-hotspot-research":
            self._ingest_hotspots(data)
        elif skill_name == "mcn-platform-rules":
            self._ingest_rules(data)
        elif skill_name == "mcn-creator-analysis":
            self._ingest_creators(data)
        elif skill_name == "mcn-trend-research":
            self._ingest_trends(data)
```

### 3.2 MCNScheduler（增强版）

```python
class MCNScheduler:
    """
    定时触发 Skill（而非 Python 函数）
    
    通过 Hermes cron 或直接调用 Claude Code skill 命令
    """
    
    def trigger_skill(self, skill_name: str):
        """触发一个 Skill 执行，等待其产出 JSON"""
        # 方式1：通过 Hermes API 触发
        # 方式2：通过 Claude Code CLI 触发
```

---

## 四、数据流全景

```
┌─ Hermes cron ──────────────────────────────────────────┐
│                                                        │
│  每日 08:00 → mcn-hotspot-research                     │
│  周一 09:00 → mcn-platform-rules                       │
│  每月1日 10:00 → mcn-creator-analysis                  │
│  每月1日 11:00 → mcn-trend-research                    │
│                                                        │
│  触发方式：Hermes cron 或 Claude Code /skill 命令      │
└────────────────────────────────────────────────────────┘
                          ↓
┌─ Skill 执行 ───────────────────────────────────────────┐
│                                                        │
│  LLM + WebSearch 完成采集、分析、评分                  │
│                                                        │
│  产出 JSON 写入：                                      │
│  ~/mcn-ai-replacement/data/skill_outputs/             │
│    mcn-hotspot-research/2026-05-17T080000.json         │
│    mcn-platform-rules/2026-05-12T090000.json           │
│    mcn-creator-analysis/2026-05-01T100000.json         │
│    mcn-trend-research/2026-05-01T110000.json           │
└────────────────────────────────────────────────────────┘
                          ↓
┌─ Python 管道层 ────────────────────────────────────────┐
│                                                        │
│  SkillOutputReader 发现新 JSON                         │
│    ↓                                                   │
│  DataQualityValidator 验证                             │
│    ↓                                                   │
│  分发入库：                                            │
│    ├── 热点 → SQLite + FeishuBase.hotspots             │
│    ├── 规则 → data/platform_rules.json                 │
│    ├── 创作者 → SQLite + FeishuBase.creators           │
│    └── 趋势 → data/trend_data.json                     │
│    ↓                                                   │
│  TwoLayerManager.sync_to_github()                      │
│    ↓                                                   │
│  标记 JSON 为 .processed                               │
└────────────────────────────────────────────────────────┘
```

---

## 五、Python 模块重组

### 5.1 需要删除

| 文件 | 原因 |
|------|------|
| `src/adapters/hermes_hotspot_adapter.py` | Skill直接处理，不需解析Markdown |
| `src/analyzers/rules_monitor.py` | Skill直接产出规则JSON |
| `src/analyzers/creator_pipeline.py` | Skill直接产出创作者JSON |
| `src/analyzers/trend_analyzer.py` | Skill直接产出趋势JSON |
| `src/skills/soul_hot_topic_matcher.py` | LLM语义评分替代关键词评分 |
| `src/skills/soul_script_writer.py` | Skill内完成脚本生成 |

### 5.2 需要简化

| 文件 | 变动 |
|------|------|
| `src/adapters/hotspot_collector.py` | 简化为读取Skill JSON |
| `src/workflows/hot_topic_workflow.py` | 简化为触发Skill+等待结果 |
| `src/skills/__init__.py` | 移除已删除的导出 |

### 5.3 保留不变

| 文件 | 说明 |
|------|------|
| `src/integrations/feishu_base_adapter.py` | 纯API调用 |
| `src/integrations/feishu_wiki_kb.py` | Wiki管理 |
| `src/integrations/feishu_im_notifier.py` | 消息通知 |
| `src/integrations/hermes_task_bridge.py` | 调度触发接口 |
| `src/knowledge/two_layer_manager.py` | 本地+GitHub |
| `src/knowledge/backup_manager.py` | 备份恢复 |
| `src/scheduler/mcn_scheduler.py` | 定时调度 |
| `src/utils/data_quality_validator.py` | 数据验证 |
| `src/skills/content_risk_scanner.py` | 安全兜底 |

### 5.4 新增

| 文件 | 说明 |
|------|------|
| `src/pipeline/__init__.py` | 管道层入口 |
| `src/pipeline/skill_output_reader.py` | JSON读取→入库 |

---

## 六、决策确认

| 决策点 | 结论 | 理由 |
|--------|------|------|
| Skill存放位置 | `~/.hermes/skills/mcn-*/SKILL.md` | Hermes可发现，Claude Code可调用 |
| Skill触发方式 | Hermes cron + `/skill` 手动命令 | 用户指定 |
| 产出方式 | JSON文件 | 用户指定 |
| Python角色 | 只做管道（读JSON→验证→入库→同步） | 不做分析 |
| 评分逻辑 | LLM语义评分 | 比关键词匹配更准确 |
| 报告解析 | 不需要 — Skill直接产出结构化JSON | 消除Markdown解析 |

---

## 七、实施计划

### Phase 1：Skill 定义（2-3天）

- [ ] 编写4个 SKILL.md（mcn-hotspot-research / platform-rules / creator-analysis / trend-research）
- [ ] 测试每个 Skill 的手动执行
- [ ] 验证 JSON 产出格式

### Phase 2：管道层（2-3天）

- [ ] 实现 SkillOutputReader
- [ ] 实现 JSON→SQLite 入库
- [ ] 实现 JSON→飞书Base 同步
- [ ] 测试完整数据流

### Phase 3：Python 瘦身（2-3天）

- [ ] 删除已被 Skill 替代的模块
- [ ] 简化 Collector/Workflow
- [ ] 更新 CLI 命令
- [ ] 全量测试确保不破坏现有功能

### Phase 4：定时调度（1-2天）

- [ ] 注册到 Hermes cron
- [ ] 测试自动化运行
- [ ] 文档更新

---

## 八、待讨论事项

1. **Skill 的 SOUL 画像引用**：Skill 在执行评分时需要加载 SOUL 画像。是否在 SKILL.md 中内嵌引用路径（`~/.hermes/skills/knowledge/soul/SKILL.md`）？

2. **WebSearch 的覆盖率**：Claude Code 的 WebSearch 能否覆盖国内平台（抖音、小红书）的实时热点？如果覆盖不到，是否回退到读取 Hermes 报告？

3. **四份旧 Manus 提示词**：`Downloads/` 下的4个md文件是给 Manus 的提示词。新架构下它们转化为 SKILL.md 后，旧文件是归档还是删除？

4. **脚本生成的定位**：`mcn-hotspot-research` Skill 做选题推荐，那脚本生成（三阶对话法+SOUL人设）是否也作为一个独立 Skill `mcn-script-writer`？还是合并在热点Skill内？

DOCEND
