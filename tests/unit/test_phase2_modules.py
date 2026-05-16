"""Phase 2 模块单元测试 — SOULScriptWriter 和 SOULHotTopicMatcher."""

import json
from pathlib import Path

import pytest

from src.skills.soul_script_writer import (
    SOULScriptWriter,
    SOULScriptWriterInput,
    SOULScriptWriterOutput,
)
from src.skills.soul_hot_topic_matcher import (
    SOULHotTopicMatcher,
    SOULHotTopicInput,
    SOULHotTopicOutput,
)


class TestSOULScriptWriter:
    """SOUL脚本生成器测试."""

    @pytest.fixture
    def writer(self):
        return SOULScriptWriter()

    def test_soul_profile_loaded(self, writer):
        """测试SOUL画像已加载."""
        assert writer.soul_profile is not None
        assert "positioning" in writer.soul_profile
        assert "three_tier_dialogue" in writer.soul_profile
        assert "finitude_triangle" in writer.soul_profile
        assert "core_audiences" in writer.soul_profile
        assert "personality" in writer.soul_profile

    def test_has_default_profile(self, writer):
        """测试即使没外部文件也有默认SOUL配置."""
        assert writer.soul_profile["source"] is not None
        assert len(writer.soul_profile["core_audiences"]) > 0

    def test_build_prompt(self, writer):
        """测试提示词构建."""
        prompt = writer._build_script_prompt(
            topic="AI焦虑",
            angle="从有限性视角",
            platform="douyin",
            duration=180,
        )
        assert "SOUL" in prompt
        assert "AI焦虑" in prompt
        assert "从有限性视角" in prompt
        assert "三阶对话法" in prompt
        assert "Hook" in prompt
        assert "痛点" in prompt
        assert "核心内容" in prompt
        assert "启发" in prompt
        assert "CTA" in prompt

    def test_parse_generated_script(self, writer):
        """测试脚本解析."""
        generated = """## Hook (前5%)
这是一个反常识的开场白

## 痛点 (10-20%)
受众感到焦虑和不安

## 核心内容 (20-80%)
用框架揭示深层逻辑

## 启发 (80-95%)
给出可用的思维工具

## CTA (最后5%)
你准备好了吗？
"""
        script = writer._parse_generated_script(generated)
        assert script["hook"] == "这是一个反常识的开场白"
        assert script["pain_point"] == "受众感到焦虑和不安"
        assert script["core_content"] == "用框架揭示深层逻辑"
        assert script["insight"] == "给出可用的思维工具"
        assert script["cta"] == "你准备好了吗？"

    def test_parse_fallback(self, writer):
        """测试备用解析器."""
        generated = "Hook\n这是开场白\n\n痛点\n感到焦虑\n\n核心内容\n深层逻辑\n\n启发\n思维工具\n\nCTA\n准备好了吗"
        script = writer._parse_generated_script(generated)
        # 至少应解析出部分内容
        assert len(script) >= 5

    def test_check_soul_alignment_good(self, writer):
        """测试SOUL人设检查 - 良好情况."""
        script = {
            "hook": "我们一起看看AI焦虑的真相",
            "pain_point": "我也不确定未来会怎样",
            "core_content": "让我们用框架来拆解这个问题",
        }
        issues = writer._check_soul_alignment(script)
        # 良好情况应该没有或很少问题
        assert len([i for i in issues if "导师口吻" in i]) == 0

    def test_check_soul_alignment_directive(self, writer):
        """测试SOUL人设检查 - 导师口吻."""
        script = {
            "hook": "你必须学会使用AI工具",
            "pain_point": "你应该感到焦虑",
            "core_content": "正确的做法是...",
            "insight": "你要明白",
            "cta": "你一定要行动",
        }
        issues = writer._check_soul_alignment(script)
        assert len(issues) > 0

    def test_validate_input_valid(self, writer):
        """测试有效输入验证."""
        input_data = SOULScriptWriterInput(
            topic="AI焦虑",
            angle="有限性视角",
            platform="douyin",
            duration=180,
        )
        is_valid, error = writer.validate_input(input_data)
        assert is_valid, error

    def test_validate_input_empty_topic(self, writer):
        """测试空选题."""
        input_data = SOULScriptWriterInput(
            topic="",
            angle="有限性视角",
            platform="douyin",
            duration=180,
        )
        is_valid, error = writer.validate_input(input_data)
        assert not is_valid

    def test_generate_prompt_only(self, writer):
        """测试快速提示词生成."""
        prompt = SOULScriptWriter.generate_prompt_only(
            topic="测试",
            angle="测试角度",
        )
        assert "测试" in prompt
        assert "SOUL" in prompt


