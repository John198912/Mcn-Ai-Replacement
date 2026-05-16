"""Database models and session management."""

from datetime import datetime
from typing import Generator

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .exceptions import DatabaseError

Base = declarative_base()


class HotTopic(Base):
    """热点话题表."""

    __tablename__ = "hot_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    platform = Column(String(50), index=True)
    discovered_date = Column(DateTime, default=datetime.utcnow)
    heat_level = Column(String(20))  # 萌芽/上升/爆发/衰退
    track_score = Column(Float)  # 赛道适配度 (0-10)
    persona_score = Column(Float)  # 人设适配度 (0-10)
    timeliness_score = Column(Float)  # 时效性 (0-10)
    differentiation_score = Column(Float)  # 差异化 (0-10)
    risk_score = Column(Float)  # 风险评分 (0-10)
    total_score = Column(Float, index=True)  # 综合得分
    recommended_angle = Column(Text)  # 推荐切入角度
    content_form = Column(String(100))  # 内容形式
    publish_window = Column(String(100))  # 发布窗口期
    risk_level = Column(String(20))  # 安全/需注意/高风险
    status = Column(String(20), default="待评估", index=True)  # 待评估/已选题/已发布/已过期
    raw_data = Column(JSON)  # 原始数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<HotTopic(id={self.id}, title='{self.title}', score={self.total_score})>"


class Creator(Base):
    """对标创作者表."""

    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_name = Column(String(200), nullable=False, index=True)
    platform = Column(String(50), index=True)
    followers = Column(Integer)
    tier = Column(String(50))  # 成长对标/学习标杆
    positioning = Column(Text)  # 一句话定位
    style_keywords = Column(JSON)  # 风格关键词列表
    content_types = Column(JSON)  # 内容类型分布 {"观点输出": 40, "教程": 30, ...}
    update_frequency = Column(String(50))  # 日更/3天1更/周更
    monetization = Column(JSON)  # 变现方式列表
    top_content = Column(JSON)  # 爆款内容列表
    learnable_points = Column(Text)  # 我可学的点
    differentiation_opportunities = Column(Text)  # 我可差异化的空间
    tracking_status = Column(String(20), default="活跃追踪", index=True)  # 活跃追踪/暂停/归档
    first_archived = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Creator(id={self.id}, name='{self.account_name}', platform='{self.platform}')>"


class Content(Base):
    """内容数据表."""

    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    platform = Column(String(50), index=True)
    publish_date = Column(DateTime, index=True)

    # 公开数据
    views = Column(Integer)
    likes = Column(Integer)
    comments = Column(Integer)
    shares = Column(Integer)
    favorites = Column(Integer)
    new_followers = Column(Integer)

    # 后台数据（需要平台权限）
    completion_rate = Column(Float)  # 完播率
    five_sec_retention = Column(Float)  # 5秒留存率
    traffic_sources = Column(JSON)  # 流量来源构成

    # 分析字段
    engagement_rate = Column(Float)  # 互动率 = (likes + comments + shares) / views
    follower_conversion_rate = Column(Float)  # 转粉率 = new_followers / views
    favorite_like_ratio = Column(Float)  # 收藏点赞比 = favorites / likes
    content_rating = Column(String(20))  # S/A/B/C

    # 内容信息
    script_text = Column(Text)  # 脚本文本
    related_topic_id = Column(Integer)  # 关联热点ID

    # 诊断
    performance_analysis = Column(Text)  # 表现分析
    optimization_suggestions = Column(Text)  # 优化建议

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Content(id={self.id}, title='{self.title}', platform='{self.platform}')>"


# Database session management
_engine = None
_SessionLocal = None


def init_database(database_url: str) -> None:
    """Initialize database and create tables.

    Args:
        database_url: Database connection URL

    Raises:
        DatabaseError: If database initialization fails
    """
    global _engine, _SessionLocal

    try:
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        Base.metadata.create_all(bind=_engine)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    except Exception as e:
        raise DatabaseError(f"Failed to initialize database: {e}")


def get_session() -> Generator[Session, None, None]:
    """Get database session.

    Yields:
        Database session

    Raises:
        DatabaseError: If session creation fails
    """
    if _SessionLocal is None:
        raise DatabaseError("Database not initialized. Call init_database() first.")

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """Get a database session (non-generator version).

    Returns:
        Database session

    Raises:
        DatabaseError: If session creation fails
    """
    if _SessionLocal is None:
        raise DatabaseError("Database not initialized. Call init_database() first.")

    return _SessionLocal()
