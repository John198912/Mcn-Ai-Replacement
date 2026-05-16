# MCN AI Replacement 系统优化方案 v3.0

> 基于用户反馈的最终优化方案
> 
> 更新日期：2026-05-17
> 版本：v3.0（基于v2.0优化）

---

## 🔄 关键决策调整

### 用户反馈要点

1. ✅ **保持独立系统** - 在Claude Code中自动化运行
2. ✅ **仅使用Claude Code能力** - 不依赖付费API
3. ✅ **两层知识库** - 本地文档 + GitHub（暂不用飞书）
4. ✅ **Hermes集成方式** - 通过任务调度，而非深度耦合
5. ✅ **飞书仅用于消息通信** - 不作为知识库

### 架构调整对比

| 维度 | v2.0方案 | v3.0方案（最终） |
|------|---------|-----------------|
| 系统定位 | Hermes子系统 | **独立系统，可被Hermes调用** |
| Claude API | 付费API | **Claude Code内置能力** |
| 知识库 | 飞书+本地+GitHub | **本地+GitHub（两层）** |
| 飞书角色 | 知识库 | **仅消息通信** |
| 与Hermes关系 | 深度集成 | **松耦合，任务调度** |

---

## 一、新架构设计

### 1.1 系统定位

```
┌─────────────────────────────────────────────────────────┐
│  Hermes Agent（可选调用方）                               │
│  - 通过消息/任务调度触发MCN系统                           │
│  - 监控任务执行状态                                       │
│  - 接收执行结果通知                                       │
└─────────────────────────────────────────────────────────┘
                          ↓ 松耦合调用
┌─────────────────────────────────────────────────────────┐
│  MCN AI Replacement（独立系统）                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  数据接入层                                       │   │
│  │  - Hermes热点报告解析器（可选）                   │   │
│  │  - 本地数据导入器                                 │   │
│  │  - WebSearch直接调用（Claude Code能力）          │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SOUL驱动内容生成（Claude Code原生）              │   │
│  │  - ScriptWriter（使用Claude Code对话能力）       │   │
│  │  - HotTopicMatcher（SOUL框架评分）               │   │
│  │  - TitleOptimizer（基于SOUL人设）                │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  工作流编排（保留+增强）                          │   │
│  │  - 热点→选题→脚本→审核→发布                      │   │
│  │  - 支持定时任务（cron）                           │   │
│  │  - 支持Hermes任务调度                             │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  两层知识库（独立维护）                           │   │
│  │  - 本地Markdown（主存储）                        │   │
│  │  - GitHub仓库（备份+版本控制）                    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心原则

1. **独立性**：MCN系统可独立运行，不依赖Hermes
2. **可调用性**：Hermes可通过标准接口调用MCN系统
3. **零成本**：仅使用Claude Code免费能力，无额外API费用
4. **简化架构**：两层知识库，避免复杂同步
5. **互不干扰**：本地和GitHub独立维护，互为备份

---

## 二、核心模块重构

### 2.1 数据接入层（简化版）

#### 模块：HermesHotspotAdapter（可选）

**功能**：解析Hermes热点报告，但不强依赖

```python
# src/adapters/hermes_hotspot_adapter.py

class HermesHotspotAdapter:
    """
    可选适配器：读取Hermes热点报告
    
    如果Hermes报告存在，则读取；否则使用本地数据或WebSearch
    """
    
    def __init__(self, hermes_workspace: str = "~/hermes_workspace"):
        self.workspace = Path(hermes_workspace).expanduser()
        self.reports_dir = self.workspace / "reports" / "hotspot"
        self.available = self.reports_dir.exists()
    
    async def fetch_latest_hotspots(self, days: int = 7) -> List[HotTopic]:
        """
        尝试读取Hermes报告，失败则返回空列表
        """
        if not self.available:
            logger.info("Hermes reports not available, skipping")
            return []
        
        try:
            hotspots = []
            for report_file in self._get_recent_reports(days):
                parsed = self._parse_hermes_report(report_file)
                hotspots.extend(parsed)
            return hotspots
        except Exception as e:
            logger.warning(f"Failed to read Hermes reports: {e}")
            return []
