# 系统架构与功能模块完整说明

> 内容创作者AI辅助系统的技术架构、功能模块、Agent分工和实施规划。

---

## 一、系统定位

**核心命题**：用AI系统替代MCN机构的标准化中台能力，让独立/小团队创作者专注不可替代的核心创意与个人表达。

### 1.1 能力覆盖

本系统聚焦MCN支持体系中 **AI可高度替代** 的9个核心模块：

| 级别 | 模块代号 | 模块名称 | AI替代度 |
|------|---------|---------|---------|
| 🟢 全自动化 | M1 | 全平台热点监测 | 95% |
| 🟢 全自动化 | M4 | 账号数据分析与诊断 | 80% |
| 🟢 全自动化 | M9 | 内容合规审核(初筛) | 90% |
| 🔵 高度辅助 | M2 | 趋势预判与赛道分析 | 75% |
| 🔵 高度辅助 | M3 | 平台规则与算法解读 | 65% |
| 🔵 高度辅助 | M7 | 选题策划与脚本共创 | 80% |
| 🔵 高度辅助 | M10 | 数据驱动的内容迭代 | 70% |
| 🔵 高度辅助 | M6 | 粉丝运营与互动管理 | 60% |
| 🆕 新增 | M19 | 对标创作者发掘与深度分析 | 85% |

### 1.2 不可替代的能力（需人工/外部资源）

- 创作者的个人魅力与创意表达
- 商务人脉与品牌关系网络
- 平台一手政策信息（可通过深度信息挖掘部分弥补）
- 拍摄/录制/精细后期制作

---

## 二、三层架构

```
┌─────────────────────────────────────────────┐
│  🧠 智能层 (AI Brain)                        │
│  ┌──────────────┬──────────────┬───────────┐ │
│  │ Manus        │ Antigravity  │ 对话系统   │ │
│  │ WideSearch   │ Skills引擎   │ 即时交互   │ │
│  │ DeepResearch │ 数据分析     │ 脚本共创   │ │
│  │ ─────────    │ 报告生成     │ 策略咨询   │ │
│  │ 广度搜索     │ 深度分析     │ 日常对话   │ │
│  └──────────────┴──────────────┴───────────┘ │
├─────────────────────────────────────────────┤
│  🔧 能力层 (Skills & Knowledge)               │
│  ┌──────────────────┬────────────────────┐   │
│  │ Skills模块池      │ 知识库              │   │
│  │ · hot-topic-matcher│ · Ima(非结构化)    │   │
│  │ · script-writer    │   报告/灵感/人设   │   │
│  │ · creator-profiler │ · 飞书多维表格     │   │
│  │ · title-optimizer  │   (结构化)         │   │
│  │ · content-risk-    │   热点/对标/数据   │   │
│  │   scanner 等       │                    │   │
│  └──────────────────┴────────────────────┘   │
├─────────────────────────────────────────────┤
│  📡 数据层 (Data Sources)                     │
│  ┌──────────────┬───────────┬─────────────┐  │
│  │ 公开数据     │ 后台数据   │ 平台API     │  │
│  │ WideSearch   │ 创作者导出 │ 星图/蒲公英 │  │
│  │ 采集         │ CSV/截图   │ 花火        │  │
│  └──────────────┴───────────┴─────────────┘  │
└─────────────────────────────────────────────┘
```

### 2.1 智能层分工

| 引擎 | 职责 | 特点 |
|------|------|------|
| **Manus** | 大规模并行搜索、信息采集 | WideSearch并行部署100+Agent，适合热点扫描/对标发掘/趋势研究 |
| **Antigravity** | 数据分析、创作辅助、Skill编排 | 本地运行，深度处理已有数据，适合脚本生成/合规审核/选题推荐 |
| **对话系统** | 创作者日常交互 | 即时问答，脚本打磨，策略咨询 |

### 2.2 方案演进：A+C结合

```
Phase MVP（当前）：
  Manus Pro 手动操作（4套提示词）
  → 结果人工审核
  → 手动导入 Ima/飞书
  → Antigravity Skills处理

Phase 2（验证后）：
  提取WideSearch核心能力本地化
  ├── 编排器Agent → LangGraph Orchestrator
  ├── 并行工作Agent → Firecrawl Worker Pool
  ├── 信息提取Skill → Antigravity Skill
  └── 结果合成 → 对话系统
```

---

## 三、9大功能模块详解

### M1：全平台热点监测

**MCN等价能力**：数据中台实时热点监测，分级推送

**AI实现方式**：
- 数据采集：Manus WideSearch并行扫描抖音/微博/小红书/B站/知乎
- 分析处理：`hot-topic-matcher` Skill 进行赛道适配+切入角度推荐
- 输出形式：结构化热点清单 → 飞书多维表格

**触发频率**：每周1-2次（MVP人工触发），未来可自动化

**相关文件**：
- 提示词：[widesearch-hot-topics.md](./prompts/widesearch-hot-topics.md)
- Skill：[hot-topic-matcher](./skills/hot-topic-matcher/SKILL-SPEC.md)
- 数据存储：[hot-topics-schema.md](./knowledge-base/schemas/hot-topics-schema.md)

---

### M19：对标创作者发掘与深度分析 🆕

**MCN等价能力**：竞品分析团队持续追踪

