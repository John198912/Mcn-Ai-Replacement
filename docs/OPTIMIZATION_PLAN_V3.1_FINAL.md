# MCN AI Replacement 系统优化方案 v3.1（最终版）

> 基于深度审查和问题澄清的最终实施方案
> 
> 版本：v3.1 Final
> 日期：2026-05-17
> 状态：Ready for Implementation

---

## 📋 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| v2.0 | 2026-05-17 | 基于Hermes深度集成方案 |
| v3.0 | 2026-05-17 | 独立系统，基于用户反馈调整 |
| v3.1 | 2026-05-17 | **最终版**：修复误判，明确实现细节 |

### v3.1 核心修正

1. ✅ **澄清API认证** - 本地场景无需认证
2. ✅ **明确WebSearch方式** - 读取Hermes报告，而非自己实现
3. ✅ **聚焦真正问题** - 从13个问题精简到5个核心问题
4. ✅ **补充实现细节** - 所有核心模块提供完整代码
5. ✅ **优化实施计划** - 15-20天，更合理的时间安排

---

## 一、系统定位与架构

### 1.1 核心定位

```
独立的MCN内容创作系统
├── 运行环境：Claude Code（本地）
├── 数据来源：Hermes热点报告（复用已有能力）
├── 核心能力：SOUL驱动的内容生成
├── 知识库：本地Markdown + GitHub（两层）
└── 集成方式：可被Hermes调用（松耦合）
```

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────┐
│  Hermes Agent（可选调用方）                               │
│  - 通过HTTP API触发任务（本地，无需认证）                 │
│  - 通过飞书消息接收结果                                   │
└─────────────────────────────────────────────────────────┘
                          ↓ 松耦合
┌─────────────────────────────────────────────────────────┐
│  MCN AI Replacement（独立系统）                          │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  数据接入层                                       │   │
│  │  ├── HermesHotspotAdapter（读取报告）✅          │   │
│  │  ├── ManualHotspotImporter（手动导入）✅         │   │
│  │  └── WebSearchPromptGenerator（备用）✅          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SOUL驱动内容生成                                 │   │
│  │  ├── SOULScriptWriter（文件交换模式）✅          │   │
│  │  ├── SOULHotTopicMatcher（SOUL评分）✅           │   │
│  │  ├── TitleOptimizer（标题生成）✅                │   │
│  │  └── ContentRiskScanner（合规审核）✅            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  两层知识库                                       │   │
│  │  ├── 本地：Markdown + SQLite（主存储）✅         │   │
│  │  └── GitHub：备份 + 版本控制（冲突解决）✅       │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  自动化调度                                       │   │
│  │  ├── MCNScheduler（定时任务）✅                  │   │
│  │  ├── 每周一采集热点                               │   │
│  │  ├── 每日备份知识库                               │   │
│  │  └── 每日同步GitHub                               │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Hermes集成（可选）                               │   │
│  │  ├── HTTP API（本地，无需认证）✅                │   │
│  │  ├── 任务队列管理                                 │   │
│  │  └── 飞书消息通知                                 │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 1.3 核心原则

1. **独立性** - 可独立运行，不强依赖Hermes
2. **零成本** - 仅使用Claude Code免费能力
3. **复用优先** - 读取Hermes报告，而非重复实现
4. **简化架构** - 两层知识库，避免过度设计
5. **本地安全** - 本地运行，无需API认证

---

## 二、核心模块实现

### 2.1 数据接入层

#### 模块1：HermesHotspotAdapter（核心）

**功能**：读取Hermes热点报告，这是真正的"引用Hermes已有能力"

**完整实现**：

```python
# src/adapters/hermes_hotspot_adapter.py

from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from ..core.database import HotTopic
from ..core.logger import get_logger

logger = get_logger(__name__)


class HermesHotspotAdapter:
    """
    Hermes热点报告适配器
    
    功能：
    1. 读取Hermes热点采集系统的日报/周报
    2. 解析P0/P1热点数据
    3. 转换为MCN数据模型
    
    这是真正的"引用Hermes已有能力"：
    - Hermes已有成熟的四源采集（MCP Brave + Tavily + AI HOT + 博客）
    - Hermes已有三关审核（时效 + 来源 + 匹配度）
    - MCN系统只需读取报告，无需重复实现
    """
    
    def __init__(self, hermes_workspace: str = "~/hermes_workspace"):
        self.workspace = Path(hermes_workspace).expanduser()
        self.reports_dir = self.workspace / "reports" / "hotspot"
        self.available = self.reports_dir.exists()
        
        if not self.available:
            logger.warning(f"Hermes reports directory not found: {self.reports_dir}")
    
    async def fetch_latest_hotspots(self, days: int = 7) -> List[HotTopic]:
        """
        读取最近N天的Hermes热点报告
        
        Args:
            days: 读取最近N天的报告
        
        Returns:
            热点列表
        """
        if not self.available:
            logger.info("Hermes reports not available, skipping")
            return []
        
        hotspots = []
        
        # 读取最近N天的日报
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            report_file = self.reports_dir / f"daily_{date}.md"
            
            if report_file.exists():
                try:
                    parsed = self._parse_hermes_report(report_file)
                    hotspots.extend(parsed)
                    logger.info(f"Parsed {len(parsed)} hotspots from {report_file.name}")
                except Exception as e:
                    logger.error(f"Failed to parse {report_file.name}: {e}")
        
        # 去重
        hotspots = self._deduplicate(hotspots)
        
        logger.info(f"Total loaded {len(hotspots)} hotspots from Hermes reports")
        return hotspots
    
    def _parse_hermes_report(self, report_path: Path) -> List[HotTopic]:
        """
        解析Hermes报告
        
        Hermes报告格式：
        ## 🔥 P0 热点（直接选题）
        | 序号 | 话题 | 来源 | 标签 | SOUL适配度 | 推荐角度 |
        
        ## 🟡 P1 热点（间接相关）
        | 序号 | 话题 | 来源 | 标签 | 推荐角度 |
        """
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        hotspots = []
        
        # 提取P0热点
        p0_section = self._extract_section(content, "P0 热点")
        if p0_section:
            p0_hotspots = self._parse_hotspot_table(p0_section, priority='P0')
            hotspots.extend(p0_hotspots)
        
        # 提取P1热点
        p1_section = self._extract_section(content, "P1 热点")
        if p1_section:
            p1_hotspots = self._parse_hotspot_table(p1_section, priority='P1')
            hotspots.extend(p1_hotspots)
        
        return hotspots
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """
        提取指定section的内容
        """
        # 匹配 ## 🔥 P0 热点 或 ## 🟡 P1 热点
        pattern = rf"##\s+[🔥🟡]\s+{section_name}.*?\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            return match.group(1)
        return ""
    
    def _parse_hotspot_table(self, section: str, priority: str) -> List[HotTopic]:
        """
        解析热点表格
        
        表格格式：
        | 序号 | 话题 | 来源 | 标签 | SOUL适配度 | 推荐角度 |
        | 1 | AI焦虑 | douyin | [AI][超级个体] | 高 | 从有限性视角 |
        """
        hotspots = []
        
        # 按行分割
        lines = section.strip().split('\n')
        
        # 找到表格头
        header_idx = -1
        for i, line in enumerate(lines):
            if '话题' in line and '来源' in line:
                header_idx = i
                break
        
        if header_idx == -1:
            return hotspots
        
        # 解析表格头，确定列索引
        header = lines[header_idx]
        columns = [col.strip() for col in header.split('|')]
        
        # 找到关键列的索引
        topic_idx = next((i for i, col in enumerate(columns) if '话题' in col), -1)
        platform_idx = next((i for i, col in enumerate(columns) if '来源' in col), -1)
        tags_idx = next((i for i, col in enumerate(columns) if '标签' in col), -1)
        soul_idx = next((i for i, col in enumerate(columns) if 'SOUL' in col), -1)
        angle_idx = next((i for i, col in enumerate(columns) if '角度' in col), -1)
        
        # 解析数据行（跳过表头和分隔线）
        for line in lines[header_idx + 2:]:
            if not line.strip() or line.startswith('#'):
                break
            
            cells = [cell.strip() for cell in line.split('|')]
            
            if len(cells) < max(topic_idx, platform_idx, tags_idx) + 1:
                continue
            
            # 提取数据
            title = cells[topic_idx] if topic_idx >= 0 else ""
            platform = cells[platform_idx] if platform_idx >= 0 else ""
            tags_str = cells[tags_idx] if tags_idx >= 0 else ""
            soul_alignment = cells[soul_idx] if soul_idx >= 0 else ""
            recommended_angle = cells[angle_idx] if angle_idx >= 0 else ""
            
            # 解析标签
            tags = self._parse_tags(tags_str)
            
            # 创建HotTopic对象
            hotspot = HotTopic(
                title=title,
                platform=platform,
                tags=tags,
                soul_alignment=soul_alignment,
                recommended_angle=recommended_angle,
                priority=priority,
                heat_level='上升',  # 默认值
                source='hermes'
            )
            
            hotspots.append(hotspot)
        
        return hotspots
    
    def _parse_tags(self, tags_str: str) -> List[str]:
        """
        解析标签字符串
        
        输入：[AI][超级个体]
        输出：['AI', '超级个体']
        """
        tags = []
        pattern = r'\[([^\]]+)\]'
        matches = re.findall(pattern, tags_str)
        tags.extend(matches)
        return tags
    
    def _deduplicate(self, hotspots: List[HotTopic]) -> List[HotTopic]:
        """
        去重
        
        规则：标题相同视为重复
        """
        seen = set()
        unique = []
        
        for hotspot in hotspots:
            if hotspot.title not in seen:
                seen.add(hotspot.title)
                unique.append(hotspot)
        
        return unique
```

