# MCN AI Replacement — 部署指南

---

## 环境要求

- Python 3.9+
- Git
- macOS / Linux

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/John198912/Mcn-Ai-Replacement.git
cd Mcn-Ai-Replacement
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 3. 配置环境

```bash
# 复制环境变量模板
cp config/.env.example config/.env

# 编辑配置（可选）
vim config/.env
```

### 4. 初始化数据库

```bash
python3 scripts/init_database.py
```

### 5. 验证安装

```bash
python3 -m pytest tests/ -q
```

---

## 配置说明

### config/.env

```bash
# Hermes工作空间（可选）
HERMES_WORKSPACE=~/hermes_workspace

# SOUL配置文件（可选，自动查找）
# SOUL_PROFILE_PATH=~/.hermes/skills/knowledge/soul/SKILL.md

# GitHub仓库
GITHUB_REPO=John198912/Mcn-Ai-Replacement

# 飞书Webhook（可选，用于任务通知）
# FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# API密钥（仅远程访问时需要）
# MCN_API_KEY=your-secret-key

# 日志
LOG_LEVEL=INFO
LOG_FILE=logs/mcn.log
```

---

## 启动方式

### 方式1：手动运行（开发/测试）

```bash
# 单次任务
python3 scripts/run_workflow.py soul-rank
python3 scripts/run_workflow.py soul-script -t "选题" -a "角度"

# API服务
python3 scripts/run_workflow.py start-api
```

### 方式2：定时任务调度器（前台运行）

```bash
python3 scripts/run_workflow.py start-scheduler
```

### 方式3：macOS launchd（开机自启）

```bash
# 1. 生成配置
python3 scripts/run_workflow.py generate-launchd > \
  ~/Library/LaunchAgents/com.mcn.scheduler.plist

# 2. 加载
launchctl load ~/Library/LaunchAgents/com.mcn.scheduler.plist

# 3. 验证
launchctl list | grep mcn

# 4. 查看日志
tail -f ~/mcn-ai-replacement/logs/scheduler.log
```

### 方式4：API服务 + launchd（开机自启）

```bash
# 创建API服务配置
cat > ~/Library/LaunchAgents/com.mcn.api.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mcn.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/USERNAME/mcn-ai-replacement/scripts/run_workflow.py</string>
        <string>start-api</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/USERNAME/mcn-ai-replacement</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.mcn.api.plist
```

---

## 目录结构

```
mcn-ai-replacement/
├── src/                    # 源代码
│   ├── adapters/          # 数据接入层
│   ├── skills/            # SOUL内容生成
│   ├── knowledge/         # 知识库管理
│   ├── scheduler/         # 定时任务
│   ├── integrations/      # Hermes集成
│   ├── workflows/         # 工作流编排
│   ├── core/              # 基础设施
│   └── utils/             # 工具函数
├── scripts/               # CLI脚本
├── config/                # 配置文件
├── data/                  # 本地数据
│   ├── database.db        # SQLite数据库
│   └── markdown/          # Markdown知识库
│       ├── hotspots/
│       ├── scripts/
│       └── creators/
├── backups/               # 备份目录
├── knowledge/             # GitHub知识库同步目录
├── logs/                  # 日志
├── tests/                 # 测试
└── docs/                  # 文档
```

---

## 健康检查

```bash
# 检查Python版本
python3 --version  # >= 3.9

# 检查依赖
pip3 list | grep -E "pydantic|sqlalchemy|click|schedule"

# 运行测试
python3 -m pytest tests/ -q

# 检查数据库
python3 -c "from src.core import init_database; init_database('sqlite:///data/database.db')"

# 检查SOUL配置
python3 -c "
from src.skills.soul_script_writer import SOULScriptWriter
w = SOULScriptWriter()
print(f'SOUL source: {w.soul_profile[\"source\"]}')"
```

---

## 常见部署问题

### Q: 找不到 schedule 模块
```bash
pip3 install schedule
```

### Q: 数据库初始化失败
```bash
rm -f data/database.db
python3 scripts/init_database.py
```

### Q: launchd 加载失败
```bash
# 检查语法
plutil -lint ~/Library/LaunchAgents/com.mcn.scheduler.plist

# 检查路径
ls -la ~/mcn-ai-replacement/scripts/run_workflow.py
```

### Q: Git推送失败
```bash
# 检查远程仓库
git remote -v

# 检查认证
git pull origin main
```

---

**版本**：v1.0  
**更新日期**：2026-05-17
