# MCN AI Replacement 优化方案补充 — 飞书CLI集成

> 基于飞书 lark-cli（user身份）新增能力，对 v3.1 方案的补充优化
> 
> 日期：2026-05-17

---

## 一、能力变化分析

### 1.1 之前 vs 现在

| 维度 | 旧限制（v3.1） | 新能力（飞书CLI） |
|------|---------------|------------------|
| 飞书角色 | 仅消息通信 | **全功能 user 身份** |
| 知识库 | 本地 + GitHub（两层） | **可增加飞书层** |
| 热点存储 | SQLite | **飞书多维表格（Base）** |
| 脚本存储 | 本地 Markdown | **飞书文档（Docs）** |
| 通知方式 | Webhook 单向推送 | **IM 双向交互** |
| 任务追踪 | 无 | **飞书任务（Task）** |
| 数据分析 | 本地 SQL 查询 | **飞书电子表格（Sheets）** |
| 调度触发 | HTTP API + cron | **飞书消息指令** |

### 1.2 已授予的飞书权限

通过 `lark-cli auth login --recommend` 已获得：

- `base:*` — 多维表格全部操作
- `docs:*` / `docx:*` — 文档读写
- `sheets:*` — 电子表格读写
- `wiki:*` — 知识库管理
- `drive:*` — 云空间文件管理
- `im:*` — 消息收发（含群组）
- `calendar:*` — 日历管理
- `task:*` — 任务管理

---

## 二、新增模块设计

### 2.1 FeishuBaseAdapter — 飞书多维表格知识库

**用途**：将热点数据同步到飞书多维表格，实现可视化、协作和AI搜索

```python
# src/adapters/feishu_base_adapter.py

class FeishuBaseAdapter:
    """
    飞书多维表格适配器
    
    替代/补充本地SQLite：
    1. 热点跟踪表：可视化评分排序
    2. 脚本库：按平台/状态筛选
    3. 对标创作者表：持续追踪
    """
    
    def __init__(self):
        self.base_token = os.getenv("MCN_FEISHU_BASE_TOKEN")
    
    async def init_tables(self):
        """初始化多维表格结构（首次使用）"""
        # 创建应用
        if not self.base_token:
            result = await self._run_lark_cli(
                "base", "+base-create",
                "--name", "MCN内容创作系统",
                "--folder-token", os.getenv("MCN_FEISHU_FOLDER_TOKEN", ""),
            )
            self.base_token = result["base_token"]
            # 保存到 .env
            self._save_base_token(self.base_token)
        
        # 创建子表
        await self._ensure_table("热点跟踪", HOTSPOT_FIELDS)
        await self._ensure_table("脚本库", SCRIPT_FIELDS)
        await self._ensure_table("对标创作者", CREATOR_FIELDS)
    
    async def sync_hotspots(self, hotspots: List[Dict]):
        """同步热点到飞书多维表格"""
        for h in hotspots:
            await self._run_lark_cli(
                "base", "+record", "+create",
                "--app-token", self.base_token,
                "--table-id", "热点跟踪",
                "--fields", json.dumps({
                    "标题": h["title"],
                    "平台": h["platform"],
                    "SOUL评分": h["total_score"],
                    "有限性方向": h["finitude_name"],
                    "目标受众": h["audience_label"],
                    "推荐角度": h["recommended_angle"],
                    "状态": "待选题",
                    "采集时间": datetime.now().isoformat(),
                })
            )
    
    async def sync_script(self, script: Dict):
        """同步脚本到飞书文档（长文本使用Docs而非Base）"""
        # 脚本正文用飞书文档存储
        content = self._script_to_doc_markdown(script)
        result = await self._run_lark_cli(
            "docx", "+create",
            "--title", f"{script['topic']} - 脚本",
            "--content", content,
        )
        # 同时在Base中记录元数据
        await self._run_lark_cli(
            "base", "+record", "+create",
            "--app-token", self.base_token,
            "--table-id", "脚本库",
            "--fields", json.dumps({
                "选题": script["topic"],
                "平台": script.get("platform", "douyin"),
                "创建时间": datetime.now().isoformat(),
                "状态": "待审核",
                "文档链接": result.get("url", ""),
            })
        )
    
    async def query_hotspots(self, status: str = None) -> List[Dict]:
        """查询飞书多维表格中的热点"""
        args = [
            "base", "+record", "+get",
            "--app-token", self.base_token,
            "--table-id", "热点跟踪",
        ]
        if status:
            args.extend(["--filter", f'{{"field":"状态","operator":"is","value":"{status}"}}'])
        
        return await self._run_lark_cli(*args)
    
    async def _run_lark_cli(self, *args) -> Dict:
        """调用 lark-cli 命令"""
        cmd = ["lark-cli"] + list(args) + ["--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
```

