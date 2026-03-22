# 内容创作者AI辅助系统 (Creator AI Assistant)

> 基于MCN机构全方位支持体系的AI化重构，面向独立/小团队内容创作者的高效、高质量、高自动化辅助系统。

## 🏗️ 系统定位

**让独立创作者拥有MCN中台70-80%的能力，专注不可替代的核心创意与个人表达。**

- **Manus做广度**：大规模并行搜索、信息采集（WideSearch/DeepResearch）
- **Antigravity做深度**：数据分析、创作辅助、Skill编排
- **Ima/飞书做存储**：知识沉淀、结构化管理、长期积累

## 📁 目录结构

```
Mcn Ai Replacement/
├── README.md                          ← 本文件，项目总览
├── SYSTEM-ARCHITECTURE.md             ← 系统架构与功能模块完整说明
├── INDEX.md                           ← 文档索引（渐进式披露）
│
├── prompts/                           ← Manus手动操作提示词
│   ├── widesearch-hot-topics.md       ← 全平台热点采集
│   ├── widesearch-creator-analysis.md ← 对标创作者发掘与分析
│   ├── deepresearch-trend-report.md   ← 赛道趋势深度研究
│   └── widesearch-platform-rules.md   ← 平台规则变动监测
│
├── skills/                            ← Antigravity Skills设计
│   ├── hot-topic-matcher/             ← 热点适配与推荐
│   │   └── SKILL-SPEC.md
│   ├── script-writer/                 ← 脚本生成
│   │   └── SKILL-SPEC.md
│   ├── content-risk-scanner/          ← 内容合规审核
│   │   └── SKILL-SPEC.md
│   ├── creator-profiler/              ← 对标创作者画像建档
│   │   └── SKILL-SPEC.md
│   ├── viral-content-analyzer/        ← 爆款内容拆解
│   │   └── SKILL-SPEC.md
│   └── title-optimizer/               ← 标题优化
│       └── SKILL-SPEC.md
│
├── knowledge-base/                    ← 知识库设计
│   ├── KB-DESIGN.md                   ← Ima+飞书知识库方案设计
│   ├── schemas/                       ← 飞书多维表格结构定义
│   │   ├── hot-topics-schema.md
│   │   ├── creator-profiles-schema.md
│   │   └── content-review-schema.md
│   └── templates/                     ← Ima知识库文档模板
│       ├── trend-report-template.md
│       └── persona-profile-template.md
│
├── platform-access/                   ← 创作者平台权限接入
│   └── PLATFORM-ACCESS-GUIDE.md       ← 平台权限申请与接入指南
│
└── playbook/                          ← MVP执行手册
    └── MVP-PLAYBOOK.md                ← 6周MVP验证步骤
```

## 🚀 快速开始

1. **阅读** [INDEX.md](./INDEX.md) 了解从哪里开始
2. **执行** `prompts/` 下的Manus提示词进行首次数据采集
3. **按照** [MVP-PLAYBOOK.md](./playbook/MVP-PLAYBOOK.md) 逐步验证

## 📋 当前阶段

**Phase MVP**：Manus手动操作 + 人工验证
