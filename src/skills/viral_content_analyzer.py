"""Viral Content Analyzer Skill - 爆款内容拆解."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_skill import BaseSkill, SkillInput, SkillOutput


class ViralContentInput(SkillInput):
    """Input for ViralContentAnalyzer."""

    content_info: Dict[str, Any] = Field(description="爆款内容信息")
    creator_profile: Optional[Dict[str, Any]] = Field(
        default=None, description="创作者画像"
    )


class ViralContentOutput(SkillOutput):
    """Output for ViralContentAnalyzer."""

    analysis: Dict[str, Any] = {}


class ViralContentAnalyzer(BaseSkill):
    """爆款内容拆解Skill.

    功能：
    1. 分析标题Hook类型
    2. 拆解内容结构
    3. 识别可迁移元素
    """

    def validate_input(
        self, input_data: ViralContentInput
    ) -> tuple[bool, Optional[str]]:
        """Validate input."""
        if not input_data.content_info:
            return False, "Content info is empty"

        return True, None

    async def execute(self, input_data: ViralContentInput) -> ViralContentOutput:
        """Execute viral content analysis."""
        try:
            content = input_data.content_info

            analysis = {
                "basic_info": {
                    "title": content.get("title", ""),
                    "platform": content.get("platform", ""),
                    "views": content.get("views", 0),
                    "likes": content.get("likes", 0),
                    "comments": content.get("comments", 0),
                },
                "title_analysis": self._analyze_title(content.get("title", "")),
                "content_structure": self._analyze_structure(content),
                "data_insights": self._analyze_data(content),
                "transferable_elements": self._identify_transferable(
                    content, input_data.creator_profile
                ),
            }

            return ViralContentOutput(success=True, analysis=analysis)

        except Exception as e:
            return ViralContentOutput(success=False, error=str(e))

    def _analyze_title(self, title: str) -> Dict[str, Any]:
        """分析标题."""
        hook_types = {
            "悬念型": ["如何", "为什么", "什么", "?"],
            "数字型": ["3个", "5个", "10个", "步骤"],
            "反常识型": ["其实", "真相", "误区", "颠覆"],
            "痛点直击型": ["焦虑", "困扰", "问题", "难题"],
            "对比型": ["vs", "对比", "区别", "差距"],
        }

        detected_types = []
        for hook_type, keywords in hook_types.items():
            if any(kw in title for kw in keywords):
                detected_types.append(hook_type)

        return {
            "hook_types": detected_types if detected_types else ["其他"],
            "length": len(title),
            "has_emoji": any(ord(c) > 127 for c in title),
        }

    def _analyze_structure(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """分析内容结构."""
        return {
            "estimated_structure": "Hook → 痛点 → 方法 → 总结",
            "key_points": ["待补充"],
        }

    def _analyze_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据表现."""
        views = content.get("views", 0)
        likes = content.get("likes", 0)
        comments = content.get("comments", 0)
        shares = content.get("shares", 0)

        engagement_rate = (likes + comments + shares) / views if views > 0 else 0

        return {
            "engagement_rate": round(engagement_rate, 4),
            "like_comment_ratio": likes / comments if comments > 0 else 0,
            "performance_level": "优秀" if engagement_rate > 0.05 else "一般",
        }

    def _identify_transferable(
        self, content: Dict[str, Any], profile: Optional[Dict[str, Any]]
    ) -> List[str]:
        """识别可迁移元素."""
        return [
            "标题Hook手法可借鉴",
            "内容结构可参考",
            "需根据个人风格调整",
        ]
