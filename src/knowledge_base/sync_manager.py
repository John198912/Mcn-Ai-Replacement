"""Data synchronization manager between local and Feishu."""

import asyncio
from typing import Any, Dict, List, Optional

from .feishu_client import FeishuClient, FeishuAPIError
from .local_storage import LocalStorage
from ..core import get_config
from ..core.logger import get_logger

logger = get_logger(__name__)


class SyncManager:
    """Manages data synchronization between local storage and Feishu."""

    def __init__(self):
        """Initialize sync manager."""
        self.config = get_config()
        self.local_storage = LocalStorage()
        self.feishu_client = None
        self.logger = logger.bind(component="SyncManager")

        # Initialize Feishu client if configured
        if self.config.has_feishu_config():
            self.feishu_client = FeishuClient(
                app_id=self.config.feishu_app_id,
                app_secret=self.config.feishu_app_secret,
            )
            self.logger.info("Feishu client initialized")
        else:
            self.logger.warning("Feishu not configured, sync will be disabled")

    async def sync_hot_topics(self, topics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync hot topics to both local and Feishu.

        Args:
            topics: List of topic dictionaries

        Returns:
            Sync result
        """
        self.logger.info("Starting hot topics sync", count=len(topics))

        result = {"local": 0, "feishu": 0, "errors": []}

        # Sync to local storage
        for topic in topics:
            try:
                self.local_storage.add_hot_topic(topic)
                result["local"] += 1
            except Exception as e:
                self.logger.error("Failed to sync topic to local", error=str(e))
                result["errors"].append(f"Local: {str(e)}")

        # Sync to Feishu if configured
        if self.feishu_client and self.config.feishu_hot_topics_app_token:
            try:
                # Convert to Feishu format
                feishu_records = [self._topic_to_feishu_format(t) for t in topics]

                await self.feishu_client.add_records(
                    app_token=self.config.feishu_hot_topics_app_token,
                    table_id=self.config.feishu_hot_topics_table_id,
                    records=feishu_records,
                )

                result["feishu"] = len(feishu_records)
                self.logger.info("Hot topics synced to Feishu", count=result["feishu"])

            except FeishuAPIError as e:
                self.logger.error("Failed to sync topics to Feishu", error=str(e))
                result["errors"].append(f"Feishu: {str(e)}")

        self.logger.info("Hot topics sync completed", result=result)
        return result

    async def sync_creators(self, creators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync creators to both local and Feishu.

        Args:
            creators: List of creator dictionaries

        Returns:
            Sync result
        """
        self.logger.info("Starting creators sync", count=len(creators))

        result = {"local": 0, "feishu": 0, "errors": []}

        # Sync to local storage
        for creator in creators:
            try:
                self.local_storage.add_creator(creator)
                result["local"] += 1
            except Exception as e:
                self.logger.error("Failed to sync creator to local", error=str(e))
                result["errors"].append(f"Local: {str(e)}")

        # Sync to Feishu if configured
        if self.feishu_client and self.config.feishu_creators_app_token:
            try:
                # Convert to Feishu format
                feishu_records = [self._creator_to_feishu_format(c) for c in creators]

                await self.feishu_client.add_records(
                    app_token=self.config.feishu_creators_app_token,
                    table_id=self.config.feishu_creators_table_id,
                    records=feishu_records,
                )

                result["feishu"] = len(feishu_records)
                self.logger.info("Creators synced to Feishu", count=result["feishu"])

            except FeishuAPIError as e:
                self.logger.error("Failed to sync creators to Feishu", error=str(e))
                result["errors"].append(f"Feishu: {str(e)}")

        self.logger.info("Creators sync completed", result=result)
        return result

    def _topic_to_feishu_format(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Convert topic to Feishu record format.

        Args:
            topic: Topic dictionary

        Returns:
            Feishu record
        """
        return {
            "热点话题": topic.get("title", ""),
            "来源平台": topic.get("platform", ""),
            "热度等级": topic.get("heat_level", ""),
            "赛道适配度": topic.get("track_score", 0),
            "人设适配度": topic.get("persona_score", 0),
            "时效性": topic.get("timeliness_score", 0),
            "差异化": topic.get("differentiation_score", 0),
            "风险评分": topic.get("risk_score", 0),
            "综合得分": topic.get("total_score", 0),
            "推荐切入角度": topic.get("recommended_angle", ""),
            "内容形式": topic.get("content_form", ""),
            "发布窗口期": topic.get("publish_window", ""),
            "风险等级": topic.get("risk_level", ""),
            "状态": topic.get("status", "待评估"),
        }

    def _creator_to_feishu_format(self, creator: Dict[str, Any]) -> Dict[str, Any]:
        """Convert creator to Feishu record format.

        Args:
            creator: Creator dictionary

        Returns:
            Feishu record
        """
        import json

        return {
            "账号名": creator.get("account_name", ""),
            "平台": creator.get("platform", ""),
            "粉丝数": creator.get("followers", 0),
            "对标层级": creator.get("tier", ""),
            "一句话定位": creator.get("positioning", ""),
            "风格关键词": json.dumps(creator.get("style_keywords", []), ensure_ascii=False),
            "内容类型分布": json.dumps(creator.get("content_types", {}), ensure_ascii=False),
            "更新频率": creator.get("update_frequency", ""),
            "变现方式": json.dumps(creator.get("monetization", []), ensure_ascii=False),
            "我可学的点": creator.get("learnable_points", ""),
            "我可差异化的空间": creator.get("differentiation_opportunities", ""),
            "追踪状态": creator.get("tracking_status", "活跃追踪"),
        }
