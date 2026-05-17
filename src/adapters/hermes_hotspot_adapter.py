"""Hermes热点报告适配器 - 读取Hermes热点采集系统的日报/周报."""

from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from ..core.logger import get_logger

logger = get_logger(__name__)


class HermesHotspotAdapter:
    """Hermes热点报告适配器.

    功能：
    1. 读取Hermes热点采集系统的日报/周报
    2. 解析P0/P1热点数据
    3. 转换为MCN可用格式

    这是真正的"引用Hermes已有能力"：
    - Hermes已有成熟的四源采集（MCP Brave + Tavily + AI HOT + 博客）
    - Hermes已有三关审核（时效 + 来源 + 匹配度）
    - MCN系统只需读取报告，无需重复实现
    """

    def __init__(self, hermes_workspace: str = "~/hermes_workspace"):
        self.workspace = Path(hermes_workspace).expanduser()
        self.reports_dir = self.workspace / "reports" / "hotspot"
        self.available = self.reports_dir.exists()

        if self.available:
            logger.info("Hermes报告目录可用", path=str(self.reports_dir))
        else:
            logger.warning("Hermes报告目录不存在", path=str(self.reports_dir))

    async def fetch_latest_hotspots(self, days: int = 7) -> List[Dict]:
        """读取最近N天的Hermes热点报告.

        Args:
            days: 读取最近N天的报告

        Returns:
            热点字典列表，包含标题、平台、评分等字段
        """
        if not self.available:
            logger.info("Hermes报告不可用")
            return []

        all_hotspots = []

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            # 尝试两种命名格式：daily_YYYY-MM-DD.md 和 report_daily_YYYY-MM-DD.md
            report_file = self.reports_dir / f"daily_{date}.md"
            if not report_file.exists():
                report_file = self.reports_dir / f"report_daily_{date}.md"

            if report_file.exists():
                try:
                    parsed = self._parse_hermes_report(report_file)
                    all_hotspots.extend(parsed)
                    logger.info("解析报告", file=report_file.name, count=len(parsed))
                except Exception as e:
                    logger.error("解析报告失败", file=report_file.name, error=str(e))

        # 去重
        all_hotspots = self._deduplicate(all_hotspots)
        logger.info("Hermes热点加载完成", total=len(all_hotspots))

        return all_hotspots

    def fetch_report_by_date(self, date_str: str) -> List[Dict]:
        """读取指定日期的Hermes报告.

        Args:
            date_str: 日期字符串，格式YYYY-MM-DD

        Returns:
            热点列表
        """
        report_file = self.reports_dir / f"daily_{date_str}.md"
        if not report_file.exists():
            logger.warning("报告不存在", date=date_str)
            return []
        return self._parse_hermes_report(report_file)

    def _parse_hermes_report(self, report_path: Path) -> List[Dict]:
        """解析Hermes报告.

        支持两种格式：

        格式1（新版）：
        | 优先级 | 标题（原文+中文） | 来源 | 概览 | 关联度 |
        | P0 | **title**（中文） | source | description | 高 |

        格式2（旧版）：
        ## 🔥 P0 热点（直接选题）
        | 序号 | 话题 | 来源 | 标签 | SOUL适配度 | 推荐角度 |
        """
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 先尝试新版格式：优先级列 + 标题列
        hotspots = self._parse_new_format(content)
        if hotspots:
            return hotspots

        # 再尝试旧版格式
        hotspots = []
        for section_name in ["P0 热点", "P1 热点"]:
            section = self._extract_section(content, section_name)
            if section:
                priority = "P0" if "P0" in section_name else "P1"
                hotspots.extend(self._parse_hotspot_table(section, priority=priority))

        if hotspots:
            return hotspots

        # 备用：列表格式
        return self._parse_list_format(content)

    def _parse_new_format(self, content: str) -> List[Dict]:
        """解析新版Hermes报告格式（优先级 | 标题 | 来源 | 概览 | 关联度）."""
        hotspots = []

        # 找到主要的热点表格
        # 寻找以 | 优先级 | 标题 开头的表格
        table_pattern = r"\|\s*优先级\s*\|.*?标题.*?\|.*?来源.*?\|.*?(?=\n\n\S|\n##|\Z)"
        matches = re.findall(table_pattern, content, re.DOTALL)

        for table_section in matches:
            lines = table_section.strip().split("\n")
            # 找到数据行（跳过表头和分隔线）
            for line in lines:
                if not line.strip() or line.startswith("|-") or "优先级" in line:
                    continue
                cells = [c.strip() for c in line.split("|") if c.strip()]
                if len(cells) < 4:
                    continue

                priority = cells[0] if cells[0] in ("P0", "P1", "P2") else "P1"
                title_cell = cells[1] if len(cells) > 1 else ""

                # 提取标题：**English title**（中文翻译）→ 取中文部分，无中文则用英文
                title = self._extract_title(title_cell)
                platform = self._extract_platform(cells[2] if len(cells) > 2 else "")
                description = cells[3] if len(cells) > 3 else ""
                tags = self._extract_tags_from_line(line)

                if title:
                    hotspots.append({
                        "title": title,
                        "platform": platform,
                        "tags": tags,
                        "description": description,
                        "priority": priority,
                        "heat_level": "上升" if priority == "P0" else "稳定",
                        "source": "hermes",
                        "recommended_angle": description[:200] if description else "",
                    })

        return hotspots

    def _extract_title(self, title_cell: str) -> str:
        """从标题单元格提取可读标题.

        输入：**Ankur Warikoo shuts down...**（印度顶级教育创作者关停...）
        输出：印度顶级教育创作者关停课程业务，暗示AI巨大冲击
        """
        # 优先取中文翻译部分（括号内的中文）
        m = re.search(r"（([^）]+)）", title_cell)
        if m:
            return m.group(1)

        # 否则取英文（去掉 ** 标记）
        title = re.sub(r"\*\*", "", title_cell)
        # 截取前100字符
        return title[:100] if len(title) > 100 else title

    def _extract_platform(self, source: str) -> str:
        """从来源推断平台."""
        source_lower = source.lower()
        if any(p in source_lower for p in ["reddit", "hn", "youtube"]):
            return "bilibili"  # 海外内容适合B站
        if any(p in source_lower for p in ["x：", "twitter", "x.com"]):
            return "douyin"
        return "douyin"

    def _extract_tags_from_line(self, line: str) -> List[str]:
        """从行内容提取标签."""
        tags = []
        tag_pattern = r"\[([^\]]+)\]"
        matches = re.findall(tag_pattern, line)
        for m in matches:
            parts = [p.strip() for p in m.split("+")]
            tags.extend(parts)
        return list(set(tags)) if tags else ["AI"]

    def _extract_section(self, content: str, section_name: str) -> str:
        """提取指定section的内容."""
        pattern = rf"##\s+[🔥🟡]\s+{re.escape(section_name)}.*?\n(.*?)(?=\n##\s|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1)
        return ""

    def _parse_hotspot_table(self, section: str, priority: str) -> List[Dict]:
        """解析热点表格."""
        hotspots = []
        lines = section.strip().split("\n")

        # 找到表格头
        header_idx = -1
        for i, line in enumerate(lines):
            if "话题" in line:
                header_idx = i
                break
        if header_idx == -1:
            return hotspots

        # 解析表头，确定列索引
        header = lines[header_idx]
        columns = [col.strip() for col in header.split("|") if col.strip()]

        topic_idx = next((i for i, col in enumerate(columns) if "话题" in col), 0)
        platform_idx = next((i for i, col in enumerate(columns) if "来源" in col), 1)
        tags_idx = next((i for i, col in enumerate(columns) if "标签" in col), 2)
        soul_idx = next((i for i, col in enumerate(columns) if "SOUL" in col or "适配" in col), -1)
        angle_idx = next((i for i, col in enumerate(columns) if "角度" in col), -1)

        for line in lines[header_idx + 2:]:
            if not line.strip() or line.lstrip().startswith("#"):
                break
            cells = [cell.strip() for cell in line.split("|") if cell.strip()]
            if len(cells) < len(columns):
                continue

            tags_str = cells[tags_idx] if tags_idx < len(cells) else ""
            tags = self._parse_tags(tags_str)

            hotspot = {
                "title": cells[topic_idx] if topic_idx < len(cells) else "",
                "platform": cells[platform_idx] if platform_idx < len(cells) else "",
                "tags": tags,
                "soul_alignment": cells[soul_idx] if soul_idx >= 0 and soul_idx < len(cells) else "",
                "recommended_angle": cells[angle_idx] if angle_idx >= 0 and angle_idx < len(cells) else "",
                "priority": priority,
                "heat_level": "上升",
                "source": "hermes",
            }
            hotspots.append(hotspot)

        return hotspots

    def _parse_list_format(self, content: str) -> List[Dict]:
        """解析列表格式（备用解析器）."""
        hotspots = []
        # 匹配常见的列表项：- **话题**：描述
        pattern = r"[-*]\s+\*?\*?([^*\n]+)\*?\*?\s*[:：]\s*(.+?)(?=\n[-*]|\n\n|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            title = match[0].strip()
            description = match[1].strip()
            # 尝试从描述中提取平台
            platform = "未知"
            for p in ["douyin", "抖音", "xiaohongshu", "小红书", "bilibili", "B站"]:
                if p.lower() in description.lower():
                    platform = p
                    break
            hotspots.append({
                "title": title,
                "platform": platform,
                "tags": [],
                "soul_alignment": "",
                "recommended_angle": "",
                "priority": "P1",
                "heat_level": "上升",
                "source": "hermes",
                "description": description,
            })
        return hotspots

    @staticmethod
    def _parse_tags(tags_str: str) -> List[str]:
        """解析标签字符串.

        输入：[AI][超级个体]
        输出：['AI', '超级个体']
        """
        pattern = r"\[([^\]]+)\]"
        return re.findall(pattern, tags_str)

    @staticmethod
    def _deduplicate(hotspots: List[Dict]) -> List[Dict]:
        """去重：标题相同视为重复."""
        seen = set()
        unique = []
        for hotspot in hotspots:
            title = hotspot.get("title", "").lower().strip()
            if title not in seen:
                seen.add(title)
                unique.append(hotspot)
        return unique
