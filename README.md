# MCN AI Replacement System

一个基于AI的内容创作辅助系统，旨在用AI技术替代MCN机构70-80%的中台支持能力。

## 🎯 系统功能

- ✅ **自动化热点采集** - 每周自动采集全平台热点话题
- ✅ **智能选题推荐** - 基于创作者人设自动评分排序
- ✅ **脚本快速生成** - 输入选题自动生成结构化脚本
- ✅ **合规自动审核** - 发布前自动检查风险点
- ✅ **知识自动沉淀** - 数据自动存储到本地和飞书
- ✅ **定时自动执行** - 无需人工干预，系统自动运行

## 📁 项目结构

```
mcn-ai-replacement/
├── src/                    # 核心代码
│   ├── adapters/          # 🆕 数据接入层（Hermes + 手动导入）
│   ├── skills/            # 8个核心Skills（含SOUL驱动）
│   ├── knowledge/         # 🆕 两层知识库（本地 + GitHub）
│   ├── scheduler/         # 🆕 定时任务调度
│   ├── integrations/      # 🆕 Hermes集成（任务桥接 + API）
│   ├── workflows/         # 工作流编排
│   ├── core/              # 基础设施
│   └── utils/             # 工具函数（含质量验证）
├── config/                # 配置文件
├── data/                  # 本地数据
├── knowledge/             # GitHub知识库同步
├── backups/               # 🆕 自动备份
├── scripts/               # CLI脚本（14个命令）
├── tests/                 # 测试（69个）
└── docs/                  # 📚 完整文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ~/mcn-ai-replacement
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制环境变量模板
cp config/.env.example config/.env

# 编辑配置文件（可选）
# vim config/.env
```

### 3. 初始化数据库

```bash
python scripts/init_database.py
```

### 4. 配置创作者人设

编辑 `config/personal_profile.json` 文件，设置你的创作者定位、风格偏好等。

### 5. 运行工作流（Phase 2完成后可用）

```bash
# 热点采集
python scripts/run_workflow.py hot-topic

# 对标分析
python scripts/run_workflow.py creator-analysis

# 内容创作
python scripts/run_workflow.py create-content --topic "AI焦虑"
```

## 📊 数据模型

### 热点话题表 (hot_topics)
- 热点标题、来源平台、热度等级
- 5维度评分（赛道关联、人设适配、时效性、差异化、风险）
- 推荐切入角度、内容形式、发布窗口期

### 对标创作者表 (creators)
- 账号信息、粉丝数、定位
- 风格关键词、内容类型分布
- 爆款内容、可学习点、差异化机会

### 内容数据表 (contents)
- 公开数据（播放、点赞、评论、转发）
- 后台数据（完播率、流量来源）
- 分析字段（互动率、转粉率、内容评级）

## 🔧 配置说明

### 关键词库 (config/keywords.yaml)

定义了5大类关键词：
- `ai_keywords` - AI相关关键词
- `personal_brand_keywords` - 个人品牌关键词
- `job_keywords` - 职场相关关键词
- `philosophy_keywords` - 认知哲学关键词
- `productivity_keywords` - 效率工具关键词

### 平台配置 (config/platforms.yaml)

定义了5大平台的配置：
- 抖音、小红书、B站、微博、知乎
- 每个平台的内容类型、最佳时长、算法偏好、风险因素

### 创作者人设 (config/personal_profile.json)

定义了创作者的：
- 基本信息（定位、目标受众、核心价值）
- 内容风格（语气、人格类型、偏好用语）
- 内容偏好（信息密度、对话感、挑战性）
- 差异化优势

## 📈 开发进度

### Phase 1: 基础设施搭建 ✅ 完成
- [x] 项目结构创建
- [x] 配置系统实现
- [x] 数据模型定义
- [x] WebSearch封装
- [x] 日志系统
- [x] 数据库初始化测试

### Phase 2: 核心Skills实现 ✅ 完成
- [x] hot_topic_matcher - 热点适配评分
- [x] script_writer - 脚本生成
- [x] content_risk_scanner - 合规审核
- [x] creator_profiler - 对标创作者建档
- [x] viral_content_analyzer - 爆款拆解
- [x] title_optimizer - 标题优化

### Phase 3: 工作流编排 ✅ 完成
- [x] WorkflowOrchestrator实现
- [x] 热点采集工作流
- [x] 对标分析工作流
- [x] 内容创作工作流
- [x] CLI命令行接口

### Phase 4: 知识库集成 ✅ 完成
- [x] 飞书API客户端
- [x] 本地SQLite存储
- [x] Markdown知识库
- [x] 数据同步机制

### Phase 5: 定时任务 ✅ 完成
- [x] 每周一热点采集 (10:00)
- [x] 每周三对标追踪 (14:00)

### Phase 6: 测试与文档 ✅ 完成
- [x] 16个测试全部通过 (11单元 + 5集成)
- [x] API文档
- [x] 部署指南
- [x] 项目文档完睾

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可

MIT License

## 📞 联系

如有问题，请提交Issue。
