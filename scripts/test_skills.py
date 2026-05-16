#!/usr/bin/env python3
"""Test script for all Skills."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, setup_logging
from src.skills import (
    HotTopicMatcher,
    HotTopicInput,
    ScriptWriter,
    ScriptWriterInput,
    ContentRiskScanner,
    ContentRiskInput,
    CreatorProfiler,
    CreatorProfilerInput,
    ViralContentAnalyzer,
    ViralContentInput,
    TitleOptimizer,
    TitleOptimizerInput,
)


async def test_hot_topic_matcher():
    """Test HotTopicMatcher Skill."""
    print("\n" + "=" * 60)
    print("1️⃣  Testing HotTopicMatcher")
    print("=" * 60)

    config = get_config()
    profile = config.personal_profile

    # 准备测试数据
    topics = [
        {
            "title": "AI大模型如何改变个人品牌打造",
            "platform": "douyin",
            "description": "探讨AI工具在个人品牌中的应用",
            "heat_level": "上升",
            "keywords": ["AI", "个人品牌", "工具"],
        },
        {
            "title": "35岁职场危机如何破局",
            "platform": "xiaohongshu",
            "description": "职场中年人的转型之路",
            "heat_level": "爆发",
            "keywords": ["职场", "35岁", "转型"],
        },
    ]

    skill = HotTopicMatcher()
    input_data = HotTopicInput(topics=topics, creator_profile=profile)

    result = await skill.run(input_data)

    if result.success:
        print(f"✅ HotTopicMatcher 执行成功")
        print(f"   排序后热点数: {len(result.ranked_topics)}")
        print(f"   Top推荐数: {len(result.top_recommendations)}")
        if result.ranked_topics:
            top = result.ranked_topics[0]
            print(f"   Top1: {top['title']}")
            print(f"   综合得分: {top['total_score']}")
            print(f"   评分详情: {top['scores']}")
    else:
        print(f"❌ HotTopicMatcher 失败: {result.error}")

    return result.success


async def test_script_writer():
    """Test ScriptWriter Skill."""
    print("\n" + "=" * 60)
    print("2️⃣  Testing ScriptWriter")
    print("=" * 60)

    config = get_config()
    profile = config.personal_profile

    skill = ScriptWriter()
    input_data = ScriptWriterInput(
        topic="AI工具提升效率",
        angle="从推荐算法PM的视角",
        platform="douyin",
        duration=180,  # 3分钟
        creator_profile=profile,
    )

    result = await skill.run(input_data)

    if result.success:
        print(f"✅ ScriptWriter 执行成功")
        print(f"   字数: {result.word_count}")
        print(f"   预估时长: {result.estimated_duration}秒")
        print(f"   脚本标题: {result.script.get('title', '')}")
        print(f"   信息密度评分: {result.analysis['information_density']['score']}")
    else:
        print(f"❌ ScriptWriter 失败: {result.error}")

    return result.success


async def test_content_risk_scanner():
    """Test ContentRiskScanner Skill."""
    print("\n" + "=" * 60)
    print("3️⃣  Testing ContentRiskScanner")
    print("=" * 60)

    # 测试包含风险词的内容
    test_content = """
    这是最好的AI工具，绝对能让你100%提升效率！
    保证让你月入10万，加微信了解详情。
    """

    skill = ContentRiskScanner()
    input_data = ContentRiskInput(
        content_text=test_content, platform="douyin", content_type="script"
    )

    result = await skill.run(input_data)

    if result.success:
        print(f"✅ ContentRiskScanner 执行成功")
        print(f"   风险等级: {result.risk_level}")
        print(f"   风险点数量: {len(result.risk_points)}")
        print(f"   可以发布: {result.safe_to_publish}")
        if result.risk_points:
            print(f"   示例风险: {result.risk_points[0]['type']} - {result.risk_points[0]['word']}")
    else:
        print(f"❌ ContentRiskScanner 失败: {result.error}")

    return result.success


async def test_creator_profiler():
    """Test CreatorProfiler Skill."""
    print("\n" + "=" * 60)
    print("4️⃣  Testing CreatorProfiler")
    print("=" * 60)

    raw_data = {
        "account_name": "@测试创作者",
        "platform": "douyin",
        "followers": 100000,
        "positioning": "AI工具实践分享者",
        "style_keywords": ["实用", "干货", "真诚"],
    }

    skill = CreatorProfiler()
    input_data = CreatorProfilerInput(raw_data=raw_data)

    result = await skill.run(input_data)

    if result.success:
        print(f"✅ CreatorProfiler 执行成功")
        print(f"   账号: {result.profile['account_name']}")
        print(f"   平台: {result.profile['platform']}")
        print(f"   粉丝: {result.profile['followers']}")
    else:
        print(f"❌ CreatorProfiler 失败: {result.error}")

    return result.success


async def test_viral_content_analyzer():
    """Test ViralContentAnalyzer Skill."""
    print("\n" + "=" * 60)
    print("5️⃣  Testing ViralContentAnalyzer")
    print("=" * 60)

    content_info = {
        "title": "3个让我效率翻倍的AI工具",
        "platform": "douyin",
        "views": 100000,
        "likes": 5000,
        "comments": 200,
        "shares": 300,
    }

    skill = ViralContentAnalyzer()
    input_data = ViralContentInput(content_info=content_info)

    result = await skill.run(input_data)

    if result.success:
        print(f"✅ ViralContentAnalyzer 执行成功")
        print(f"   标题Hook类型: {result.analysis['title_analysis']['hook_types']}")
        print(f"   互动率: {result.analysis['data_insights']['engagement_rate']}")
        print(f"   表现水平: {result.analysis['data_insights']['performance_level']}")
    else:
        print(f"❌ ViralContentAnalyzer 失败: {result.error}")

    return result.success


async def test_title_optimizer():
    """Test TitleOptimizer Skill."""
    print("\n" + "=" * 60)
    print("6️⃣  Testing TitleOptimizer")
    print("=" * 60)

    skill = TitleOptimizer()
    input_data = TitleOptimizerInput(
        script_summary="分享3个AI工具提升工作效率的实践经验", platform="douyin"
    )

    result = await skill.run(input_data)

    if result.success:
        print(f"✅ TitleOptimizer 执行成功")
        print(f"   生成标题数: {len(result.title_candidates)}")
        if result.title_candidates:
            top = result.title_candidates[0]
            print(f"   Top1标题: {top['title']}")
            print(f"   策略: {top['strategy']}")
            print(f"   预估CTR: {top['estimated_ctr']}")
    else:
        print(f"❌ TitleOptimizer 失败: {result.error}")

    return result.success


async def main():
    """Run all tests."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║           MCN AI System - Skills 测试                        ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Setup logging
    setup_logging(log_level="INFO")

    # Run all tests
    results = []

    results.append(await test_hot_topic_matcher())
    results.append(await test_script_writer())
    results.append(await test_content_risk_scanner())
    results.append(await test_creator_profiler())
    results.append(await test_viral_content_analyzer())
    results.append(await test_title_optimizer())

    # Summary
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 所有Skills测试通过！")
        print("\n📦 已实现的Skills:")
        print("   P0 (必须):")
        print("     1. HotTopicMatcher      - 热点适配评分")
        print("     2. ScriptWriter         - 脚本生成")
        print("     3. ContentRiskScanner   - 合规审核")
        print("   P1 (重要):")
        print("     4. CreatorProfiler      - 对标创作者建档")
        print("     5. ViralContentAnalyzer - 爆款拆解")
        print("     6. TitleOptimizer       - 标题优化")
        print("\n🚀 准备就绪，可以开始 Phase 3：工作流编排")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
