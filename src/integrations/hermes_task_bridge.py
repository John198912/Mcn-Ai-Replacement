"""Hermes任务桥接器 - 接收Hermes的任务调度请求."""

from typing import Dict, Any
import asyncio
import uuid
import os
from datetime import datetime
from ..core.logger import get_logger

logger = get_logger(__name__)


class HermesTaskBridge:
    """Hermes任务桥接器.

    特性：
    1. 本地运行，无需API认证（仅监听127.0.0.1）
    2. 任务队列管理
    3. 飞书消息通知（可选）
    4. 状态查询

    Usage:
        bridge = HermesTaskBridge()
        task_id = await bridge.receive_task({
            "task_type": "hot_topic",
            "params": {},
        })
        status = bridge.get_task_status(task_id)
    """

    def __init__(self):
        self.task_status: Dict[str, Dict] = {}
        self._workflow_funcs: Dict[str, Any] = {}
        self.feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL")

    def register_workflow(self, task_type: str, func):
        """注册工作流函数.

        Args:
            task_type: 任务类型（hot_topic / create_content / creator_analysis）
            func: 工作流函数
        """
        self._workflow_funcs[task_type] = func
        logger.info("已注册工作流", task_type=task_type)

    async def receive_task(self, task: Dict) -> str:
        """接收Hermes的任务请求.

        Args:
            task: 任务字典，包含：
                - task_id (可选): 任务ID
                - task_type: 任务类型
                - params: 参数
                - callback (可选): 飞书webhook URL

        Returns:
            task_id
        """
        task_id = task.get("task_id", str(uuid.uuid4()))
        task_type = task.get("task_type", "unknown")

        self.task_status[task_id] = {
            "status": "pending",
            "task_type": task_type,
            "created_at": datetime.now().isoformat(),
        }

        logger.info("收到Hermes任务", task_id=task_id, task_type=task_type)

        # 异步执行
        asyncio.create_task(self._execute_task(task_id, task))

        return task_id

    async def _execute_task(self, task_id: str, task: Dict):
        """执行任务."""
        task_type = task["task_type"]
        params = task.get("params", {})

        try:
            # 更新状态
            self.task_status[task_id]["status"] = "running"
            self.task_status[task_id]["started_at"] = datetime.now().isoformat()

            # 查找工作流函数
            func = self._workflow_funcs.get(task_type)
            if func is None:
                raise ValueError(f"未知任务类型: {task_type}（已注册：{list(self._workflow_funcs.keys())}）")

            # 执行
            result = await func(**params)

            # 更新状态
            self.task_status[task_id]["status"] = "completed"
            self.task_status[task_id]["completed_at"] = datetime.now().isoformat()
            self.task_status[task_id]["result"] = result

            # 通知Hermes
            await self._notify_hermes(task, result, status="completed")

        except Exception as e:
            logger.error("任务执行失败", task_id=task_id, error=str(e))
            self.task_status[task_id]["status"] = "failed"
            self.task_status[task_id]["error"] = str(e)

            await self._notify_hermes(task, {"error": str(e)}, status="failed")

    async def _notify_hermes(self, task: Dict, result: Dict, status: str):
        """通过飞书消息通知Hermes."""
        webhook_url = task.get("callback") or self.feishu_webhook
        if not webhook_url:
            logger.debug("无webhook URL，跳过通知")
            return

        status_emoji = "✅" if status == "completed" else "❌"
        message = {
            "msg_type": "text",
            "content": {
                "text": (
                    f"MCN任务完成\n"
                    f"任务ID: {task.get('task_id', 'N/A')}\n"
                    f"任务类型: {task.get('task_type', 'N/A')}\n"
                    f"状态: {status_emoji} {status}\n"
                    f"时间: {datetime.now().isoformat()}"
                )
            },
        }

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json=message, timeout=10)
            logger.info("飞书通知已发送")
        except Exception as e:
            logger.error("飞书通知失败", error=str(e))

    def get_task_status(self, task_id: str) -> Dict:
        """查询任务状态.

        Args:
            task_id: 任务ID

        Returns:
            状态字典
        """
        return self.task_status.get(task_id, {"status": "not_found"})

    def list_tasks(self, status_filter: str = None) -> Dict:
        """列出任务.

        Args:
            status_filter: 状态过滤（pending / running / completed / failed）

        Returns:
            任务字典
        """
        if status_filter:
            return {
                tid: t
                for tid, t in self.task_status.items()
                if t.get("status") == status_filter
            }
        return self.task_status