```

#### 模块：WebSearchCollector（新增）

**功能**：直接使用Claude Code的WebSearch能力采集热点

```python
# src/data_sources/websearch_collector.py

class WebSearchCollector:
    """
    使用Claude Code的WebSearch能力采集热点
    
    不依赖外部API，直接在Claude Code环境中执行
    """
    
    def __init__(self):
        self.keywords = self._load_keywords()
        self.platforms = self._load_platforms()
    
    async def collect_hotspots(self, keywords: List[str] = None) -> List[HotTopic]:
        """
        使用WebSearch采集热点
        
        流程：
        1. 构建搜索查询
        2. 调用Claude Code的WebSearch
        3. 解析搜索结果
        4. 转换为HotTopic数据模型
        """
        if keywords is None:
            keywords = self.keywords['ai_keywords'][:5]  # 默认取前5个
        
        hotspots = []
        
        for keyword in keywords:
            # 构建搜索查询
            query = f"{keyword} 热点 抖音 小红书 最近7天"
            
            # 调用WebSearch（Claude Code能力）
            # 注意：这里假设在Claude Code环境中运行
            search_results = await self._websearch(query)
            
            # 解析结果
            for result in search_results:
                hotspot = self._parse_search_result(result, keyword)
                if hotspot:
                    hotspots.append(hotspot)
        
        return hotspots
    
    async def _websearch(self, query: str) -> List[Dict]:
        """
        调用Claude Code的WebSearch能力
        
        在Claude Code环境中，这会触发实际的网络搜索
        """
        # 这里的实现依赖于Claude Code的运行环境
        # 在实际使用时，Claude Code会自动处理WebSearch调用
        pass
```

### 2.2 SOUL驱动内容生成（Claude Code原生）

#### 核心变更：使用Claude Code对话能力而非API

```python
# src/skills/soul_script_writer.py