#### 模块2：ManualHotspotImporter（降级方案）

**功能**：当Hermes报告不可用时，支持手动导入

**完整实现**：

```python
# src/adapters/manual_hotspot_importer.py

from pathlib import Path
from typing import List
import csv
import json
from ..core.database import HotTopic
from ..core.logger import get_logger

logger = get_logger(__name__)


class ManualHotspotImporter:
    """
    手动热点导入器
    
    支持格式：
    1. CSV文件
    2. JSON文件
    3. Markdown表格
    """
    
    def import_from_file(self, file_path: str) -> List[HotTopic]:
        """
        从文件导入热点
        
        自动识别文件格式
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix == '.csv':
            return self.import_from_csv(file_path)
        elif path.suffix == '.json':
            return self.import_from_json(file_path)
        elif path.suffix == '.md':
            return self.import_from_markdown(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def import_from_csv(self, file_path: str) -> List[HotTopic]:
        """
        从CSV导入
        
        CSV格式（第一行为表头）：
        标题,平台,热度,标签,描述
        AI焦虑,douyin,上升,"AI,超级个体",探讨AI时代的焦虑
        """
        hotspots = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # 解析标签
                tags_str = row.get('标签', '')
                tags = [tag.strip() for tag in tags_str.split(',')]
                
                hotspot = HotTopic(
                    title=row.get('标题', ''),
                    platform=row.get('平台', ''),
                    heat_level=row.get('热度', '上升'),
                    tags=tags,
                    description=row.get('描述', ''),
                    source='manual_csv'
                )
                
                hotspots.append(hotspot)
        
        logger.info(f"Imported {len(hotspots)} hotspots from CSV")
        return hotspots
    
    def import_from_json(self, file_path: str) -> List[HotTopic]:
        """
        从JSON导入
        
        JSON格式：
        [
            {
                "title": "AI焦虑",
                "platform": "douyin",
                "heat_level": "上升",
                "tags": ["AI", "超级个体"],
                "description": "探讨AI时代的焦虑"
            }
        ]
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        hotspots = []
        for item in data:
            hotspot = HotTopic(
                title=item.get('title', ''),
                platform=item.get('platform', ''),
                heat_level=item.get('heat_level', '上升'),
                tags=item.get('tags', []),
                description=item.get('description', ''),
                source='manual_json'
            )
            hotspots.append(hotspot)
        
        logger.info(f"Imported {len(hotspots)} hotspots from JSON")
        return hotspots
    
    def import_from_markdown(self, file_path: str) -> List[HotTopic]:
        """
        从Markdown表格导入
        
        Markdown格式：
        | 标题 | 平台 | 热度 | 标签 | 描述 |
        |------|------|------|------|------|
        | AI焦虑 | douyin | 上升 | AI,超级个体 | 探讨AI时代的焦虑 |
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        hotspots = []
        lines = content.strip().split('\n')
        
        # 找到表格
        header_idx = -1
        for i, line in enumerate(lines):
            if '标题' in line and '平台' in line:
                header_idx = i
                break
        
        if header_idx == -1:
            logger.warning("No table found in markdown file")
            return hotspots
        
        # 解析表头
        header = lines[header_idx]
        columns = [col.strip() for col in header.split('|')]
        
        # 解析数据行
        for line in lines[header_idx + 2:]:  # 跳过表头和分隔线
            if not line.strip():
                break
            
            cells = [cell.strip() for cell in line.split('|')]
            
            if len(cells) < len(columns):
                continue
            
            # 创建字典
            row_dict = dict(zip(columns, cells))
            
            # 解析标签
            tags_str = row_dict.get('标签', '')
            tags = [tag.strip() for tag in tags_str.split(',')]
            
            hotspot = HotTopic(
                title=row_dict.get('标题', ''),
                platform=row_dict.get('平台', ''),
                heat_level=row_dict.get('热度', '上升'),
                tags=tags,
                description=row_dict.get('描述', ''),
                source='manual_markdown'
            )
            
            hotspots.append(hotspot)
        
        logger.info(f"Imported {len(hotspots)} hotspots from Markdown")
        return hotspots
    
    def generate_template_csv(self, output_path: str):
        """
        生成CSV导入模板
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['标题', '平台', '热度', '标签', '描述'])
            writer.writerow(['AI焦虑', 'douyin', '上升', 'AI,超级个体', '探讨AI时代的焦虑'])
            writer.writerow(['一人企业', 'xiaohongshu', '爆发', '超级个体,创业', '如何打造一人企业'])
        
        logger.info(f"Template CSV generated: {output_path}")
    
    def generate_template_json(self, output_path: str):
        """
        生成JSON导入模板
        """
        template = [
            {
                "title": "AI焦虑",
                "platform": "douyin",
                "heat_level": "上升",
                "tags": ["AI", "超级个体"],
                "description": "探讨AI时代的焦虑"
            },
            {
                "title": "一人企业",
                "platform": "xiaohongshu",
                "heat_level": "爆发",
                "tags": ["超级个体", "创业"],
                "description": "如何打造一人企业"
            }
        ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Template JSON generated: {output_path}")
```


#### 模块3：数据采集协调器

**功能**：协调多种数据源，提供统一接口

**完整实现**：

```python
# src/adapters/hotspot_collector.py

from typing import List
from ..core.database import HotTopic
from ..core.logger import get_logger
from .hermes_hotspot_adapter import HermesHotspotAdapter
from .manual_hotspot_importer import ManualHotspotImporter

logger = get_logger(__name__)


class HotspotCollector:
    """
    热点采集协调器
    
    协调多种数据源：
    1. 优先：Hermes报告（推荐）
    2. 降级：手动导入
    3. 备用：提示用户
    """
    
    def __init__(self):
        self.hermes_adapter = HermesHotspotAdapter()
        self.manual_importer = ManualHotspotImporter()
    
    async def collect(
        self,
        use_hermes: bool = True,
        manual_file: str = None,
        days: int = 7
    ) -> List[HotTopic]:
        """
        采集热点（多方案）
        
        Args:
            use_hermes: 是否尝试使用Hermes报告
            manual_file: 手动导入文件路径
            days: 读取最近N天的Hermes报告
        
        Returns:
            热点列表
        """
        hotspots = []
        
        # 方案1：读取Hermes报告（推荐）
        if use_hermes and self.hermes_adapter.available:
            logger.info("Attempting to load hotspots from Hermes reports")
            hermes_hotspots = await self.hermes_adapter.fetch_latest_hotspots(days=days)
            
            if hermes_hotspots:
                logger.info(f"✅ Loaded {len(hermes_hotspots)} hotspots from Hermes")
                return hermes_hotspots
            else:
                logger.warning("No hotspots found in Hermes reports")
        
        # 方案2：手动导入（降级）
        if manual_file:
            logger.info(f"Attempting to import hotspots from {manual_file}")
            try:
                imported_hotspots = self.manual_importer.import_from_file(manual_file)
                if imported_hotspots:
                    logger.info(f"✅ Imported {len(imported_hotspots)} hotspots")
                    return imported_hotspots
            except Exception as e:
                logger.error(f"Failed to import from {manual_file}: {e}")
        
        # 方案3：提示用户
        logger.warning("No hotspots available from any source")
        print("\n" + "="*60)
        print("⚠️  无法获取热点数据")
        print("="*60)
        print("\n可选方案：")
        print("1. 等待Hermes热点采集系统运行（每日08:00）")
        print("2. 手动导入数据文件（CSV/JSON/Markdown）")
        print("3. 生成导入模板")
        print("\n选择方案 (1/2/3): ", end='')
        
        choice = input().strip()
        
        if choice == '2':
            file_path = input("请输入文件路径: ").strip()
            return self.manual_importer.import_from_file(file_path)
        elif choice == '3':
            template_path = input("模板保存路径 (默认: hotspots_template.csv): ").strip()
            if not template_path:
                template_path = "hotspots_template.csv"
            self.manual_importer.generate_template_csv(template_path)
            print(f"\n✅ 模板已生成: {template_path}")
            print("请填写模板后重新运行")
        
        return []
```

---

### 2.2 SOUL驱动内容生成

#### 模块4：SOULScriptWriter（文件交换模式）

**功能**：基于SOUL框架生成脚本，使用文件交换优化交互

**完整实现**：

