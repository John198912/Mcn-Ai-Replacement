"""Workflow orchestration system."""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..core.logger import get_logger
from ..core.exceptions import WorkflowError
from ..skills.base_skill import BaseSkill

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStep:
    """Represents a single step in a workflow."""

    def __init__(
        self,
        name: str,
        skill: BaseSkill,
        depends_on: List[str] = None,
        input_mapper: Optional[Callable] = None,
    ):
        """Initialize workflow step.

        Args:
            name: Step name
            skill: Skill to execute
            depends_on: List of step names this step depends on
            input_mapper: Optional function to map previous results to skill input
        """
        self.name = name
        self.skill = skill
        self.depends_on = depends_on or []
        self.input_mapper = input_mapper
        self.status = WorkflowStatus.PENDING
        self.result = None
        self.error = None


class WorkflowOrchestrator:
    """Orchestrates workflow execution with dependency management."""

    def __init__(self, name: str = "workflow"):
        """Initialize orchestrator.

        Args:
            name: Workflow name
        """
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.results: Dict[str, Any] = {}
        self.logger = logger.bind(workflow=name)

    def add_step(
        self,
        name: str,
        skill: BaseSkill,
        depends_on: List[str] = None,
        input_mapper: Optional[Callable] = None,
    ) -> "WorkflowOrchestrator":
        """Add a step to the workflow.

        Args:
            name: Step name
            skill: Skill to execute
            depends_on: List of step names this step depends on
            input_mapper: Optional function to map previous results to skill input

        Returns:
            Self for chaining
        """
        self.steps[name] = WorkflowStep(name, skill, depends_on, input_mapper)
        self.logger.info("Step added", step=name, depends_on=depends_on)
        return self

    async def execute(self, initial_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the workflow.

        Args:
            initial_input: Initial input data

        Returns:
            Dictionary of all step results

        Raises:
            WorkflowError: If workflow execution fails
        """
        self.logger.info("Workflow execution started", steps=len(self.steps))

        # Store initial input
        self.results = {"initial": initial_input or {}}

        # Get execution order
        try:
            execution_order = self._topological_sort()
        except Exception as e:
            raise WorkflowError(f"Failed to determine execution order: {e}")

        self.logger.info("Execution order determined", order=execution_order)

        # Execute steps in order
        for step_name in execution_order:
            step = self.steps[step_name]

            try:
                # Wait for dependencies
                await self._wait_for_dependencies(step)

                # Prepare input
                step_input = self._prepare_step_input(step)

                # Execute step
                self.logger.info("Executing step", step=step_name)
                step.status = WorkflowStatus.RUNNING

                result = await step.skill.run(step_input)

                if result.success:
                    step.status = WorkflowStatus.COMPLETED
                    step.result = result
                    self.results[step_name] = result
                    self.logger.info("Step completed", step=step_name)
                else:
                    step.status = WorkflowStatus.FAILED
                    step.error = result.error
                    self.logger.error("Step failed", step=step_name, error=result.error)
                    raise WorkflowError(f"Step '{step_name}' failed: {result.error}")

            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.error = str(e)
                self.logger.error("Step execution error", step=step_name, error=str(e))
                raise WorkflowError(f"Step '{step_name}' execution error: {e}")

        self.logger.info("Workflow execution completed", total_steps=len(self.steps))
        return self.results

    def _topological_sort(self) -> List[str]:
        """Perform topological sort to determine execution order.

        Returns:
            List of step names in execution order

        Raises:
            WorkflowError: If circular dependency detected
        """
        visited = set()
        temp_mark = set()
        order = []

        def visit(name: str):
            if name in temp_mark:
                raise WorkflowError(f"Circular dependency detected involving '{name}'")

            if name in visited:
                return

            temp_mark.add(name)

            step = self.steps[name]
            for dep in step.depends_on:
                if dep not in self.steps:
                    raise WorkflowError(f"Unknown dependency '{dep}' for step '{name}'")
                visit(dep)

            temp_mark.remove(name)
            visited.add(name)
            order.append(name)

        for name in self.steps:
            if name not in visited:
                visit(name)

        return order

    async def _wait_for_dependencies(self, step: WorkflowStep) -> None:
        """Wait for all dependencies to complete.

        Args:
            step: Step to check dependencies for

        Raises:
            WorkflowError: If any dependency failed
        """
        for dep_name in step.depends_on:
            dep_step = self.steps[dep_name]

            # Wait for dependency to complete
            while dep_step.status == WorkflowStatus.RUNNING:
                await asyncio.sleep(0.1)

            # Check if dependency succeeded
            if dep_step.status == WorkflowStatus.FAILED:
                raise WorkflowError(
                    f"Dependency '{dep_name}' failed, cannot execute '{step.name}'"
                )

    def _prepare_step_input(self, step: WorkflowStep) -> Any:
        """Prepare input for a step.

        Args:
            step: Step to prepare input for

        Returns:
            Input data for the step
        """
        if step.input_mapper:
            # Use custom input mapper
            return step.input_mapper(self.results)
        elif not step.depends_on:
            # No dependencies, use initial input
            return self.results.get("initial", {})
        else:
            # Merge results from dependencies
            merged = {}
            for dep_name in step.depends_on:
                dep_result = self.results.get(dep_name)
                if dep_result and hasattr(dep_result, "data") and dep_result.data:
                    merged.update(dep_result.data)

            return merged

    def get_step_status(self, step_name: str) -> Optional[WorkflowStatus]:
        """Get status of a specific step.

        Args:
            step_name: Name of the step

        Returns:
            Step status or None if step not found
        """
        step = self.steps.get(step_name)
        return step.status if step else None

    def get_step_result(self, step_name: str) -> Optional[Any]:
        """Get result of a specific step.

        Args:
            step_name: Name of the step

        Returns:
            Step result or None if step not found or not completed
        """
        return self.results.get(step_name)

    def get_summary(self) -> Dict[str, Any]:
        """Get workflow execution summary.

        Returns:
            Summary dictionary
        """
        total = len(self.steps)
        completed = sum(
            1 for s in self.steps.values() if s.status == WorkflowStatus.COMPLETED
        )
        failed = sum(
            1 for s in self.steps.values() if s.status == WorkflowStatus.FAILED
        )
        pending = sum(
            1 for s in self.steps.values() if s.status == WorkflowStatus.PENDING
        )

        return {
            "workflow_name": self.name,
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "success_rate": completed / total if total > 0 else 0,
        }
