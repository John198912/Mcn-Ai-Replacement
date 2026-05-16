"""Content creation workflow - 选题→脚本→标题→审核."""

from typing import Any, Dict

from ..skills import (
    ScriptWriter,
    ScriptWriterInput,
    TitleOptimizer,
    TitleOptimizerInput,
    ContentRiskScanner,
    ContentRiskInput,
)
from ..core import get_config
from ..core.logger import get_logger

logger = get_logger(__name__)


async def run_content_creation_workflow(
    topic: str, angle: str, platform: str = "douyin", duration: int = 180
) -> Dict[str, Any]:
    """Execute content creation workflow.

    Args:
        topic: Content topic
        angle: Content angle
        platform: Target platform
        duration: Target duration in seconds

    Returns:
        Workflow results with script, titles, and risk assessment
    """
    logger.info(
        "Starting content creation workflow",
        topic=topic,
        platform=platform,
        duration=duration,
    )

    config = get_config()
    profile = config.personal_profile

    try:
        # Step 1: Generate script
        logger.info("Step 1: Generating script")
        script_writer = ScriptWriter()
        script_input = ScriptWriterInput(
            topic=topic,
            angle=angle,
            platform=platform,
            duration=duration,
            creator_profile=profile,
        )

        script_result = await script_writer.run(script_input)

        if not script_result.success:
            logger.error("Script generation failed", error=script_result.error)
            return {"success": False, "error": f"Script generation failed: {script_result.error}"}

        logger.info(
            "Script generated",
            word_count=script_result.word_count,
            duration=script_result.estimated_duration,
        )

        # Step 2: Generate titles
        logger.info("Step 2: Generating titles")
        title_optimizer = TitleOptimizer()

        # Create script summary from title and core content
        script_summary = (
            script_result.script.get("title", "")
            + " "
            + script_result.script.get("core_content", "")[:100]
        )

        title_input = TitleOptimizerInput(
            script_summary=script_summary, platform=platform
        )

        title_result = await title_optimizer.run(title_input)

        if not title_result.success:
            logger.warning("Title generation failed", error=title_result.error)
            title_candidates = []
        else:
            title_candidates = title_result.title_candidates
            logger.info("Titles generated", count=len(title_candidates))

        # Step 3: Risk scanning
        logger.info("Step 3: Scanning for risks")
        risk_scanner = ContentRiskScanner()

        # Combine all script parts for scanning
        full_script = "\n\n".join(
            [
                script_result.script.get("title", ""),
                script_result.script.get("hook", ""),
                script_result.script.get("pain_point", ""),
                script_result.script.get("core_content", ""),
                script_result.script.get("insight", ""),
                script_result.script.get("cta", ""),
            ]
        )

        risk_input = ContentRiskInput(
            content_text=full_script, platform=platform, content_type="script"
        )

        risk_result = await risk_scanner.run(risk_input)

        if not risk_result.success:
            logger.warning("Risk scanning failed", error=risk_result.error)
            risk_assessment = {"risk_level": "未知", "safe_to_publish": False}
        else:
            risk_assessment = {
                "risk_level": risk_result.risk_level,
                "risk_points": risk_result.risk_points,
                "suggestions": risk_result.suggestions,
                "safe_to_publish": risk_result.safe_to_publish,
            }
            logger.info(
                "Risk assessment completed",
                risk_level=risk_result.risk_level,
                safe=risk_result.safe_to_publish,
            )

        # Compile final result
        result = {
            "success": True,
            "topic": topic,
            "angle": angle,
            "platform": platform,
            "script": {
                "title": script_result.script.get("title", ""),
                "hook": script_result.script.get("hook", ""),
                "pain_point": script_result.script.get("pain_point", ""),
                "core_content": script_result.script.get("core_content", ""),
                "insight": script_result.script.get("insight", ""),
                "cta": script_result.script.get("cta", ""),
                "word_count": script_result.word_count,
                "estimated_duration": script_result.estimated_duration,
                "analysis": script_result.analysis,
            },
            "titles": title_candidates[:5],  # Top 5 titles
            "risk_assessment": risk_assessment,
            "ready_to_publish": risk_assessment.get("safe_to_publish", False)
            and script_result.word_count > 0,
        }

        logger.info(
            "Content creation workflow completed",
            ready=result["ready_to_publish"],
        )

        return result

    except Exception as e:
        logger.error("Content creation workflow failed", error=str(e))
        return {"success": False, "error": str(e)}