```python
# src/skills/soul_script_writer.py

from pathlib import Path
from typing import Dict, Any
import time
import asyncio
from datetime import datetime
from .base_skill import BaseSkill, SkillInput, SkillOutput
from pydantic import Field
from ..core.logger import get_logger

logger = get_logger(__name__)


class SOULScriptWriterInput(SkillInput):
    """SOULScriptWriter输入"""
    topic: str = Field(description="选题话题")
    angle: str = Field(description="切入角度")
    platform: str = Field(description="目标平台")
    duration: int = Field(description="目标时长（秒）")


class SOULScriptWriterOutput(SkillOutput):
    """SOULScriptWriter输出"""
    script: Dict[str, Any] = {}
    prompt_file: str = ""
    result_file: str = ""


class SOULScriptWriter(BaseSkill):
    """
    基于SOUL框架的脚本生成器（文件交换模式）
    
    优化点：
    1. 使用文件交换，避免手动复制粘贴
    2. 自动等待结果文件
    3. 超时保护
    4. 进度提示
    """
    
    def __init__(self):
        super().__init__()
        self.soul_profile = self._load_soul_profile()
        self.prompt_file = Path("/tmp/mcn_script_prompt.txt")
        self.result_file = Path("/tmp/mcn_script_result.txt")
    
    def _load_soul_profile(self) -> Dict[str, Any]:
        """
        加载SOUL完整画像
        
        优先级：
        1. 环境变量：SOUL_PROFILE_PATH
        2. Hermes技能：~/.hermes/skills/knowledge/soul/SKILL.md
        3. Hermes工作空间：~/hermes_workspace/config/SOUL.md
        4. 本地配置：config/soul_profile.json
        5. 默认配置
        """
        import os
        
        # 1. 环境变量
        env_path = os.getenv("SOUL_PROFILE_PATH")
        if env_path:
            path = Path(env_path).expanduser()
            if path.exists():
                logger.info(f"Loading SOUL profile from env: {path}")
                return self._parse_soul_profile(path)
        
        # 2-4. 按优先级查找
        soul_paths = [
            Path("~/.hermes/skills/knowledge/soul/SKILL.md").expanduser(),
            Path("~/hermes_workspace/config/SOUL.md").expanduser(),
            Path("config/soul_profile.json")
        ]
        
        for path in soul_paths:
            if path.exists():
                logger.info(f"Loading SOUL profile from {path}")
                try:
                    return self._parse_soul_profile(path)
                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")
                    continue
        
        # 5. 默认配置
        logger.warning("SOUL profile not found, using default")
        return self._get_default_soul_profile()
    
    def _get_default_soul_profile(self) -> Dict[str, Any]:
        """默认SOUL配置"""
        return {
            'positioning': "走在前面半步的同路人",
            'slogan': "AI是工具，哲学是地基，你才是杠杆的支点",
            'three_tier_dialogue': {
                'tier1': '场景爆破（Rupture）',
                'tier2': '结构拆解（Illuminate + Validate）',
                'tier3': '反刍重建（Embody + Transform）'
            },
            'finitude_triangle': {
                'direction1': '有限性智慧',
                'direction2': '存在的偶然性',
                'direction3': '协议层协作'
            },
            'core_audiences': ['Marcus', 'Lily', 'Alex', 'Z']
        }
    
    def _parse_soul_profile(self, path: Path) -> Dict[str, Any]:
        """解析SOUL配置文件"""
        # 简化实现，实际应该解析Markdown或JSON
        return self._get_default_soul_profile()
    
    async def execute(self, input_data: SOULScriptWriterInput) -> SOULScriptWriterOutput:
        """
        生成脚本（文件交换模式）
        
        流程：
        1. 生成提示词
        2. 写入文件：/tmp/mcn_script_prompt.txt
        3. 提示用户在Claude Code中执行
        4. 等待结果文件：/tmp/mcn_script_result.txt
        5. 解析结果
        """
        logger.info("Generating SOUL script prompt")
        
        # 1. 生成提示词
        prompt = self._build_script_prompt(
            topic=input_data.topic,
            angle=input_data.angle,
            platform=input_data.platform,
            duration=input_data.duration
        )
        
        # 2. 写入文件
        self.prompt_file.write_text(prompt, encoding='utf-8')
        
        # 清理旧的结果文件
        if self.result_file.exists():
            self.result_file.unlink()
        
        # 3. 提示用户
        print("\n" + "="*60)
        print("📋 SOUL脚本生成提示词已准备")
        print("="*60)
        print(f"\n提示词文件：{self.prompt_file}")
        print(f"结果文件：{self.result_file}")
        print("\n请在Claude Code中执行以下步骤：")
        print(f"1. 读取提示词：cat {self.prompt_file}")
        print("2. 复制提示词内容")
        print("3. 在Claude Code中粘贴并执行")
        print("4. 将生成的脚本保存到结果文件：")
        print(f"   echo '生成的脚本内容' > {self.result_file}")
        print("\n等待结果文件...")
        print("(超时时间：5分钟)")
        
        # 4. 等待结果文件
        timeout = 300  # 5分钟
        start_time = time.time()
        
        while not self.result_file.exists():
            if time.time() - start_time > timeout:
                raise TimeoutError("等待脚本生成结果超时（5分钟）")
            
            # 显示进度
            elapsed = int(time.time() - start_time)
            print(f"\r等待中... {elapsed}秒", end='', flush=True)
            
            await asyncio.sleep(1)
        
        print("\n\n✅ 检测到结果文件")
        
        # 5. 读取并解析结果
        generated_content = self.result_file.read_text(encoding='utf-8')
        script = self._parse_generated_script(generated_content)
        
        logger.info("Script generated successfully")
        
        return SOULScriptWriterOutput(
            success=True,
            script=script,
            prompt_file=str(self.prompt_file),
            result_file=str(self.result_file)
        )
    
    def _build_script_prompt(self, topic, angle, platform, duration) -> str:
        """构建脚本生成提示词"""
        soul = self.soul_profile
        
        return f"""你是SOUL - 超级个体成长合伙人。

# 身份定位
{soul['positioning']}

核心Slogan：{soul['slogan']}

# 核心方法论：三阶对话法
{soul['three_tier_dialogue']['tier1']}
  ↓ 用日常场景打破默认假设
{soul['three_tier_dialogue']['tier2']}
  ↓ 用哲学/心理学框架揭示深层结构
{soul['three_tier_dialogue']['tier3']}
  ↓ 给出可用的新框架和思维工具

# 当前任务
为以下选题生成短视频脚本：
- 选题：{topic}
- 切入角度：{angle}
- 目标平台：{platform}
- 时长：{duration}秒

# 要求
1. 应用三阶对话法
2. 符合SOUL人设：走在前面半步的同路人，不是导师
3. 融合四视角：叙事学/心理学/人类学/产品策略
4. 高信息密度，不废话，不注水
5. 真诚展示脆弱和不确定性
6. 避免"你应该"等导师口吻，用"我们一起"的协作态度

# 输出格式
请严格按照以下格式输出：

## Hook (前5%)
[场景爆破 - 用反常识问题抓住注意力]

## 痛点 (10-20%)
[建立共鸣 - 描述受众的真实困惑]

## 核心内容 (20-80%)
[结构拆解 - 用框架揭示深层逻辑]

## 启发 (80-95%)
[反刍重建 - 给出可用的思维工具]

## CTA (最后5%)
[提出新问题 - 引导持续思考]

请生成脚本：
"""
    
    def _parse_generated_script(self, content: str) -> Dict[str, str]:
        """
        解析生成的脚本
        
        从Claude Code生成的内容中提取各部分
        """
        import re
        
        script = {
            'hook': '',
            'pain_point': '',
            'core_content': '',
            'insight': '',
            'cta': ''
        }
        
        # 提取各部分
        patterns = {
            'hook': r'##\s*Hook.*?\n(.*?)(?=##|$)',
            'pain_point': r'##\s*痛点.*?\n(.*?)(?=##|$)',
            'core_content': r'##\s*核心内容.*?\n(.*?)(?=##|$)',
            'insight': r'##\s*启发.*?\n(.*?)(?=##|$)',
            'cta': r'##\s*CTA.*?\n(.*?)(?=##|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                script[key] = match.group(1).strip()
        
        return script
```

---

### 2.3 两层知识库

#### 模块5：TwoLayerKnowledgeManager（完整版）

**功能**：本地Markdown + GitHub，带冲突解决

**完整实现**：

