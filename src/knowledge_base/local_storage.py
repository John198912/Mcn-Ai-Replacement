"""Local storage management with SQLite."""

from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..core.database import HotTopic, Creator, Content, get_db_session
from ..core.logger import get_logger

logger = get_logger(__name__)


class LocalStorage:
    """Local storage manager for SQLite database."""

    def __init__(self):
        """Initialize local storage."""
        self.logger = logger.bind(component="LocalStorage")

    def add_hot_topic(self, topic_data: Dict[str, Any]) -> int:
        """Add a hot topic to database.

        Args:
            topic_data: Topic data dictionary

        Returns:
            Topic ID
        """
        session = get_db_session()
        try:
            topic = HotTopic(
                title=topic_data.get("title", ""),
                platform=topic_data.get("platform", ""),
                heat_level=topic_data.get("heat_level", ""),
                track_score=topic_data.get("track_score", 0),
                persona_score=topic_data.get("persona_score", 0),
                timeliness_score=topic_data.get("timeliness_score", 0),
                differentiation_score=topic_data.get("differentiation_score", 0),
                risk_score=topic_data.get("risk_score", 0),
                total_score=topic_data.get("total_score", 0),
                recommended_angle=topic_data.get("recommended_angle", ""),
                content_form=topic_data.get("content_form", ""),
                publish_window=topic_data.get("publish_window", ""),
                risk_level=topic_data.get("risk_level", ""),
                status=topic_data.get("status", "待评估"),
                raw_data=topic_data.get("raw_data", {}),
            )

            session.add(topic)
            session.commit()

            topic_id = topic.id
            self.logger.info("Hot topic added", topic_id=topic_id)
            return topic_id

        except Exception as e:
            session.rollback()
            self.logger.error("Failed to add hot topic", error=str(e))
            raise
        finally:
            session.close()

    def get_hot_topics(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 10,
    ) -> List[HotTopic]:
        """Get hot topics from database.

        Args:
            status: Filter by status
            platform: Filter by platform
            limit: Maximum number of results

        Returns:
            List of hot topics
        """
        session = get_db_session()
        try:
            query = session.query(HotTopic)

            if status:
                query = query.filter(HotTopic.status == status)

            if platform:
                query = query.filter(HotTopic.platform == platform)

            topics = query.order_by(desc(HotTopic.total_score)).limit(limit).all()

            self.logger.info("Hot topics retrieved", count=len(topics))
            return topics

        finally:
            session.close()

    def add_creator(self, creator_data: Dict[str, Any]) -> int:
        """Add a creator to database.

        Args:
            creator_data: Creator data dictionary

        Returns:
            Creator ID
        """
        session = get_db_session()
        try:
            creator = Creator(
                account_name=creator_data.get("account_name", ""),
                platform=creator_data.get("platform", ""),
                followers=creator_data.get("followers", 0),
                tier=creator_data.get("tier", ""),
                positioning=creator_data.get("positioning", ""),
                style_keywords=creator_data.get("style_keywords", []),
                content_types=creator_data.get("content_types", {}),
                update_frequency=creator_data.get("update_frequency", ""),
                monetization=creator_data.get("monetization", []),
                top_content=creator_data.get("top_content", []),
                learnable_points=creator_data.get("learnable_points", ""),
                differentiation_opportunities=creator_data.get(
                    "differentiation_opportunities", ""
                ),
                tracking_status=creator_data.get("tracking_status", "活跃追踪"),
            )

            session.add(creator)
            session.commit()

            creator_id = creator.id
            self.logger.info("Creator added", creator_id=creator_id)
            return creator_id

        except Exception as e:
            session.rollback()
            self.logger.error("Failed to add creator", error=str(e))
            raise
        finally:
            session.close()

    def get_creators(
        self, platform: Optional[str] = None, limit: int = 10
    ) -> List[Creator]:
        """Get creators from database.

        Args:
            platform: Filter by platform
            limit: Maximum number of results

        Returns:
            List of creators
        """
        session = get_db_session()
        try:
            query = session.query(Creator)

            if platform:
                query = query.filter(Creator.platform == platform)

            creators = query.order_by(desc(Creator.followers)).limit(limit).all()

            self.logger.info("Creators retrieved", count=len(creators))
            return creators

        finally:
            session.close()

    def add_content(self, content_data: Dict[str, Any]) -> int:
        """Add content to database.

        Args:
            content_data: Content data dictionary

        Returns:
            Content ID
        """
        session = get_db_session()
        try:
            content = Content(
                title=content_data.get("title", ""),
                platform=content_data.get("platform", ""),
                publish_date=content_data.get("publish_date"),
                views=content_data.get("views", 0),
                likes=content_data.get("likes", 0),
                comments=content_data.get("comments", 0),
                shares=content_data.get("shares", 0),
                favorites=content_data.get("favorites", 0),
                new_followers=content_data.get("new_followers", 0),
                completion_rate=content_data.get("completion_rate"),
                five_sec_retention=content_data.get("five_sec_retention"),
                traffic_sources=content_data.get("traffic_sources", {}),
                engagement_rate=content_data.get("engagement_rate"),
                follower_conversion_rate=content_data.get("follower_conversion_rate"),
                favorite_like_ratio=content_data.get("favorite_like_ratio"),
                content_rating=content_data.get("content_rating", ""),
                script_text=content_data.get("script_text", ""),
                related_topic_id=content_data.get("related_topic_id"),
                performance_analysis=content_data.get("performance_analysis", ""),
                optimization_suggestions=content_data.get(
                    "optimization_suggestions", ""
                ),
            )

            session.add(content)
            session.commit()

            content_id = content.id
            self.logger.info("Content added", content_id=content_id)
            return content_id

        except Exception as e:
            session.rollback()
            self.logger.error("Failed to add content", error=str(e))
            raise
        finally:
            session.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Statistics dictionary
        """
        session = get_db_session()
        try:
            stats = {
                "hot_topics": session.query(func.count(HotTopic.id)).scalar(),
                "creators": session.query(func.count(Creator.id)).scalar(),
                "contents": session.query(func.count(Content.id)).scalar(),
            }

            self.logger.info("Statistics retrieved", stats=stats)
            return stats

        finally:
            session.close()
