"""Unit tests for Skills."""

import json
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.skills.base_skill import SkillInput, SkillOutput
from src.skills.hot_topic_matcher import HotTopicMatcher, HotTopicInput
from src.skills.content_risk_scanner import ContentRiskScanner, ContentRiskInput
from src.skills.title_optimizer import TitleOptimizer, TitleOptimizerInput
from src.skills.creator_profiler import CreatorProfiler, CreatorProfilerInput


@pytest.fixture
def creator_profile():
    """Load test creator profile."""
    profile_path = Path(__file__).parent.parent.parent / "config" / "personal_profile.json"
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestHotTopicMatcher:
    """Tests for HotTopicMatcher."""

    @pytest.mark.asyncio
    async def test_basic_scoring(self, creator_profile):
        """Test basic topic scoring."""
        skill = HotTopicMatcher()
        topics = [
            {
                "title": "AI大模型如何改变个人品牌打造",
                "platform": "douyin",
                "description": "探讨AI在个人品牌中的应用",
                "heat_level": "上升",
                "keywords": ["AI", "个人品牌", "工具"],
            }
        ]

        input_data = HotTopicInput(topics=topics, creator_profile=creator_profile)
        result = await skill.run(input_data)

        assert result.success
        assert len(result.ranked_topics) == 1
        assert result.ranked_topics[0]["total_score"] > 0
        assert len(result.top_recommendations) == 1

    @pytest.mark.asyncio
    async def test_validation_empty_topics(self):
        """Test validation with empty topics."""
        skill = HotTopicMatcher()
        input_data = HotTopicInput(topics=[], creator_profile={})

        is_valid, error = skill.validate_input(input_data)
        assert not is_valid
        assert "empty" in error.lower()

    @pytest.mark.asyncio
    async def test_multiple_topics_scoring(self, creator_profile):
        """Test scoring multiple topics."""
        skill = HotTopicMatcher()
        topics = [
            {
                "title": f"Topic {i}",
                "platform": "douyin",
                "description": f"Description {i}",
                "heat_level": "上升",
                "keywords": ["AI"],
            }
            for i in range(5)
        ]

        input_data = HotTopicInput(topics=topics, creator_profile=creator_profile)
        result = await skill.run(input_data)

        assert result.success
        assert len(result.ranked_topics) == 5
        assert len(result.top_recommendations) == 5


class TestContentRiskScanner:
    """Tests for ContentRiskScanner."""

    @pytest.mark.asyncio
    async def test_safe_content(self):
        """Test scanning safe content."""
        skill = ContentRiskScanner()
        input_data = ContentRiskInput(
            content_text="这是一个正常的视频脚本，分享AI工具的使用体验",
            platform="douyin",
        )

        result = await skill.run(input_data)

        assert result.success
        assert result.risk_level == "安全"
        assert result.safe_to_publish

    @pytest.mark.asyncio
    async def test_risky_content(self):
        """Test scanning risky content."""
        skill = ContentRiskScanner()
        input_data = ContentRiskInput(
            content_text="这是最好的AI工具，绝对能让你100%提升效率！",
            platform="douyin",
        )

        result = await skill.run(input_data)

        assert result.success
        # Should have at least some risk points
        assert len(result.risk_points) > 0

    @pytest.mark.asyncio
    async def test_platform_specific_rules(self):
        """Test platform-specific rule detection."""
        skill = ContentRiskScanner()
        input_data = ContentRiskInput(
            content_text="加微信了解详情，关注送福利",
            platform="douyin",
        )

        result = await skill.run(input_data)

        assert result.success
        # Check for platform-specific violations
        platform_risks = [r for r in result.risk_points if r["type"] == "平台规则违规"]
        assert len(platform_risks) > 0

    @pytest.mark.asyncio
    async def test_validation_empty_content(self):
        """Test validation with empty content."""
        skill = ContentRiskScanner()
        input_data = ContentRiskInput(content_text="", platform="")

        is_valid, error = skill.validate_input(input_data)
        assert not is_valid


class TestTitleOptimizer:
    """Tests for TitleOptimizer."""

    @pytest.mark.asyncio
    async def test_basic_title_generation(self):
        """Test basic title generation."""
        skill = TitleOptimizer()
        input_data = TitleOptimizerInput(
            script_summary="分享AI工具提升效率的经验", platform="douyin"
        )

        result = await skill.run(input_data)

        assert result.success
        assert len(result.title_candidates) == 6  # 6 strategies
        # Check that titles are sorted by CTR
        for i in range(len(result.title_candidates) - 1):
            assert (
                result.title_candidates[i]["estimated_ctr"]
                >= result.title_candidates[i + 1]["estimated_ctr"]
            )

    @pytest.mark.asyncio
    async def test_validation(self):
        """Test validation."""
        skill = TitleOptimizer()
        input_data = TitleOptimizerInput(script_summary="", platform="")

        is_valid, error = skill.validate_input(input_data)
        assert not is_valid


class TestCreatorProfiler:
    """Tests for CreatorProfiler."""

    @pytest.mark.asyncio
    async def test_basic_profiling(self):
        """Test basic creator profiling."""
        skill = CreatorProfiler()
        input_data = CreatorProfilerInput(
            raw_data={
                "account_name": "@test_creator",
                "platform": "douyin",
                "followers": 50000,
                "positioning": "测试定位",
            }
        )

        result = await skill.run(input_data)

        assert result.success
        assert result.profile["account_name"] == "@test_creator"
        assert result.profile["followers"] == 50000

    @pytest.mark.asyncio
    async def test_validation(self):
        """Test validation."""
        skill = CreatorProfiler()
        input_data = CreatorProfilerInput(raw_data={})

        is_valid, error = skill.validate_input(input_data)
        assert not is_valid
