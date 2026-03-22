# 知识库方案设计：Ima + 飞书多维表格

> 非结构化知识 → Ima | 结构化数据 → 飞书多维表格

---

## 一、存储分层

| 数据类型 | 存储位置 | 原因 | 更新频率 |
|---------|---------|------|---------|
| 热点清单 | 飞书多维表格 | 需筛选/排序/状态跟踪 | 每周1-2次 |
| 对标创作者档案 | 飞书多维表格 | 结构化字段，持续更新 | 每月+每周追踪 |
| 内容数据复盘 | 飞书多维表格 | 数字型，需图表可视化 | 每条内容发布后 |
| 平台规则变动 | 飞书多维表格 | 按平台/时间/影响度索引 | 每2周 |
| 趋势研究报告 | Ima知识库 | 长文档，AI检索问答 | 每月 |
| 爆款拆解深度分析 | Ima知识库 | 长文分析，AI学习 | 不定期 |
| 脚本/选题草稿 | Ima知识库 | 写作场景，AI辅助修改 | 不定期 |
| 创作者人设档案 | Ima知识库 | 长文本，AI理解校验 | 低频 |

---

## 二、飞书多维表格设计

### 需要创建的表格

1. **热点跟踪表** → [hot-topics-schema](./schemas/hot-topics-schema.md)
2. **对标创作者库** → [creator-profiles-schema](./schemas/creator-profiles-schema.md)
3. **内容数据表** → [content-review-schema](./schemas/content-review-schema.md)

### 飞书API自动化路径（Phase 2+）

```
Phase MVP：手动复制粘贴Manus结果到飞书表格
Phase 2：Python脚本调用飞书开放API写入
Phase 3：OpenClaw飞书集成插件自动化
```

飞书开放平台关键文档：
- 多维表格API：`https://open.feishu.cn/document/server-docs/docs/bitable-v1`
- 2500+开放接口文档：`https://open.feishu.cn`

---

## 三、Ima知识库设计

### 知识库分区

| 知识库名称 | 内容 | 标签体系 |
|-----------|------|---------|
| 📊 趋势研究 | 月度/季度趋势报告 | `年月`、`赛道`、`置信度` |
| 🔥 爆款拆解 | 对标创作者爆款分析 | `创作者名`、`平台`、`内容类型` |
| ✍️ 创作素材 | 脚本草稿、选题灵感 | `状态`、`平台`、`选题方向` |
| 👤 人设档案 | 创作者个人定位文档 | `版本`、`更新日期` |
| 📏 平台规则 | 算法解读、规则变动详细分析 | `平台`、`日期`、`影响度` |

### 文档模板

- 趋势报告模板 → [trend-report-template](./templates/trend-report-template.md)
- 人设档案模板 → [persona-profile-template](./templates/persona-profile-template.md)

### Ima API自动化路径（Phase 2+）

```
Phase MVP：手动导入报告到Ima
Phase 2：Ima"技能"API（2026.3已开放）自动写入笔记
```

Ima技能API文档：`https://ima.qq.com/developer`（2026.3开放）

---

## 四、日常工作流中的知识库使用

### 选题时
1. 打开飞书热点跟踪表 → 筛选"高适配度"热点
2. 在Ima中问："我的赛道最近有什么被忽略的好选题？"
3. 交叉对比对标创作者库中的"已覆盖话题"

### 写脚本时
1. 在Ima中搜索爆款拆解 → 找到类似话题的结构参考
2. 调用script-writer Skill → 生成初稿
3. 在Ima中对比人设档案 → 校验一致性

### 复盘时
1. 内容数据录入飞书表格
2. 对比对标创作者同类内容数据
3. 在Ima中记录优化心得