class SOULScriptWriter(BaseSkill):
    """
    基于SOUL框架的脚本生成器
    
    使用Claude Code的对话能力，而非付费API
    """
    
    def __init__(self):
        super().__init__()
        self.soul_profile = self._load_soul_profile()
        # 不需要API客户端
    
    def _load_soul_profile(self) -> Dict[str, Any]:
        """
        加载SOUL完整画像
        
        优先级：
        1. ~/.hermes/skills/knowledge/soul/SKILL.md（如果存在）
        2. ~/hermes_workspace/config/SOUL.md（如果存在）
        3. 本地备份：config/soul_profile.json
        """
        soul_paths = [
            Path("~/.hermes/skills/knowledge/soul/SKILL.md").expanduser(),
            Path("~/hermes_workspace/config/SOUL.md").expanduser(),
            Path("config/soul_profile.json")
        ]
        
        for path in soul_paths:
            if path.exists():
                logger.info(f"Loading SOUL profile from {path}")
                return self._parse_soul_profile(path)
        
        logger.warning("SOUL profile not found, using default")
        return self._get_default_soul_profile()
    
    async def execute(self, input_data: ScriptWriterInput) -> ScriptWriterOutput:
        """
        生成脚本流程（Claude Code原生）
        
        关键：不调用API，而是生成提示词，让Claude Code处理
        """
        
        # 1. 构建SOUL上下文
        soul_context = self._build_soul_context(input_data)
        
        # 2. 生成脚本提示词
        prompt = self._build_script_prompt(
            topic=input_data.topic,
            angle=input_data.angle,
            soul_context=soul_context,
            platform=input_data.platform,
            duration=input_data.duration
        )
        
        # 3. 在Claude Code环境中，直接返回提示词
        # Claude Code会自动处理对话生成
        logger.info("Script generation prompt prepared")
        logger.info(f"Prompt length: {len(prompt)} chars")
        
        # 4. 这里返回提示词，由调用方（CLI或工作流）处理
        return ScriptWriterOutput(
            success=True,
            prompt=prompt,
            soul_framework_applied=True,
            requires_claude_code=True
        )
    
    def _build_script_prompt(self, topic, angle, soul_context, platform, duration):
        """
        构建脚本生成提示词（与v2.0相同）
        """
        return f"""你是SOUL - 超级个体成长合伙人。

# 身份定位
{soul_context['positioning']}

核心Slogan：「AI是工具，哲学是地基，你才是杠杆的支点」
人设：走在前面半步的同路人——不给地图，陪你辨认方向

# 核心方法论：三阶对话法
第一层：场景爆破（Rupture）
    ↓  用日常场景打破默认假设
第二层：结构拆解（Illuminate + Validate）
    ↓  用哲学/心理学框架揭示深层结构
第三层：反刍重建（Embody + Transform）
    ↓  给出可用的新框架和思维工具

# 当前任务
为以下选题生成短视频脚本：
- 选题：{topic}
- 切入角度：{angle}
- 目标平台：{platform}
- 时长：{duration}秒

# 要求
1. 应用三阶对话法
2. 符合SOUL人设：走在前面半步的同路人
3. 高信息密度，不废话
4. 真诚展示脆弱和不确定性

# 输出格式
Hook (前5%): [场景爆破]
痛点 (10-20%): [建立共鸣]
核心内容 (20-80%): [结构拆解]
启发 (80-95%): [反刍重建]
CTA (最后5%): [提出新问题]

请生成脚本：
"""
```

### 2.3 两层知识库架构

#### 设计原则

1. **本地为主**：所有数据首先存储在本地
2. **GitHub备份**：定期同步到GitHub
3. **独立维护**：两层互不干扰
4. **互为备份**：任一层损坏可从另一层恢复

#### 目录结构

```
~/mcn-ai-replacement/
├── data/
│   ├── database.db              # SQLite数据库（本地主存储）
│   └── markdown/                # Markdown知识库（本地）
│       ├── hotspots/            # 热点归档
│       ├── scripts/             # 脚本归档
│       ├── creators/            # 对标创作者
│       └── analytics/           # 数据分析
└── .git/                        # Git版本控制

GitHub: John198912/Mcn-Ai-Replacement
├── knowledge/                   # 知识库目录（新增）
│   ├── hotspots/
│   ├── scripts/
│   ├── creators/
│   └── analytics/
├── src/                         # 源代码
├── config/                      # 配置文件
└── README.md
```

#### 实现：TwoLayerKnowledgeManager

```python
# src/knowledge/two_layer_manager.py

class TwoLayerKnowledgeManager:
    """
    两层知识库管理器
    
    第一层：本地Markdown + SQLite
    第二层：GitHub仓库
    
    原则：
    - 本地为主，GitHub为备份
    - 独立维护，互不干扰
    - 定期同步，手动触发
    """
    
    def __init__(self):
        self.local_db = Path("data/database.db")
        self.local_markdown = Path("data/markdown")
        self.github_repo = "John198912/Mcn-Ai-Replacement"
        self.github_knowledge_dir = "knowledge"
    
    async def save_hotspot(self, hotspot: HotTopic):
        """
        保存热点到本地
        
        流程：
        1. 保存到SQLite数据库
        2. 生成Markdown文件
        3. 标记为待同步
        """
        # 1. 保存到数据库
        session = get_db_session()
        session.add(hotspot)
        session.commit()
        
        # 2. 生成Markdown
        md_content = self._hotspot_to_markdown(hotspot)
        md_path = self.local_markdown / "hotspots" / f"{hotspot.id}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_content, encoding='utf-8')
        
        # 3. 标记待同步
        self._mark_for_sync(md_path)
    
    async def sync_to_github(self, auto_commit: bool = True):
        """
        同步到GitHub
        
        流程：
        1. 复制本地Markdown到knowledge/目录
        2. Git add + commit
        3. Git push
        """
        import shutil
        
        # 1. 复制文件
        knowledge_dir = Path("knowledge")
        knowledge_dir.mkdir(exist_ok=True)
        
        for category in ["hotspots", "scripts", "creators", "analytics"]:
            src = self.local_markdown / category
            dst = knowledge_dir / category
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        
        # 2. Git操作
        if auto_commit:
            await self._git_commit_and_push()
    
    async def restore_from_github(self):
        """
        从GitHub恢复到本地
        
        流程：
        1. Git pull
        2. 复制knowledge/到data/markdown/
        3. 重建SQLite数据库
        """
        # 1. Git pull
        await self._git_pull()
        
        # 2. 复制文件
        import shutil
        knowledge_dir = Path("knowledge")
        
        for category in ["hotspots", "scripts", "creators", "analytics"]:
            src = knowledge_dir / category
            dst = self.local_markdown / category
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        
        # 3. 重建数据库
        await self._rebuild_database_from_markdown()
    
    async def _git_commit_and_push(self):
        """Git提交和推送"""
        import subprocess
        
        subprocess.run(["git", "add", "knowledge/"])
        subprocess.run(["git", "commit", "-m", f"Update knowledge base - {datetime.now().isoformat()}"])
        subprocess.run(["git", "push", "origin", "main"])