**与传统方案对比**：

| 特性 | SQLite | 飞书Base |
|------|--------|---------|
| 可视化 | ❌ 需要额外工具 | ✅ 内置视图 |
| 协作 | ❌ 单机 | ✅ 多人实时 |
| AI搜索 | ❌ 无 | ✅ 飞书AI |
| 仪表盘 | ❌ 无 | ✅ 内置Dashboard |
| 离线可用 | ✅ | ❌ 需要网络 |
| 速度 | ✅ 极快 | ⚠️ API调用 |

**建议**：飞书Base + 本地SQLite 双写，互为备份。

---

### 2.2 FeishuIMNotifier — 消息通知升级为双向交互

**之前**：单向飞书Webhook推送

**现在**：可通过IM消息接收指令

```python
# src/integrations/feishu_im_notifier.py

class FeishuIMNotifier:
    """
    飞书消息通知器（双向交互）
    
    升级点：
    1. 主动推送结果 → 保留
    2. 🆕 接收消息指令 → 新增
    3. 🆕 群组协作 → 新增
    """
    
    def __init__(self):
        self.bot_identity = "--as bot"  # bot发消息
        self.user_identity = "--as user"  # user读消息
    
    async def send_completion_notice(self, task_result: Dict):
        """发送任务完成通知"""
        message = self._format_task_result(task_result)
        await self._run_lark_cli(
            "im", "+message", "+send",
            "--receive-id-type", "open_id",
            "--receive-id", os.getenv("FEISHU_USER_OPEN_ID"),
            "--msg-type", "interactive",
            "--content", json.dumps(message),
        )
    
    async def send_weekly_report(self, report: Dict):
        """发送周报到指定群组"""
        await self._run_lark_cli(
            "im", "+message", "+send",
            "--receive-id-type", "chat_id",
            "--receive-id", os.getenv("MCN_FEISHU_CHAT_ID"),
            "--msg-type", "post",
            "--content", self._format_weekly_report(report),
        )
    
    async def poll_commands(self) -> List[Dict]:
        """
        🆕 轮询消息指令
        
        支持指令：
        - /hot 查询今日热点
        - /script <选题> 生成脚本
        - /sync 同步知识库
        - /status 查看系统状态
        """
        # 读取最近消息
        messages = await self._run_lark_cli(
            "im", "+message", "+list",
            self.user_identity,
            "--receive-id-type", "chat_id",
            "--receive-id", os.getenv("MCN_FEISHU_CHAT_ID"),
            "--page-size", "10",
        )
        
        commands = []
        for msg in messages.get("items", []):
            cmd = self._parse_command(msg.get("content", ""))
            if cmd:
                commands.append(cmd)
        
        return commands
    
    def _parse_command(self, content: str) -> Dict | None:
        """解析消息中的指令"""
        content = content.strip()
        if content.startswith("/hot"):
            return {"command": "hot_topics", "args": {}}
        elif content.startswith("/script"):
            topic = content.replace("/script", "").strip()
            return {"command": "create_script", "args": {"topic": topic}}
        elif content.startswith("/sync"):
            return {"command": "sync_knowledge", "args": {}}
        elif content.startswith("/status"):
            return {"command": "system_status", "args": {}}
        return None
    
    async def _run_lark_cli(self, *args) -> Dict:
        cmd = ["lark-cli"] + list(args) + ["--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
```

---

### 2.3 FeishuWikiKB — 飞书知识库

**用途**：用飞书Wiki替代本地Markdown目录作为知识仓库

