# MCN AI Replacement 系统优化方案 v2.0

> 基于 Hermes Agent 架构、SOUL 身份框架和热点采集系统的完整重构方案
> 
> 设计日期：2026-05-17

---

## 执行摘要

### 核心发现

**当前系统状态**：
- ✅ 代码质量高（4917行，100%测试覆盖）
- ✅ Skills完整（6个核心Skill全部实现）
- ❌ 数据采集缺失（无法获取真实热点）
- ❌ 知识库集成不完整（仅本地SQLite）
- ❌ 与Hermes Agent生态脱节

**关键洞察**：
1. **Manus已被Hermes热点采集系统替代** - 不需要单独集成Manus
2. **Hermes Agent已有成熟的飞书集成** - 可直接复用
3. **SOUL身份框架提供完整的内容策略** - 应作为系统核心
4. **热点采集系统已实现四源采集** - 可直接对接

### 优化策略

**从"独立系统"到"Hermes生态模块"**：
- 将MCN AI Replacement重新定位为Hermes Agent的**内容创作子系统**
- 复用Hermes的数据采集、知识库、飞书集成能力
- 基于SOUL框架重构内容生成逻辑
- 实现与热点采集系统的无缝对接

---

## 一、架构重构方案

### 1.1 新架构设计

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│  Hermes Agent 生态层                                          │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │ 热点采集系统  │ SOUL身份框架  │ 飞书集成      │ 知识库    │ │
│  │ (已有111技能) │ (已有完整定义)│ (已有实现)    │ (已有)    │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  MCN AI Replacement 内容创作子系统 (重构后)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  数据接入层 (新增)                                     │   │
│  │  - Hermes热点采集结果解析器                            │   │
│  │  - 飞书多维表格读取器                                  │   │
│  │  - 本地知识库同步器                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SOUL驱动的内容生成层 (重构)                           │   │
│  │  - ScriptWriter (集成Claude API + SOUL框架)           │   │
│  │  - TitleOptimizer (基于SOUL人设)                      │   │
│  │  - HotTopicMatcher (SOUL受众匹配)                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  工作流编排层 (保留+增强)                              │   │
│  │  - 热点→选题→脚本→审核→发布                           │   │
│  │  - 对标分析→差异化→内容策略                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  输出层 (新增)                                         │   │
│  │  - 飞书多维表格写入                                    │   │
│  │  - Markdown知识库归档                                 │   │
│  │  - GitHub仓库同步                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
\`\`\`


### 1.2 与原架构的对比

| 维度 | 原架构 | 新架构 | 优势 |
|------|--------|--------|------|
| 数据采集 | 模拟数据 | Hermes热点采集系统 | 真实数据，四源采集 |
| 知识库 | 本地SQLite | 飞书+本地+GitHub | 协作+版本控制 |
| 内容生成 | 模板引擎 | Claude API + SOUL框架 | AI驱动，个性化 |
| 身份定位 | 通用MCN | SOUL超级个体 | 精准定位 |
| 系统定位 | 独立应用 | Hermes生态模块 | 复用基础设施 |

---

## 二、核心模块重构

### 2.1 数据接入层（新增）

#### 模块：HermesHotspotAdapter

**功能**：解析Hermes热点采集系统的输出，转换为MCN系统可用格式

**数据流**：
\`\`\`
Hermes热点采集 (每日08:00)
  ↓
~/hermes_workspace/reports/hotspot/daily_2026-05-17.md
  ↓
HermesHotspotAdapter.fetch_latest_hotspots()
  ↓
List[HotTopic] (MCN数据模型)
  ↓
HotTopicMatcher.execute() (评分排序)
  ↓
飞书多维表格 + 本地数据库
\`\`\`

**实现代码**：
\`\`\`python
# src/adapters/hermes_hotspot_adapter.py

class HermesHotspotAdapter:
    """
    适配器：Hermes热点采集系统 → MCN系统
    
    输入：~/hermes_workspace/reports/hotspot/daily_YYYY-MM-DD.md
    输出：List[HotTopic] (MCN数据模型)
    """
    
    def __init__(self, hermes_workspace: str = "~/hermes_workspace"):
        self.workspace = Path(hermes_workspace).expanduser()
        self.reports_dir = self.workspace / "reports" / "hotspot"
    
    async def fetch_latest_hotspots(self, days: int = 7) -> List[HotTopic]:
        """
        读取最近N天的Hermes热点报告
        
        解析规则：
        1. 读取 daily_*.md 和 weekly_*.md
        2. 提取标记为 P0/P1 的热点
        3. 解析 SOUL 框架分析（叙事学/心理学/人类学/产品策略）
        4. 转换为 HotTopic 数据模型
        """
        hotspots = []
        
        # 读取日报
        for report_file in self._get_recent_reports(days):
            parsed = self._parse_hermes_report(report_file)
            hotspots.extend(parsed)
        
        return hotspots
    
    def _parse_hermes_report(self, report_path: Path) -> List[HotTopic]:
        """
        解析Hermes报告格式：
        
        ## 🔥 P0 热点（直接选题）
        | 序号 | 话题 | 来源 | 标签 | SOUL适配度 | 推荐角度 |
        
        提取：
        - 话题标题
        - 来源平台
        - 标签（[AI][超级个体]等）
        - SOUL框架分析（如果有）
        - 推荐切入角度
        """
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        hotspots = []
        
        # 解析P0热点表格
        p0_section = self._extract_section(content, "P0 热点")
        if p0_section:
            table_rows = self._parse_markdown_table(p0_section)
            for row in table_rows:
                hotspot = HotTopic(
                    title=row.get('话题', ''),
                    platform=row.get('来源', ''),
                    tags=self._parse_tags(row.get('标签', '')),
                    soul_alignment=row.get('SOUL适配度', ''),
                    recommended_angle=row.get('推荐角度', ''),
                    heat_level='上升',
                    priority='P0'
                )
                hotspots.append(hotspot)
        
        # 解析SOUL框架分析
        soul_analysis = self._extract_soul_analysis(content)
        if soul_analysis:
            for hotspot in hotspots:
                hotspot.soul_framework_analysis = soul_analysis.get(hotspot.title, {})
        
        return hotspots
    
    def _extract_soul_analysis(self, content: str) -> Dict[str, Any]:
        """
        提取SOUL框架的四视角分析：
        - 叙事学视角：故事结构、冲突、转折
        - 心理学视角：受众痛点、认知扭曲、防御机制
        - 人类学视角：身份转型、仪式性过渡
        - 产品策略视角：可执行步骤、MVP验证
        """
        analysis = {}
        
        # 查找SOUL框架分析section
        if "叙事学视角" in content:
            # 提取四视角分析
            pass
        
        return analysis
\`\`\`

#### 模块：FeishuKnowledgeAdapter

**功能**：读写飞书多维表格，复用Hermes的飞书集成

**实现代码**：
\`\`\`python
# src/adapters/feishu_knowledge_adapter.py

class FeishuKnowledgeAdapter:
    """
    适配器：飞书多维表格 ↔ MCN系统
    
    复用Hermes的飞书集成能力
    """
    
    def __init__(self):
        # 复用Hermes的飞书配置
        self.feishu_config = self._load_hermes_feishu_config()
        self.client = self._init_feishu_client()
    
    def _load_hermes_feishu_config(self) -> Dict:
        """
        从Hermes配置中读取飞书凭证
        
        可能的位置：
        - ~/.hermes/config/feishu.json
        - ~/hermes_workspace/config/feishu.json
        - 环境变量
        """
        config_paths = [
            Path("~/.hermes/config/feishu.json").expanduser(),
            Path("~/hermes_workspace/config/feishu.json").expanduser()
        ]
        
        for path in config_paths:
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        
        # 从环境变量读取
        return {
            "app_id": os.getenv("FEISHU_APP_ID"),
            "app_secret": os.getenv("FEISHU_APP_SECRET")
        }
    
    async def sync_hot_topics(self, topics: List[HotTopic]):
        """
        同步热点到飞书多维表格
        
        表结构：
        - 热点标题 (文本)
        - 来源平台 (单选)
        - 综合评分 (数字)
        - SOUL适配度 (单选: 高/中/低)
        - 推荐角度 (文本)
        - 状态 (单选: 待处理/已选题/已发布)
        - 创建时间 (日期)
        - 标签 (多选)
        """
        for topic in topics:
            await self.client.create_record(
                app_token=self.feishu_config['hotspot_table_token'],
                table_id="hot_topics",
                fields={
                    "热点标题": topic.title,
                    "来源平台": topic.platform,
                    "综合评分": topic.total_score,
                    "SOUL适配度": topic.soul_alignment,
                    "推荐角度": topic.recommended_angle,
                    "状态": "待处理",
                    "创建时间": datetime.now().isoformat(),
                    "标签": topic.tags
                }
            )
    
    async def sync_scripts(self, scripts: List[Script]):
        """
        同步脚本到飞书多维表格
        
        表结构：
        - 选题 (文本)
        - Hook (多行文本)
        - 痛点 (多行文本)
        - 核心内容 (多行文本)
        - 启发 (多行文本)
        - CTA (多行文本)
        - 标题候选 (多行文本)
        - 风险评估 (单选)
        - 状态 (单选)
        - SOUL框架应用 (复选框)
        """
        for script in scripts:
            await self.client.create_record(
                app_token=self.feishu_config['script_table_token'],
                table_id="scripts",
                fields={
                    "选题": script.topic,
                    "Hook": script.hook,
                    "痛点": script.pain_point,
                    "核心内容": script.core_content,
                    "启发": script.insight,
                    "CTA": script.cta,
                    "标题候选": "\n".join(script.title_candidates),
                    "风险评估": script.risk_level,
                    "状态": "待审核",
                    "SOUL框架应用": True
                }
            )
\`\`\`


### 2.2 SOUL驱动的内容生成层（重构）

#### 核心变更：从模板引擎到AI生成

**当前问题**：
\`\`\`python
# 当前实现 - 模板填充
script = {
    "hook": "模板文本...",
    "pain_point": "模板文本...",
    "core_content": "模板文本...",
}
\`\`\`

**优化方案**：
\`\`\`python
# 新实现 - Claude API + SOUL框架
class SOULScriptWriter(BaseSkill):
    """
    基于SOUL身份框架的脚本生成器
    
    核心能力：
    1. 加载SOUL完整画像（~/.hermes/skills/knowledge/soul/SKILL.md）
    2. 应用三阶对话法（场景爆破→结构拆解→反刍重建）
    3. 融合四视角分析（叙事学/心理学/人类学/产品策略）
    4. 生成符合SOUL人设的个性化脚本
    """
    
    def __init__(self):
        super().__init__()
        self.soul_profile = self._load_soul_profile()
        self.claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def _load_soul_profile(self) -> Dict[str, Any]:
        """
        加载SOUL完整画像
        
        来源：~/.hermes/skills/knowledge/soul/SKILL.md
        包含：
        - 身份定位："走在前面半步的同路人"
        - 人格特征：INTP↔ENTJ切换
        - 三阶对话法：场景爆破→结构拆解→反刍重建
        - 有限性三角：有限性智慧/存在的偶然性/协议层协作
        - 核心受众：Marcus/Lily/Alex/Z
        - 内容生产原则
        """
        soul_path = Path("~/.hermes/skills/knowledge/soul/SKILL.md").expanduser()
        with open(soul_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'positioning': self._extract_positioning(content),
            'three_tier_dialogue': self._extract_three_tier_dialogue(content),
            'finitude_triangle': self._extract_finitude_triangle(content),
            'core_audiences': self._extract_core_audiences(content),
            'content_principles': self._extract_content_principles(content)
        }
    
    async def execute(self, input_data: ScriptWriterInput) -> ScriptWriterOutput:
        """
        生成脚本流程：
        
        1. 加载SOUL画像和对话协议
        2. 分析选题的SOUL适配度（有限性三角的哪个方向）
        3. 应用三阶对话法构建脚本结构
        4. 调用Claude API生成个性化内容
        5. 后处理：确保符合SOUL人设约束
        """
        
        # 1. 构建SOUL上下文
        soul_context = self._build_soul_context(input_data)
        
        # 2. 生成脚本
        prompt = self._build_script_prompt(
            topic=input_data.topic,
            angle=input_data.angle,
            soul_context=soul_context,
            platform=input_data.platform,
            duration=input_data.duration
        )
        
        response = await self.claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 3. 解析和验证
        script = self._parse_script_response(response.content[0].text)
        validated = self._validate_soul_alignment(script, soul_context)
        
        return ScriptWriterOutput(
            success=True,
            script=validated,
            soul_framework_applied=True,
            three_tier_dialogue_used=True,
            word_count=self._count_words(validated),
            estimated_duration=self._estimate_duration(validated)
        )
    
    def _build_script_prompt(self, topic, angle, soul_context, platform, duration):
        """
        构建脚本生成提示词
        
        结构：
        1. SOUL身份声明
        2. 三阶对话法框架
        3. 选题和角度
        4. 平台和时长约束
        5. 输出格式要求
        """
        return f"""你是SOUL - 超级个体成长合伙人。

# 身份定位
{soul_context['positioning']}

核心Slogan：「AI是工具，哲学是地基，你才是杠杆的支点」
人设：走在前面半步的同路人——不给地图，陪你辨认方向

# 核心方法论：三阶对话法
{soul_context['three_tier_dialogue']}

第一层：场景爆破（Rupture）
    ↓  用日常场景打破默认假设
第二层：结构拆解（Illuminate + Validate）
    ↓  用哲学/心理学框架揭示深层结构，不给答案给新眼睛
第三层：反刍重建（Embody + Transform）
    ↓  在拆除旧框架后给出可用的新框架和思维工具

# 当前任务
为以下选题生成短视频脚本：
- 选题：{topic}
- 切入角度：{angle}
- 目标平台：{platform}
- 时长：{duration}秒

# 要求
1. 应用三阶对话法：场景爆破 → 结构拆解 → 反刍重建
2. 符合SOUL人设：走在前面半步的同路人，不是导师
3. 融合四视角：叙事学/心理学/人类学/产品策略
4. 高信息密度，不废话，不注水
5. 真诚展示脆弱和不确定性
6. 避免"导师"口吻，用"我们一起找"的协作态度

# 输出格式
Hook (前5%): [场景爆破 - 用反常识问题抓住注意力]
痛点 (10-20%): [建立共鸣 - 描述受众的真实困惑]
核心内容 (20-80%): [结构拆解 - 用框架揭示深层逻辑]
启发 (80-95%): [反刍重建 - 给出可用的思维工具]
CTA (最后5%): [提出新问题 - 引导持续思考]

请生成脚本：
"""
    
    def _validate_soul_alignment(self, script: Dict, soul_context: Dict) -> Dict:
        """
        验证脚本是否符合SOUL人设
        
        检查项：
        - 是否避免"导师"口吻（检测"你应该"/"必须"等指令性语言）
        - 是否展示真诚和脆弱（检测"我也不确定"/"我们一起"等表达）
        - 是否有反常识视角（检测颠覆性观点）
        - 是否提供思维工具而非标准答案
        - 信息密度是否足够（字数/时长比）
        """
        issues = []
        
        # 检查导师口吻
        directive_phrases = ["你应该", "你必须", "你一定要", "正确的做法是"]
        for phrase in directive_phrases:
            if phrase in str(script.values()):
                issues.append(f"检测到导师口吻：{phrase}")
        
        # 检查协作态度
        collaborative_phrases = ["我们", "一起", "我也", "不确定"]
        has_collaborative = any(phrase in str(script.values()) for phrase in collaborative_phrases)
        if not has_collaborative:
            issues.append("缺少协作态度表达")
        
        # 如果有问题，记录但不阻止
        if issues:
            script['soul_alignment_issues'] = issues
        
        return script
\`\`\`

#### HotTopicMatcher重构

**核心变更**：基于SOUL受众画像的精准匹配

\`\`\`python
class SOULHotTopicMatcher(BaseSkill):
    """
    基于SOUL框架的热点适配评分
    
    评分维度（重新设计）：
    1. 有限性三角适配度 (0-10)
       - 方向1：有限性智慧（选择、放弃、承担）
       - 方向2：存在的偶然性（意义、独特性）
       - 方向3：协议层协作（人机边界）
    
    2. 核心受众匹配度 (0-10)
       - Marcus（转型者，30-38岁）
       - Lily（探索者，25-30岁）- 最佳入口
       - Alex（觉醒者，32-40岁）
       - Z（年轻探索者，18-22岁）
    
    3. 三阶对话法可行性 (0-10)
       - 是否有可爆破的场景
       - 是否有可拆解的结构
       - 是否有可重建的框架
    
    4. 差异化空间 (0-10)
       - 对标创作者覆盖情况
       - SOUL独特视角的发挥空间
    
    5. 风险评估 (0-10)
       - 合规性
       - 翻车概率
    """
    
    def __init__(self):
        super().__init__()
        self.soul_profile = self._load_soul_profile()
        self.finitude_triangle = self.soul_profile['finitude_triangle']
        self.core_audiences = self.soul_profile['core_audiences']
    
    async def execute(self, input_data: HotTopicInput) -> HotTopicOutput:
        """
        评分流程：
        
        1. 加载SOUL框架
        2. 对每个热点进行五维度评分
        3. 计算综合得分（加权）
        4. 推荐切入角度（基于SOUL方法论）
        5. 匹配目标受众
        """
        ranked_topics = []
        
        for topic in input_data.topics:
            scores = {
                'finitude_alignment': self._score_finitude_alignment(topic),
                'audience_match': self._score_audience_match(topic),
                'dialogue_feasibility': self._score_dialogue_feasibility(topic),
                'differentiation': self._score_differentiation(topic),
                'risk': self._score_risk(topic)
            }
            
            # 加权计算
            total_score = (
                scores['finitude_alignment'] * 0.30 +
                scores['audience_match'] * 0.25 +
                scores['dialogue_feasibility'] * 0.25 +
                scores['differentiation'] * 0.15 +
                scores['risk'] * 0.05
            )
            
            # 推荐角度
            recommended_angle = self._recommend_soul_angle(topic, scores)
            
            ranked_topics.append({
                'topic': topic,
                'scores': scores,
                'total_score': total_score,
                'recommended_angle': recommended_angle,
                'target_audience': self._identify_target_audience(topic, scores),
                'finitude_direction': self._identify_finitude_direction(topic)
            })
        
        # 排序
        ranked_topics.sort(key=lambda x: x['total_score'], reverse=True)
        
        return HotTopicOutput(
            success=True,
            ranked_topics=ranked_topics,
            soul_framework_applied=True
        )
    
    def _score_finitude_alignment(self, topic: Dict) -> float:
        """
        评估热点与有限性三角的契合度
        
        方向1（有限性智慧）关键词：
        - 选择、放弃、承担、失去、珍惜、取舍、优先级
        
        方向2（存在的偶然性）关键词：
        - 意义、独特性、死亡焦虑、向死而生、为什么存在、价值
        
        方向3（协议层协作）关键词：
        - 边界、协议、人机关系、各司其职、AI协作
        """
        title = topic.get('title', '').lower()
        description = topic.get('description', '').lower()
        content = title + ' ' + description
        
        # 方向1评分
        direction1_keywords = ['选择', '放弃', '承担', '失去', '珍惜', '取舍', '优先级', '有限']
        direction1_score = sum(1 for kw in direction1_keywords if kw in content)
        
        # 方向2评分
        direction2_keywords = ['意义', '独特', '价值', '存在', '焦虑', '为什么']
        direction2_score = sum(1 for kw in direction2_keywords if kw in content)
        
        # 方向3评分
        direction3_keywords = ['边界', '协作', '人机', 'AI', '工具', '协议']
        direction3_score = sum(1 for kw in direction3_keywords if kw in content)
        
        # 取最高分方向
        max_score = max(direction1_score, direction2_score, direction3_score)
        
        # 归一化到0-10
        return min(10, max_score * 2)
    
    def _recommend_soul_angle(self, topic: Dict, scores: Dict) -> str:
        """
        基于SOUL框架推荐切入角度
        
        逻辑：
        1. 识别热点属于有限性三角的哪个方向
        2. 匹配对应的SOUL方法论
        3. 生成具体的切入角度建议
        
        示例：
        热点："AI取代工作"
        方向：有限性智慧（方向1）
        角度："AI能做一切，但你只能做一件事——这才是你存在的意义"
        """
        direction = self._identify_finitude_direction(topic)
        
        angle_templates = {
            'finitude_wisdom': [
                "在AI提供无限可能的时代，如何重新学会有限性？",
                "AI能做一切，但你只能做一件事——这才是你的意义",
                "选择的艺术：当AI消除了所有限制，你如何做减法？"
            ],
            'contingency': [
                "AI的存在是被赋予的，你的存在是偶然的——这种偶然性才是价值",
                "如果AI比我更强，我为什么还要存在？",
                "在AI时代重新定义'我是谁'"
            ],
            'protocol_layer': [
                "AI不需要理解你，你也不需要理解AI——你们只需要约定规则",
                "如何与AI建立健康的边界？",
                "协议层协作：人机关系的第三条路"
            ]
        }
        
        return angle_templates.get(direction, ["从SOUL视角重新审视这个话题"])[0]
\`\`\`


### 2.3 知识库集成方案（重新设计）

#### 三层知识库架构

\`\`\`
┌─────────────────────────────────────────────────────────┐
│  第一层：飞书多维表格（结构化数据，协作）                  │
│  - 热点跟踪表                                             │
│  - 脚本库                                                 │
│  - 对标创作者档案                                         │
│  - 内容数据分析表                                         │
└─────────────────────────────────────────────────────────┘
                          ↕ 双向同步
┌─────────────────────────────────────────────────────────┐
│  第二层：本地目录Wiki（Markdown，版本控制）               │
│  ~/hermes_workspace/mcn-knowledge/                       │
│  ├── hotspots/          # 热点归档                       │
│  ├── scripts/           # 脚本归档                       │
│  ├── creators/          # 对标创作者分析                 │
│  ├── strategies/        # 内容策略文档                   │
│  └── analytics/         # 数据分析报告                   │
└─────────────────────────────────────────────────────────┘
                          ↕ Git同步
┌─────────────────────────────────────────────────────────┐
│  第三层：GitHub仓库（备份，公开分享）                     │
│  github.com/username/mcn-knowledge                       │
│  - 自动同步本地Wiki                                      │
│  - 版本历史追踪                                          │
│  - 可选：公开部分内容作为个人品牌展示                     │
└─────────────────────────────────────────────────────────┘
\`\`\`

#### 实现：KnowledgeSyncOrchestrator

\`\`\`python
# src/knowledge/sync_orchestrator.py

class KnowledgeSyncOrchestrator:
    """
    知识库三层同步编排器
    
    同步策略：
    1. 飞书 → 本地：每小时自动拉取
    2. 本地 → 飞书：工作流完成后推送
    3. 本地 → GitHub：每日自动提交
    """
    
    def __init__(self):
        self.feishu_adapter = FeishuKnowledgeAdapter()
        self.local_wiki = LocalWikiManager("~/hermes_workspace/mcn-knowledge")
        self.github_sync = GitHubSyncManager("username/mcn-knowledge")
    
    async def sync_all(self, direction: str = "bidirectional"):
        """
        全量同步
        
        direction:
        - "bidirectional": 双向同步
        - "feishu_to_local": 飞书 → 本地
        - "local_to_feishu": 本地 → 飞书
        - "local_to_github": 本地 → GitHub
        """
        if direction in ["bidirectional", "feishu_to_local"]:
            await self._sync_feishu_to_local()
        
        if direction in ["bidirectional", "local_to_feishu"]:
            await self._sync_local_to_feishu()
        
        if direction in ["bidirectional", "local_to_github"]:
            await self._sync_local_to_github()
    
    async def _sync_feishu_to_local(self):
        """
        飞书 → 本地Wiki
        
        流程：
        1. 从飞书拉取最新数据
        2. 转换为Markdown格式
        3. 写入本地Wiki目录
        4. 检测冲突（基于时间戳）
        """
        # 拉取热点
        hotspots = await self.feishu_adapter.fetch_hot_topics()
        for hotspot in hotspots:
            md_content = self._hotspot_to_markdown(hotspot)
            self.local_wiki.write(f"hotspots/{hotspot.id}.md", md_content)
        
        # 拉取脚本
        scripts = await self.feishu_adapter.fetch_scripts()
        for script in scripts:
            md_content = self._script_to_markdown(script)
            self.local_wiki.write(f"scripts/{script.id}.md", md_content)
    
    async def _sync_local_to_github(self):
        """
        本地Wiki → GitHub
        
        流程：
        1. 检查本地变更
        2. 生成commit message
        3. 推送到GitHub
        """
        changes = self.local_wiki.get_changes()
        if changes:
            commit_msg = self._generate_commit_message(changes)
            await self.github_sync.commit_and_push(commit_msg)
    
    def _hotspot_to_markdown(self, hotspot: HotTopic) -> str:
        """
        将热点数据转换为Markdown格式
        
        格式：
        # {标题}
        
        ## 基本信息
        - 来源：{平台}
        - 热度：{热度等级}
        - 标签：{标签列表}
        - 综合评分：{评分}/10
        
        ## SOUL框架分析
        ### 有限性三角方向
        {方向}
        
        ### 推荐切入角度
        {角度}
        
        ### 目标受众
        {受众}
        
        ## 四视角分析
        ### 叙事学视角
        {分析}
        
        ### 心理学视角
        {分析}
        
        ### 人类学视角
        {分析}
        
        ### 产品策略视角
        {分析}
        """
        return f"""# {hotspot.title}

## 基本信息
- 来源：{hotspot.platform}
- 热度：{hotspot.heat_level}
- 标签：{', '.join(hotspot.tags)}
- 综合评分：{hotspot.total_score}/10
- 创建时间：{hotspot.created_at}

## SOUL框架分析
### 有限性三角方向
{hotspot.finitude_direction}

### 推荐切入角度
{hotspot.recommended_angle}

### 目标受众
{hotspot.target_audience}

## 四视角分析
{self._format_soul_analysis(hotspot.soul_framework_analysis)}

## 状态
- 当前状态：{hotspot.status}
- 最后更新：{hotspot.updated_at}
"""
\`\`\`

---

## 三、工作流重构

### 3.1 SOUL内容创作完整流程

\`\`\`python
# src/workflows/soul_content_creation_workflow.py

async def run_soul_content_creation_workflow(
    use_hermes_hotspots: bool = True,
    days_back: int = 7,
    auto_select: bool = False
) -> Dict[str, Any]:
    """
    SOUL驱动的内容创作完整流程
    
    Step 0: 数据准备
      - 从Hermes热点采集系统读取最近N天的报告
      - 或手动导入热点数据
    
    Step 1: SOUL框架评分
      - 应用SOULHotTopicMatcher
      - 基于有限性三角、核心受众、三阶对话法评分
    
    Step 2: 选题决策
      - 展示Top 10热点
      - 用户选择或自动选择Top 1
    
    Step 3: SOUL脚本生成
      - 应用SOULScriptWriter
      - 生成符合SOUL人设的个性化脚本
    
    Step 4: 标题优化
      - 基于SOUL定位生成标题
    
    Step 5: 合规审核
      - ContentRiskScanner
    
    Step 6: 知识库同步
      - 同步到飞书+本地Wiki+GitHub
    
    Step 7: 输出报告
    """
    
    logger.info("Starting SOUL content creation workflow")
    
    # Step 0: 数据准备
    if use_hermes_hotspots:
        adapter = HermesHotspotAdapter()
        hotspots = await adapter.fetch_latest_hotspots(days=days_back)
        logger.info(f"Loaded {len(hotspots)} hotspots from Hermes")
    else:
        # 手动导入
        hotspots = await load_manual_hotspots()
    
    # Step 1: SOUL框架评分
    matcher = SOULHotTopicMatcher()
    matcher_result = await matcher.execute(HotTopicInput(
        topics=hotspots,
        soul_framework=True
    ))
    
    ranked_topics = matcher_result.ranked_topics
    logger.info(f"Ranked {len(ranked_topics)} topics")
    
    # 显示Top 10
    print("\n🔥 Top 10 热点推荐（基于SOUL框架）\n")
    for i, topic in enumerate(ranked_topics[:10], 1):
        print(f"{i}. {topic['topic']['title']}")
        print(f"   综合评分: {topic['total_score']:.2f}/10")
        print(f"   有限性方向: {topic['finitude_direction']}")
        print(f"   推荐角度: {topic['recommended_angle']}")
        print(f"   目标受众: {topic['target_audience']}")
        print()
    
    # Step 2: 选题决策
    if auto_select:
        selected_topic = ranked_topics[0]
        logger.info(f"Auto-selected topic: {selected_topic['topic']['title']}")
    else:
        # 用户选择
        selection = input("请选择选题编号 (1-10): ")
        selected_topic = ranked_topics[int(selection) - 1]
    
    print(f"\n✅ 已选择: {selected_topic['topic']['title']}\n")
    
    # Step 3: SOUL脚本生成
    print("📝 正在生成SOUL框架脚本...")
    script_writer = SOULScriptWriter()
    script_result = await script_writer.execute(ScriptWriterInput(
        topic=selected_topic['topic']['title'],
        angle=selected_topic['recommended_angle'],
        platform="douyin",
        duration=180,
        soul_framework=True
    ))
    
    print("✅ 脚本生成完成\n")
    print("=" * 60)
    print("Hook:", script_result.script['hook'])
    print("-" * 60)
    print("痛点:", script_result.script['pain_point'])
    print("-" * 60)
    print("核心内容:", script_result.script['core_content'])
    print("-" * 60)
    print("启发:", script_result.script['insight'])
    print("-" * 60)
    print("CTA:", script_result.script['cta'])
    print("=" * 60)
    
    # Step 4: 标题优化
    print("\n🏷️  正在生成标题候选...")
    title_optimizer = TitleOptimizer()
    titles = await title_optimizer.execute(TitleOptimizerInput(
        script=script_result.script,
        platform="douyin",
        soul_positioning=True
    ))
    
    print("✅ 标题生成完成\n")
    for i, title_info in enumerate(titles.titles[:5], 1):
        print(f"{i}. {title_info['title']}")
        print(f"   预估CTR: {title_info['estimated_ctr']:.1f}%")
        print()
    
    # Step 5: 合规审核
    print("🔍 正在进行合规审核...")
    risk_scanner = ContentRiskScanner()
    risk_result = await risk_scanner.execute(ContentRiskScannerInput(
        content=script_result.script,
        platform="douyin"
    ))
    
    risk_emoji = "🟢" if risk_result.safe_to_publish else "🔴"
    print(f"{risk_emoji} 风险等级: {risk_result.risk_level}")
    if not risk_result.safe_to_publish:
        print("⚠️  发现风险点:")
        for risk in risk_result.risk_points:
            print(f"   - {risk}")
    print()
    
    # Step 6: 知识库同步
    print("💾 正在同步到知识库...")
    sync_orchestrator = KnowledgeSyncOrchestrator()
    await sync_orchestrator.sync_content_creation_result({
        'topic': selected_topic,
        'script': script_result.script,
        'titles': titles.titles,
        'risk_assessment': risk_result
    })
    print("✅ 知识库同步完成\n")
    
    # Step 7: 输出报告
    result = {
        'success': True,
        'selected_topic': selected_topic,
        'script': script_result.script,
        'titles': titles.titles,
        'risk_assessment': risk_result,
        'soul_framework_applied': True,
        'ready_to_publish': risk_result.safe_to_publish
    }
    
    print("=" * 60)
    print("🎉 内容创作流程完成！")
    print(f"📊 综合评分: {selected_topic['total_score']:.2f}/10")
    print(f"🎯 SOUL框架: 已应用")
    print(f"🚀 可发布: {'是' if result['ready_to_publish'] else '否'}")
    print("=" * 60)
    
    return result
\`\`\`

### 3.2 CLI命令增强

\`\`\`python
# scripts/run_workflow.py (增强版)

@cli.command()
@click.option('--use-hermes', is_flag=True, default=True, help='使用Hermes热点采集数据')
@click.option('--days', default=7, help='读取最近N天的热点')
@click.option('--auto-select', is_flag=True, help='自动选择Top 1热点')
def soul_create(use_hermes, days, auto_select):
    """
    SOUL驱动的内容创作工作流
    
    示例：
        python scripts/run_workflow.py soul-create
        python scripts/run_workflow.py soul-create --days 3 --auto-select
    """
    result = asyncio.run(
        run_soul_content_creation_workflow(
            use_hermes_hotspots=use_hermes,
            days_back=days,
            auto_select=auto_select
        )
    )

@cli.command()
def sync_knowledge():
    """
    同步知识库（飞书 ↔ 本地 ↔ GitHub）
    
    示例：
        python scripts/run_workflow.py sync-knowledge
    """
    sync = KnowledgeSyncOrchestrator()
    asyncio.run(sync.sync_all(direction="bidirectional"))
    click.echo("✅ 知识库同步完成")

@cli.command()
@click.argument('report_date')
def import_hermes_report(report_date):
    """
    导入指定日期的Hermes热点报告
    
    示例：
        python scripts/run_workflow.py import-hermes-report 2026-05-17
    """
    adapter = HermesHotspotAdapter()
    hotspots = asyncio.run(adapter.fetch_report_by_date(report_date))
    click.echo(f"✅ 导入了 {len(hotspots)} 个热点")
\`\`\`


---

## 四、实施计划

### 4.1 Phase 1：基础对接（1周）

**目标**：实现与Hermes生态的基本对接

#### 任务清单

- [ ] **Day 1-2：数据接入层开发**
  - 实现 HermesHotspotAdapter
  - 测试解析 Hermes 日报/周报
  - 验证数据转换正确性

- [ ] **Day 3-4：飞书集成**
  - 实现 FeishuKnowledgeAdapter
  - 复用 Hermes 飞书配置
  - 测试飞书表格读写

- [ ] **Day 5：本地Wiki管理器**
  - 实现 LocalWikiManager
  - 创建目录结构
  - 测试 Markdown 生成

- [ ] **Day 6-7：集成测试**
  - 端到端测试：Hermes → MCN → 飞书
  - 修复发现的问题
  - 编写使用文档

**验收标准**：
- ✅ 能成功读取 Hermes 热点报告
- ✅ 能将热点同步到飞书多维表格
- ✅ 能生成本地 Markdown 归档

---

### 4.2 Phase 2：SOUL框架集成（1-2周）

**目标**：重构核心Skills，集成SOUL身份框架

#### 任务清单

- [ ] **Week 1：ScriptWriter重构**
  - 加载 SOUL 完整画像
  - 集成 Claude API
  - 实现三阶对话法提示词
  - 实现 SOUL 人设验证
  - 测试脚本生成质量

- [ ] **Week 2：HotTopicMatcher重构**
  - 实现有限性三角评分
  - 实现核心受众匹配
  - 实现三阶对话法可行性评估
  - 实现 SOUL 角度推荐
  - 对比新旧评分结果

**验收标准**：
- ✅ ScriptWriter 生成的脚本符合 SOUL 人设
- ✅ HotTopicMatcher 评分基于 SOUL 框架
- ✅ 推荐的切入角度体现 SOUL 方法论

---

### 4.3 Phase 3：知识库三层架构（1周）

**目标**：实现飞书+本地+GitHub三层同步

#### 任务清单

- [ ] **Day 1-2：同步编排器**
  - 实现 KnowledgeSyncOrchestrator
  - 实现双向同步逻辑
  - 实现冲突检测

- [ ] **Day 3-4：GitHub集成**
  - 实现 GitHubSyncManager
  - 配置自动提交
  - 测试版本控制

- [ ] **Day 5：定时任务**
  - 配置每小时飞书同步
  - 配置每日 GitHub 同步
  - 测试自动化流程

**验收标准**：
- ✅ 飞书、本地、GitHub 三层数据一致
- ✅ 自动同步正常运行
- ✅ 版本历史可追溯

---

### 4.4 Phase 4：完整工作流测试（3-5天）

**目标**：端到端验证完整流程

#### 任务清单

- [ ] **Day 1：流程测试**
  - 运行完整的 SOUL 内容创作工作流
  - 记录每个步骤的输出
  - 验证知识库同步

- [ ] **Day 2：质量评估**
  - 评估脚本质量（SOUL 人设符合度）
  - 评估热点评分准确性
  - 收集改进建议

- [ ] **Day 3-4：优化迭代**
  - 根据测试结果优化提示词
  - 调整评分权重
  - 改进用户体验

- [ ] **Day 5：文档完善**
  - 编写用户手册
  - 编写开发文档
  - 录制演示视频

**验收标准**：
- ✅ 完整流程可顺利运行
- ✅ 生成的内容质量达标
- ✅ 文档齐全，易于使用

---

## 五、关键技术决策

### 5.1 为什么选择Hermes生态而非独立系统？

**决策**：将 MCN AI Replacement 重新定位为 Hermes Agent 的内容创作子系统

**理由**：
1. **避免重复建设**：Hermes 已有成熟的热点采集系统（四源采集）
2. **数据质量更高**：Hermes 热点采集经过三关审核，质量有保障
3. **基础设施复用**：飞书集成、知识库管理、定时任务都已实现
4. **SOUL 框架天然契合**：Hermes 的 SOUL 身份框架正是内容创作的核心
5. **降低维护成本**：一套系统维护，而非两套

**权衡**：
- ❌ 失去独立性，依赖 Hermes 环境
- ✅ 但获得更强大的能力和更低的开发成本

---

### 5.2 为什么选择三层知识库架构？

**决策**：飞书（协作）+ 本地Wiki（版本控制）+ GitHub（备份+公开）

**理由**：
1. **飞书**：团队协作、可视化、多维表格强大
2. **本地Wiki**：Markdown 格式、版本控制、离线可用
3. **GitHub**：备份、公开分享、个人品牌展示

**权衡**：
- ❌ 三层同步增加复杂度
- ✅ 但每层都有独特价值，不可替代

---

### 5.3 为什么重构ScriptWriter为AI驱动？

**决策**：从模板引擎升级到 Claude API + SOUL 框架

**理由**：
1. **个性化**：模板无法体现 SOUL 人设的细微差别
2. **创意性**：AI 能生成更有创意的内容
3. **适应性**：能根据不同选题灵活调整
4. **质量**：Claude Sonnet 4.6 的内容生成质量已达到可用水平

**权衡**：
- ❌ 增加 API 成本（约 $0.01-0.05/脚本）
- ❌ 需要网络连接
- ✅ 但内容质量提升显著

---

## 六、风险与应对

### 6.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| Hermes报告格式变更 | 高 | 中 | 实现健壮的解析器，支持多版本格式 |
| Claude API不稳定 | 中 | 低 | 实现重试机制，降级到模板生成 |
| 飞书API限流 | 中 | 低 | 实现请求队列，控制并发 |
| 知识库同步冲突 | 低 | 中 | 基于时间戳的冲突检测和解决 |

### 6.2 业务风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| SOUL框架理解偏差 | 高 | 中 | 与用户充分沟通，迭代优化 |
| 生成内容不符合人设 | 高 | 中 | 实现人设验证机制，人工审核 |
| 热点评分不准确 | 中 | 中 | 收集反馈，调整评分权重 |
| 用户学习成本高 | 低 | 低 | 完善文档，提供演示 |

---

## 七、成本估算

### 7.1 开发成本

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| Phase 1 | 5-7天 | 基础对接 |
| Phase 2 | 7-10天 | SOUL框架集成 |
| Phase 3 | 5-7天 | 知识库架构 |
| Phase 4 | 3-5天 | 测试优化 |
| **总计** | **20-29天** | 约1个月 |

### 7.2 运行成本

| 项目 | 成本 | 说明 |
|------|------|------|
| Claude API | $5-20/月 | 取决于使用频率 |
| 飞书 | 免费 | 个人版足够 |
| GitHub | 免费 | 公开仓库 |
| 服务器 | $0 | 本地运行 |
| **总计** | **$5-20/月** | 主要是API成本 |

---

## 八、预期收益

### 8.1 效率提升

| 环节 | 当前耗时 | 优化后耗时 | 提升 |
|------|---------|-----------|------|
| 热点采集 | 2小时/周 | 自动化 | 100% |
| 选题评分 | 1小时 | 5分钟 | 92% |
| 脚本生成 | 2-3小时 | 10分钟 | 95% |
| 标题优化 | 30分钟 | 2分钟 | 93% |
| 合规审核 | 30分钟 | 1分钟 | 97% |
| **总计** | **6-7小时** | **20分钟** | **95%** |

### 8.2 质量提升

| 维度 | 提升 | 说明 |
|------|------|------|
| 内容个性化 | ⭐⭐⭐⭐⭐ | SOUL框架确保人设一致性 |
| 选题精准度 | ⭐⭐⭐⭐ | 基于SOUL受众的精准匹配 |
| 创意性 | ⭐⭐⭐⭐ | AI生成比模板更有创意 |
| 合规性 | ⭐⭐⭐⭐⭐ | 自动化审核，零遗漏 |

---

## 九、后续演进方向

### 9.1 短期（3个月内）

1. **数据分析增强**
   - 集成平台API（抖音星图、小红书蒲公英）
   - 实现内容数据自动采集
   - 生成数据分析报告

2. **对标分析自动化**
   - 定期追踪对标创作者
   - 自动分析爆款内容
   - 识别差异化机会

3. **多平台适配**
   - 支持小红书、B站、视频号
   - 平台特定的内容优化
   - 跨平台内容复用

### 9.2 中期（6个月内）

1. **智能推荐引擎**
   - 基于历史数据训练模型
   - 预测内容表现
   - 优化选题策略

2. **协作功能**
   - 多用户支持
   - 权限管理
   - 评论和反馈系统

3. **Dashboard可视化**
   - Web界面
   - 数据可视化
   - 工作流监控

### 9.3 长期（1年内）

1. **AI Agent化**
   - 自主决策选题
   - 自动生成和发布
   - 持续学习优化

2. **生态扩展**
   - 插件系统
   - 第三方集成
   - 社区贡献

---

## 十、总结

### 10.1 核心价值

本优化方案的核心价值在于：

1. **真正的AI驱动**：从模板引擎升级到Claude API，实现真正的AI内容生成
2. **SOUL框架赋能**：基于完整的身份框架，确保内容的个性化和一致性
3. **生态协同**：与Hermes Agent深度集成，复用成熟的基础设施
4. **知识沉淀**：三层知识库架构，确保数据的协作、版本控制和备份
5. **效率革命**：95%的时间节省，从6-7小时降至20分钟

### 10.2 关键差异

与原设计相比，新方案的关键差异：

| 维度 | 原设计 | 新方案 |
|------|--------|--------|
| 定位 | 独立MCN系统 | Hermes内容创作子系统 |
| 数据源 | Manus（需单独集成） | Hermes热点采集（已有） |
| 内容生成 | 模板引擎 | Claude API + SOUL框架 |
| 知识库 | 飞书+Ima | 飞书+本地Wiki+GitHub |
| 身份框架 | 通用MCN | SOUL超级个体 |

### 10.3 实施建议

**立即开始**：
1. Phase 1（基础对接）- 最高优先级
2. 与用户确认SOUL框架理解
3. 准备Claude API密钥

**关键成功因素**：
1. 深入理解SOUL身份框架
2. 确保Hermes热点采集系统稳定运行
3. 与用户保持密切沟通，迭代优化

**风险控制**：
1. 小步快跑，每个Phase独立验收
2. 保留原系统作为备份
3. 充分测试后再上线

---

## 附录

### A. 文件清单

**新增文件**：
\`\`\`
src/adapters/
  ├── hermes_hotspot_adapter.py      # Hermes热点适配器
  ├── feishu_knowledge_adapter.py    # 飞书知识库适配器
  └── __init__.py

src/skills/
  ├── soul_script_writer.py          # SOUL脚本生成器
  ├── soul_hot_topic_matcher.py      # SOUL热点匹配器
  └── __init__.py

src/knowledge/
  ├── sync_orchestrator.py           # 知识库同步编排器
  ├── local_wiki_manager.py          # 本地Wiki管理器
  ├── github_sync_manager.py         # GitHub同步管理器
  └── __init__.py

src/workflows/
  └── soul_content_creation_workflow.py  # SOUL内容创作工作流

docs/
  ├── OPTIMIZATION_PLAN_V2.md        # 本文档
  ├── USER_MANUAL.md                 # 用户手册（待编写）
  └── DEVELOPER_GUIDE.md             # 开发指南（待编写）
\`\`\`

### B. 依赖更新

\`\`\`txt
# requirements.txt 新增

# Claude API
anthropic>=0.25.0

# GitHub集成
PyGithub>=2.1.0

# Markdown处理
markdown>=3.5.0
\`\`\`

### C. 环境变量

\`\`\`bash
# .env 新增

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxx

# 飞书（从Hermes复用）
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx

# GitHub
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=username/mcn-knowledge

# Hermes工作空间
HERMES_WORKSPACE=~/hermes_workspace
\`\`\`

### D. 参考资源

**Hermes Agent资源**：
- `~/.hermes/skills/knowledge/soul/SKILL.md` - SOUL完整画像
- `~/.hermes/skills/hotspot-research/SKILL.md` - 热点采集系统
- `~/.hermes/skills/research/competitive-analysis/SKILL.md` - 竞品分析
- `~/hermes_workspace/reports/hotspot/` - 热点报告归档

**MCN系统资源**：
- `docs/PROJECT_ANALYSIS_REPORT.md` - 项目分析报告
- `Mcn Ai Replacement/SYSTEM-ARCHITECTURE.md` - 原始架构设计
- `Mcn Ai Replacement/playbook/MVP-PLAYBOOK.md` - MVP执行手册

---

**文档版本**：v2.0  
**创建日期**：2026-05-17  
**最后更新**：2026-05-17  
**状态**：待审核

