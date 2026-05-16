# MCN AI Replacement — 快速开始指南

> 5分钟完成安装到第一个SOUL脚本生成

---

## Step 1：安装（1分钟）

```bash
cd ~/mcn-ai-replacement
pip3 install -r requirements.txt
python3 scripts/init_database.py
```

## Step 2：测试（30秒）

```bash
python3 -m pytest tests/ -q
# 看到 69 passed 即表示安装成功
```

## Step 3：获取热点（1分钟）

```bash
# 生成模板
python3 scripts/run_workflow.py generate-template

# 编辑模板，填入你的热点
vim hotspots_template.csv

# 导入并评分
python3 scripts/run_workflow.py soul-rank --manual-file hotspots_template.csv
```

## Step 4：生成脚本（2分钟）

```bash
# 生成提示词
python3 scripts/run_workflow.py soul-script \
  -t "你的选题" \
  -a "你的角度" \
  --prompt-only

# 复制提示词到Claude Code执行
# 将结果保存到 /tmp/mcn_script_result.txt
```

## Step 5：保存和同步（30秒）

```bash
# 备份
python3 scripts/run_workflow.py backup

# 同步GitHub
python3 scripts/run_workflow.py sync-github
```

---

## 常用工作流

### 每周选题（5分钟）

```bash
# 1. 从Hermes自动获取热点（如果可用）
python3 scripts/run_workflow.py soul-rank --top 10

# 2. 选择Top 1，生成脚本提示词
python3 scripts/run_workflow.py soul-script \
  -t "选择的选题" \
  -a "推荐的角度" \
  --prompt-only
```

### 内容创作（10分钟）

```bash
# 1. 启动脚本生成（交互模式）
python3 scripts/run_workflow.py soul-script \
  -t "AI焦虑" \
  -a "从有限性视角解读AI时代的焦虑" \
  -p douyin -d 180

# 2. 按提示在Claude Code中执行

# 3. 获得完整结构化脚本
```

### 日常维护（1分钟）

```bash
# 每日备份
python3 scripts/run_workflow.py backup

# 每周同步
python3 scripts/run_workflow.py sync-github
```

---

## 自动运行

```bash
# 一键启动定时任务
python3 scripts/run_workflow.py start-scheduler

# 或配置开机自启
python3 scripts/run_workflow.py generate-launchd > \
  ~/Library/LaunchAgents/com.mcn.scheduler.plist
launchctl load ~/Library/LaunchAgents/com.mcn.scheduler.plist
```

---

## 下一步

- 阅读 [用户手册](./USER_MANUAL.md)
- 查看 [部署指南](./DEPLOYMENT_GUIDE.md)
- 了解 [优化方案](./OPTIMIZATION_PLAN_V3.1_FINAL.md)

---

**准备好了吗？开始你的第一条SOUL驱动内容：**

```bash
python3 scripts/run_workflow.py soul-rank --top 5
```