```python
# src/knowledge/feishu_wiki_kb.py

class FeishuWikiKB:
    """
    飞书知识库管理器
    
    组织结构：
    MCN内容创作系统/
    ├── 热点归档/
    │   ├── 2026-W21/
    │   │   ├── 热点1分析
    │   │   └── ...
    │   └── ...
    ├── 脚本库/
    │   ├── 抖音/
    │   ├── 小红书/
    │   └── B站/
    ├── 对标创作者/
    └── 策略文档/
    """
    
    def __init__(self):
        self.space_id = os.getenv("MCN_FEISHU_WIKI_SPACE_ID")
    
    async def init_wiki(self):
        """初始化知识库结构"""
        if not self.space_id:
            result = await self._run_lark_cli(
                "wiki", "+space", "+create",
                "--name", "MCN内容创作知识库",
                "--description", "AI驱动的MCN内容创作知识沉淀",
            )
            self.space_id = result["space_id"]
        
        # 确保目录结构存在
        for folder in ["热点归档", "脚本库", "对标创作者", "策略文档"]:
            await self._ensure_node(self.space_id, folder)
    
    async def archive_hotspot(self, hotspot: Dict):
        """归档热点分析到Wiki"""
        week = datetime.now().strftime("%Y-W%V")
        parent = await self._ensure_node(self.space_id, f"热点归档/{week}")
        
        await self._run_lark_cli(
            "wiki", "+node", "+create",
            "--space-id", self.space_id,
            "--parent-token", parent["token"],
            "--title", hotspot["title"][:50],
            "--content", self._format_hotspot_page(hotspot),
        )
    
    async def archive_script(self, script: Dict):
        """归档脚本到Wiki"""
        platform = script.get("platform", "通用")
        parent = await self._ensure_node(self.space_id, f"脚本库/{platform}")
        
        await self._run_lark_cli(
            "wiki", "+node", "+create",
            "--space-id", self.space_id,
            "--parent-token", parent["token"],
            "--title", f"{script['topic']} - {datetime.now():%m-%d}",
            "--content", self._format_script_page(script),
        )
    
    async def search(self, query: str) -> List[Dict]:
        """搜索知识库"""
        return await self._run_lark_cli(
            "wiki", "+node", "+search",
            "--space-id", self.space_id,
            "--query", query,
        )
```

---

## 三、架构升级方案

### 3.1 从两层到三层知识库

```
之前（v3.1）：
  ┌──────────┐    ┌──────────┐
  │ 本地SQLite│ ←→ │ GitHub   │
  │ Markdown │    │ 备份     │
  └──────────┘    └──────────┘

现在（飞书CLI后）：
  ┌──────────┐    ┌──────────────┐    ┌──────────┐
  │ 本地SQLite│ ←→ │ 飞书Base/Docs │ ←→ │ GitHub   │
  │ Markdown │    │ Wiki/Sheets   │    │ 归档     │
  └──────────┘    └──────────────┘    └──────────┘
   离线主存储       在线协作+可视化      版本控制
```

### 3.2 模块调整

| 模块 | v3.1 方案 | 飞书CLI补充 |
|------|----------|------------|
| 知识库 | TwoLayerKnowledgeManager | + FeishuBaseAdapter / FeishuWikiKB |
| 通知 | 飞书Webhook | + FeishuIMNotifier（双向） |
| 任务 | 无 | 🆕 FeishuTaskTracker |
| 日程 | MCNScheduler | + 飞书Calendar同步 |

### 3.3 数据流升级

```
                    ┌──────────────────┐
                    │  飞书消息指令     │ ← 用户可通过IM发指令
                    └────────┬─────────┘
                             ↓
  ┌──────────────────────────────────────────────┐
  │              MCN AI Replacement              │
  │                                              │
  │  采集 → 评分 → 生成 → 审核                   │
  │    ↓      ↓      ↓      ↓                   │
  │  ┌────┬──────┬──────┬──────┐                │
  │  │Base│ Docs │ Wiki │Sheets│ ← 飞书存储层   │
  │  └────┴──────┴──────┴──────┘                │
  │    ↕      ↕      ↕      ↕                    │
  │  ┌────┴──────┴──────┴──────┐                │
  │  │     本地 SQLite/MD       │ ← 本地备份     │
  │  └─────────────────────────┘                │
  └──────────────────────────────────────────────┘
```