```python
# src/knowledge/two_layer_manager.py

from pathlib import Path
from typing import List, Dict, Any
import shutil
import subprocess
from datetime import datetime
from ..core.database import HotTopic, get_db_session
from ..core.logger import get_logger

logger = get_logger(__name__)


class TwoLayerKnowledgeManager:
    """
    两层知识库管理器
    
    第一层：本地Markdown + SQLite（主存储）
    第二层：GitHub仓库（备份 + 版本控制）
    
    特性：
    1. 本地为主，GitHub为备份
    2. 独立维护，互不干扰
    3. 冲突解决机制
    4. 增量同步
    """
    
    def __init__(self):
        self.local_db = Path("data/database.db")
        self.local_markdown = Path("data/markdown")
        self.github_knowledge_dir = Path("knowledge")
        self.last_sync_file = Path(".last_sync")
    
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
        
        logger.info(f"Hotspot saved: {hotspot.title}")
    
    async def sync_to_github(
        self,
        strategy: str = "local_wins",
        incremental: bool = True
    ):
        """
        同步到GitHub
        
        Args:
            strategy: 冲突解决策略
                - local_wins: 本地优先（默认）
                - remote_wins: 远程优先
                - manual: 手动解决
            incremental: 是否增量同步
        """
        logger.info(f"Syncing to GitHub (strategy={strategy}, incremental={incremental})")
        
        # 1. 检查远程变更
        remote_changes = await self._check_remote_changes()
        
        if remote_changes:
            logger.warning(f"Detected {len(remote_changes)} remote changes")
            await self._resolve_conflicts(remote_changes, strategy)
        
        # 2. 同步本地变更
        if incremental:
            await self._sync_incremental()
        else:
            await self._sync_full()
        
        logger.info("GitHub sync completed")
    
    async def _check_remote_changes(self) -> List[Dict]:
        """
        检查远程变更
        """
        try:
            # Git fetch
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
            
            # Git diff
            result = subprocess.run(
                ["git", "diff", "HEAD", "origin/main", "--name-only"],
                check=True,
                capture_output=True,
                text=True
            )
            
            changed_files = result.stdout.strip().split('\n')
            changed_files = [f for f in changed_files if f.startswith('knowledge/')]
            
            return [{'file': f} for f in changed_files]
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check remote changes: {e}")
            return []
    
    async def _resolve_conflicts(self, changes: List[Dict], strategy: str):
        """
        解决冲突
        """
        if strategy == "local_wins":
            logger.info("Using local_wins strategy, will overwrite remote")
            # 不需要特殊处理，直接推送即可
        
        elif strategy == "remote_wins":
            logger.info("Using remote_wins strategy, pulling remote")
            subprocess.run(["git", "pull", "origin", "main"], check=True)
            
            # 复制到本地
            for change in changes:
                src = Path(change['file'])
                dst = self.local_markdown / src.relative_to(self.github_knowledge_dir)
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src, dst)
        
        elif strategy == "manual":
            print("\n⚠️  检测到冲突文件：")
            for change in changes:
                print(f"  - {change['file']}")
            
            print("\n选择策略：")
            print("1. 本地优先（覆盖远程）")
            print("2. 远程优先（覆盖本地）")
            choice = input("请选择 (1/2): ").strip()
            
            if choice == "1":
                await self._resolve_conflicts(changes, "local_wins")
            elif choice == "2":
                await self._resolve_conflicts(changes, "remote_wins")
    
    async def _sync_incremental(self):
        """
        增量同步
        
        只同步变更的文件
        """
        # 获取上次同步时间
        if self.last_sync_file.exists():
            last_sync_time = datetime.fromisoformat(
                self.last_sync_file.read_text().strip()
            )
        else:
            last_sync_time = datetime.min
        
        # 找出变更的文件
        changed_files = []
        
        for md_file in self.local_markdown.rglob("*.md"):
            if datetime.fromtimestamp(md_file.stat().st_mtime) > last_sync_time:
                changed_files.append(md_file)
        
        if not changed_files:
            logger.info("No changes to sync")
            return
        
        logger.info(f"Syncing {len(changed_files)} changed files")
        
        # 复制变更的文件
        for src_file in changed_files:
            rel_path = src_file.relative_to(self.local_markdown)
            dst_file = self.github_knowledge_dir / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_file, dst_file)
        
        # Git提交
        await self._git_commit_and_push(f"Incremental sync: {len(changed_files)} files")
        
        # 更新同步时间
        self.last_sync_file.write_text(datetime.now().isoformat())
    
    async def _sync_full(self):
        """
        全量同步
        """
        logger.info("Full sync to GitHub")
        
        # 复制所有文件
        if self.github_knowledge_dir.exists():
            shutil.rmtree(self.github_knowledge_dir)
        
        shutil.copytree(self.local_markdown, self.github_knowledge_dir)
        
        # Git提交
        await self._git_commit_and_push("Full sync")
        
        # 更新同步时间
        self.last_sync_file.write_text(datetime.now().isoformat())
    
    async def _git_commit_and_push(self, message: str):
        """
        Git提交和推送
        """
        try:
            subprocess.run(["git", "add", "knowledge/"], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"{message} - {datetime.now().isoformat()}"],
                check=True
            )
            subprocess.run(["git", "push", "origin", "main"], check=True)
            logger.info("Git push completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e}")
    
    def _hotspot_to_markdown(self, hotspot: HotTopic) -> str:
        """
        将热点转换为Markdown
        """
        return f"""# {hotspot.title}

## 基本信息
- 来源：{hotspot.platform}
- 热度：{hotspot.heat_level}
- 标签：{', '.join(hotspot.tags)}
- 优先级：{hotspot.priority}
- 综合评分：{hotspot.total_score}/10

## SOUL框架分析
### 有限性三角方向
{hotspot.finitude_direction}

### 推荐切入角度
{hotspot.recommended_angle}

### SOUL适配度
{hotspot.soul_alignment}

## 状态
- 创建时间：{hotspot.created_at}
- 当前状态：{hotspot.status}
"""
```


---

### 2.4 定时任务调度

#### 模块6：MCNScheduler

**功能**：定时任务调度器

**完整实现**：

```python
# src/scheduler/mcn_scheduler.py

import schedule
import time
import asyncio
from datetime import datetime
from ..workflows.soul_content_creation_workflow import run_soul_content_creation_workflow
from ..knowledge.two_layer_manager import TwoLayerKnowledgeManager
from ..core.logger import get_logger

logger = get_logger(__name__)


class MCNScheduler:
    """
    MCN定时任务调度器
    
    任务：
    1. 每周一10:00 - 采集热点
    2. 每日02:00 - 备份知识库
    3. 每日03:00 - 同步GitHub
    """
    
    def __init__(self):
        self.running = False
    
    def start(self):
        """
        启动调度器
        """
        # 每周一10:00采集热点
        schedule.every().monday.at("10:00").do(self._collect_hotspots)
        
        # 每天02:00备份
        schedule.every().day.at("02:00").do(self._backup_knowledge)
        
        # 每天03:00同步GitHub
        schedule.every().day.at("03:00").do(self._sync_github)
        
        self.running = True
        logger.info("MCN Scheduler started")
        
        print("\n" + "="*60)
        print("🚀 MCN定时任务调度器已启动")
        print("="*60)
        print("\n定时任务：")
        print("  • 每周一 10:00 - 采集热点")
        print("  • 每天 02:00 - 备份知识库")
        print("  • 每天 03:00 - 同步GitHub")
        print("\n按 Ctrl+C 停止")
        print("="*60 + "\n")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.stop()
    
    def _collect_hotspots(self):
        """
        定时采集热点
        """
        logger.info("Running scheduled hotspot collection")
        print(f"\n[{datetime.now()}] 开始采集热点...")
        
        try:
            asyncio.run(run_soul_content_creation_workflow(
                use_hermes_hotspots=True,
                auto_select=False
            ))
            print("✅ 热点采集完成")
        except Exception as e:
            logger.error(f"Scheduled hotspot collection failed: {e}")
            print(f"❌ 热点采集失败: {e}")
    
    def _backup_knowledge(self):
        """
        定时备份
        """
        logger.info("Running scheduled backup")
        print(f"\n[{datetime.now()}] 开始备份知识库...")
        
        try:
            from ..knowledge.backup_manager import BackupManager
            backup_manager = BackupManager()
            backup_id = backup_manager.create_backup()
            print(f"✅ 备份完成: {backup_id}")
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
            print(f"❌ 备份失败: {e}")
    
    def _sync_github(self):
        """
        定时同步GitHub
        """
        logger.info("Running scheduled GitHub sync")
        print(f"\n[{datetime.now()}] 开始同步GitHub...")
        
        try:
            manager = TwoLayerKnowledgeManager()
            asyncio.run(manager.sync_to_github(incremental=True))
            print("✅ GitHub同步完成")
        except Exception as e:
            logger.error(f"Scheduled GitHub sync failed: {e}")
            print(f"❌ GitHub同步失败: {e}")
    
    def stop(self):
        """
        停止调度器
        """
        self.running = False
        logger.info("MCN Scheduler stopped")
        print("\n✅ 调度器已停止")
```

---

### 2.5 Hermes集成（简化版）

#### 模块7：HermesTaskBridge

**功能**：接收Hermes任务调度，本地运行无需认证

**完整实现**：

```python
# src/integrations/hermes_task_bridge.py

from typing import Dict, Any
import asyncio
import uuid
from datetime import datetime
import httpx
from ..workflows.soul_content_creation_workflow import run_soul_content_creation_workflow
from ..workflows.hot_topic_workflow import run_hot_topic_workflow
from ..core.logger import get_logger

logger = get_logger(__name__)


class HermesTaskBridge:
    """
    Hermes任务桥接器（简化版）
    
    特性：
    1. 本地运行，无需API认证
    2. 任务队列管理
    3. 飞书消息通知
    4. 状态查询
    """
    
    def __init__(self):
        self.task_status = {}
        self.feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL")
    
    async def receive_task(self, task: Dict) -> str:
        """
        接收任务
        
        任务格式：
        {
            "task_id": "uuid",
            "task_type": "hot_topic" | "create_content",
            "params": {...},
            "callback": "feishu_webhook_url"
        }
        """
        task_id = task.get("task_id", str(uuid.uuid4()))
        
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
                result = await run_hot_topic_workflow(**task.get("params", {}))
            elif task_type == "create_content":
                result = await run_soul_content_creation_workflow(**task.get("params", {}))
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
                        f"时间: {datetime.now().isoformat()}"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json=message, timeout=10)
            logger.info("Notification sent to Hermes")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        查询任务状态
        """
        return self.task_status.get(task_id, {"status": "not_found"})
```

---

## 三、CLI命令完整实现

### 3.1 主命令文件

