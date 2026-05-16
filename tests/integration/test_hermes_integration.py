"""Hermes集成测试 — 任务桥接、API端点、飞书通知."""

import os
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.integrations.hermes_task_bridge import HermesTaskBridge


class TestHermesTaskBridge:
    """Hermes任务桥接器测试."""

    @pytest.fixture
    def bridge(self):
        return HermesTaskBridge()

    def test_initial_state(self, bridge):
        """测试初始状态."""
        assert bridge.task_status == {}
        assert len(bridge._workflow_funcs) == 0

    def test_register_workflow(self, bridge):
        """测试注册工作流."""
        async def mock_workflow(**kwargs):
            return {"success": True}

        bridge.register_workflow("test_type", mock_workflow)
        assert "test_type" in bridge._workflow_funcs

    @pytest.mark.asyncio
    async def test_receive_task(self, bridge):
        """测试接收任务."""
        async def mock_workflow(**kwargs):
            return {"success": True, "data": kwargs}

        bridge.register_workflow("simple_task", mock_workflow)

        task = {
            "task_id": "test-001",
            "task_type": "simple_task",
            "params": {"key": "value"},
        }

        task_id = await bridge.receive_task(task)
        assert task_id == "test-001"

        status = bridge.get_task_status(task_id)
        assert status["task_type"] == "simple_task"

    @pytest.mark.asyncio
    async def test_task_execution(self, bridge):
        """测试任务异步执行."""
        executed = []

        async def mock_workflow(param1=None):
            executed.append(param1)
            return {"success": True, "result": param1}

        bridge.register_workflow("exec_task", mock_workflow)

        task = {
            "task_id": "exec-001",
            "task_type": "exec_task",
            "params": {"param1": "hello"},
        }

        task_id = await bridge.receive_task(task)

        # 等待异步执行完成
        import asyncio
        await asyncio.sleep(0.3)

        assert len(executed) == 1
        assert executed[0] == "hello"

        status = bridge.get_task_status(task_id)
        assert status["status"] == "completed"
        assert status["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_task_execution_failure(self, bridge):
        """测试任务执行失败."""
        async def failing_workflow():
            raise ValueError("Something went wrong")

        bridge.register_workflow("failing_task", failing_workflow)

        task = {
            "task_id": "fail-001",
            "task_type": "failing_task",
            "params": {},
        }

        await bridge.receive_task(task)
        import asyncio
        await asyncio.sleep(0.3)

        status = bridge.get_task_status("fail-001")
        assert status["status"] == "failed"
        assert "Something went wrong" in status["error"]

    @pytest.mark.asyncio
    async def test_unknown_task_type(self, bridge):
        """测试未知任务类型."""
        task = {
            "task_id": "unknown-001",
            "task_type": "nonexistent_type",
            "params": {},
        }

        await bridge.receive_task(task)
        import asyncio
        await asyncio.sleep(0.3)

        status = bridge.get_task_status("unknown-001")
        assert status["status"] == "failed"
        assert "未知任务类型" in status["error"]

    def test_get_nonexistent_task(self, bridge):
        """测试查询不存在的任务."""
        status = bridge.get_task_status("nonexistent")
        assert status["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_auto_generate_task_id(self, bridge):
        """测试自动生成任务ID."""
        async def simple_workflow():
            return {"ok": True}

        bridge.register_workflow("auto_id", simple_workflow)

        task = {"task_type": "auto_id", "params": {}}
        task_id = await bridge.receive_task(task)

        assert task_id is not None
        assert len(task_id) > 0
        assert task_id != "auto_id"  # 应该生成了UUID

    def test_list_tasks(self, bridge):
        """测试列出任务."""
        bridge.task_status = {
            "t1": {"status": "completed", "task_type": "type_a"},
            "t2": {"status": "failed", "task_type": "type_b"},
            "t3": {"status": "pending", "task_type": "type_a"},
        }

        all_tasks = bridge.list_tasks()
        assert len(all_tasks) == 3

        completed = bridge.list_tasks(status_filter="completed")
        assert len(completed) == 1
        assert "t1" in completed

    @pytest.mark.asyncio
    async def test_feishu_notification_disabled(self, bridge):
        """测试飞书通知未配置时的情况."""
        bridge.feishu_webhook = None  # 无webhook

        async def simple_workflow():
            return {"success": True}

        bridge.register_workflow("notify_test", simple_workflow)
        task = {"task_id": "notify-001", "task_type": "notify_test", "params": {}}

        await bridge.receive_task(task)
        import asyncio
        await asyncio.sleep(0.3)

        # 应该正常完成，不报错
        status = bridge.get_task_status("notify-001")
        assert status["status"] == "completed"

    @pytest.mark.asyncio
    async def test_feishu_notification_with_callback(self, bridge):
        """测试飞书通知（通过callback）."""
        async def simple_workflow():
            return {"success": True}

        bridge.register_workflow("callback_test", simple_workflow)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200

            task = {
                "task_id": "callback-001",
                "task_type": "callback_test",
                "params": {},
                "callback": "https://example.com/webhook",
            }

            await bridge.receive_task(task)
            import asyncio
            await asyncio.sleep(0.3)

            # 检查是否尝试发送通知
            assert mock_post.called

    def test_multiple_workflow_registration(self, bridge):
        """测试注册多个工作流."""
        async def wf1():
            return {"name": "wf1"}

        async def wf2():
            return {"name": "wf2"}

        bridge.register_workflow("type_a", wf1)
        bridge.register_workflow("type_b", wf2)

        assert len(bridge._workflow_funcs) == 2
        assert "type_a" in bridge._workflow_funcs
        assert "type_b" in bridge._workflow_funcs