class TestSOULHotTopicMatcher:
    """SOUL热点适配评分测试."""

    @pytest.fixture
    def matcher(self):
        return SOULHotTopicMatcher()

    @pytest.mark.asyncio
    async def test_basic_scoring(self, matcher):
        """测试基本评分."""
        topics = [
            {
                "title": "AI时代如何重新学会选择和放弃",
                "platform": "douyin",
                "description": "探讨有限性智慧",
                "tags": ["AI", "超级个体"],
            }
        ]
        input_data = SOULHotTopicInput(topics=topics)
        result = await matcher.execute(input_data)

        assert result.success
        assert len(result.ranked_topics) == 1
        topic = result.ranked_topics[0]
        assert "total_score" in topic
        assert topic["total_score"] > 0
        assert "finitude_direction" in topic
        assert "target_audience" in topic
        assert "recommended_angle" in topic

    @pytest.mark.asyncio
    async def test_multiple_topics_ranking(self, matcher):
        """测试多热点排序."""
        topics = [
            {
                "title": "AI时代的选择与放弃",  # 明确有限性
                "platform": "douyin",
                "description": "选择放弃承担失去",
            },
            {
                "title": "今天天气不错",  # 无关联
                "platform": "douyin",
                "description": "天气很好适合出去玩",
            },
            {
                "title": "如何找到存在的意义",  # 方向2
                "platform": "douyin",
                "description": "意义独特价值存在",
            },
        ]
        input_data = SOULHotTopicInput(topics=topics)
        result = await matcher.execute(input_data)

        assert result.success
        assert len(result.ranked_topics) == 3

        # 有SOUL关键词的应该排在前面
        first = result.ranked_topics[0]
        assert first["total_score"] > 0

        # "今天天气不错" 应该排在最后
        last = result.ranked_topics[-1]
        assert "天气" in last["topic"]["title"].lower()

    @pytest.mark.asyncio
    async def test_top_picks(self, matcher):
        """测试Top推荐."""
        topics = [
            {"title": f"热点{i}", "platform": "douyin", "description": f"描述{i}"}
            for i in range(10)
        ]
        input_data = SOULHotTopicInput(topics=topics)
        result = await matcher.execute(input_data)

        assert len(result.top_picks) <= 5
        assert result.top_picks == result.ranked_topics[:5]

    @pytest.mark.asyncio
    async def test_finitude_direction_assignment(self, matcher):
        """测试有限性方向分配."""
        topics = [
            {
                "title": "学会选择和放弃",
                "description": "选择承担失去珍惜有限",
                "platform": "douyin",
            }
        ]
        input_data = SOULHotTopicInput(topics=topics)
        result = await matcher.execute(input_data)

        topic = result.ranked_topics[0]
        assert topic["finitude_direction"] == "direction1"  # 有限性智慧

    @pytest.mark.asyncio
    async def test_risk_scoring(self, matcher):
        """测试风险评分."""
        safe_topic = [
            {"title": "学习方法分享", "platform": "douyin", "description": "正能量"}
        ]
        risky_topic = [
            {"title": "争议翻车敏感话题", "platform": "douyin", "description": "翻车争议"}
        ]

        safe_result = await matcher.execute(SOULHotTopicInput(topics=safe_topic))
        risky_result = await matcher.execute(SOULHotTopicInput(topics=risky_topic))

        safe_score = safe_result.ranked_topics[0]["risk_score"]
        risky_score = risky_result.ranked_topics[0]["risk_score"]

        # 安全话题的风险评分应该更高（更安全）
        assert safe_score > risky_score

    @pytest.mark.asyncio
    async def test_validation_empty_topics(self, matcher):
        """测试空热点列表验证."""
        input_data = SOULHotTopicInput(topics=[])
        is_valid, error = matcher.validate_input(input_data)
        assert not is_valid
        assert "empty" in error.lower()

    def test_score_single_sync(self, matcher):
        """测试同步单热点评分."""
        topic = {"title": "AI时代的有限性选择", "platform": "douyin"}
        result = matcher.score_single(topic)
        assert "total_score" in result
        assert result["total_score"] > 0

    def test_batch_score_sync(self, matcher):
        """测试同步批量评分."""
        topics = [
            {"title": f"热点{i}", "platform": "douyin"}
            for i in range(5)
        ]
        results = matcher.batch_score(topics)
        assert len(results) == 5
        # 应该已排序
        for i in range(len(results) - 1):
            assert results[i]["total_score"] >= results[i + 1]["total_score"]
