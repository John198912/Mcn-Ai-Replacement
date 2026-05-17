"""lark-cli 调用工具 — 统一的subprocess封装."""

import json
import os
import subprocess
from typing import Any, Dict, Optional
from ..core.logger import get_logger

logger = get_logger(__name__)


def lark(*args: str, timeout: int = 30, json_output: bool = True) -> Dict[str, Any]:
    """调用 lark-cli 并返回JSON结果.

    lark-cli 默认输出 JSON 到 stdout。某些查询命令需要 --format json。
    """
    cmd = ["lark-cli"] + list(args)

    logger.debug("lark-cli call", cmd=" ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        output = result.stdout.strip()

        if result.returncode != 0:
            # 尝试从 stderr 或 stdout 提取错误信息
            stderr = result.stderr.strip()
            try:
                error_data = json.loads(stderr or output)
                msg = error_data.get("error", {}).get("message", stderr or "lark-cli failed")
            except (json.JSONDecodeError, KeyError):
                msg = stderr or output or "lark-cli failed"
            raise RuntimeError(f"lark-cli error: {msg}")

        # 解析 JSON 输出
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # 可能包含多行 JSON（进度输出），取最后一段
                for line in reversed(output.split("\n")):
                    line = line.strip()
                    if line.startswith("{"):
                        return json.loads(line)
                return {"ok": True, "raw_output": output}

        return {"ok": True}

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"lark-cli timeout after {timeout}s: {' '.join(cmd)}")
    except json.JSONDecodeError:
        logger.warning("lark-cli JSON parse failed", output=output[:200])
        return {"ok": True, "raw_output": output}


def lark_no_json(*args: str, timeout: int = 30) -> str:
    """调用 lark-cli 返回原始文本（用于非JSON输出场景）."""
    cmd = ["lark-cli"] + list(args)
    logger.debug("lark-cli call (raw)", cmd=" ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"lark-cli error: {result.stderr.strip()}")
    return result.stdout.strip()


def lark_async(*args: str, timeout: int = 30) -> Dict[str, Any]:
    """lark-cli 调用（同步封装，用于 async 上下文中通过 run_in_executor 调用）.

    因为 lark-cli 本身是同步CLI，不需要真正的异步。
    此函数等同于 lark()，命名用于语义清晰。
    """
    return lark(*args, timeout=timeout)
