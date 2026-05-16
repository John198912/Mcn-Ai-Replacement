"""Integration tests for workflows."""

import asyncio
import json
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import get_config, init_database, setup_logging
from src.workflows.orchestrator import WorkflowOrchestrator, WorkflowStatus
from src.skills.hot_topic_matcher import HotTopicMatcher, HotTopicInput
from src.workflows.hot_topic_workflow import run_hot_topic_workflow
from src.workflows.content_creation_workflow import run_content_creation_workflow


@pytest.fixture(scope="module")
def setup():
    """Setup for integration tests."""
    setup_logging(log_level="INFO")
    config = get_config()
    init_database(config.database_url)
    return config


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    @pytest.mark.asyncio
    async def test_basic_workflow(self, setup):
        """Test basic workflow execution."""
        workflow = WorkflowOrchestrator(name="test_workflow")

        # Create a simple mock skill
        from src.skills.base_skill import BaseSkill, SkillInput, SkillOutput

        class MockSkill(BaseSkill):
            def __init__(self, return_data=None):
                super().__init__()
                self.return_data = return_data or {"status": "ok"}

            def validate_input(self, input_data):
                return True, None

            async def execute(self, input_data):
                return SkillOutput(success=True, data=self.return_data)

        skill1 = MockSkill({"step": 1})
        skill2 = MockSkill({"step": 2})

        workflow.add_step("step1", skill1)
        workflow.add_step("step2", skill2, depends_on=["step1"])

        results = await workflow.execute({"initial": "data"})

        assert "step1" in results
        assert "step2" in results
        assert results["step1"].success
        assert results["step2"].success

        summary = workflow.get_summary()
        assert summary["total_steps"] == 2
        assert summary["completed"] == 2

    @pytest.mark.asyncio
    async def test_workflow_topological_order(self, setup):
        """Test that workflow respects dependencies."""
        workflow = WorkflowOrchestrator(name="order_test")

        from src.skills.base_skill import BaseSkill, SkillInput, SkillOutput

        execution_order = []

        class TrackingSkill(BaseSkill):
            def __init__(self, name):
                super().__init__()
                self.skill_name = name

            def validate_input(self, input_data):
                return True, None

            async def execute(self, input_data):
                execution_order.append(self.skill_name)
                return SkillOutput(success=True, data={"name": self.skill_name})

        workflow.add_step("A", TrackingSkill("A"))
        workflow.add_step("B", TrackingSkill("B"), depends_on=["A"])
        workflow.add_step("C", TrackingSkill("C"), depends_on=["A"])
        workflow.add_step("D", TrackingSkill("D"), depends_on=["B", "C"])

        await workflow.execute({})

        # A must be first, D must be last
        assert execution_order[0] == "A"
        assert execution_order[-1] == "D"

    @pytest.mark.asyncio
    async def test_workflow_error_propagation(self, setup):
        """Test error propagation in workflow."""
        workflow = WorkflowOrchestrator(name="error_test")

        from src.skills.base_skill import BaseSkill, SkillInput, SkillOutput

        class FailingSkill(BaseSkill):
            def validate_input(self, input_data):
                return True, None

            async def execute(self, input_data):
                return SkillOutput(success=False, error="Simulated error")

        class NormalSkill(BaseSkill):
            def validate_input(self, input_data):
                return True, None

            async def execute(self, input_data):
                return SkillOutput(success=True, data={"ok": True})

        workflow.add_step("fail", FailingSkill())

        with pytest.raises(Exception):
            await workflow.execute({})

        summary = workflow.get_summary()
        assert summary["failed"] == 1


class TestContentCreationWorkflow:
    """Integration tests for content creation workflow."""

    @pytest.mark.asyncio
    async def test_full_content_creation(self, setup):
        """Test the full content creation workflow."""
        result = await run_content_creation_workflow(
            topic="AI工具提升效率",
            angle="从实践者角度",
            platform="douyin",
            duration=180,
        )

        assert result["success"]
        assert result["script"]["title"]
        assert len(result["script"]["hook"]) > 0
        assert len(result["titles"]) > 0  # at least one title generated
        assert "risk_assessment" in result
        assert result["ready_to_publish"] is not None


class TestHotTopicWorkflow:
    """Integration tests for hot topic workflow."""

    @pytest.mark.asyncio
    async def test_hot_topic_workflow(self, setup):
        """Test the hot topic workflow."""
        result = await run_hot_topic_workflow(keywords=["ai_keywords"])

        assert result["success"]
        assert result["collected"] > 0
        assert result["stored"] > 0
        assert len(result["top_topics"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
