"""Creator Profiler Skill - 对标创作者建档."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_skill import BaseSkill, SkillInput, SkillOutput


class CreatorProfilerInput(SkillInput):
    """Input for CreatorProfiler."""

    raw_data: Dict[str, Any] = Field(description="原始创作者数据")
    existing_profile: Optional[Dict[str, Any]] = Field(
        default=None, description="现有档案（用于更新）"
    )


class CreatorProfilerOutput(SkillOutput):
    """Output for CreatorProfiler."""

    profile: Dict[str, Any] = {}


class CreatorProfiler(BaseSkill):
    """对标创作者建档Skill.

    功能：
    1. 将原始数据结构化为标准档案
    2. 支持增量更新
    """

    def validate_input(
        self, input_data: CreatorProfilerInput
    ) -> tuple[bool, Optional[str]]:
        """Validate input."""
        if not input_data.raw_data:
            return False, "Raw data is empty"

        required_fields = ["account_name", "platform"]
        for field in required_fields:
            if field not in input_data.raw_data:
                return False, f"Missing required field: {field}"

        return True, None

    async def execute(self, input_data: CreatorProfilerInput) -> CreatorProfilerOutput:
        """Execute creator profiling."""
        try:
            raw = input_data.raw_data
            existing = input_data.existing_profile or {}

            # 构建标准化档案
            profile = {
                "account_name": raw.get("account_name", ""),
                "platform": raw.get("platform", ""),
                "followers": raw.get("followers", 0),
                "tier": raw.get("tier", "成长对标"),
                "positioning": raw.get("positioning", raw.get("description", "")),
                "style_keywords": raw.get("style_keywords", []),
                "content_types": raw.get("content_types", {}),
                "update_frequency": raw.get("update_frequency", ""),
                "monetization": raw.get("monetization", []),
                "top_content": raw.get("top_content", []),
                "learnable_points": raw.get("learnable_points", ""),
                "differentiation_opportunities": raw.get(
                    "differentiation_opportunities", ""
                ),
                "tracking_status": existing.get("tracking_status", "活跃追踪"),
            }

            return CreatorProfilerOutput(success=True, profile=profile)

        except Exception as e:
            return CreatorProfilerOutput(success=False, error=str(e))
