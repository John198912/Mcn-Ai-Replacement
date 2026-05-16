"""Creator analysis workflow - 创作者发掘→建档→拆解."""

from typing import Any, Dict, List

from ..skills import (
    CreatorProfiler,
    CreatorProfilerInput,
    ViralContentAnalyzer,
    ViralContentInput,
)
from ..core import get_db_session
from ..core.database import Creator
from ..core.logger import get_logger

logger = get_logger(__name__)


async def run_creator_analysis_workflow(
    creators_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute creator analysis workflow.

    Args:
        creators_data: List of raw creator data

    Returns:
        Workflow results with profiled creators
    """
    logger.info("Starting creator analysis workflow", count=len(creators_data))

    profiled_creators = []
    analyzed_content = []

    try:
        for creator_data in creators_data:
            # Step 1: Profile creator
            logger.info("Profiling creator", account=creator_data.get("account_name"))

            profiler = CreatorProfiler()
            profiler_input = CreatorProfilerInput(raw_data=creator_data)

            profiler_result = await profiler.run(profiler_input)

            if not profiler_result.success:
                logger.warning(
                    "Creator profiling failed",
                    account=creator_data.get("account_name"),
                    error=profiler_result.error,
                )
                continue

            profile = profiler_result.profile
            profiled_creators.append(profile)

            # Step 2: Analyze top content (if available)
            top_content = creator_data.get("top_content", [])
            if top_content:
                logger.info(
                    "Analyzing top content",
                    account=profile["account_name"],
                    content_count=len(top_content),
                )

                for content in top_content[:3]:  # Analyze top 3
                    analyzer = ViralContentAnalyzer()
                    analyzer_input = ViralContentInput(
                        content_info=content, creator_profile=profile
                    )

                    analyzer_result = await analyzer.run(analyzer_input)

                    if analyzer_result.success:
                        analyzed_content.append(
                            {
                                "creator": profile["account_name"],
                                "content_title": content.get("title", ""),
                                "analysis": analyzer_result.analysis,
                            }
                        )

            # Step 3: Store to database
            logger.info("Storing creator profile", account=profile["account_name"])

            session = get_db_session()
            try:
                creator = Creator(
                    account_name=profile["account_name"],
                    platform=profile["platform"],
                    followers=profile.get("followers", 0),
                    tier=profile.get("tier", ""),
                    positioning=profile.get("positioning", ""),
                    style_keywords=profile.get("style_keywords", []),
                    content_types=profile.get("content_types", {}),
                    update_frequency=profile.get("update_frequency", ""),
                    monetization=profile.get("monetization", []),
                    top_content=creator_data.get("top_content", []),
                    learnable_points=profile.get("learnable_points", ""),
                    differentiation_opportunities=profile.get(
                        "differentiation_opportunities", ""
                    ),
                    tracking_status="活跃追踪",
                )

                session.add(creator)
                session.commit()
                logger.info("Creator stored", account=profile["account_name"])

            except Exception as e:
                session.rollback()
                logger.error(
                    "Failed to store creator",
                    account=profile["account_name"],
                    error=str(e),
                )
            finally:
                session.close()

        logger.info(
            "Creator analysis workflow completed",
            profiled=len(profiled_creators),
            analyzed_content=len(analyzed_content),
        )

        return {
            "success": True,
            "profiled_creators": profiled_creators,
            "analyzed_content": analyzed_content,
            "total_processed": len(creators_data),
            "total_profiled": len(profiled_creators),
        }

    except Exception as e:
        logger.error("Creator analysis workflow failed", error=str(e))
        return {"success": False, "error": str(e)}
