"""飞书IM消息通知器 — 双向交互."""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from .lark_cli_utils import lark
from ..core.logger import get_logger

logger = get_logger(__name__)


class FeishuIMNotifier:
    """飞书IM消息通知器.

    功能：
    1. 发送任务完成通知
    2. 发送周报
    3. 🆕 轮询消息指令（/hot /script /sync /status）
    """

    def __init__(self):
        self.user_open_id = os.getenv("FEISHU_USER_OPEN_ID")
        self.chat_id = os.getenv("MCN_FEISHU_CHAT_ID")

    # ==================== 发送消息 ====================

    def send_text(self, text: str, chat_id: str = None) -> bool:
        """发送文本消息."""
        target = chat_id or self.user_open_id
        if not target:
            logger.warning("无消息接收目标，跳过发送")
            return False

        try:
            if chat_id:
                lark("im", "+messages-send", "--chat-id", target, "--text", text)
            else:
                lark("im", "+messages-send", "--user-id", target, "--text", text)
            logger.info("飞书消息已发送", target=target[:20])
            return True
        except RuntimeError as e:
            logger.error("消息发送失败", error=str(e))
            return False

    def send_task_result(self, task_type: str, status: str, summary: str) -> bool:
        """发送任务执行结果."""
        emoji = "✅" if status == "completed" else "❌"
        text = (
            f"{emoji} MCN任务{'完成' if status == 'completed' else '失败'}\n"
            f"任务：{task_type}\n"
            f"时间：{datetime.now():%m-%d %H:%M}\n"
            f"\n{summary}"
        )
        return self.send_text(text)

    def send_weekly_report(self, stats: Dict) -> bool:
        """发送周报到指定群组."""
        text = (
            f"📊 MCN内容创作周报\n"
            f"周期：{stats.get('week', '')}\n"
            f"\n"
            f"🔥 热点采集：{stats.get('hotspots', 0)} 条\n"
            f"📝 脚本生成：{stats.get('scripts', 0)} 份\n"
            f"🏆 Top选题：{stats.get('top_topic', '无')}\n"
            f"\n"
            f"💾 备份状态：{'正常' if stats.get('backup_ok') else '异常'}\n"
            f"🔄 GitHub同步：{'正常' if stats.get('sync_ok') else '异常'}\n"
        )
        return self.send_text(text, chat_id=self.chat_id)

    # ==================== 消息指令 ====================

    def poll_commands(self, chat_id: str = None, limit: int = 5) -> List[Dict]:
        """轮询消息指令.

        支持指令：
        - /hot        → 查询今日热点
        - /hot <N>    → 查询Top N热点
        - /script <选题> → 生成脚本
        - /sync       → 同步知识库
        - /status     → 查看系统状态

        Args:
            chat_id: 群组ID
            limit: 读取最近N条消息

        Returns:
            指令列表
        """
        target = chat_id or self.chat_id
        if not target:
            return []

        try:
            messages = lark(
                "im", "+chat-messages-list",
                "--chat-id", target,
                "--page-size", str(min(limit, 20)),
            )
        except RuntimeError:
            return []

        commands = []
        for msg in messages.get("items", []):
            body = msg.get("body", {}).get("content", "")
            # 解析纯文本
            text = self._extract_text(body)
            if text and text.startswith("/"):
                cmd = self._parse_command(text)
                if cmd:
                    cmd["message_id"] = msg.get("message_id", "")
                    commands.append(cmd)

        return commands

    def _extract_text(self, body: str) -> str:
        """从消息body中提取文本."""
        try:
            data = json.loads(body) if isinstance(body, str) else body
            return data.get("text", "")
        except (json.JSONDecodeError, TypeError):
            return str(body) if isinstance(body, str) else ""

    def _parse_command(self, text: str) -> Optional[Dict]:
        """解析消息指令."""
        text = text.strip()

        if text.startswith("/hot"):
            parts = text.split()
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
            return {"command": "hot_topics", "args": {"top_n": n}}

        if text.startswith("/script"):
            topic = text.replace("/script", "").strip()
            if topic:
                return {"command": "create_script", "args": {"topic": topic}}

        if text.startswith("/sync"):
            return {"command": "sync_knowledge", "args": {}}

        if text.startswith("/status"):
            return {"command": "system_status", "args": {}}

        return None

    # ==================== 文件发送 ====================

    def send_file(self, file_path: str, chat_id: str = None) -> bool:
        """发送文件到飞书."""
        target = chat_id or self.chat_id
        if not target or not os.path.exists(file_path):
            return False

        try:
            lark(
                "im", "+messages-send",
                "--chat-id", target,
                "--file", file_path,
            )
            logger.info("文件已发送", path=file_path)
            return True
        except RuntimeError as e:
            logger.error("文件发送失败", error=str(e))
            return False