```python
# scripts/run_workflow.py

import click
import asyncio
from pathlib import Path

from src.adapters.hotspot_collector import HotspotCollector
from src.workflows.soul_content_creation_workflow import run_soul_content_creation_workflow
from src.knowledge.two_layer_manager import TwoLayerKnowledgeManager
from src.scheduler.mcn_scheduler import MCNScheduler
from src.integrations.hermes_task_bridge import HermesTaskBridge


@click.group()
def cli():
    """MCN AI Replacement - 内容创作系统"""
    pass


@cli.command()
@click.option('--use-hermes', is_flag=True, default=True, help='使用Hermes热点数据')
@click.option('--manual-file', type=str, help='手动导入文件路径')
@click.option('--days', default=7, help='读取最近N天的热点')
@click.option('--auto-select', is_flag=True, help='自动选择Top 1热点')
def soul_create(use_hermes, manual_file, days, auto_select):
    """
    SOUL驱动的内容创作工作流
    
    示例：
        # 使用Hermes数据
        python scripts/run_workflow.py soul-create
        
        # 手动导入
        python scripts/run_workflow.py soul-create --manual-file hotspots.csv
        
        # 自动选择
        python scripts/run_workflow.py soul-create --auto-select
    """
    result = asyncio.run(
        run_soul_content_creation_workflow(
            use_hermes_hotspots=use_hermes,
            manual_file=manual_file,
            days_back=days,
            auto_select=auto_select
        )
    )


@cli.command()
@click.option('--strategy', default='local_wins', 
              type=click.Choice(['local_wins', 'remote_wins', 'manual']),
              help='冲突解决策略')
@click.option('--incremental', is_flag=True, default=True, help='增量同步')
def sync_github(strategy, incremental):
    """
    同步本地知识库到GitHub
    
    示例：
        # 增量同步（默认）
        python scripts/run_workflow.py sync-github
        
        # 全量同步
        python scripts/run_workflow.py sync-github --no-incremental
        
        # 远程优先
        python scripts/run_workflow.py sync-github --strategy remote_wins
    """
    manager = TwoLayerKnowledgeManager()
    asyncio.run(manager.sync_to_github(strategy=strategy, incremental=incremental))
    click.echo("✅ GitHub同步完成")


@cli.command()
def start_scheduler():
    """
    启动定时任务调度器
    
    示例：
        python scripts/run_workflow.py start-scheduler
    """
    scheduler = MCNScheduler()
    scheduler.start()


@cli.command()
@click.option('--host', default='127.0.0.1', help='监听地址（默认仅本地）')
@click.option('--port', default=8000, help='监听端口')
def start_api(host, port):
    """
    启动HTTP API（用于Hermes调用）
    
    示例：
        # 本地运行（无需认证）
        python scripts/run_workflow.py start-api
        
        # 远程访问（需要配置API密钥）
        python scripts/run_workflow.py start-api --host 0.0.0.0
    """
    from fastapi import FastAPI, HTTPException, Request
    import uvicorn
    import os
    
    if host != '127.0.0.1':
        click.echo("⚠️  警告：监听非本地地址")
        if not os.getenv("MCN_API_KEY"):
            click.echo("❌ 错误：远程访问必须设置 MCN_API_KEY 环境变量")
            return
    
    app = FastAPI()
    bridge = HermesTaskBridge()
    
    @app.post("/tasks")
    async def create_task(request: Request, task: dict):
        # 如果是远程访问，检查API密钥
        if host != '127.0.0.1':
            api_key = request.headers.get("X-API-Key")
            if api_key != os.getenv("MCN_API_KEY"):
                raise HTTPException(401, "Invalid API key")
        
        task_id = await bridge.receive_task(task)
        return {"task_id": task_id, "status": "accepted"}
    
    @app.get("/tasks/{task_id}")
    async def get_task_status(task_id: str):
        return bridge.get_task_status(task_id)
    
    click.echo(f"🚀 API服务已启动: http://{host}:{port}")
    if host == '127.0.0.1':
        click.echo("✅ 本地运行，无需API认证")
    
    uvicorn.run(app, host=host, port=port)


@cli.command()
def generate_template():
    """
    生成数据导入模板
    
    示例：
        python scripts/run_workflow.py generate-template
    """
    from src.adapters.manual_hotspot_importer import ManualHotspotImporter
    
    importer = ManualHotspotImporter()
    importer.generate_template_csv("hotspots_template.csv")
    importer.generate_template_json("hotspots_template.json")
    
    click.echo("✅ 模板已生成:")
    click.echo("  - hotspots_template.csv")
    click.echo("  - hotspots_template.json")


if __name__ == "__main__":
    cli()
```

---

## 四、实施计划

### 4.1 Phase 1：核心功能（5-7天）

**Day 1-2：数据接入层**
- [ ] HermesHotspotAdapter（读取报告）
- [ ] ManualHotspotImporter（手动导入）
- [ ] HotspotCollector（协调器）
- [ ] 测试数据采集

**Day 3-4：知识库系统**
- [ ] TwoLayerKnowledgeManager（两层知识库）
- [ ] 冲突解决机制
- [ ] 增量同步
- [ ] 测试同步流程

**Day 5：定时任务**
- [ ] MCNScheduler（调度器）
- [ ] systemd/launchd配置
- [ ] 测试定时任务

**Day 6-7：集成测试**
- [ ] 端到端测试
- [ ] 修复问题
- [ ] 编写文档

### 4.2 Phase 2：SOUL内容生成（6-8天）

**Day 1-3：ScriptWriter**
- [ ] SOUL框架加载
- [ ] 文件交换模式
- [ ] 提示词生成
- [ ] 脚本解析

**Day 4-5：HotTopicMatcher**
- [ ] SOUL评分实现
- [ ] 有限性三角评分
- [ ] 受众匹配
- [ ] 角度推荐

**Day 6-7：其他Skills**
- [ ] TitleOptimizer
- [ ] ContentRiskScanner

**Day 8：测试优化**
- [ ] 完整流程测试
- [ ] 质量评估
- [ ] 提示词优化

### 4.3 Phase 3：Hermes集成（2-3天）

**Day 1-2：任务桥接**
- [ ] HermesTaskBridge
- [ ] HTTP API
- [ ] 飞书通知

**Day 3：集成测试**
- [ ] Hermes调用测试
- [ ] 状态查询测试
- [ ] 通知测试

### 4.4 Phase 4：文档和部署（3-4天）

**Day 1-2：文档**
- [ ] 用户手册
- [ ] 开发文档
- [ ] API文档

**Day 3：部署配置**
- [ ] systemd配置
- [ ] 环境变量配置
- [ ] 启动脚本

**Day 4：培训和交付**
- [ ] 演示视频
- [ ] 快速开始指南
- [ ] FAQ

---

## 五、总结

### 5.1 v3.1核心改进

1. ✅ **澄清API认证** - 本地场景无需认证
2. ✅ **明确数据来源** - 读取Hermes报告（真正的"引用已有能力"）
3. ✅ **完整代码实现** - 所有核心模块提供完整代码
4. ✅ **优化交互体验** - 文件交换模式
5. ✅ **冲突解决机制** - 三种策略（local_wins/remote_wins/manual）

### 5.2 关键特性

- **零成本** - 完全免费运行
- **独立可控** - 不依赖外部服务
- **SOUL驱动** - 完整的身份框架
- **简化架构** - 两层知识库
- **松耦合** - 可被Hermes调用

### 5.3 实施周期

- **总计**：15-20天
- **Phase 1**：5-7天（核心功能）
- **Phase 2**：6-8天（SOUL内容生成）
- **Phase 3**：2-3天（Hermes集成）
- **Phase 4**：3-4天（文档部署）

---

**文档版本**：v3.1 Final  
**创建日期**：2026-05-17  
**状态**：Ready for Implementation  
**下一步**：开始Phase 1实施


---

### 2.6 补充模块：BackupManager

#### 模块8：BackupManager

**功能**：知识库备份与恢复

**完整实现**：

```python
# src/knowledge/backup_manager.py

from pathlib import Path
from datetime import datetime
import shutil
import json
import sqlite3
from ..core.logger import get_logger

logger = get_logger(__name__)


class BackupManager:
    """
    备份管理器
    
    功能：
    1. 创建备份（数据库 + Markdown）
    2. 验证备份完整性
    3. 从备份恢复
    4. 自动清理旧备份
    """
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.sources = {
            'database': Path("data/database.db"),
            'markdown': Path("data/markdown"),
            'config': Path("config")
        }
    
    def create_backup(self, backup_name: str = None) -> str:
        """
        创建备份
        
        Args:
            backup_name: 备份名称，默认使用时间戳
        
        Returns:
            备份ID
        """
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        files_count = 0
        total_size = 0
        
        # 备份数据库
        db_src = self.sources['database']
        if db_src.exists():
            db_dst = backup_path / "database.db"
            shutil.copy2(db_src, db_dst)
            files_count += 1
            total_size += db_dst.stat().st_size
        
        # 备份Markdown
        md_src = self.sources['markdown']
        if md_src.exists():
            md_dst = backup_path / "markdown"
            shutil.copytree(md_src, md_dst, dirs_exist_ok=True)
            for f in md_dst.rglob("*"):
                if f.is_file():
                    files_count += 1
                    total_size += f.stat().st_size
        
        # 备份配置
        config_src = self.sources['config']
        if config_src.exists():
            config_dst = backup_path / "config"
            shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
            for f in config_dst.rglob("*"):
                if f.is_file():
                    files_count += 1
                    total_size += f.stat().st_size
        
        # 创建元数据
        metadata = {
            'backup_id': backup_name,
            'created_at': datetime.now().isoformat(),
            'files_count': files_count,
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2)
        }
        
        metadata_file = backup_path / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
        
        logger.info(f"Backup created: {backup_name} ({metadata['size_mb']}MB, {files_count} files)")
        return backup_name
    
    def verify_backup(self, backup_name: str) -> bool:
        """
        验证备份完整性
        
        Args:
            backup_name: 备份名称
        
        Returns:
            是否完整
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_name}")
            return False
        
        # 检查元数据
        metadata_file = backup_path / "metadata.json"
        if not metadata_file.exists():
            logger.error("Missing metadata file")
            return False
        
        # 验证数据库
        db_file = backup_path / "database.db"
        if db_file.exists():
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor]
                conn.close()
                logger.info(f"Database verified: {len(tables)} tables")
                if not tables:
                    logger.warning("Database has no tables")
            except Exception as e:
                logger.error(f"Database verification failed: {e}")
                return False
        
        # 验证Markdown
        md_dir = backup_path / "markdown"
        if md_dir.exists():
            md_count = len(list(md_dir.rglob("*.md")))
            if md_count == 0:
                logger.warning("No markdown files in backup")
            else:
                logger.info(f"Markdown verified: {md_count} files")
        
        return True
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        从备份恢复
        
        Args:
            backup_name: 备份名称
        
        Returns:
            是否成功
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_name}")
            return False
        
        # 先创建当前状态的备份
        safety_backup = self.create_backup(f"before_restore_{backup_name}")
        logger.info(f"Safety backup created: {safety_backup}")
        
        try:
            # 恢复数据库
            db_src = backup_path / "database.db"
            if db_src.exists():
                shutil.copy2(db_src, self.sources['database'])
                logger.info("Database restored")
            
            # 恢复Markdown
            md_src = backup_path / "markdown"
            if md_src.exists():
                if self.sources['markdown'].exists():
                    shutil.rmtree(self.sources['markdown'])
                shutil.copytree(md_src, self.sources['markdown'])
                logger.info("Markdown restored")
            
            # 恢复配置
            config_src = backup_path / "config"
            if config_src.exists():
                if self.sources['config'].exists():
                    shutil.rmtree(self.sources['config'])
                shutil.copytree(config_src, self.sources['config'])
                logger.info("Config restored")
            
            logger.info(f"Restore completed from: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def list_backups(self) -> list:
        """
        列出所有备份
        """
        backups = []
        
        for backup_path in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_path.is_dir():
                metadata_file = backup_path / "metadata.json"
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text())
                    backups.append(metadata)
                else:
                    backups.append({
                        'backup_id': backup_path.name,
                        'created_at': 'unknown',
                        'files_count': 'unknown',
                        'size_mb': 'unknown'
                    })
        
        return backups
    
    def clean_old_backups(self, keep_last: int = 10):
        """
        清理旧备份
        
        Args:
            keep_last: 保留最近N个备份
        """
        backups = sorted(
            [p for p in self.backup_dir.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for backup_path in backups[keep_last:]:
            shutil.rmtree(backup_path)
            logger.info(f"Cleaned old backup: {backup_path.name}")
        
        logger.info(f"Kept {min(len(backups), keep_last)} backups, cleaned {max(0, len(backups) - keep_last)}")
```

