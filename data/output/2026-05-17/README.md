# MCN AI Replacement 模块执行输出

> 执行日期：2026-05-17
> 执行顺序：按 M1 → M7 → M9 → M19 → M3 依次执行

## 输出文件索引

| 序号 | 模块 | 文件 | 说明 |
|------|------|------|------|
| 01 | M1 热点监测 | `01_hot_topics_with_soul_ranking.md` | Hermes报告采集76个热点，SOUL框架评分排序Top 15 |
| 02 | M7 脚本共创 | `02_soul_script.md` | SOUL驱动生成短视频脚本（三阶对话法+四视角） |
| 03 | M7+M9 内容流水线 | `03_content_creation_pipeline.md` | 脚本生成→标题优化→风险审核 完整流水线 |
| 04 | M19 对标分析 | `04_creator_analysis.md` | 3位对标创作者画像、爆款拆解、差异化策略 |
| 05 | M3 平台规则 | `05_platform_rules_status.md` | 5大平台政策状态、内容安全提示 |

## 核心发现

1. **热点方面**：76个热点中，"AI工具+个体创业"方向与SOUL画像匹配度最高（协议层协作方向）
2. **脚本方面**：生成脚本命中3个高风险点（绝对化用语），需修改后发布
3. **对标方面**：发现了「AI工具×认知框架×产品思维」三位一体的差异化空白
4. **平台方面**：五大平台整体政策收紧，内容合规审核必要性高

## 数据来源

- 热点数据：Hermes 日报报告 `~/hermes_workspace/reports/hotspot/`（最近7天）
- 创作者人设：`config/personal_profile.json`
- SOUL画像：`~/.hermes/skills/knowledge/soul/SKILL.md`
