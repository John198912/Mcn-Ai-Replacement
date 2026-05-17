"""对标分析流水线 — 四层分析：发掘→拆解→对比→反哺."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from ..core.logger import get_logger

logger = get_logger(__name__)


class CreatorPipeline:
    """对标分析流水线.

    四层分析：
    1. 发掘 — 解析创作者发现表，建档
    2. 拆解 — 解析深度分析，提取爆款规律
    3. 对比 — 构建差异化矩阵
    4. 反哺 — 差异化信号注入评分，对标参考注入脚本

    对标数据存储：data/creator_pipeline.json
    """

    def __init__(self, data_file: str = None):
        self.data_file = Path(data_file or "data/creator_pipeline.json")
        self.data = self._load_data()
        self._init_structure()

    def _load_data(self) -> Dict:
        if self.data_file.exists():
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        return {}

    def _save_data(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))

    def _init_structure(self):
        defaults = {
            "creators": [],        # 创作者档案列表
            "viral_patterns": [],  # 爆款规律
            "differentiation": {}, # 差异化机会
            "last_updated": None,
        }
        for key, val in defaults.items():
            if key not in self.data:
                self.data[key] = val

    # ==================== 报告导入 ====================

    def import_report(self, report_path: str) -> Dict:
        """导入 widesearch-creator-analysis 报告.

        自动识别并解析四层内容：
        - 创作者发现表
        - Top 5 深度拆解
        - 对比矩阵
        - 差异化建议

        Returns:
            导入统计
        """
        content = Path(report_path).read_text(encoding="utf-8")
        stats = {}

        # 第一层：创作者发现
        discovery = self._parse_discovery_table(content)
        for creator in discovery:
            self._upsert_creator(creator)
        stats["discovered"] = len(discovery)

        # 第二层：深度拆解
        deep_analyses = self._parse_deep_analysis(content)
        for analysis in deep_analyses:
            self._attach_deep_analysis(analysis)
        stats["deep_analyzed"] = len(deep_analyses)

        # 第三层：对比矩阵
        comparison = self._parse_comparison_matrix(content)
        if comparison:
            self.data["comparison"] = comparison
            stats["compared"] = len(comparison)

        # 第四层：差异化机会
        diff_signals = self._parse_differentiation(content)
        if diff_signals:
            self.data["differentiation"] = diff_signals
            stats["differentiation_signals"] = len(diff_signals)

        # 提取爆款规律
        viral = self._extract_viral_patterns(content)
        self.data["viral_patterns"].extend(viral)
        stats["viral_patterns"] = len(viral)

        self.data["last_updated"] = datetime.now().isoformat()
        self._save_data()

        logger.info("对标报告已导入", **stats)
        return stats

    def _parse_discovery_table(self, content: str) -> List[Dict]:
        """解析创作者发现表.

        | 平台 | 账号名称 | 粉丝数 | 层级 | 内容定位 | 更新频率 | 近期代表作 | 内容风格 | 对标价值 |
        """
        creators = []
        pattern = r"\|\s*平台\s*\|.*?账号名称.*?\|.*?粉丝数.*?\|.*?(?=\n\n\S|\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return creators

        lines = match.group().strip().split("\n")
        for line in lines:
            if not line.strip() or line.startswith("|-") or "平台" in line:
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) < 8:
                continue

            creators.append({
                "platform": cells[0],
                "account_name": cells[1],
                "followers": cells[2],
                "tier": cells[3] if len(cells) > 3 else "",
                "positioning": cells[4] if len(cells) > 4 else "",
                "frequency": cells[5] if len(cells) > 5 else "",
                "top_content": cells[6] if len(cells) > 6 else "",
                "style": cells[7] if len(cells) > 7 else "",
                "learnable": cells[8] if len(cells) > 8 else "",
                "first_seen": datetime.now().strftime("%Y-%m-%d"),
            })
        return creators

    def _parse_deep_analysis(self, content: str) -> List[Dict]:
        """解析Top 5深度拆解.

        识别 #### A. 创作者画像、#### B. 内容策略分析 等结构.
        """
        analyses = []
        # 按创作者分割
        sections = re.split(r"\n#{2,4}\s+(?:Top\s*\d+|创作者|[A-D][.\s])", content)
        for section in sections[1:]:
            lines = section.strip().split("\n")
            if not lines:
                continue

            title = lines[0].strip() if lines else ""
            body = "\n".join(lines[1:])

            # 提取关键信息
            name = self._extract_field(body, "账号名|账号名称")
            if not name:
                name = title[:30]

            analysis = {
                "account_name": name,
                "positioning": self._extract_field(body, "人设定位|核心定位"),
                "audience": self._extract_field(body, "目标受众"),
                "business_model": self._extract_field(body, "商业模式|变现方式"),
                "content_patterns": self._extract_field(body, "内容策略|内容模式"),
                "growth_path": self._extract_field(body, "增长路径|起号策略"),
                "viral_formula": self._extract_field(body, "爆款公式|爆款规律"),
                "differentiation": self._extract_field(body, "差异化|独特优势"),
            }
            if any(analysis.values()):
                analyses.append(analysis)
        return analyses

    def _parse_comparison_matrix(self, content: str) -> List[Dict]:
        """解析对比矩阵."""
        matrix = []
        pattern = r"\|\s*维度\s*\|.*?\|.*?\|.*?\|.*?(?=\n\n|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return matrix

        lines = match.group().strip().split("\n")
        for line in lines:
            if not line.strip() or line.startswith("|-") or "维度" in line:
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 4:
                matrix.append({
                    "dimension": cells[0],
                    "competitor_a": cells[1] if len(cells) > 1 else "",
                    "competitor_b": cells[2] if len(cells) > 2 else "",
                    "me": cells[3] if len(cells) > 3 else "",
                    "gap": cells[4] if len(cells) > 4 else "",
                })
        return matrix

    def _parse_differentiation(self, content: str) -> Dict:
        """解析差异化机会."""
        return {
            "content_whitespace": self._extract_list(content, "内容空白|空白机会"),
            "underserved_angles": self._extract_list(content, "未被满足|受众痛点"),
            "unique_strengths": self._extract_list(content, "我的优势|独特优势"),
        }

    def _extract_viral_patterns(self, content: str) -> List[Dict]:
        """提取爆款规律."""
        patterns = []
        # 查找 Hook模式、标题公式、结构模板
        hooks = re.findall(r"(?:Hook|标题)[公式模式：:].*?(.+?)(?=\n|$)", content)
        for hook in hooks[:5]:
            patterns.append({"type": "hook_formula", "content": hook.strip()})

        structures = re.findall(r"(?:结构|框架)[：:]\s*(.+?)(?=\n|$)", content)
        for struct in structures[:5]:
            patterns.append({"type": "structure_template", "content": struct.strip()})

        return patterns

    # ==================== 创作者管理 ====================

    def _upsert_creator(self, creator: Dict):
        """更新或新增创作者."""
        for i, existing in enumerate(self.data["creators"]):
            if existing.get("account_name") == creator.get("account_name"):
                existing.update(creator)
                return
        self.data["creators"].append(creator)

    def _attach_deep_analysis(self, analysis: Dict):
        """将深度分析附着到对应创作者."""
        name = analysis.get("account_name", "")
        for creator in self.data["creators"]:
            if creator.get("account_name") == name:
                creator["deep_analysis"] = analysis
                return

    def list_creators(self, tier: str = None) -> List[Dict]:
        """列出对标创作者."""
        creators = self.data.get("creators", [])
        if tier:
            creators = [c for c in creators if c.get("tier") == tier]
        return creators

    # ==================== 差异化信号 ====================

    def get_differentiation_signals(self) -> Dict:
        """获取差异化信号，注入 SOULHotTopicMatcher.

        Returns:
            {content_gaps: [...], viral_patterns: [...], unique_angles: [...]}
        """
        return {
            "content_gaps": self.data.get("differentiation", {}).get("content_whitespace", []),
            "viral_patterns": [
                p.get("content", "") for p in self.data.get("viral_patterns", [])[:5]
            ],
            "unique_angles": self.data.get("differentiation", {}).get("unique_strengths", []),
            "top_creators_count": len(self.data.get("creators", [])),
        }

    def get_script_references(self, topic: str) -> List[Dict]:
        """根据选题查找对标参考内容.

        Returns:
            相关对标创作者的处理方式参考
        """
        refs = []
        topic_lower = topic.lower()
        for creator in self.data.get("creators", []):
            positioning = creator.get("positioning", "").lower()
            learnable = creator.get("learnable", "").lower()
            # 子串匹配
            if topic_lower in positioning or positioning in topic_lower or \
               topic_lower in learnable or learnable in topic_lower:
                refs.append({
                    "account": creator.get("account_name", ""),
                    "approach": creator.get("learnable", ""),
                    "style": creator.get("style", ""),
                    "top_content": creator.get("top_content", ""),
                })
        return refs[:3]

    # ==================== 工具方法 ====================

    @staticmethod
    def _extract_field(text: str, field_names: str) -> str:
        """提取字段值."""
        for name in field_names.split("|"):
            pattern = rf"(?:\*{name}\*|{name})[：:]\s*(.+?)(?=\n\*\*|\n-|\n\n|\Z)"
            m = re.search(pattern, text, re.DOTALL)
            if m:
                return m.group(1).strip()[:200]
        return ""

    @staticmethod
    def _extract_list(text: str, field_names: str) -> List[str]:
        """提取列表型字段."""
        items = []
        for name in field_names.split("|"):
            pattern = rf"(?:\*{name}\*|{name})[：:]\s*\n((?:\s*[-*]\s*.+\n?)+)"
            m = re.search(pattern, text, re.DOTALL)
            if m:
                items = [re.sub(r"^\s*[-*]\s*", "", i).strip()
                         for i in m.group(1).strip().split("\n") if i.strip()]
        return items