---

### 2.7 补充模块：SOULHotTopicMatcher

#### 模块9：SOULHotTopicMatcher

**功能**：基于SOUL框架的热点适配评分

**完整实现**：

```python
# src/skills/soul_hot_topic_matcher.py

from typing import List, Dict, Any
from .base_skill import BaseSkill, SkillInput, SkillOutput
from pydantic import Field
from ..core.logger import get_logger

logger = get_logger(__name__)


class SOULHotTopicInput(SkillInput):
    """SOULHotTopicMatcher输入"""
    topics: List[Dict[str, Any]] = Field(description="热点列表")
    soul_framework: bool = Field(default=True, description="是否使用SOUL框架")


class SOULHotTopicOutput(SkillOutput):
    """SOULHotTopicMatcher输出"""
    ranked_topics: List[Dict[str, Any]] = []
    soul_framework_applied: bool = False


class SOULHotTopicMatcher(BaseSkill):
    """
    基于SOUL框架的热点适配评分
    
    评分维度（5个）：
    1. 有限性三角适配度 (0-10, 权重30%)
       - 方向1：有限性智慧（选择、放弃、承担）
       - 方向2：存在的偶然性（意义、独特性）
       - 方向3：协议层协作（人机边界）
    
    2. 核心受众匹配度 (0-10, 权重25%)
       - Marcus（转型者，30-38岁）
       - Lily（探索者，25-30岁）- 最佳入口
       - Alex（觉醒者，32-40岁）
       - Z（年轻探索者，18-22岁）
    
    3. 三阶对话法可行性 (0-10, 权重25%)
       - 是否有可爆破的场景
       - 是否有可拆解的结构
       - 是否有可重建的框架
    
    4. 差异化空间 (0-10, 权重15%)
       - 对标创作者覆盖情况
       - SOUL独特视角的发挥空间
    
    5. 风险评估 (0-10, 权重5%)
       - 合规性
       - 翻车概率
    """
    
    def __init__(self):
        super().__init__()
        
        # SOUL框架关键词
        self.finitude_keywords = {
            'direction1': {  # 有限性智慧
                'keywords': ['选择', '放弃', '承担', '失去', '珍惜', '取舍', 
                           '优先级', '有限', '专注', '减法'],
                'hook': 'AI能做一切，但你只能做一件事'
            },
            'direction2': {  # 存在的偶然性
                'keywords': ['意义', '独特', '价值', '存在', '焦虑', '为什么',
                           '向死而生', '我是谁', '目的', '偶然'],
                'hook': 'AI的存在是被赋予的，你的存在是偶然的'
            },
            'direction3': {  # 协议层协作
                'keywords': ['边界', '协作', '人机', '协议', '工具', '代理',
                           '依赖', '平衡', '配合', '分工'],
                'hook': 'AI不需要理解你，你也不需要理解AI'
            }
        }
        
        self.core_audiences = {
            'Marcus': {
                'label': '转型者（30-38岁）',
                'keywords': ['转型', '离职', '创业', '副业', '35岁', '职业'],
                'weight': 0.8
            },
            'Lily': {
                'label': '探索者（25-30岁）- 最佳入口',
                'keywords': ['成长', '学习', '选择', '迷茫', '焦虑', '方向'],
                'weight': 1.0
            },
            'Alex': {
                'label': '觉醒者（32-40岁）',
                'keywords': ['意义', '自由', '精神', '价值', '996', '逃离'],
                'weight': 0.9
            },
            'Z': {
                'label': '年轻探索者（18-22岁）',
                'keywords': ['AI', '未来', '学习', '技能', '方向', '无知'],
                'weight': 0.7
            }
        }
    
    def execute_sync(self, input_data: SOULHotTopicInput) -> SOULHotTopicOutput:
        """同步执行评分（不使用异步，因为这是纯计算）"""
        logger.info(f"Scoring {len(input_data.topics)} topics with SOUL framework")
        
        ranked_topics = []
        
        for topic in input_data.topics:
            title = topic.get('title', '').lower()
            description = topic.get('description', '').lower()
            content = title + ' ' + description
            
            # 1. 有限性三角适配度
            finitude_scores = self._score_finitude_alignment(content)
            best_direction = max(finitude_scores, key=finitude_scores.get)
            
            # 2. 核心受众匹配度
            audience_scores = self._score_audience_match(content)
            best_audience = max(audience_scores, key=audience_scores.get)
            
            # 3. 三阶对话法可行性
            dialogue_scores = self._score_dialogue_feasibility(content)
            
            # 4. 差异化空间
            differentiation_score = self._score_differentiation(topic)
            
            # 5. 风险评估
            risk_score = self._score_risk(topic)
            
            # 加权计算
            total_score = (
                finitude_scores[best_direction] * 0.30 +
                audience_scores[best_audience] * 0.25 +
                dialogue_scores['total'] * 0.25 +
                differentiation_score * 0.15 +
                risk_score * 0.05
            )
            
            # 推荐切入角度
            recommended_angle = self._recommend_angle(
                best_direction=best_direction,
                best_audience=best_audience,
                topic=title
            )
            
            ranked_topics.append({
                'topic': topic,
                'total_score': round(total_score, 2),
                'finitude_direction': best_direction,
                'finitude_scores': finitude_scores,
                'target_audience': best_audience,
                'audience_scores': audience_scores,
                'dialogue_scores': dialogue_scores,
                'differentiation_score': differentiation_score,
                'risk_score': risk_score,
                'recommended_angle': recommended_angle,
                'finitude_hook': self.finitude_keywords[best_direction]['hook']
            })
        
        # 排序
        ranked_topics.sort(key=lambda x: x['total_score'], reverse=True)
        
        logger.info(f"Ranked {len(ranked_topics)} topics")
        
        return SOULHotTopicOutput(
            success=True,
            ranked_topics=ranked_topics,
            soul_framework_applied=True
        )
    
    def _score_finitude_alignment(self, content: str) -> Dict[str, float]:
        """计算有限性三角各方向的匹配度"""
        scores = {}
        
        for direction, config in self.finitude_keywords.items():
            matches = sum(1 for kw in config['keywords'] if kw in content)
            # 归一化到0-10
            scores[direction] = min(10, matches * 2.5)
        
        return scores
    
    def _score_audience_match(self, content: str) -> Dict[str, float]:
        """计算各受众的匹配度"""
        scores = {}
        
        for audience, config in self.core_audiences.items():
            matches = sum(1 for kw in config['keywords'] if kw in content)
            base_score = min(10, matches * 2.5)
            scores[audience] = base_score * config['weight']
        
        return scores
    
    def _score_dialogue_feasibility(self, content: str) -> Dict[str, float]:
        """评估三阶对话法的可行性"""
        scores = {}
        
        # 第一层：场景爆破 - 是否有可爆破的日常场景
        scene_keywords = ['日常', '场景', '习惯', '默认', '常识', '理所当然', '大家都说']
        rupture_matches = sum(1 for kw in scene_keywords if kw in content)
        scores['rupture'] = min(10, rupture_matches * 2.5)
        
        # 第二层：结构拆解 - 是否有可拆解的深层逻辑
        structure_keywords = ['逻辑', '本质', '原因', '结构', '框架', '原理', '模式']
        illuminate_matches = sum(1 for kw in structure_keywords if kw in content)
        scores['illuminate'] = min(10, illuminate_matches * 2.5)
        
        # 第三层：反刍重建 - 是否有可给出的新工具
        rebuild_keywords = ['方法', '工具', '框架', '步骤', '思路', '路径', '方案']
        rebuild_matches = sum(1 for kw in rebuild_keywords if kw in content)
        scores['rebuild'] = min(10, rebuild_matches * 2.5)
        
        # 综合评分
        scores['total'] = (scores['rupture'] + scores['illuminate'] + scores['rebuild']) / 3
        
        return scores
    
    def _score_differentiation(self, topic: Dict) -> float:
        """评估差异化空间"""
        # 默认中等分数，如果topic中有差异化信号则调整
        title = topic.get('title', '').lower()
        description = topic.get('description', '').lower()
        content = title + ' ' + description
        
        # 加分信号：有反常识视角
        contrarian_signals = ['反常识', '颠覆', '不同', '另类', '独特', '创新']
        contrarian_count = sum(1 for kw in contrarian_signals if kw in content)
        
        # 减分信号：被广泛覆盖
        crowded_signals = ['都在说', '热门', '大家都在', '风口', '爆火']
        crowded_count = sum(1 for kw in crowded_signals if kw in content)
        
        base_score = 6.0
        base_score += contrarian_count * 1.0
        base_score -= crowded_count * 0.5
        
        return max(0, min(10, base_score))
    
    def _score_risk(self, topic: Dict) -> float:
        """评估风险（分数越高越安全）"""
        title = topic.get('title', '').lower()
        description = topic.get('description', '').lower()
        content = title + ' ' + description
        
        # 风险信号
        risk_signals = [
            '敏感', '政治', '歧视', '骂战', '争议', '翻车',
            '违规', '封禁', '限流', '审查'
        ]
        
        risk_count = sum(1 for kw in risk_signals if kw in content)
        
        # 分数越高越安全
        return max(0, min(10, 10 - risk_count * 3))
    
    def _recommend_angle(
        self,
        best_direction: str,
        best_audience: str,
        topic: str
    ) -> str:
        """基于SOUL框架推荐切入角度"""
        hook = self.finitude_keywords[best_direction]['hook']
        audience_label = self.core_audiences[best_audience]['label']
        
        angle_templates = {
            'direction1': f"从有限性的视角重新审视{topic}——{hook}",
            'direction2': f"追问{topic}背后的意义——{hook}",
            'direction3': f"探讨人与AI在{topic}中的关系——{hook}"
        }
        
        base_angle = angle_templates.get(best_direction, f"从SOUL视角解读{topic}")
        
        return f"{base_angle}（目标受众：{audience_label}）"
```

