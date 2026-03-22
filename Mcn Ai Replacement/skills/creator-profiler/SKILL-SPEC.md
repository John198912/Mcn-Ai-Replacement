---
name: creator-profiler
description: 将Manus采集的对标创作者数据结构化建档，建立可持续追踪的创作者画像
---

# creator-profiler Skill

## 概述

将Manus WideSearch采集的原始对标创作者信息，结构化整理为标准画像格式，支持持续更新和追踪。

## 触发场景

- Manus对标分析结果产出后
- 创作者手动录入新的对标账号

## 输入

1. **Manus对标分析结果**：原始文本（Markdown/JSON）
2. **现有档案**（可选）：已建档的创作者列表

## 输出画像格式

```json
{
  "account_name": "@账号名",
  "platform": "抖音/小红书/B站",
  "followers": 100000,
  "tier": "成长对标/学习标杆",
  "positioning": "一句话定位",
  "style_keywords": ["关键词1", "关键词2"],
  "content_types": {"观点输出": 40, "教程": 30, "故事": 20, "测评": 10},
  "update_frequency": "日更/3天1更/周更",
  "monetization": ["广告", "课程", "咨询"],
  "top_content": [
    {"title": "...", "likes": 5000, "comments": 200, "date": "2026-03-15"}
  ],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "gap_opportunities": ["我可以差异化的点"],
  "last_updated": "2026-03-23",
  "tracking_notes": "追踪备注"
}
```

## 依赖

- Manus对标分析提示词产出
- 飞书多维表格Schema：[creator-profiles-schema](../../knowledge-base/schemas/creator-profiles-schema.md)

## 开发优先级

**P0** — Phase 1

## 实现状态

- [ ] Schema确认
- [ ] Skill设计完成
- [ ] 测试验证
