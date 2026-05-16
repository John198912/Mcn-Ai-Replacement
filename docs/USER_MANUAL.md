# MCN AI Replacement — 用户手册

> 基于SOUL框架的AI内容创作辅助系统

---

## 快速开始

### 5分钟上手

```bash
# 1. 进入项目目录
cd ~/mcn-ai-replacement

# 2. 安装依赖（首次运行）
pip3 install -r requirements.txt

# 3. 初始化数据库
python3 scripts/init_database.py

# 4. 生成数据模板
python3 scripts/run_workflow.py generate-template

# 5. 填写模板后导入并评分
python3 scripts/run_workflow.py soul-rank --manual-file hotspots_template.csv
```

---

## 核心工作流

### 工作流1：热点采集和SOUL评分

从Hermes报告或手动文件获取热点，进行SOUL框架评分排序。

```bash
# 方式A：从Hermes报告自动采集（需要Hermes已运行）
python3 scripts/run_workflow.py soul-rank

# 方式B：从CSV文件导入
python3 scripts/run_workflow.py soul-rank --manual-file my_hotspots.csv --top 10

# 方式C：直接采集原始数据（不评分）
python3 scripts/run_workflow.py collect-hotspots
```

**输出示例**：
```
🏆 SOUL适配度排名（Top 5）：

 1. [8.5] AI时代如何重新学会选择和放弃
    方向：有限性智慧  |  受众：探索者（25-30岁）
    角度：从'有限性'重新审视...

 2. [7.2] 超级个体如何打造一人企业
    方向：有限性智慧  |  受众：转型者（30-38岁）
    角度：从'有限性'重新审视...
```

### 工作流2：SOUL脚本生成

基于SOUL框架生成个性化短视频脚本。

```bash
# 生成脚本（交互模式，等待Claude Code执行）
python3 scripts/run_workflow.py soul-script \
  -t "AI时代如何重新学会选择" \
  -a "从有限性视角" \
  -p douyin \
  -d 180

# 仅生成提示词（手动复制使用）
python3 scripts/run_workflow.py soul-script \
  -t "你的选题" \
  -a "你的角度" \
  --prompt-only
```

**文件交换流程**：
1. 运行命令后，提示词写入 `/tmp/mcn_script_prompt.txt`
2. 在Claude Code中执行提示词
3. 将结果保存到 `/tmp/mcn_script_result.txt`
4. 系统自动检测并解析结果

### 工作流3：知识库管理

```bash
# 同步到GitHub
python3 scripts/run_workflow.py sync-github

# 增量同步（默认）
python3 scripts/run_workflow.py sync-github --incremental

# 远程优先模式（冲突时使用远程版本）
python3 scripts/run_workflow.py sync-github --strategy remote_wins

# 创建备份
python3 scripts/run_workflow.py backup

# 列出所有备份
python3 scripts/run_workflow.py list-backups

# 从备份恢复
python3 scripts/run_workflow.py restore backup_20260517_100000
```

---

## 数据格式

### CSV导入格式

```csv
标题,平台,热度,标签,描述,推荐角度,优先级
AI时代如何学会选择,douyin,上升,"AI,有限性",探讨选择的意义,从有限性视角,P0
```

### JSON导入格式

```json
[
  {
    "title": "AI时代如何学会选择",
    "platform": "douyin",
    "heat_level": "上升",
    "tags": ["AI", "有限性"],
    "description": "探讨选择的意义",
    "recommended_angle": "从有限性视角",
    "priority": "P0"
  }
]
```

### 支持的平台

| 平台 | 标识 |
|------|------|
| 抖音 | `douyin` |
| 小红书 | `xiaohongshu` |
| B站 | `bilibili` |
| 微博 | `weibo` |
| 知乎 | `zhihu` |

### 热度等级

`爆发` > `上升` > `稳定` > `衰退`

---

## SOUL框架说明

### 有限性三角

系统基于SOUL的"有限性三角"进行热点适配评分：

| 方向 | 核心问题 | 关键词 | 典型受众 |
|------|---------|--------|---------|
| 有限性智慧 | 如何在无限可能中学会选择？ | 选择、放弃、承担 | Marcus（转型者） |
| 存在的偶然性 | 如果AI比我强，我为什么存在？ | 意义、独特、价值 | Alex（觉醒者） |
| 协议层协作 | 如何与AI建立健康边界？ | 边界、协议、共生 | Z（年轻探索者） |

### 三阶对话法

脚本生成遵循三阶对话法：

