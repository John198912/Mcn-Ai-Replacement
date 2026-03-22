# MVP Playbook：6周验证手册

> 每周清晰的任务清单。从Manus手动操作开始，逐步搭建并验证系统。

---

## Week 1：首次数据采集

### 目标
用Manus执行首次WideSearch，验证提示词效果

### 任务清单

- [ ] **Day 1-2：热点采集**
  - 打开Manus Pro
  - 复制 [widesearch-hot-topics.md](../prompts/widesearch-hot-topics.md) 提示词执行
  - 审核结果：标注每条热点的有效性（✅有效 / ❌无效 / ⚠️需调整）
  - 记录提示词优化建议

- [ ] **Day 3-4：对标创作者发掘**
  - 复制 [widesearch-creator-analysis.md](../prompts/widesearch-creator-analysis.md) 提示词A执行
  - 审核结果：每个发掘的创作者是否确实有价值
  - 选出Top5，确认深度分析质量

- [ ] **Day 5：知识库初始化**
  - 在飞书创建3张多维表格（按Schema）：
    - [热点跟踪表](../knowledge-base/schemas/hot-topics-schema.md)
    - [对标创作者库](../knowledge-base/schemas/creator-profiles-schema.md)
    - [内容数据表](../knowledge-base/schemas/content-review-schema.md)
  - 将审核通过的热点录入飞书
  - 将对标创作者档案录入飞书

- [ ] **Day 5：Ima初始化**
  - 创建Ima知识库分区（趋势研究/爆款拆解/创作素材/人设档案/平台规则）
  - 将对标分析的深度拆解导入Ima
  - 将 [人设档案模板](../knowledge-base/templates/persona-profile-template.md) 填充并导入

### 产出
- ✅ 首份热点清单（飞书表格）
- ✅ 对标创作者档案（飞书表格+Ima）
- ✅ 提示词优化记录

---

## Week 2：趋势研究 + 提示词迭代

### 目标
执行DeepResearch，优化提示词

### 任务清单

- [ ] **Day 1-2：趋势研究**
  - 复制 [deepresearch-trend-report.md](../prompts/deepresearch-trend-report.md) 提示词执行
  - 审核报告质量：趋势判断是否有实际价值
  - 将报告按 [模板](../knowledge-base/templates/trend-report-template.md) 整理后导入Ima

- [ ] **Day 3：规则扫描**
  - 复制 [widesearch-platform-rules.md](../prompts/widesearch-platform-rules.md) 提示词执行
  - 审核变动信息的准确性
  - 有效变动录入飞书

- [ ] **Day 4-5：提示词迭代V2**
  - 基于Week 1-2的执行反馈，优化4套提示词：
    - 哪些搜索路径效果好 → 强化
    - 哪些搜索路径效果差 → 调整关键词
    - 输出格式是否需要调整
    - 信息量是否合适
  - 用优化后的热点采集提示词再执行一次，对比效果

### 产出
- ✅ 首份趋势报告（Ima）
- ✅ 规则变动清单（飞书）
- ✅ V2版优化提示词

---

## Week 3：Antigravity Skills开发（第一批）

### 目标
开发P0级Skills，与Manus采集的数据对接

### 任务清单

- [ ] **Day 1-2：content-risk-scanner**
  - 在Antigravity中按 [SKILL-SPEC](../skills/content-risk-scanner/SKILL-SPEC.md) 开发
  - 构建广告法禁用词知识库
  - 用已有脚本文案做测试

- [ ] **Day 3-4：script-writer**
  - 在Antigravity中按 [SKILL-SPEC](../skills/script-writer/SKILL-SPEC.md) 开发
  - 确保读取personal.json中的风格参数
  - 选2-3个Week 1的热点选题做脚本生成测试

- [ ] **Day 5：hot-topic-matcher**
  - 在Antigravity中按 [SKILL-SPEC](../skills/hot-topic-matcher/SKILL-SPEC.md) 开发
  - 用Week 1/2的热点数据做适配度评分测试

### 产出
- ✅ 3个可用的Antigravity Skills
- ✅ 每个Skill的测试记录

---

## Week 4：Skills开发（第二批）+ 对标分析

### 目标
完成对标相关Skills，执行对标追踪

### 任务清单

- [ ] **Day 1-2：creator-profiler + viral-content-analyzer**
  - 开发对标创作者画像和爆款拆解Skills
  - 用Week 1的对标数据做测试

- [ ] **Day 3：title-optimizer**
  - 开发标题优化Skill
  - 用Week 3生成的脚本做标题测试

- [ ] **Day 4-5：对标创作者首次追踪**
  - 执行对标追踪提示词B
  - 更新飞书对标创作者库
  - 测试：用追踪发现的爆款调用viral-content-analyzer

### 产出
- ✅ 6个可用的Antigravity Skills
- ✅ 对标追踪流程验证

---

## Week 5：全流程跑通

### 目标
完整走一遍：采集→分析→选题→脚本→审核→发布

### 任务清单

- [ ] **Day 1：数据采集**
  - Manus热点采集（V2提示词）
  - 结果入飞书

- [ ] **Day 2：选题决策**
  - hot-topic-matcher评分排序
  - 结合对标数据，选定1个选题

- [ ] **Day 3：脚本创作**
  - script-writer生成初稿
  - 人工打磨优化
  - title-optimizer生成标题候选

- [ ] **Day 4：审核 & 制作**
  - content-risk-scanner合规审核
  - 拍摄/录制
  - 后期制作

- [ ] **Day 5：发布 & 记录**
  - 发布到目标平台
  - 在飞书内容数据表创建记录
  - 记录全流程耗时和痛点

### 产出
- ✅ 首条"全流程AI辅助"产出的内容
- ✅ 全流程耗时和效率数据
- ✅ 痛点记录

---

## Week 6：复盘 + Phase 2规划

### 目标
数据驱动复盘，决定Phase 2方向

### 任务清单

- [ ] **Day 1-2：数据复盘**
  - Week 5发布的内容数据收集（等3-5天数据稳定）
  - 后台数据手动导出填入飞书
  - 对比历史内容数据：AI辅助是否有提升

- [ ] **Day 3：系统复盘**
  - 评估各环节：
    - Manus提示词效果：哪套最有价值
    - Skills效果：哪个最有用，哪个需要改
    - 知识库流程：手动录入是否成为瓶颈
    - 整体效率：节省了多少时间

- [ ] **Day 4-5：Phase 2规划**
  - 基于复盘结果决定：
    - [ ] 是否推进WideSearch本地化
    - [ ] 是否投入飞书/Ima API自动化
    - [ ] 是否申请平台API权限
    - [ ] 哪些Skills需要优化/新增
  - 更新SYSTEM-ARCHITECTURE.md

### 产出
- ✅ MVP复盘报告
- ✅ Phase 2实施计划
- ✅ 系统架构更新

---

## 关键检查点

| 检查点 | 时间 | 判定标准 | 通过则 | 不通过则 |
|--------|------|---------|--------|---------|
| Manus提示词有效 | Week 2末 | ≥60%热点被标注有效 | 继续Phase | 优化提示词再试 |
| Skills可正常工作 | Week 4末 | 6个Skill通过测试 | 继续Phase | 排查修复 |
| 全流程跑通 | Week 5末 | 成功产出1条内容 | 进入复盘 | 定位卡点修复 |
| 效率有提升 | Week 6末 | 选题+脚本环节效率≥提升30% | 进入Phase 2 | 调整方案 |
