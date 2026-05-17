"""飞书多维表格适配器 — 热点和脚本同步到飞书Base."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from .lark_cli_utils import lark
from ..core.logger import get_logger

logger = get_logger(__name__)

# 字段类型使用字符串：text/number/select/datetime/checkbox/link/attachment
HOTSPOT_FIELDS = [
    {"field_name": "标题", "type": "text"},
    {"field_name": "平台", "type": "select"},
    {"field_name": "热度", "type": "select"},
    {"field_name": "SOUL评分", "type": "number"},
    {"field_name": "有限性方向", "type": "select"},
    {"field_name": "目标受众", "type": "select"},
    {"field_name": "推荐角度", "type": "text"},
    {"field_name": "状态", "type": "select"},
    {"field_name": "采集时间", "type": "datetime"},
]

SCRIPT_FIELDS = [
    {"field_name": "选题", "type": "text"},
    {"field_name": "平台", "type": "select"},
    {"field_name": "Hook", "type": "text"},
    {"field_name": "创建时间", "type": "datetime"},
    {"field_name": "状态", "type": "select"},
    {"field_name": "文档链接", "type": "text"},
]


class FeishuBaseAdapter:
    """飞书多维表格适配器.

    lark-cli 命令映射：
    | 操作   | 命令                                    |
    |--------|----------------------------------------|
    | 创建Base | lark-cli base +base-create --name ...  |
    | 创建表   | lark-cli base +table-create ...        |
    | 写记录   | lark-cli base +record-upsert ...       |
    | 读记录   | lark-cli base +record-get --format json|
    | 列表     | lark-cli base +table-list ...          |
    """

    def __init__(self):
        # 确保 .env 已加载
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        self.base_token = os.getenv("MCN_FEISHU_BASE_TOKEN")
        self.folder_token = os.getenv("MCN_FEISHU_FOLDER_TOKEN")

    # ==================== 初始化 ====================

    def ensure_base(self) -> str:
        """确保多维表格存在."""
        if self.base_token:
            try:
                lark("base", "+base-get", "--base-token", self.base_token)
                logger.info("飞书Base已存在", token=self.base_token[:20])
                return self.base_token
            except RuntimeError:
                logger.warning("现有Base token无效，重新创建")
                self.base_token = None

        args = ["base", "+base-create", "--name", "MCN内容创作系统"]
        if self.folder_token:
            args.extend(["--folder-token", self.folder_token])

        result = lark(*args)
        # base_token 在 data.base.base_token
        self.base_token = (
            result.get("data", {}).get("base", {}).get("base_token", "")
            or result.get("base_token", "")
        )

        if self.base_token:
            self._save_token(self.base_token)
            logger.info("飞书Base已创建", token=self.base_token[:20])

        return self.base_token

    def ensure_tables(self):
        """确保必要的子表存在."""
        token = self.ensure_base()
        if not token:
            raise RuntimeError("无法获取 Base token")

        existing = {}
        try:
            tables = lark("base", "+table-list", "--base-token", token)
            # lark-cli 返回 data.tables
            table_list = tables.get("data", {}).get("tables", [])
            for t in table_list:
                existing[t.get("name", "")] = t.get("id", "")
        except RuntimeError:
            pass

        if "热点跟踪" not in existing:
            self._create_table(token, "热点跟踪", HOTSPOT_FIELDS)
            logger.info("子表已创建", name="热点跟踪")
        if "脚本库" not in existing:
            self._create_table(token, "脚本库", SCRIPT_FIELDS)
            logger.info("子表已创建", name="脚本库")

    def _create_table(self, base_token: str, name: str, fields: List[Dict]):
        """创建子表."""
        lark(
            "base", "+table-create",
            "--base-token", base_token,
            "--name", name,
            "--fields", json.dumps(fields, ensure_ascii=False),
        )

    def _save_token(self, token: str):
        """保存 base_token."""
        os.environ["MCN_FEISHU_BASE_TOKEN"] = token
        env_file = Path(__file__).parent.parent.parent / "config" / ".env"
        if not env_file.exists():
            env_file.write_text(f"MCN_FEISHU_BASE_TOKEN={token}\n")
        else:
            content = env_file.read_text()
            if "MCN_FEISHU_BASE_TOKEN" not in content:
                with open(env_file, "a") as f:
                    f.write(f"MCN_FEISHU_BASE_TOKEN={token}\n")

    # ==================== 热点同步 ====================

    def sync_hotspot(self, hotspot: Dict) -> bool:
        """同步单个热点到飞书Base."""
        token = self.ensure_base()
        if not token:
            return False

        fields = {
            "标题": (hotspot.get("title", "") or "")[:100],
            "平台": hotspot.get("platform", "douyin"),
            "热度": hotspot.get("heat_level", "上升"),
            "SOUL评分": hotspot.get("total_score", 0),
            "有限性方向": (hotspot.get("finitude_name", "") or "")[:50],
            "目标受众": (hotspot.get("audience_label", "") or "")[:50],
            "推荐角度": (hotspot.get("recommended_angle", "") or "")[:500],
            "状态": "待选题",
            "采集时间": datetime.now().strftime("%Y-%m-%d"),
        }

        try:
            lark(
                "base", "+record-upsert",
                "--base-token", token,
                "--table-id", "热点跟踪",
                "--json", json.dumps(fields, ensure_ascii=False),
            )
            logger.info("热点已同步", title=fields["标题"][:30])
            return True
        except RuntimeError as e:
            logger.error("热点同步失败", error=str(e))
            return False

    def sync_hotspots_batch(self, hotspots: List[Dict]) -> int:
        """批量同步热点."""
        self.ensure_tables()
        success = 0
        for h in hotspots:
            if self.sync_hotspot(h):
                success += 1
        logger.info("批量同步完成", total=len(hotspots), success=success)
        return success

    # ==================== 脚本同步 ====================

    def sync_script(self, script: Dict) -> bool:
        """同步脚本元数据到飞书Base."""
        token = self.ensure_base()
        if not token:
            return False

        fields = {
            "选题": (script.get("topic", "") or "")[:100],
            "平台": script.get("platform", "douyin"),
            "Hook": (script.get("hook", "") or "")[:200],
            "创建时间": datetime.now().strftime("%Y-%m-%d"),
            "状态": "待审核",
        }
        if script.get("doc_url"):
            fields["文档链接"] = script["doc_url"]

        try:
            lark(
                "base", "+record-upsert",
                "--base-token", token,
                "--table-id", "脚本库",
                "--json", json.dumps(fields, ensure_ascii=False),
            )
            logger.info("脚本已同步", topic=fields["选题"][:30])
            return True
        except RuntimeError as e:
            logger.error("脚本同步失败", error=str(e))
            return False

    # ==================== 查询 ====================

    def query_hotspots(self, limit: int = 20) -> List[Dict]:
        """查询飞书Base中的热点."""
        token = self.ensure_base()
        if not token:
            return []

        try:
            result = lark(
                "base", "+record-get",
                "--base-token", token,
                "--table-id", "热点跟踪",
                "--format", "json",
                "-q", f".items[:{limit}]",
            )
            return result if isinstance(result, list) else result.get("items", [])
        except RuntimeError as e:
            logger.error("查询热点失败", error=str(e))
            return []

    def update_hotspot_status(self, title: str, new_status: str) -> bool:
        """更新热点状态."""
        token = self.ensure_base()
        if not token:
            return False

        try:
            lark(
                "base", "+record-upsert",
                "--base-token", token,
                "--table-id", "热点跟踪",
                "--json", json.dumps({"标题": title, "状态": new_status},
                                     ensure_ascii=False),
            )
            logger.info("状态已更新", title=title[:30], status=new_status)
            return True
        except RuntimeError as e:
            logger.error("状态更新失败", error=str(e))
            return False

    # ==================== 健康检查 ====================

    def health_check(self) -> Dict:
        """检查飞书Base是否可用."""
        if not self.base_token:
            return {"ok": False, "error": "未配置 MCN_FEISHU_BASE_TOKEN"}

        try:
            lark("base", "+base-get", "--base-token", self.base_token)
            return {"ok": True, "base_token": self.base_token[:20] + "..."}
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}
