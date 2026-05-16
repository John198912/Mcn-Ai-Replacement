"""工作流错误处理中间件."""

from functools import wraps
from typing import Callable, Any
from ..core.logger import get_logger

logger = get_logger(__name__)


class WorkflowError(Exception):
    """工作流异常基类."""

    def __init__(self, message: str, step: str = None, recoverable: bool = True):
        super().__init__(message)
        self.step = step
        self.recoverable = recoverable


class HermesReportNotFoundError(WorkflowError):
    """Hermes报告未找到异常."""
    pass


class ScriptGenerationTimeoutError(WorkflowError):
    """脚本生成超时异常."""
    pass


class KnowledgeBaseSyncError(WorkflowError):
    """知识库同步异常."""
    pass


def with_error_handling(
    step_name: str,
    max_retries: int = 0,
    fallback: Callable = None,
):
    """工作流步骤错误处理装饰器.

    Args:
        step_name: 步骤名称
        max_retries: 最大重试次数
        fallback: 降级函数

    Usage:
        @with_error_handling(step_name="collect_hotspots", max_retries=1)
        async def collect_hotspots():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info("重试", step=step_name, attempt=attempt)
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_error = e
                    logger.error(
                        "步骤执行失败",
                        step=step_name,
                        attempt=f"{attempt + 1}/{max_retries + 1}",
                        error=str(e),
                    )

            if fallback:
                logger.info("执行降级方案", step=step_name)
                try:
                    return await fallback(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error("降级方案也失败", step=step_name, error=str(fallback_error))
                    raise WorkflowError(
                        f"{step_name} 失败且降级方案也失败",
                        step=step_name,
                        recoverable=False,
                    ) from last_error

            raise WorkflowError(
                f"{step_name} 失败（{max_retries + 1}次尝试）",
                step=step_name,
                recoverable=False,
            ) from last_error

        return wrapper
    return decorator