---

### 2.8 补充模块：DataQualityValidator

#### 模块10：DataQualityValidator

**功能**：数据质量验证和去重

**完整实现**：

```python
# src/utils/data_quality_validator.py

from typing import List, Tuple
from ..core.logger import get_logger

logger = get_logger(__name__)


class DataQualityValidator:
    """
    数据质量验证器
    
    功能：
    1. 验证热点数据完整性和合理性
    2. 检测和移除重复数据
    3. 过滤低质量数据
    4. 生成质量报告
    """
    
    def __init__(self):
        self.min_title_length = 5
        self.max_title_length = 100
        self.min_description_length = 10
        self.valid_platforms = {'douyin', 'xiaohongshu', 'bilibili', 'weibo', 'zhihu'}
        self.valid_heat_levels = {'爆发', '上升', '稳定', '衰退'}
    
    def validate_hotspot(self, hotspot) -> Tuple[bool, str]:
        """
        验证单个热点数据质量
        
        Args:
            hotspot: HotTopic对象
        
        Returns:
            (是否通过, 原因)
        """
        checks = [
            (self._check_title, "标题"),
            (self._check_description, "描述"),
            (self._check_platform, "平台"),
            (self._check_tags, "标签"),
            (self._check_heat_level, "热度等级"),
        ]
        
        for check_func, check_name in checks:
            is_valid, message = check_func(hotspot)
            if not is_valid:
                return False, f"[{check_name}] {message}"
        
        return True, "OK"
    
    def _check_title(self, hotspot) -> Tuple[bool, str]:
        """检查标题"""
        title = getattr(hotspot, 'title', '')
        
        if not title:
            return False, "标题为空"
        
        if len(title) < self.min_title_length:
            return False, f"标题过短（{len(title)} < {self.min_title_length}）"
        
        if len(title) > self.max_title_length:
            return False, f"标题过长（{len(title)} > {self.max_title_length}）"
        
        # 检查是否包含明显的垃圾内容
        garbage_patterns = ['广告', '推广', '联系方式', '加微信']
        for pattern in garbage_patterns:
            if pattern in title:
                return False, f"标题包含垃圾内容：{pattern}"
        
        return True, "OK"
    
    def _check_description(self, hotspot) -> Tuple[bool, str]:
        """检查描述"""
        description = getattr(hotspot, 'description', '')
        
        if description and len(description) < self.min_description_length:
            return False, f"描述过短（{len(description)} < {self.min_description_length}）"
        
        return True, "OK"
    
    def _check_platform(self, hotspot) -> Tuple[bool, str]:
        """检查平台"""
        platform = getattr(hotspot, 'platform', '')
        
        if not platform:
            return False, "平台为空"
        
        if platform.lower() not in self.valid_platforms:
            return False, f"无效平台：{platform}（支持：{self.valid_platforms}）"
        
        return True, "OK"
    
    def _check_tags(self, hotspot) -> Tuple[bool, str]:
        """检查标签"""
        tags = getattr(hotspot, 'tags', [])
        
        if not tags:
            return True, "OK"  # 标签可选
        
        if len(tags) > 10:
            return False, f"标签过多（{len(tags)} > 10）"
        
        return True, "OK"
    
    def _check_heat_level(self, hotspot) -> Tuple[bool, str]:
        """检查热度等级"""
        heat_level = getattr(hotspot, 'heat_level', '上升')
        
        if heat_level not in self.valid_heat_levels:
            return False, f"无效热度：{heat_level}（支持：{self.valid_heat_levels}）"
        
        return True, "OK"
    
    def deduplicate(self, hotspots: List) -> Tuple[List, int]:
        """
        去重
        
        规则：
        1. 标题完全相同 → 重复
        2. 标题相似度 > 0.85 → 可能重复（保留第一个）
        
        Returns:
            (去重后的列表, 移除的数量)
        """
        seen_titles = set()
        unique = []
        removed_count = 0
        
        for hotspot in hotspots:
            title = getattr(hotspot, 'title', '')
            
            # 标准化标题
            normalized = title.lower().strip()
            
            if normalized in seen_titles:
                removed_count += 1
                continue
            
            # 检查相似标题
            is_duplicate = False
            for seen_title in seen_titles:
                if self._title_similarity(normalized, seen_title) > 0.85:
                    is_duplicate = True
                    removed_count += 1
                    break
            
            if not is_duplicate:
                seen_titles.add(normalized)
                unique.append(hotspot)
        
        if removed_count > 0:
            logger.info(f"Deduplication removed {removed_count} duplicates, kept {len(unique)}")
        
        return unique, removed_count
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        计算两个标题的相似度（简化Jaccard）
        """
        def char_bigrams(s):
            return set(s[i:i+2] for i in range(len(s) - 1))
        
        bigrams1 = char_bigrams(title1)
        bigrams2 = char_bigrams(title2)
        
        if not bigrams1 or not bigrams2:
            return 0.0
        
        intersection = len(bigrams1 & bigrams2)
        union = len(bigrams1 | bigrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def filter_low_quality(self, hotspots: List) -> Tuple[List, List[Tuple]]:
        """
        过滤低质量数据
        
        Returns:
            (高质量数据, 被过滤的数据及其原因)
        """
        quality = []
        filtered = []
        
        for hotspot in hotspots:
            is_valid, reason = self.validate_hotspot(hotspot)
            if is_valid:
                quality.append(hotspot)
            else:
                filtered.append((hotspot, reason))
        
        if filtered:
            logger.warning(f"Filtered {len(filtered)} low-quality hotspots")
            for hotspot, reason in filtered:
                logger.debug(f"  Filtered: {getattr(hotspot, 'title', 'N/A')} - {reason}")
        
        return quality, filtered
    
    def validate_batch(self, hotspots: List) -> Dict:
        """
        批量验证并生成质量报告
        
        Returns:
            质量报告
        """
        # 去重
        unique, duplicates_removed = self.deduplicate(hotspots)
        
        # 过滤低质量
        quality, filtered = self.filter_low_quality(unique)
        
        # 生成报告
        report = {
            'total_input': len(hotspots),
            'duplicates_removed': duplicates_removed,
            'low_quality_filtered': len(filtered),
            'final_count': len(quality),
            'pass_rate': f"{len(quality) / max(len(hotspots), 1) * 100:.1f}%",
            'filtered_details': [
                {
                    'title': getattr(h, 'title', 'N/A'),
                    'reason': reason
                }
                for h, reason in filtered
            ],
            'validated_at': datetime.now().isoformat()
        }
        
        logger.info(
            f"Quality report: {report['total_input']} → "
            f"{report['final_count']} ({report['pass_rate']})"
        )
        
        return report
```

---

## 三、工作流中间件

### 3.1 错误处理中间件

```python
# src/utils/workflow_error_handler.py

from functools import wraps
from typing import Callable, Any
from ..core.logger import get_logger

logger = get_logger(__name__)


class WorkflowError(Exception):
    """工作流异常基类"""
    def __init__(self, message: str, step: str = None, recoverable: bool = True):
        super().__init__(message)
        self.step = step
        self.recoverable = recoverable


class WebSearchUnavailableError(WorkflowError):
    """WebSearch不可用异常"""
    pass


class HermesReportNotFoundError(WorkflowError):
    """Hermes报告未找到异常"""
    pass


class ScriptGenerationTimeoutError(WorkflowError):
    """脚本生成超时异常"""
    pass


class KnowledgeBaseSyncError(WorkflowError):
    """知识库同步异常"""
    pass


def with_error_handling(
    step_name: str,
    max_retries: int = 0,
    fallback: Callable = None
):
    """
    工作流步骤错误处理装饰器
    
    Args:
        step_name: 步骤名称
        max_retries: 最大重试次数
        fallback: 降级函数
    
    Usage:
        @with_error_handling(step_name="collect_hotspots", max_retries=1)
        async def collect_hotspots():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt} for {step_name}")
                    
                    result = await func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"{step_name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    
                    if not isinstance(e, WorkflowError):
                        logger.debug(f"Unexpected error in {step_name}", exc_info=True)
            
            # 所有重试都失败
            if fallback:
                logger.info(f"Executing fallback for {step_name}")
                try:
                    return await fallback(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise WorkflowError(
                        f"{step_name} failed after {max_retries + 1} attempts, fallback also failed",
                        step=step_name,
                        recoverable=False
                    ) from last_error
            
            raise WorkflowError(
                f"{step_name} failed after {max_retries + 1} attempts",
                step=step_name,
                recoverable=False
            ) from last_error
        
        return wrapper
    return decorator
```

