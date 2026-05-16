"""Title Optimizer Skill - 标题优化."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_skill import BaseSkill, SkillInput, SkillOutput


class TitleOptimizerInput(SkillInput):
    """Input for TitleOptimizer."""

    script_summary: str = Field(description="脚本摘要")
    platform: str = Field(description="目标平台")
    reference_titles: Optional[List[str]] = Field(
        default=None, description="参考标题"
    )


class TitleOptimizerOutput(SkillOutput):
    """Output for TitleOptimizer."""

    title_candidates: List[Dict[str, Any]] = []


class TitleOptimizer(BaseSkill):
    """标题优化Skill.

    功能：
    1. 生成多版本标题候选
    2. 预估CTR
    3. 提供封面建议
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize TitleOptimizer."""
        super().__init__(config)

        # 标题策略模板
        self.title_strategies = {
            "反常识型": "你以为{topic}是{A}？其实是{B}",
            "数字型": "{N}个让我{result}的{method}",
            "痛点直击": "{age}岁{situation}后，我终于明白了...",
            "悬念型": "做了{action}之后，发生了出乎意料的事",
            "对比型": "{A}和{B}的人，差距在这里",
            "身份认同": "每个想{goal}的人，都需要知道...",
        }

    def validate_input(
        self, input_data: TitleOptimizerInput
    ) -> tuple[bool, Optional[str]]:
        """Validate input."""
        if not input_data.script_summary:
            return False, "Script summary is empty"

        if not input_data.platform:
            return False, "Platform is missing"

        return True, None

    async def execute(self, input_data: TitleOptimizerInput) -> TitleOptimizerOutput:
        """Execute title optimization."""
        try:
            # 生成多个标题候选
            candidates = []

            for strategy, template in self.title_strategies.items():
                title = self._generate_title(
                    input_data.script_summary, strategy, template
                )

                # 预估CTR
                ctr_score = self._estimate_ctr(title, input_data.platform)

                # 检查搜索词匹配
                search_match = self._check_search_match(
                    title, input_data.script_summary
                )

                candidates.append(
                    {
                        "title": title,
                        "strategy": strategy,
                        "estimated_ctr": ctr_score,
                        "search_match": search_match,
                        "length": len(title),
                        "explanation": f"使用{strategy}策略",
                    }
                )

            # 按CTR排序
            candidates.sort(key=lambda x: x["estimated_ctr"], reverse=True)

            return TitleOptimizerOutput(success=True, title_candidates=candidates)

        except Exception as e:
            return TitleOptimizerOutput(success=False, error=str(e))

    def _generate_title(
        self, summary: str, strategy: str, template: str
    ) -> str:
        """生成标题."""
        # 简化版：基于摘要生成
        # 实际应用中应该使用LLM生成
        if "反常识" in strategy:
            return f"你以为{summary[:10]}？其实完全相反"
        elif "数字" in strategy:
            return f"3个让我突破{summary[:10]}的方法"
        elif "痛点" in strategy:
            return f"35岁{summary[:10]}后，我终于明白了..."
        elif "悬念" in strategy:
            return f"做了{summary[:10]}之后，发生了意想不到的事"
        elif "对比" in strategy:
            return f"{summary[:10]}的人，差距在这里"
        else:
            return f"每个想{summary[:10]}的人，都需要知道这个"

    def _estimate_ctr(self, title: str, platform: str) -> float:
        """预估CTR."""
        # 简化版评分
        score = 5.0

        # 长度加分
        if 15 <= len(title) <= 30:
            score += 1.0

        # 包含数字加分
        if any(c.isdigit() for c in title):
            score += 0.5

        # 包含问号加分
        if "？" in title or "?" in title:
            score += 0.5

        # 包含悬念词加分
        suspense_words = ["意想不到", "出乎意料", "终于", "原来", "其实"]
        if any(word in title for word in suspense_words):
            score += 1.0

        return min(10.0, score)

    def _check_search_match(self, title: str, summary: str) -> str:
        """检查搜索词匹配."""
        # 简化版：检查关键词重叠
        title_words = set(title)
        summary_words = set(summary[:50])

        overlap = len(title_words & summary_words)

        if overlap > 5:
            return "高"
        elif overlap > 2:
            return "中"
        else:
            return "低"
