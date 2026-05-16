"""Custom exceptions for MCN AI system."""


class MCNAIException(Exception):
    """Base exception for MCN AI system."""
    pass


class ConfigError(MCNAIException):
    """Configuration related errors."""
    pass


class DatabaseError(MCNAIException):
    """Database related errors."""
    pass


class SkillError(MCNAIException):
    """Skill execution errors."""
    pass


class WorkflowError(MCNAIException):
    """Workflow execution errors."""
    pass


class DataSourceError(MCNAIException):
    """Data source errors."""
    pass