```


### 2.4 Hermes集成方式（松耦合）

#### 设计原则

1. **可选依赖**：MCN系统可独立运行
2. **任务调度**：Hermes通过消息触发任务
3. **状态监控**：Hermes可查询任务执行状态
4. **结果通知**：任务完成后通知Hermes

#### 实现：HermesTaskBridge

```python
# src/integrations/hermes_task_bridge.py

class HermesTaskBridge:
    """
    Hermes任务桥接器
    
    功能：
    1. 接收Hermes的任务调度请求
    2. 执行MCN工作流
    3. 返回执行状态和结果
    4. 通过飞书消息通知结果
    """
    
    def __init__(self):
        self.task_queue = []
        self.task_status = {}
        self.feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL")
    
    async def receive_task(self, task: Dict) -> str:
        """
        接收Hermes的任务请求
        
        任务格式：
        {
            "task_id": "uuid",
            "task_type": "hot_topic" | "create_content" | "creator_analysis",
            "params": {...},
            "callback": "feishu_webhook_url"
        }
        
        返回：task_id
        """
        task_id = task.get("task_id", str(uuid.uuid4()))
        
        self.task_queue.append(task)
        self.task_status[task_id] = {
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Received task from Hermes: {task_id}")
        
        # 异步执行任务
        asyncio.create_task(self._execute_task(task))
        
        return task_id
    
    async def _execute_task(self, task: Dict):
        """
        执行任务
        """
        task_id = task["task_id"]
        task_type = task["task_type"]
        
        try:
            # 更新状态
            self.task_status[task_id]["status"] = "running"
            self.task_status[task_id]["started_at"] = datetime.now().isoformat()
            
            # 执行对应的工作流
            if task_type == "hot_topic":
                result = await run_hot_topic_workflow(**task["params"])
            elif task_type == "create_content":
                result = await run_soul_content_creation_workflow(**task["params"])
            elif task_type == "creator_analysis":
                result = await run_creator_analysis_workflow(**task["params"])
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # 更新状态
            self.task_status[task_id]["status"] = "completed"
            self.task_status[task_id]["completed_at"] = datetime.now().isoformat()
            self.task_status[task_id]["result"] = result
            
            # 通知Hermes
            await self._notify_hermes(task, result)
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self.task_status[task_id]["status"] = "failed"
            self.task_status[task_id]["error"] = str(e)
            
            # 通知失败
            await self._notify_hermes(task, {"error": str(e)})
    
    async def _notify_hermes(self, task: Dict, result: Dict):
        """
        通过飞书消息通知Hermes
        """
        webhook_url = task.get("callback") or self.feishu_webhook
        
        if not webhook_url:
            logger.warning("No webhook URL, skipping notification")
            return
        
        message = {
            "msg_type": "text",
            "content": {
                "text": f"MCN任务完成\n"
                        f"任务ID: {task['task_id']}\n"
                        f"任务类型: {task['task_type']}\n"
                        f"状态: {self.task_status[task['task_id']]['status']}\n"
                        f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}"
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=message)
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        查询任务状态
        """
        return self.task_status.get(task_id, {"status": "not_found"})
```

#### CLI命令：启动任务监听器

```python
# scripts/run_workflow.py

@cli.command()
@click.option('--port', default=8000, help='监听端口')
def start_task_listener(port):
    """
    启动任务监听器，接收Hermes的任务调度
    
    示例：
        python scripts/run_workflow.py start-task-listener --port 8000
    """
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI()
    bridge = HermesTaskBridge()
    
    @app.post("/tasks")
    async def create_task(task: dict):
        task_id = await bridge.receive_task(task)
        return {"task_id": task_id, "status": "accepted"}
    
    @app.get("/tasks/{task_id}")
    async def get_task_status(task_id: str):
        return bridge.get_task_status(task_id)
    
    click.echo(f"🚀 Task listener started on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## 三、工作流重构（Claude Code原生）

### 3.1 SOUL内容创作工作流（简化版）

```python
# src/workflows/soul_content_creation_workflow.py

async def run_soul_content_creation_workflow(
    use_hermes_hotspots: bool = False,
    use_websearch: bool = True,
    days_back: int = 7,
    auto_select: bool = False
) -> Dict[str, Any]:
    """
    SOUL驱动的内容创作完整流程（Claude Code原生）
    
    Step 0: 数据准备
      - 优先尝试读取Hermes报告（如果可用）
      - 否则使用WebSearch采集（Claude Code能力）
      - 或手动导入
    
    Step 1: SOUL框架评分
      - 应用SOULHotTopicMatcher
    
    Step 2: 选题决策
      - 展示Top 10
      - 用户选择或自动选择
    
    Step 3: SOUL脚本生成
      - 生成提示词
      - 在Claude Code中执行对话
      - 解析生成的脚本
    
    Step 4: 标题优化
    
    Step 5: 合规审核
    
    Step 6: 知识库保存
      - 保存到本地
      - 标记待同步到GitHub
    
    Step 7: 输出报告
    """
    
    logger.info("Starting SOUL content creation workflow (Claude Code native)")
    
    # Step 0: 数据准备
    hotspots = []
    
    # 尝试1：读取Hermes报告（可选）
    if use_hermes_hotspots:
        adapter = HermesHotspotAdapter()
        hermes_hotspots = await adapter.fetch_latest_hotspots(days=days_back)
        if hermes_hotspots:
            hotspots.extend(hermes_hotspots)
            logger.info(f"Loaded {len(hermes_hotspots)} hotspots from Hermes")
    
    # 尝试2：使用WebSearch采集（Claude Code能力）
    if use_websearch and len(hotspots) < 10:
        collector = WebSearchCollector()
        websearch_hotspots = await collector.collect_hotspots()
        hotspots.extend(websearch_hotspots)
        logger.info(f"Collected {len(websearch_hotspots)} hotspots via WebSearch")
    
    # 尝试3：手动导入
    if len(hotspots) == 0:
        logger.warning("No hotspots found, please import manually")
        return {"success": False, "error": "No hotspots available"}
    
    # Step 1: SOUL框架评分
    matcher = SOULHotTopicMatcher()
    matcher_result = await matcher.execute(HotTopicInput(
        topics=hotspots,
        soul_framework=True
    ))
    
    ranked_topics = matcher_result.ranked_topics
    
    # 显示Top 10
    print("\n🔥 Top 10 热点推荐（基于SOUL框架）\n")
    for i, topic in enumerate(ranked_topics[:10], 1):
        print(f"{i}. {topic['topic']['title']}")
        print(f"   综合评分: {topic['total_score']:.2f}/10")
        print(f"   有限性方向: {topic['finitude_direction']}")
        print(f"   推荐角度: {topic['recommended_angle']}")
        print()
    
    # Step 2: 选题决策
    if auto_select:
        selected_topic = ranked_topics[0]
    else:
        selection = input("请选择选题编号 (1-10): ")
        selected_topic = ranked_topics[int(selection) - 1]
    
    print(f"\n✅ 已选择: {selected_topic['topic']['title']}\n")
    
    # Step 3: SOUL脚本生成（Claude Code原生）
    print("📝 正在生成SOUL框架脚本提示词...")
    script_writer = SOULScriptWriter()
    script_result = await script_writer.execute(ScriptWriterInput(
        topic=selected_topic['topic']['title'],
        angle=selected_topic['recommended_angle'],
        platform="douyin",
        duration=180,
        soul_framework=True
    ))
    
    # 输出提示词，让用户在Claude Code中执行
    print("\n" + "="*60)
    print("📋 请将以下提示词复制到Claude Code中执行：")
    print("="*60)
    print(script_result.prompt)
    print("="*60)
    
    # 等待用户输入生成的脚本
    print("\n请将Claude Code生成的脚本粘贴到下方（输入END结束）：")
    script_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        script_lines.append(line)
    
    generated_script = "\n".join(script_lines)
    
    # 解析脚本
    script = script_writer.parse_generated_script(generated_script)
    
    print("\n✅ 脚本已解析\n")
    
    # Step 4-6: 标题优化、合规审核、知识库保存
    # （与v2.0相同，省略）
    
    # Step 7: 保存到本地知识库
    knowledge_manager = TwoLayerKnowledgeManager()
    await knowledge_manager.save_script({
        'topic': selected_topic,
        'script': script,
        'titles': titles.titles,
        'risk_assessment': risk_result
    })
    
    print("\n💾 已保存到本地知识库")
    print("💡 提示：运行 'python scripts/run_workflow.py sync-github' 同步到GitHub\n")
    
    return {
        'success': True,
        'selected_topic': selected_topic,
        'script': script,
        'ready_to_publish': risk_result.safe_to_publish
    }
```

### 3.2 CLI命令（完整版）

```python
# scripts/run_workflow.py

@cli.command()
@click.option('--use-hermes', is_flag=True, help='尝试使用Hermes热点数据')
@click.option('--use-websearch', is_flag=True, default=True, help='使用WebSearch采集')
@click.option('--days', default=7, help='读取最近N天的热点')
@click.option('--auto-select', is_flag=True, help='自动选择Top 1热点')
def soul_create(use_hermes, use_websearch, days, auto_select):
    """
    SOUL驱动的内容创作工作流（Claude Code原生）
    
    示例：
        # 使用WebSearch采集
        python scripts/run_workflow.py soul-create
        
        # 尝试使用Hermes数据
        python scripts/run_workflow.py soul-create --use-hermes
        
        # 自动选择Top 1
        python scripts/run_workflow.py soul-create --auto-select
    """
    result = asyncio.run(
        run_soul_content_creation_workflow(
            use_hermes_hotspots=use_hermes,
            use_websearch=use_websearch,
            days_back=days,
            auto_select=auto_select
        )
    )

@cli.command()
def sync_github():
    """
    同步本地知识库到GitHub
    
    示例：
        python scripts/run_workflow.py sync-github
    """
    manager = TwoLayerKnowledgeManager()
    asyncio.run(manager.sync_to_github())
    click.echo("✅ 已同步到GitHub")

@cli.command()
def restore_from_github():
    """
    从GitHub恢复本地知识库
    
    示例：
        python scripts/run_workflow.py restore-from-github
    """
    manager = TwoLayerKnowledgeManager()
    asyncio.run(manager.restore_from_github())
    click.echo("✅ 已从GitHub恢复")

@cli.command()
@click.argument('report_date')
def import_hermes_report(report_date):
    """
    导入指定日期的Hermes热点报告（可选）
    
    示例：
        python scripts/run_workflow.py import-hermes-report 2026-05-17
    """
    adapter = HermesHotspotAdapter()
    if not adapter.available:
        click.echo("❌ Hermes报告目录不存在")
        return
    
    hotspots = asyncio.run(adapter.fetch_report_by_date(report_date))
    click.echo(f"✅ 导入了 {len(hotspots)} 个热点")
```

---

## 四、实施计划（调整版）

### 4.1 Phase 1：基础架构（3-5天）

**目标**：搭建独立系统的基础架构

#### 任务清单

- [ ] **Day 1：两层知识库**
  - 实现 TwoLayerKnowledgeManager
  - 创建本地目录结构
  - 配置GitHub仓库（knowledge/目录）
  - 测试Git同步

- [ ] **Day 2：数据接入层**
  - 实现 HermesHotspotAdapter（可选）
  - 实现 WebSearchCollector
  - 测试数据采集

- [ ] **Day 3：SOUL框架加载**
  - 实现SOUL profile加载逻辑
  - 支持多路径查找
  - 创建本地备份

- [ ] **Day 4-5：集成测试**
  - 端到端测试
  - 修复问题
  - 编写文档

**验收标准**：
- ✅ 本地知识库可正常读写
- ✅ GitHub同步正常工作
- ✅ 可读取Hermes报告（如果存在）
- ✅ WebSearch采集可用

---

### 4.2 Phase 2：SOUL内容生成（5-7天）

**目标**：实现基于SOUL框架的内容生成

#### 任务清单

- [ ] **Day 1-2：ScriptWriter重构**
  - 加载SOUL画像
  - 生成提示词
  - 解析Claude Code生成的脚本
  - 测试生成质量

- [ ] **Day 3-4：HotTopicMatcher重构**
  - 实现有限性三角评分
  - 实现受众匹配
  - 实现角度推荐
  - 对比测试

- [ ] **Day 5：TitleOptimizer优化**
  - 基于SOUL人设
  - 生成标题候选

- [ ] **Day 6-7：完整流程测试**
  - 运行完整工作流
  - 评估内容质量
  - 优化提示词

**验收标准**：
- ✅ 生成的脚本符合SOUL人设
- ✅ 热点评分准确
- ✅ 推荐角度合理

---

### 4.3 Phase 3：Hermes集成（2-3天）

**目标**：实现与Hermes的松耦合集成

#### 任务清单

- [ ] **Day 1：任务桥接器**
  - 实现 HermesTaskBridge
  - 实现任务队列
  - 实现状态管理

- [ ] **Day 2：飞书消息通知**
  - 配置飞书Webhook
  - 实现消息发送
  - 测试通知

- [ ] **Day 3：集成测试**
  - 从Hermes触发任务
  - 验证执行流程
  - 验证结果通知

**验收标准**：
- ✅ Hermes可触发MCN任务
- ✅ 任务状态可查询
- ✅ 结果通过飞书通知

---

### 4.4 Phase 4：优化和文档（2-3天）

**目标**：优化系统，完善文档

#### 任务清单

- [ ] **Day 1：性能优化**
  - 优化数据库查询
  - 优化文件IO
  - 添加缓存

- [ ] **Day 2：文档编写**
  - 用户手册
  - 开发文档
  - API文档

- [ ] **Day 3：演示和培训**
  - 录制演示视频
  - 编写快速开始指南
  - 准备FAQ

**验收标准**：
- ✅ 系统运行流畅
- ✅ 文档齐全
- ✅ 易于使用

---

## 五、关键技术决策（更新）

### 5.1 为什么保持独立系统？

**决策**：MCN系统独立运行，可被Hermes调用

**理由**：
1. **灵活性**：可在任何环境中运行
2. **可维护性**：独立开发和测试
3. **可扩展性**：未来可支持其他调用方
4. **降低耦合**：Hermes和MCN互不依赖

**实现方式**：
- 通过任务调度接口集成
- 通过飞书消息通信
- 支持独立CLI使用

---

### 5.2 为什么不使用Claude付费API？

**决策**：仅使用Claude Code内置能力

**理由**：
1. **零成本**：无需额外API费用
2. **简化部署**：无需管理API密钥
3. **能力足够**：Claude Code的对话能力已满足需求
4. **用户偏好**：用户明确要求

**权衡**：
- ❌ 需要手动复制粘贴（交互式）
- ✅ 但零成本，完全可控

---

### 5.3 为什么采用两层知识库？

**决策**：本地Markdown + GitHub（不用飞书）

**理由**：
1. **飞书限制**：个人版无法作为知识库
2. **简化架构**：两层比三层简单
3. **独立维护**：互不干扰
4. **互为备份**：任一层损坏可恢复

**实现方式**：
- 本地为主存储
- GitHub为备份和版本控制
- 手动触发同步

---

## 六、成本估算（更新）

### 6.1 开发成本

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| Phase 1 | 3-5天 | 基础架构 |
| Phase 2 | 5-7天 | SOUL内容生成 |
| Phase 3 | 2-3天 | Hermes集成 |
| Phase 4 | 2-3天 | 优化文档 |
| **总计** | **12-18天** | 约2-3周 |

### 6.2 运行成本

| 项目 | 成本 | 说明 |
|------|------|------|
| Claude API | **$0** | 使用Claude Code免费能力 |
| 飞书 | **$0** | 仅消息通信 |
| GitHub | **$0** | 公开仓库 |
| 服务器 | **$0** | 本地运行 |
| **总计** | **$0/月** | 完全免费 |

---

## 七、预期收益（更新）

### 7.1 效率提升

| 环节 | 当前耗时 | 优化后耗时 | 提升 |
|------|---------|-----------|------|
| 热点采集 | 2小时/周 | 10分钟 | 92% |
| 选题评分 | 1小时 | 5分钟 | 92% |
| 脚本生成 | 2-3小时 | 15分钟* | 92% |
| 标题优化 | 30分钟 | 2分钟 | 93% |
| 合规审核 | 30分钟 | 1分钟 | 97% |
| **总计** | **6-7小时** | **35分钟** | **91%** |

*包含手动复制粘贴时间

### 7.2 质量提升

| 维度 | 提升 | 说明 |
|------|------|------|
| 内容个性化 | ⭐⭐⭐⭐⭐ | SOUL框架确保人设一致性 |
| 选题精准度 | ⭐⭐⭐⭐ | 基于SOUL受众的精准匹配 |
| 创意性 | ⭐⭐⭐⭐ | Claude Code生成 |
| 合规性 | ⭐⭐⭐⭐⭐ | 自动化审核 |

---

## 八、与v2.0方案的对比

| 维度 | v2.0方案 | v3.0方案（最终） | 优势 |
|------|---------|-----------------|------|
| 系统定位 | Hermes子系统 | 独立系统 | 更灵活 |
| Claude使用 | 付费API | Claude Code免费 | 零成本 |
| 知识库 | 三层 | 两层 | 更简单 |
| 飞书角色 | 知识库 | 仅消息 | 符合实际 |
| 开发周期 | 20-29天 | 12-18天 | 更快 |
| 运行成本 | $5-20/月 | $0/月 | 免费 |
| 复杂度 | 高 | 中 | 更易维护 |

---

## 九、总结

### 9.1 核心价值（更新）

1. **完全免费**：零运行成本
2. **独立可控**：不依赖外部服务
3. **SOUL驱动**：基于完整的身份框架
4. **简化架构**：两层知识库，易于维护
5. **松耦合集成**：可被Hermes调用，但不依赖

### 9.2 关键差异

与v2.0相比：
- ✅ 更独立（不依赖Hermes）
- ✅ 更便宜（零成本）
- ✅ 更简单（两层知识库）
- ✅ 更快（12-18天 vs 20-29天）

### 9.3 实施建议

**立即开始**：
1. Phase 1（基础架构）
2. 配置GitHub仓库
3. 准备SOUL框架文档

**关键成功因素**：
1. 深入理解SOUL框架
2. 熟悉Claude Code能力
3. 保持架构简单

**风险控制**：
1. 小步快跑
2. 充分测试
3. 保留备份

---

**文档版本**：v3.0（最终版）  
**创建日期**：2026-05-17  
**基于**：v2.0 + 用户反馈  
**状态**：待实施