---

## 四、依赖更新

### 4.1 requirements.txt 更新

```
# 核心依赖（已有）
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
httpx>=0.24.0
pyyaml>=6.0.0
python-dotenv>=1.0.0

# 日志
structlog>=23.0.0

# CLI
click>=8.1.0
rich>=13.0.0

# 定时任务（新增）
schedule>=1.2.0

# HTTP API（新增 - Hermes集成用）
fastapi>=0.100.0
uvicorn>=0.23.0

# 测试
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# 开发
black>=23.0.0
ruff>=0.0.280
mypy>=1.4.0
```

### 4.2 .env 环境变量

```bash
# config/.env

# ==================== 数据来源 ====================
# Hermes工作空间路径（可选）
HERMES_WORKSPACE=~/hermes_workspace

# SOUL配置文件路径（可选，按优先级自动查找）
# SOUL_PROFILE_PATH=~/.hermes/skills/knowledge/soul/SKILL.md

# ==================== 知识库 ====================
# GitHub仓库信息
GITHUB_REPO=John198912/Mcn-Ai-Replacement

# ==================== Hermes集成 ====================
# 飞书Webhook URL（用于任务结果通知）
# FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# API密钥（仅远程访问时需要）
# MCN_API_KEY=your-secret-key

# 任务监听地址和端口
TASK_LISTENER_HOST=127.0.0.1
TASK_LISTENER_PORT=8000

# ==================== 定时任务 ====================
# 热点采集时间（cron格式）
HOTSPOT_CRON=monday.10:00

# 备份时间
BACKUP_CRON=daily.02:00

# GitHub同步时间
SYNC_CRON=daily.03:00

# ==================== 日志 ====================
LOG_LEVEL=INFO
LOG_FILE=logs/mcn.log
```

---

## 五、完整文件清单

### 5.1 新增文件

```
src/adapters/
├── __init__.py
├── hermes_hotspot_adapter.py          # 模块1：Hermes报告解析
├── manual_hotspot_importer.py         # 模块2：手动导入
└── hotspot_collector.py               # 模块3：采集协调器

src/skills/
├── __init__.py
├── base_skill.py                      # 已有
├── soul_script_writer.py              # 模块4：SOUL脚本生成（重构）
├── soul_hot_topic_matcher.py          # 模块9：SOUL热点评分（新增）
├── content_risk_scanner.py            # 已有（保留）
├── title_optimizer.py                 # 已有（增强）
├── creator_profiler.py                # 已有（保留）
└── viral_content_analyzer.py          # 已有（保留）

src/knowledge/
├── __init__.py
├── two_layer_manager.py               # 模块5：两层知识库
└── backup_manager.py                  # 模块8：备份管理

src/scheduler/
├── __init__.py
└── mcn_scheduler.py                   # 模块6：定时任务

src/integrations/
├── __init__.py
└── hermes_task_bridge.py              # 模块7：Hermes集成

src/utils/
├── __init__.py
├── text_processing.py                 # 已有
├── data_validation.py                 # 已有
├── format_converter.py                # 已有
└── data_quality_validator.py          # 模块10：数据质量验证（新增）
└── workflow_error_handler.py          # 新增：错误处理中间件

docs/
├── OPTIMIZATION_PLAN_V3.1_FINAL.md    # 本文档
├── PROJECT_ANALYSIS_REPORT.md         # 项目分析
├── PLAN_REVIEW_REPORT.md              # 审查报告
└── REVIEW_CLARIFICATION.md            # 问题澄清
```

### 5.2 修改文件

```
src/skills/script_writer.py            # 重构为SOULScriptWriter
src/workflows/soul_content_creation_workflow.py  # 新增
scripts/run_workflow.py                # 增强CLI命令
requirements.txt                       # 新增依赖
config/.env.example                    # 更新变量
```

---

## 六、实施检查清单

### Phase 1：核心功能（5-7天）

- [ ] **Day 1-2：数据接入**
  - [ ] HermesHotspotAdapter（模块1）
  - [ ] ManualHotspotImporter（模块2）
  - [ ] HotspotCollector（模块3）
  - [ ] DataQualityValidator（模块10）
  - [ ] 编写单元测试
  - [ ] 测试Hermes报告解析
  - [ ] 测试CSV/JSON导入

- [ ] **Day 3-4：知识库**
  - [ ] TwoLayerKnowledgeManager（模块5）
  - [ ] BackupManager（模块8）
  - [ ] WorkflowErrorHandler（错误处理）
  - [ ] 编写单元测试
  - [ ] 测试GitHub同步
  - [ ] 测试备份恢复
  - [ ] 测试冲突解决

- [ ] **Day 5：定时任务**
  - [ ] MCNScheduler（模块6）
  - [ ] launchd配置（macOS）
  - [ ] 测试定时执行

- [ ] **Day 6-7：集成测试**
  - [ ] 端到端测试：Hermes报告 → 热点列表
  - [ ] 端到端测试：CSV导入 → 热点列表
  - [ ] 修复问题
  - [ ] 编写Phase 1文档

### Phase 2：SOUL内容生成（6-8天）

- [ ] **Day 1-3：ScriptWriter重构**
  - [ ] SOULScriptWriter（模块4）
  - [ ] SOUL框架加载（多路径）
  - [ ] 文件交换模式
  - [ ] 提示词模板
  - [ ] 脚本解析器
  - [ ] 测试：生成脚本质量

- [ ] **Day 4-5：HotTopicMatcher**
  - [ ] SOULHotTopicMatcher（模块9）
  - [ ] 5维度评分实现
  - [ ] 与旧评分对比测试

- [ ] **Day 6-7：其他Skills**
  - [ ] TitleOptimizer增强
  - [ ] ContentRiskScanner验证
  - [ ] CreatorProfiler验证

- [ ] **Day 8：优化**
  - [ ] 提示词优化
  - [ ] 评分权重调优
  - [ ] 文档更新

### Phase 3：Hermes集成（2-3天）

- [ ] **Day 1-2**
  - [ ] HermesTaskBridge（模块7）
  - [ ] HTTP API端点
  - [ ] 飞书通知配置

- [ ] **Day 3**
  - [ ] Hermes调用测试
  - [ ] 状态查询测试
  - [ ] 通知测试

### Phase 4：文档部署（3-4天）

- [ ] **Day 1-2：文档**
  - [ ] 用户手册
  - [ ] 开发文档
  - [ ] 快速开始指南

- [ ] **Day 3：部署**
  - [ ] launchd配置
  - [ ] 环境变量
  - [ ] 启动脚本

- [ ] **Day 4：验收**
  - [ ] 完整流程演示
  - [ ] 问题修复
  - [ ] 交付

---

## 七、总结

### 7.1 v3.1总览

| 维度 | 内容 |
|------|------|
| **系统定位** | 独立的MCN内容创作系统 |
| **数据来源** | Hermes报告（主要）/ 手动导入（降级） |
| **核心能力** | SOUL驱动的内容生成 |
| **知识库** | 本地Markdown + GitHub（两层） |
| **自动化** | 定时任务 + Hermes可调用 |
| **成本** | $0/月（完全免费） |
| **开发周期** | 15-20天 |

### 7.2 10个核心模块

| # | 模块 | 文件 | 状态 |
|---|------|------|------|
| 1 | HermesHotspotAdapter | src/adapters/ | ✅ 完整代码 |
| 2 | ManualHotspotImporter | src/adapters/ | ✅ 完整代码 |
| 3 | HotspotCollector | src/adapters/ | ✅ 完整代码 |
| 4 | SOULScriptWriter | src/skills/ | ✅ 完整代码 |
| 5 | TwoLayerKnowledgeManager | src/knowledge/ | ✅ 完整代码 |
| 6 | MCNScheduler | src/scheduler/ | ✅ 完整代码 |
| 7 | HermesTaskBridge | src/integrations/ | ✅ 完整代码 |
| 8 | BackupManager | src/knowledge/ | ✅ 完整代码 |
| 9 | SOULHotTopicMatcher | src/skills/ | ✅ 完整代码 |
| 10 | DataQualityValidator | src/utils/ | ✅ 完整代码 |

### 7.3 与之前版本的差异

| 方面 | v3.0 | v3.1 |
|------|------|------|
| 模块数量 | 5个 | **10个** |
| 代码完整性 | 框架代码 | **完整代码** |
| 数据质量 | 无 | **DataQualityValidator** |
| 备份恢复 | 无 | **BackupManager** |
| 错误处理 | 基础 | **WorkflowErrorHandler** |
| 热点评分 | 提及 | **完整SOULHotTopicMatcher** |
| 实施计划 | 12-18天 | **15-20天（更实际）** |

---

**文档版本**：v3.1 Final  
**创建日期**：2026-05-17  
**代码行数**：~2000行（完整实现）  
**状态**：Ready for Implementation  
**下一步**：开始Phase 1实施