```
第一层：场景爆破 → 用反常识问题抓住注意力
   ↓
第二层：结构拆解 → 用框架揭示深层逻辑
   ↓
第三层：反刍重建 → 给出可用的思维工具
```

### 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 有限性三角适配 | 30% | 与SOUL核心命题的契合度 |
| 核心受众匹配 | 25% | 对目标受众的吸引力 |
| 三阶对话法可行性 | 25% | 是否适合三阶展开 |
| 差异化空间 | 15% | SOUL独特视角的发挥空间 |
| 风险评估 | 5% | 合规性和翻车概率 |

---

## 定时任务

```bash
# 启动调度器（阻塞运行）
python3 scripts/run_workflow.py start-scheduler

# 生成macOS launchd配置（开机自启）
python3 scripts/run_workflow.py generate-launchd > \
  ~/Library/LaunchAgents/com.mcn.scheduler.plist

# 加载配置
launchctl load ~/Library/LaunchAgents/com.mcn.scheduler.plist

# 卸载配置
launchctl unload ~/Library/LaunchAgents/com.mcn.scheduler.plist
```

**定时任务列表**：
- 每周一 10:00 — 采集热点
- 每天 02:00 — 备份知识库
- 每天 03:00 — 同步GitHub

---

## Hermes集成

### 启动API服务

```bash
# 本地运行（无需认证）
python3 scripts/run_workflow.py start-api

# 自定义端口
python3 scripts/run_workflow.py start-api --port 9000
```

### API端点

```
POST /tasks          创建任务
GET  /tasks/{id}     查询任务状态
GET  /tasks?status=completed  过滤任务
```

### 任务格式

```json
{
  "task_type": "hot_topic",
  "params": {},
  "callback": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
}
```

### 从Hermes调用示例

```python
import requests

# MCN系统运行在本地
response = requests.post(
    "http://127.0.0.1:8000/tasks",
    json={
        "task_type": "create_content",
        "params": {"topic": "AI焦虑", "platform": "douyin"},
    }
)
task_id = response.json()["task_id"]

# 查询状态
status = requests.get(f"http://127.0.0.1:8000/tasks/{task_id}").json()
```

---

## SOUL配置

### 画像加载优先级

1. 环境变量 `SOUL_PROFILE_PATH`
2. `~/.hermes/skills/knowledge/soul/SKILL.md`
3. `~/hermes_workspace/config/SOUL.md`
4. `config/soul_profile.json`
5. 内置默认配置

### 自定义SOUL配置

```bash
# 方式1：设置环境变量
export SOUL_PROFILE_PATH=~/my_soul_config.md

# 方式2：创建本地配置
echo '# 我的SOUL画像
定位：技术思考者
核心受众：开发者、创业者
' > config/soul_profile.json
```

---

## 常见问题

### Q: Hermes报告在哪里？
A: Hermes热点采集系统每天08:00自动运行，报告保存在 `~/hermes_workspace/reports/hotspot/daily_YYYY-MM-DD.md`。

### Q: 没有Hermes报告怎么办？
A: 使用手动导入：
```bash
python3 scripts/run_workflow.py generate-template  # 生成模板
# 填写模板
python3 scripts/run_workflow.py soul-rank --manual-file hotspots.csv
```

### Q: 脚本生成提示词后如何操作？
A: 文件交换模式：提示词在 `/tmp/mcn_script_prompt.txt`，在Claude Code中执行后将结果保存到 `/tmp/mcn_script_result.txt`。

### Q: GitHub同步冲突怎么办？
A: 三种策略：
```bash
# 本地优先
python3 scripts/run_workflow.py sync-github --strategy local_wins

# 远程优先
python3 scripts/run_workflow.py sync-github --strategy remote_wins

# 手动解决
python3 scripts/run_workflow.py sync-github --strategy manual
```

### Q: 如何修改评分权重？
A: 编辑 `src/skills/soul_hot_topic_matcher.py` 中的权重计算逻辑。

---

## 命令速查

| 命令 | 用途 |
|------|------|
| `soul-rank` | 热点SOUL评分排序 |
| `soul-script` | SOUL脚本生成 |
| `collect-hotspots` | 采集热点 |
| `generate-template` | 生成数据模板 |
| `sync-github` | 同步GitHub |
| `backup` | 创建备份 |
| `list-backups` | 列出备份 |
| `restore <id>` | 恢复备份 |
| `start-scheduler` | 启动定时任务 |
| `start-api` | 启动API服务 |
| `generate-launchd` | 生成启动配置 |

---

**版本**：v1.0  
**更新日期**：2026-05-17
