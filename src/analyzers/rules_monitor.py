"""平台规则情报系统 — 解析规则变动报告，动态管理平台规则库."""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..core.logger import get_logger

logger = get_logger(__name__)

# 平台→中文名映射
PLATFORM_NAMES = {
    "douyin": "抖音", "xiaohongshu": "小红书",
    "bilibili": "B站", "weibo": "微博", "zhihu": "知乎",
}


class RulesMonitor:
    """平台规则情报系统.

    功能：
    1. 解析 widesearch-platform-rules 报告
    2. 维护各平台动态规则库
    3. 检查脚本是否符合最新平台规则
    4. 生成脚本规则提醒上下文

    规则库结构：
    {
      "douyin": {
        "algorithm_changes": [{"date": "", "content": "", "source": "", "confidence": ""}],
        "content_policies": [...],
        "restricted_topics": [...],
        "promotions": [...],
        "overall_stance": "tightening|relaxing|neutral",
        "last_updated": "ISO datetime"
      }
    }
    """

    def __init__(self, rules_file: str = None):
        self.rules_file = Path(rules_file or "data/platform_rules.json")
        self.rules: Dict[str, Dict] = self._load_rules()
        self._init_default_rules()

    def _load_rules(self) -> Dict:
        if self.rules_file.exists():
            return json.loads(self.rules_file.read_text(encoding="utf-8"))
        return {}

    def _save_rules(self):
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        self.rules_file.write_text(json.dumps(self.rules, ensure_ascii=False, indent=2))

    def _init_default_rules(self):
        """初始化默认规则库（各平台入口）."""
        for platform in PLATFORM_NAMES:
            if platform not in self.rules:
                self.rules[platform] = {
                    "algorithm_changes": [],
                    "content_policies": [],
                    "restricted_topics": [],
                    "promotions": [],
                    "overall_stance": "neutral",
                    "last_updated": None,
                }

    # ==================== 报告解析 ====================

    def import_report(self, report_path: str) -> Dict:
        """导入 widesearch-platform-rules 报告.

        解析报告中的变动清单表格、重点解读、扶持机会等。

        Returns:
            导入统计 {platform: changes_count}
        """
        content = Path(report_path).read_text(encoding="utf-8")
        stats = {}

        # 1. 解析变动清单表格
        changes = self._parse_changes_table(content)
        for change in changes:
            platform = change["platform"]
            self._add_change(platform, change)
            stats[platform] = stats.get(platform, 0) + 1

        # 2. 解析重点解读
        interpretations = self._parse_interpretations(content)
        for interp in interpretations:
            platform = interp.get("platform", "douyin")
            self.rules[platform].setdefault("interpretations", []).append(interp)

        # 3. 解析扶持机会
        promotions = self._parse_promotions(content)
        for promo in promotions:
            platform = promo.get("platform", "douyin")
            self.rules[platform]["promotions"].append(promo)

        # 4. 解析信号汇总
        signals = self._parse_signals(content)
        for platform, stance in signals.items():
            self.rules[platform]["overall_stance"] = stance
        self.rules[platform]["last_updated"] = datetime.now().isoformat()

        self._save_rules()
        logger.info("规则报告已导入", stats=stats)
        return stats

    def _parse_changes_table(self, content: str) -> List[Dict]:
        """解析变动清单表格.

        | 平台 | 变动类型 | 变动内容摘要 | 发现来源 | 可信度 | 影响范围 | 对我的影响 |
        """
        changes = []
        # 找到表格：以 | 平台 | 变动类型 开头
        pattern = r"\|\s*平台\s*\|.*?变动.*?\|.*?(?=\n\n\S|\n##|\Z)"
        table_match = re.search(pattern, content, re.DOTALL)
        if not table_match:
            return changes

        lines = table_match.group().strip().split("\n")
        for line in lines:
            if not line.strip() or line.startswith("|-") or "平台" in line:
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) < 6:
                continue

            platform_name = cells[0]
            platform = self._resolve_platform(platform_name)

            changes.append({
                "platform": platform,
                "type": cells[1] if len(cells) > 1 else "",
                "content": cells[2] if len(cells) > 2 else "",
                "source": cells[3] if len(cells) > 3 else "",
                "confidence": cells[4] if len(cells) > 4 else "待验证",
                "scope": cells[5] if len(cells) > 5 else "",
                "impact": cells[6] if len(cells) > 6 else "中",
                "date": datetime.now().strftime("%Y-%m-%d"),
            })
        return changes

    def _parse_interpretations(self, content: str) -> List[Dict]:
        """解析重点解读部分.

        #### [变动标题]
        - **变动详情**：...
        - **对我的具体影响**：...
        - **建议调整**：...
        """
        interpretations = []
        # 找到 #### 标题块
        blocks = re.split(r"\n####\s+", content)
        for block in blocks[1:]:  # 跳过第一个（不是解读）
            lines = block.strip().split("\n")
            title = lines[0].strip() if lines else ""
            body = "\n".join(lines[1:])

            # 提取关键字段
            detail = self._extract_field(body, "变动详情")
            impact = self._extract_field(body, "对我的具体影响")
            suggestion = self._extract_field(body, "建议调整")

            if title:
                interpretations.append({
                    "title": title,
                    "detail": detail,
                    "impact": impact,
                    "suggestion": suggestion,
                    "platform": self._resolve_platform(title),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })
        return interpretations

    def _parse_promotions(self, content: str) -> List[Dict]:
        """解析平台扶持机会表格."""
        promotions = []
        pattern = r"\|\s*平台\s*\|.*?活动名称.*?\|.*?(?=\n\n|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return promotions

        lines = match.group().strip().split("\n")
        for line in lines:
            if not line.strip() or line.startswith("|-") or "平台" in line:
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 6:
                promotions.append({
                    "platform": self._resolve_platform(cells[0]),
                    "name": cells[1] if len(cells) > 1 else "",
                    "condition": cells[2] if len(cells) > 2 else "",
                    "deadline": cells[3] if len(cells) > 3 else "",
                    "benefit": cells[4] if len(cells) > 4 else "",
                    "recommend": cells[5] if len(cells) > 5 else "",
                })
        return promotions

    def _parse_signals(self, content: str) -> Dict[str, str]:
        """解析信号汇总 — 各平台收紧/放松趋势."""
        signals = {}
        for platform in PLATFORM_NAMES:
            platform_name = PLATFORM_NAMES[platform]
            if platform_name in content:
                if "收紧" in content:
                    signals[platform] = "tightening"
                elif "放松" in content:
                    signals[platform] = "relaxing"
                else:
                    signals[platform] = "neutral"
        return signals

    def _resolve_platform(self, text: str) -> str:
        """从文本中解析平台标识."""
        mapping = {
            "抖音": "douyin", "douyin": "douyin",
            "小红书": "xiaohongshu", "xiaohongshu": "xiaohongshu",
            "B站": "bilibili", "bilibili": "bilibili", "b站": "bilibili",
            "微博": "weibo", "weibo": "weibo",
            "知乎": "zhihu", "zhihu": "zhihu",
        }
        for key, val in mapping.items():
            if key.lower() in text.lower():
                return val
        return "douyin"

    @staticmethod
    def _extract_field(text: str, field_name: str) -> str:
        """提取字段值：**字段名**：内容."""
        pattern = rf"\*{field_name}\*[：:]\s*(.+?)(?=\n\*\*|\n\n|\Z)"
        m = re.search(pattern, text, re.DOTALL)
        return m.group(1).strip() if m else ""

    def _add_change(self, platform: str, change: Dict):
        """添加变动记录."""
        if platform not in self.rules:
            self._init_default_rules()
        change_type = change.get("type", "")
        if "算法" in change_type:
            self.rules[platform]["algorithm_changes"].append(change)
        elif "规则" in change_type or "规范" in change_type:
            self.rules[platform]["content_policies"].append(change)
        else:
            self.rules[platform]["content_policies"].append(change)

    # ==================== 规则查询 ====================

    def check_content(self, script: Dict, platform: str) -> List[Dict]:
        """检查脚本是否符合平台最新规则.

        Returns:
            风险点列表 [{type, content, severity, suggestion}]
        """
        risks = []
        if platform not in self.rules:
            return risks

        rules = self.rules[platform]
        script_text = " ".join(str(v) for v in script.values())

        # 检查限制话题
        for change in rules.get("content_policies", []):
            keywords = self._extract_restricted_keywords(change.get("content", ""))
            for kw in keywords:
                if kw in script_text:
                    risks.append({
                        "type": "restricted_topic",
                        "content": f"涉及限制话题「{kw}」",
                        "severity": "high",
                        "rule_ref": change.get("content", "")[:100],
                        "suggestion": change.get("suggestion", "建议避开此话题"),
                    })

        # 检查整体政策方向
        if rules.get("overall_stance") == "tightening":
            risks.append({
                "type": "policy_trend",
                "content": f"{PLATFORM_NAMES.get(platform, platform)}正在收紧审核",
                "severity": "medium",
                "suggestion": "建议内容更加保守，避免擦边表达",
            })

        return risks

    def _extract_restricted_keywords(self, text: str) -> List[str]:
        """从规则文本中提取限制关键词."""
        # 查找引号内的关键词
        quoted = re.findall(r'[「「]([^」」]+)[」」]', text)
        if quoted:
            return quoted
        # 查找顿号分隔的词
        if "、" in text:
            return [w.strip() for w in text.split("、") if len(w.strip()) >= 2]
        return []

    def get_rule_context(self, platform: str) -> str:
        """获取平台规则摘要，注入脚本生成提示词.

        Returns:
            规则上下文文本
        """
        if platform not in self.rules:
            return ""

        rules = self.rules[platform]
        if not rules.get("last_updated"):
            return ""

        lines = [f"## {PLATFORM_NAMES.get(platform, platform)} 平台最新规则提醒"]

        # 整体态势
        stance_map = {"tightening": "收紧", "relaxing": "放松", "neutral": "平稳"}
        stance = stance_map.get(rules.get("overall_stance", "neutral"), "平稳")
        lines.append(f"- 当前审核态势：**{stance}**")

        # 最新变动（取最近3条）
        all_changes = rules.get("content_policies", []) + rules.get("algorithm_changes", [])
        all_changes.sort(key=lambda x: x.get("date", ""), reverse=True)
        for c in all_changes[:3]:
            lines.append(f"- {c.get('type', '')}：{c.get('content', '')[:80]}")

        # 扶持机会
        for p in rules.get("promotions", [])[:2]:
            lines.append(f"- 📢 扶持活动：{p.get('name', '')}（截止{p.get('deadline', '')}）")

        lines.append("")
        lines.append("请在脚本中避免触及以上规则。")
        return "\n".join(lines)

    # ==================== 状态查询 ====================

    def status(self, platform: str = None) -> List[Dict]:
        """查看各平台规则状态."""
        platforms = [platform] if platform else list(PLATFORM_NAMES.keys())
        result = []
        for p in platforms:
            if p in self.rules:
                rules = self.rules[p]
                result.append({
                    "platform": p,
                    "name": PLATFORM_NAMES.get(p, p),
                    "stance": rules.get("overall_stance", "neutral"),
                    "changes_count": len(rules.get("content_policies", []))
                                    + len(rules.get("algorithm_changes", [])),
                    "promotions_count": len(rules.get("promotions", [])),
                    "last_updated": rules.get("last_updated", "从未"),
                })
        return result
