"""飞书集成模块测试."""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.integrations.lark_cli_utils import lark, lark_no_json
from src.integrations.feishu_base_adapter import FeishuBaseAdapter
from src.integrations.feishu_wiki_kb import FeishuWikiKB
from src.integrations.feishu_im_notifier import FeishuIMNotifier


class TestLarkCLIUtils:
    """lark-cli 工具函数测试."""

    @patch("subprocess.run")
    def test_lark_success(self, mock_run):
        """测试正常调用."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"ok":true,"data":"test"}',
            stderr="",
        )
        result = lark("base", "+base-get", "--app-token", "xxx")
        assert result["ok"] is True
        assert result["data"] == "test"

    @patch("subprocess.run")
    def test_lark_error(self, mock_run):
        """测试错误调用."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr='{"error":{"message":"permission denied"}}',
        )
        with pytest.raises(RuntimeError, match="permission denied"):
            lark("base", "+base-get", "--app-token", "invalid")

    @patch("subprocess.run")
    def test_lark_json_fallback(self, mock_run):
        """测试非JSON输出时优雅降级."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="OK: done",
            stderr="",
        )
        result = lark("some", "command")
        assert result["ok"] is True

    @patch("subprocess.run")
    def test_lark_timeout(self, mock_run):
        """测试超时."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("lark-cli", 1)
        with pytest.raises(RuntimeError, match="timeout"):
            lark("base", "+base-get", timeout=1)


class TestFeishuBaseAdapter:
    """飞书Base适配器测试."""

    @pytest.fixture
    def adapter(self):
        return FeishuBaseAdapter()

    def test_init(self, adapter):
        """测试初始化."""
        assert adapter.base_token is None or isinstance(adapter.base_token, str)

    @patch.object(FeishuBaseAdapter, "ensure_base")
    def test_sync_hotspot(self, mock_ensure, adapter):
        """测试热点同步."""
        mock_ensure.return_value = "test_token"
        with patch("src.integrations.feishu_base_adapter.lark") as mock_lark:
            result = adapter.sync_hotspot({
                "title": "测试热点标题内容",
                "platform": "douyin",
                "total_score": 8.5,
                "finitude_name": "有限性智慧",
                "audience_label": "探索者（25-30岁）",
                "recommended_angle": "从有限性视角",
            })
            assert result is True
            assert mock_lark.called

    @patch.object(FeishuBaseAdapter, "ensure_base")
    def test_sync_hotspot_error_handling(self, mock_ensure, adapter):
        """测试热点同步错误处理."""
        mock_ensure.return_value = "test_token"
        with patch("src.integrations.feishu_base_adapter.lark",
                   side_effect=RuntimeError("API error")):
            result = adapter.sync_hotspot({"title": "test"})
            assert result is False  # 应该优雅降级

    def test_ensure_base_creates_new(self, adapter):
        """测试创建新Base."""
        adapter.base_token = None
        with patch("src.integrations.feishu_base_adapter.lark") as mock_lark:
            mock_lark.return_value = {"base_token": "new_token"}
            token = adapter.ensure_base()
            assert token == "new_token"


class TestFeishuIMNotifier:
    """飞书IM通知器测试."""

    @pytest.fixture
    def notifier(self):
        return FeishuIMNotifier()

    def test_parse_hot_command(self, notifier):
        """测试 /hot 指令."""
        cmd = notifier._parse_command("/hot")
        assert cmd["command"] == "hot_topics"
        assert cmd["args"]["top_n"] == 5

    def test_parse_hot_with_number(self, notifier):
        """测试 /hot 10 指令."""
        cmd = notifier._parse_command("/hot 10")
        assert cmd["command"] == "hot_topics"
        assert cmd["args"]["top_n"] == 10

    def test_parse_script_command(self, notifier):
        """测试 /script 指令."""
        cmd = notifier._parse_command("/script AI焦虑")
        assert cmd["command"] == "create_script"
        assert cmd["args"]["topic"] == "AI焦虑"

    def test_parse_sync_command(self, notifier):
        """测试 /sync 指令."""
        cmd = notifier._parse_command("/sync")
        assert cmd["command"] == "sync_knowledge"

    def test_parse_status_command(self, notifier):
        """测试 /status 指令."""
        cmd = notifier._parse_command("/status")
        assert cmd["command"] == "system_status"

    def test_parse_unknown_text(self, notifier):
        """测试非指令文本."""
        cmd = notifier._parse_command("今天天气不错")
        assert cmd is None

    @patch("src.integrations.feishu_im_notifier.lark")
    def test_send_text(self, mock_lark, notifier):
        """测试发送文本消息."""
        notifier.user_open_id = "ou_test"
        result = notifier.send_text("测试消息")
        assert result is True

    def test_send_text_no_target(self, notifier):
        """测试无目标时跳过."""
        notifier.user_open_id = None
        notifier.chat_id = None
        result = notifier.send_text("测试")
        assert result is False  # 无目标优雅跳过


class TestFeishuWikiKB:
    """飞书Wiki知识库测试."""

    @pytest.fixture
    def wiki(self):
        return FeishuWikiKB()

    def test_init(self, wiki):
        """测试初始化."""
        assert wiki.space_id is None or isinstance(wiki.space_id, str)
        assert isinstance(wiki._node_cache, dict)

    def test_format_hotspot_page(self, wiki):
        """测试热点页面格式化."""
        page = wiki._format_hotspot_page({
            "title": "测试热点",
            "platform": "douyin",
            "heat_level": "上升",
            "tags": ["AI"],
            "total_score": 8.5,
            "finitude_name": "有限性智慧",
            "audience_label": "探索者",
            "recommended_angle": "测试角度",
        })
        assert "# 测试热点" in page
        assert "douyin" in page
        assert "8.5" in page

    def test_format_script_page(self, wiki):
        """测试脚本页面格式化."""
        page = wiki._format_script_page({
            "topic": "AI焦虑",
            "hook": "测试Hook内容",
            "pain_point": "测试痛点",
            "core_content": "测试核心内容",
            "insight": "测试启发",
            "cta": "测试CTA",
            "platform": "douyin",
        })
        assert "# AI焦虑" in page
        assert "测试Hook内容" in page
        assert "测试核心内容" in page
