"""Base class for all Skills."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel

from ..core.logger import get_logger


class SkillInput(BaseModel):
    """Base class for Skill input."""

    model_config = {"arbitrary_types_allowed": True}


class SkillOutput(BaseModel):
    """Base class for Skill output."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


class BaseSkill(ABC):
    """Base class for all Skills.

    All Skills must inherit from this class and implement:
    - execute(): Main execution logic
    - validate_input(): Input validation
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Skill.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        """Execute the Skill's main logic.

        Args:
            input_data: Input data for the Skill

        Returns:
            SkillOutput with results

        Raises:
            SkillError: If execution fails
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: SkillInput) -> tuple[bool, Optional[str]]:
        """Validate input data.

        Args:
            input_data: Input data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    def _log_execution_start(self, input_data: SkillInput) -> None:
        """Log execution start."""
        self.logger.info(
            "Skill execution started",
            skill=self.__class__.__name__,
            input_type=type(input_data).__name__,
        )

    def _log_execution_end(self, success: bool, error: Optional[str] = None) -> None:
        """Log execution end."""
        if success:
            self.logger.info(
                "Skill execution completed",
                skill=self.__class__.__name__,
            )
        else:
            self.logger.error(
                "Skill execution failed",
                skill=self.__class__.__name__,
                error=error,
            )

    async def run(self, input_data: SkillInput) -> SkillOutput:
        """Run the Skill with validation and logging.

        Args:
            input_data: Input data

        Returns:
            SkillOutput with results
        """
        self._log_execution_start(input_data)

        # Validate input
        is_valid, error_msg = self.validate_input(input_data)
        if not is_valid:
            self._log_execution_end(False, error_msg)
            return SkillOutput(success=False, error=error_msg)

        # Execute
        try:
            result = await self.execute(input_data)
            self._log_execution_end(result.success, result.error)
            return result
        except Exception as e:
            error_msg = f"Skill execution failed: {str(e)}"
            self._log_execution_end(False, error_msg)
            return SkillOutput(success=False, error=error_msg)