---

## 四、新增CLI命令

```python
# scripts/run_workflow.py 新增命令

@cli.command()
def feishu_init():
    """初始化飞书知识库结构.
    
    创建多维表格、Wiki空间等
    """
    adapter = FeishuBaseAdapter()
    asyncio.run(adapter.init_tables())
    
    wiki = FeishuWikiKB()
    asyncio.run(wiki.init_wiki())
    
    click.echo("✅ 飞书知识库初始化完成")

@cli.command()
@click.option("--to", default="all", 
              type=click.Choice(["base", "wiki", "all"]),
              help="同步目标")
def feishu_sync(to):
    """同步本地数据到飞书.
    
    将SQLite中的热点和脚本同步到飞书Base/Wiki
    """
    click.echo(f"🔄 同步到飞书 ({to})...")
    # ... 实现同步逻辑

@cli.command()
def feishu_listen():
    """启动飞书消息监听（接收指令）.
    
    轮询飞书消息，解析指令并执行
    """
    notifier = FeishuIMNotifier()
    click.echo("👂 开始监听飞书消息指令...")
    click.echo("支持指令：/hot /script /sync /status")
    
    while True:
        commands = asyncio.run(notifier.poll_commands())
        for cmd in commands:
            click.echo(f"收到指令: {cmd}")
            # 执行对应操作
        time.sleep(30)
```

---

## 五、实施计划补充

### Phase 5：飞书CLI集成（3-5天）

| Day | 任务 | 产出 |
|-----|------|------|
| 1 | FeishuBaseAdapter 实现 + 测试 | 多维表格同步 |
| 2 | FeishuWikiKB 实现 + 测试 | Wiki知识库 |
| 3 | FeishuIMNotifier 双向交互 | 消息指令 |
| 4 | 飞书集成测试 | 端到端验证 |
| 5 | CLI命令 + 文档 | 可用功能 |

### 优先级建议

| 模块 | 优先级 | 理由 |
|------|--------|------|
| **FeishuBaseAdapter** | 🔴 P0 | 替代SQLite可视化短板，最大价值点 |
| **FeishuIMNotifier（通知）** | 🟡 P1 | 已有Webhook，升级为双向 |
| **FeishuWikiKB** | 🟡 P1 | Wiki搜索能力，长文档存储 |
| **FeishuIMNotifier（指令）** | 🟢 P2 | IM指令交互，锦上添花 |

---

## 六、关键决策点

### 6.1 飞书Base vs 本地SQLite

| 方案 | 优点 | 缺点 |
|------|------|------|
| 纯飞书Base | 可视化、协作、AI搜索 | 依赖网络、API限流 |
| 纯本地SQLite | 离线、极速、可控 | 无可视化、单机 |
| **双写（推荐）** | 兼顾两者优点 | 增加复杂度 |

### 6.2 飞书存储的数据类型

| 数据类型 | 推荐存储 | 理由 |
|---------|---------|------|
| 热点结构化数据（评分、状态） | **飞书Base** | 可视化筛选排序 |
| 脚本长文本 | **飞书Docs** | 富文本，版本历史 |
| 分析报告 | **飞书Wiki** | 层级结构，全文搜索 |
| 对标创作者数据 | **飞书Base** | 持续更新追踪 |
| 统计数据 | **飞书Sheets** | 图表分析 |

### 6.3 lark-cli 调用方式

```python
# 推荐：subprocess 调用（稳定可靠）
import subprocess
import json

def lark(*args) -> dict:
    result = subprocess.run(
        ["lark-cli"] + list(args) + ["--json"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"lark-cli failed: {result.stderr}")
    return json.loads(result.stdout)

# 使用示例
# lark("base", "+record", "+create", "--app-token", token, ...)
# lark("wiki", "+node", "+search", "--space-id", sid, "--query", q)
```

---

**文档版本**：v1.0（补充）  
**基于**：v3.1 Final  
**状态**：待讨论
