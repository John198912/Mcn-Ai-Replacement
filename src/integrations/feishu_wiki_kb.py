"""飞书Wiki知识库管理器 — 长文档和报告归档."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from .lark_cli_utils import lark
from ..core.logger import get_logger

logger = get_logger(__name__)


class FeishuWikiKB:
    """飞书Wiki知识库管理器.

    组织结构：
    MCN内容创作知识库/
    ├── 热点归档/
    ├── 脚本库/
    ├── 对标创作者/
    └── 策略文档/

    lark-cli 命令映射：
    | 操作      | 命令                                          |
    |-----------|----------------------------------------------|
    | 创建空间  | lark-cli wiki spaces create --data '...' --yes|
    | 列出空间  | lark-cli wiki +space-list                    |
    | 创建节点  | lark-cli wiki +node-create ...               |
    | 列出节点  | lark-cli wiki +node-list ...                 |
    """

    def __init__(self):
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        self.space_id = os.getenv("MCN_FEISHU_WIKI_SPACE_ID")
        self._node_cache: Dict[str, str] = {}

    # ==================== 初始化 ====================

    def ensure_space(self) -> str:
        """确保Wiki空间存在."""
        if self.space_id:
            try:
                result = lark("wiki", "+space-list", "-q", f'.items[] | select(.space_id=="{self.space_id}")')
                if result and result.get("space_id"):
                    logger.info("Wiki空间已存在", space_id=self.space_id[:20])
                    return self.space_id
            except RuntimeError:
                pass

            # 尝试用 spaces get 验证
            try:
                lark("wiki", "spaces", "get", "--params",
                     json.dumps({"space_id": self.space_id}))
                logger.info("Wiki空间已存在", space_id=self.space_id[:20])
                return self.space_id
            except RuntimeError:
                logger.warning("现有空间ID无效，重新创建")
                self.space_id = None

        # 创建新空间
        data = json.dumps({
            "name": "MCN内容创作知识库",
            "description": "AI驱动的MCN内容创作知识沉淀",
        }, ensure_ascii=False)
        result = lark("wiki", "spaces", "create", "--data", data, "--yes")
        self.space_id = result.get("data", {}).get("space", {}).get("space_id", "")
        if self.space_id:
            os.environ["MCN_FEISHU_WIKI_SPACE_ID"] = self.space_id
            self._save_token(self.space_id)
            logger.info("Wiki空间已创建", space_id=self.space_id[:20])
        return self.space_id

    def _save_token(self, token: str):
        """保存 space_id."""
        env_file = Path(__file__).parent.parent.parent / "config" / ".env"
        if not env_file.exists():
            env_file.write_text(f"MCN_FEISHU_WIKI_SPACE_ID={token}\n")
        else:
            content = env_file.read_text()
            if "MCN_FEISHU_WIKI_SPACE_ID" not in content:
                with open(env_file, "a") as f:
                    f.write(f"MCN_FEISHU_WIKI_SPACE_ID={token}\n")

    def ensure_structure(self):
        """确保知识库目录结构存在."""
        self.ensure_space()
        folders = ["热点归档", "脚本库", "对标创作者", "策略文档"]
        for folder in folders:
            self._ensure_folder(folder)

    def _ensure_folder(self, path: str) -> str:
        """确保文件夹存在，返回 node_token."""
        if path in self._node_cache:
            return self._node_cache[path]

        parts = path.split("/")
        parent_token = None

        for part in parts:
            node_token = self._find_child(parent_token, part)
            if not node_token:
                args = [
                    "wiki", "+node-create",
                    "--space-id", self.space_id,
                    "--title", part,
                ]
                if parent_token:
                    args.extend(["--parent-node-token", parent_token])

                result = lark(*args)
                node_token = result.get("node_token") or result.get("data", {}).get("node_token", "")
                if not node_token:
                    raise RuntimeError(f"创建文件夹失败: {part}")
            parent_token = node_token

        self._node_cache[path] = parent_token
        return parent_token

    def _find_child(self, parent_token: Optional[str], title: str) -> Optional[str]:
        """查找指定父节点下的子节点."""
        try:
            args = ["wiki", "+node-list", "--space-id", self.space_id]
            if parent_token:
                args.extend(["--parent-node-token", parent_token])
            result = lark(*args)
            for node in result.get("items", []):
                if node.get("title") == title:
                    return node.get("node_token")
        except RuntimeError:
            pass
        return None

    # ==================== 归档 ====================

    def archive_hotspot_analysis(self, hotspot: Dict) -> Optional[str]:
        """归档热点分析到Wiki."""
        self.ensure_space()
        week = datetime.now().strftime("%Y-W%V")
        parent_token = self._ensure_folder(f"热点归档/{week}")

        title = (hotspot.get("title", "未命名") or "未命名")[:80]
        content = self._format_hotspot_page(hotspot)

        try:
            result = lark(
                "wiki", "+node-create",
                "--space-id", self.space_id,
                "--parent-node-token", parent_token,
                "--title", title,
                "--obj-type", "docx",
            )
            node_token = result.get("node_token") or result.get("data", {}).get("node_token", "")
            url = f"https://bytedance.feishu.cn/wiki/{node_token}"
            logger.info("热点已归档到Wiki", title=title[:30])
            return url
        except RuntimeError as e:
            logger.error("Wiki归档失败", error=str(e))
            return None

    def archive_script(self, script: Dict) -> Optional[str]:
        """归档脚本到Wiki."""
        self.ensure_space()
        platform = script.get("platform", "通用")
        parent_token = self._ensure_folder(f"脚本库/{platform}")

        title = f"{script.get('topic', '未命名')} - {datetime.now():%m-%d %H:%M}"
        content = self._format_script_page(script)

        try:
            result = lark(
                "wiki", "+node-create",
                "--space-id", self.space_id,
                "--parent-node-token", parent_token,
                "--title", title[:80],
                "--obj-type", "docx",
            )
            node_token = result.get("node_token") or result.get("data", {}).get("node_token", "")
            url = f"https://bytedance.feishu.cn/wiki/{node_token}"
            logger.info("脚本已归档到Wiki", title=title[:30])
            return url
        except RuntimeError as e:
            logger.error("Wiki归档失败", error=str(e))
            return None

    # ==================== 格式化 ====================

    def _format_hotspot_page(self, h: Dict) -> str:
        return (
            f"# {h.get('title', '')}\n\n"
            f"## 基本信息\n"
            f"- 平台：{h.get('platform', '')}\n"
            f"- 热度：{h.get('heat_level', '')}\n"
            f"- 标签：{', '.join(h.get('tags', []))}\n"
            f"- 优先级：{h.get('priority', '')}\n\n"
            f"## SOUL框架分析\n"
            f"- 综合评分：{h.get('total_score', 0)}/10\n"
            f"- 有限性方向：{h.get('finitude_name', '')}\n"
            f"- 目标受众：{h.get('audience_label', '')}\n\n"
            f"## 推荐切入角度\n"
            f"{h.get('recommended_angle', '')}\n\n"
            f"## 状态\n"
            f"- 采集时间：{datetime.now().isoformat()}\n"
        )

    def _format_script_page(self, s: Dict) -> str:
        return (
            f"# {s.get('topic', '')}\n\n"
            f"## Hook (前5%)\n{s.get('hook', '')}\n\n"
            f"## 痛点 (10-20%)\n{s.get('pain_point', '')}\n\n"
            f"## 核心内容 (20-80%)\n{s.get('core_content', '')}\n\n"
            f"## 启发 (80-95%)\n{s.get('insight', '')}\n\n"
            f"## CTA (最后5%)\n{s.get('cta', '')}\n\n"
            f"## 参数\n"
            f"- 平台：{s.get('platform', '')}\n"
            f"- 创建时间：{datetime.now().isoformat()}\n"
        )
