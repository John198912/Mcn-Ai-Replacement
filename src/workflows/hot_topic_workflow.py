"""Hot topic workflow - 热点采集→评分→存储."""

from typing import Any, Dict

from .orchestrator import WorkflowOrchestrator
from ..skills import HotTopicMatcher, HotTopicInput
from ..data_sources import WebSearchEngine
from ..core import get_config, get_db_session
from ..core.database import HotTopic
from ..core.logger import get_logger

logger = get_logger(__name__)


async def run_hot_topic_workflow(keywords: list = None) -> Dict[str, Any]:
    """Execute hot topic collection workflow.

    Args:
        keywords: Optional list of keyword categories to search

    Returns:
        Workflow results
    """
    logger.info("Starting hot topic workflow")

    # Load config
    config = get_config()
    profile = config.personal_profile

    # Default keywords if not provided
    if not keywords:
        keywords = ["ai_keywords", "personal_brand_keywords", "job_keywords"]

    # Create workflow
    workflow = WorkflowOrchestrator(name="hot_topic_workflow")

    # Step 1: Collect hot topics (simulated - actual WebSearch needs Claude Code environment)
    async def collect_topics(results: Dict[str, Any]) -> Dict[str, Any]:
        """Collect hot topics from web search."""
        logger.info("Collecting hot topics", keywords=keywords)

        # Get keywords from config
        all_keywords = []
        for category in keywords:
            all_keywords.extend(config.get_keywords_by_category(category))

        # Simulate search results (in actual implementation, use WebSearchEngine)
        # For now, return mock data
        topics = [
            {
                "title": f"AI大模型如何改变{kw}",
                "platform": "douyin",
                "description": f"探讨AI在{kw}领域的应用",
                "heat_level": "上升",
                "keywords": ["AI", kw],
            }
            for kw in all_keywords[:3]  # Just take first 3 for demo
        ]

        logger.info("Topics collected", count=len(topics))
        return {"topics": topics, "creator_profile": profile}

    # Step 2: Match and score topics
    def map_to_matcher(results: Dict[str, Any]) -> HotTopicInput:
        """Map collected topics to HotTopicMatcher input."""
        initial = results.get("initial", {})
        return HotTopicInput(
            topics=initial.get("topics", []),
            creator_profile=initial.get("creator_profile", {}),
        )

    # Step 3: Store to database
    async def store_topics(results: Dict[str, Any]) -> Dict[str, Any]:
        """Store ranked topics to database."""
        matcher_result = results.get("match_topics")
        if not matcher_result or not matcher_result.success:
            logger.error("Matcher failed, cannot store topics")
            return {"stored": 0}

        ranked_topics = matcher_result.ranked_topics
        session = get_db_session()

        stored_count = 0
        try:
            for topic in ranked_topics:
                # Create HotTopic record
                hot_topic = HotTopic(
                    title=topic.get("title", ""),
                    platform=topic.get("platform", ""),
                    heat_level=topic.get("heat_level", ""),
                    track_score=topic.get("scores", {}).get("track_relevance", 0),
                    persona_score=topic.get("scores", {}).get("persona_fit", 0),
                    timeliness_score=topic.get("scores", {}).get("timeliness", 0),
                    differentiation_score=topic.get("scores", {}).get(
                        "differentiation", 0
                    ),
                    risk_score=topic.get("scores", {}).get("risk", 0),
                    total_score=topic.get("total_score", 0),
                    recommended_angle=", ".join(
                        topic.get("recommended_angles", [])[:2]
                    ),
                    content_form=", ".join(topic.get("content_forms", [])[:2]),
                    publish_window=topic.get("publish_window", ""),
                    risk_level=topic.get("risk_level", ""),
                    status="待评估",
                    raw_data=topic,
                )

                session.add(hot_topic)
                stored_count += 1

            session.commit()
            logger.info("Topics stored to database", count=stored_count)

        except Exception as e:
            session.rollback()
            logger.error("Failed to store topics", error=str(e))
            raise
        finally:
            session.close()

        return {"stored": stored_count, "topics": ranked_topics}

    # Build workflow
    # Note: We use a simplified approach here since we can't directly add async functions as steps
    # In actual implementation, we'd wrap these in Skill classes

    # For now, let's execute the workflow manually
    try:
        # Step 1: Collect
        initial_data = await collect_topics({})

        # Step 2: Match
        matcher = HotTopicMatcher()
        matcher_input = HotTopicInput(
            topics=initial_data["topics"],
            creator_profile=initial_data["creator_profile"],
        )
        matcher_result = await matcher.run(matcher_input)

        # Step 3: Store
        store_result = await store_topics({"match_topics": matcher_result})

        logger.info("Hot topic workflow completed successfully")

        return {
            "success": True,
            "collected": len(initial_data["topics"]),
            "ranked": len(matcher_result.ranked_topics) if matcher_result.success else 0,
            "stored": store_result["stored"],
            "top_topics": matcher_result.top_recommendations
            if matcher_result.success
            else [],
        }

    except Exception as e:
        logger.error("Hot topic workflow failed", error=str(e))
        return {"success": False, "error": str(e)}