**AI实现方式**：
- 发掘：Manus WideSearch按赛道/关键词并行搜索多平台头部创作者
- 画像建档：`creator-profiler` Skill 结构化录入
- 爆款拆解：`viral-content-analyzer` Skill 分析内容结构
- 差异化：`gap-analyzer`（Phase 2）识别空白机会

**全链路应用**：
- 爆款选题 → 反哺M7选题
- 内容结构模板 → 反哺script-writer
- 赛道趋势信号 → 反哺M2趋势预判
- 标题/封面benchmark → 反哺title-optimizer

**相关文件**：
- 提示词：[widesearch-creator-analysis.md](./prompts/widesearch-creator-analysis.md)
- Skill：[creator-profiler](./skills/creator-profiler/SKILL-SPEC.md) / [viral-content-analyzer](./skills/viral-content-analyzer/SKILL-SPEC.md)
- 数据存储：[creator-profiles-schema.md](./knowledge-base/schemas/creator-profiles-schema.md)

---

### M4：账号数据分析与诊断

**数据来源**：
- 公开数据（WideSearch）：粉丝数/视频列表/点赞评论数
- 后台数据（手动导出）：完播率/流量来源/粉丝画像
- 平台API（申请后）：自动拉取核心指标

**相关文件**：
- 数据存储：[content-review-schema.md](./knowledge-base/schemas/content-review-schema.md)

---

### M9：内容合规审核

**纯Skill实现，无外部依赖**：
- `content-risk-scanner` Skill：广告法禁用词+平台社区规范+版权检查

**相关文件**：
- Skill：[content-risk-scanner](./skills/content-risk-scanner/SKILL-SPEC.md)

---

### M2：趋势预判与赛道分析

**AI实现方式**：Manus DeepResearch深度研究 → 趋势报告

**相关文件**：
- 提示词：[deepresearch-trend-report.md](./prompts/deepresearch-trend-report.md)
- 模板：[trend-report-template.md](./knowledge-base/templates/trend-report-template.md)

---

### M3：平台规则与算法解读

**AI实现方式**：Manus WideSearch监控 + `algorithm-decoder` Skill（Phase 2）

**相关文件**：
- 提示词：[widesearch-platform-rules.md](./prompts/widesearch-platform-rules.md)

---

### M7：选题策划与脚本共创

**核心Skills链**：
1. `hot-topic-matcher`（M1联动）→ 热点适配
2. `viral-content-analyzer`（M19联动）→ 爆款模式参考
3. `script-writer` → 脚本生成
4. `title-optimizer` → 标题优化

**相关文件**：
- Skill：[script-writer](./skills/script-writer/SKILL-SPEC.md) / [title-optimizer](./skills/title-optimizer/SKILL-SPEC.md)

---

### M10：数据驱动的内容迭代

**功能**：
- 单条内容复盘（后台数据+公开评论）
- 评论区情绪分析
- 迭代建议生成

**相关文件**：
- 数据存储：[content-review-schema.md](./knowledge-base/schemas/content-review-schema.md)

---

### M6：粉丝运营与互动管理

**功能**：
- 智能回复建议（基于人设的对话提示词）
- 互动策略建议
- 社群话题策划

---

## 四、知识库架构

### 存储分层

| 数据类型 | 存储位置 | 原因 |
|---------|---------|------|
| 热点清单 | 飞书多维表格 | 结构化，需筛选排序 |
| 对标创作者档案 | 飞书多维表格 | 结构化，持续更新 |
| 内容数据复盘 | 飞书多维表格 | 数字型数据，需图表 |
| 趋势研究报告 | Ima知识库 | 长文档，AI问答检索 |
| 脚本/选题草稿 | Ima知识库 | 写作场景，AI辅助 |
| 创作者人设档案 | Ima知识库 | 长文本，AI理解校验 |

**详细方案**：[KB-DESIGN.md](./knowledge-base/KB-DESIGN.md)

---

## 五、创作者平台权限

星图/蒲公英/花火提供的 **完播率、流量来源、粉丝画像** 等独占性数据是系统从"够用"到"强大"的关键。

**详细指南**：[PLATFORM-ACCESS-GUIDE.md](./platform-access/PLATFORM-ACCESS-GUIDE.md)

---

## 六、Antigravity本地化定位

| 能力 | Antigravity可行性 | 说明 |
|------|-----------------|------|
| Skill开发 | ✅ 完全可行 | 已有成熟框架 |
| 对话交互 | ✅ 完全可行 | 核心能力 |
| 文件读写 | ✅ 完全可行 | 操作本地文件 |
| 代码执行 | ✅ 完全可行 | Python/JS脚本 |
| 网页搜索 | ⚠️ 有限 | 单次可以，无法并行 |
| 定时任务 | ❌ 需外部调度 | Windows任务计划 |
| 并行Agent | ❌ 不支持 | 需Manus |

**结论**：Antigravity做深度分析+创作辅助，Manus做广度搜索+数据采集。

---

## 七、实施路线图

### Phase MVP（6周）

| 周次 | 重点 | 产出 |
|------|------|------|
| W1-2 | Manus手动采集+人工验证 | 首批热点/对标/趋势数据 |
| W3-4 | Antigravity Skills开发 | 核心Skills可用 |
| W5-6 | 全流程跑通 | 首条完整流程内容 |

### Phase 2（1-2月）
- 本地化WideSearch核心能力
- 飞书/Ima API自动化写入
- 申请平台权限

### Phase 3（2-3月）
- 全链路智能化
- Dashboard可视化
- 长期IP辅助
