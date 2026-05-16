"""Hot Topic Matcher Skill - 热点适配与推荐."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_skill import BaseSkill, SkillInput, SkillOutput
from ..core.exceptions import SkillError
from ..utils.text_processing import calculate_similarity, extract_keywords


class HotTopicInput(SkillInput):
    """Input for HotTopicMatcher."""

    topics: List[Dict[str, Any]] = Field(description="原始热点列表")
    creator_profile: Dict[str, Any] = Field(description="创作者画像")
    benchmark_data: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="对标数据（可选）"
    )


class HotTopicOutput(SkillOutput):
    """Output for HotTopicMatcher."""

    ranked_topics: List[Dict[str, Any]] = []
    top_recommendations: List[Dict[str, Any]] = []


class HotTopicMatcher(BaseSkill):
    """热点适配与推荐Skill.

    功能：
    1. 对每个热点计算5个维度评分
    2. 加权计算综合得分
    3. 排序并生成Top推荐
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize HotTopicMatcher.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # 评分权重配置
        self.weights = self.config.get(
            "weights",
            {
                "track_relevance": 0.30,  # 赛道关联度
                "persona_fit": 0.25,  # 人设适配度
                "timeliness": 0.20,  # 时效性
                "differentiation": 0.15,  # 差异化
                "risk": 0.10,  # 风险评分
            },
        )

    def validate_input(self, input_data: HotTopicInput) -> tuple[bool, Optional[str]]:
        """Validate input data.

        Args:
            input_data: Input data

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not input_data.topics:
            return False, "Topics list is empty"

        if not input_data.creator_profile:
            return False, "Creator profile is missing"

        # Check required fields in creator profile
        required_fields = ["track_focus", "content_style"]
        for field in required_fields:
            if field not in input_data.creator_profile:
                return False, f"Creator profile missing field: {field}"

        return True, None

    async def execute(self, input_data: HotTopicInput) -> HotTopicOutput:
        """Execute hot topic matching.

        Args:
            input_data: Input data

        Returns:
            HotTopicOutput with ranked topics
        """
        try:
            self.logger.info(
                "Starting hot topic matching",
                num_topics=len(input_data.topics),
            )

            # 1. 计算每个热点的评分
            scored_topics = []
            for topic in input_data.topics:
                scores = await self._calculate_scores(
                    topic, input_data.creator_profile, input_data.benchmark_data
                )

                # 计算综合得分
                total_score = self._weighted_score(scores)

                scored_topic = {
                    **topic,
                    "scores": scores,
                    "total_score": total_score,
                }
                scored_topics.append(scored_topic)

            # 2. 排序
            ranked = sorted(
                scored_topics, key=lambda x: x["total_score"], reverse=True
            )

            self.logger.info(
                "Topics scored and ranked",
                total_topics=len(ranked),
                top_score=ranked[0]["total_score"] if ranked else 0,
            )

            # 3. 生成Top5推荐
            top5 = await self._generate_recommendations(
                ranked[:5], input_data.creator_profile
            )

            return HotTopicOutput(
                success=True,
                ranked_topics=ranked,
                top_recommendations=top5,
                metadata={
                    "total_topics": len(ranked),
                    "weights": self.weights,
                },
            )

        except Exception as e:
            self.logger.error("Hot topic matching failed", error=str(e))
            return HotTopicOutput(success=False, error=str(e))

    async def _calculate_scores(
        self,
        topic: Dict[str, Any],
        profile: Dict[str, Any],
        benchmark: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, float]:
        """计算5个维度评分.

        Args:
            topic: 热点数据
            profile: 创作者画像
            benchmark: 对标数据

        Returns:
            评分字典
        """
        return {
            "track_relevance": await self._score_track_relevance(topic, profile),
            "persona_fit": await self._score_persona_fit(topic, profile),
            "timeliness": self._score_timeliness(topic),
            "differentiation": await self._score_differentiation(topic, benchmark),
            "risk": self._score_risk(topic),
        }

    async def _score_track_relevance(
        self, topic: Dict[str, Any], profile: Dict[str, Any]
    ) -> float:
        """赛道关联度评分 (0-10).

        Args:
            topic: 热点数据
            profile: 创作者画像

        Returns:
            评分 (0-10)
        """
        # 获取创作者的赛道关键词
        track_focus = profile.get("track_focus", [])

        # 构建热点文本
        topic_text = (
            topic.get("title", "")
            + " "
            + topic.get("description", "")
            + " "
            + " ".join(topic.get("keywords", []))
        )

        # 计算关键词匹配度
        matches = 0
        for track in track_focus:
            if track.lower() in topic_text.lower():
                matches += 1

        # 使用文本相似度作为补充
        track_text = " ".join(track_focus)
        similarity = calculate_similarity(topic_text, track_text)

        # 综合评分
        keyword_score = min(10, matches * 2.5)  # 关键词匹配
        similarity_score = similarity * 10  # 相似度

        final_score = keyword_score * 0.7 + similarity_score * 0.3

        self.logger.debug(
            "Track relevance scored",
            topic_title=topic.get("title", "")[:30],
            matches=matches,
            similarity=similarity,
            score=final_score,
        )

        return round(final_score, 2)

    async def _score_persona_fit(
        self, topic: Dict[str, Any], profile: Dict[str, Any]
    ) -> float:
        """人设适配度评分 (0-10).

        Args:
            topic: 热点数据
            profile: 创作者画像

        Returns:
            评分 (0-10)
        """
        # 获取内容风格偏好
        content_style = profile.get("content_style", {})
        tone = content_style.get("tone", "")
        voice_characteristics = content_style.get("voice_characteristics", [])

        # 获取差异化优势
        differentiation = profile.get("differentiation", {})
        unique_angles = differentiation.get("unique_angles", [])

        # 检查热点是否适合创作者的风格
        topic_text = topic.get("title", "") + " " + topic.get("description", "")

        # 简单的风格匹配（实际应用中可以使用更复杂的NLP模型）
        style_match = 0

        # 检查是否有独特角度可以切入
        angle_match = 0
        for angle in unique_angles:
            if any(
                keyword in topic_text.lower()
                for keyword in angle.lower().split()[:3]
            ):
                angle_match += 1

        # 基础分数
        base_score = 5.0

        # 角度匹配加分
        angle_bonus = min(3.0, angle_match * 1.5)

        # 风格匹配加分
        style_bonus = 2.0 if tone else 0

        final_score = base_score + angle_bonus + style_bonus

        return round(min(10, final_score), 2)

    def _score_timeliness(self, topic: Dict[str, Any]) -> float:
        """时效性评分 (0-10).

        Args:
            topic: 热点数据

        Returns:
            评分 (0-10)
        """
        # 获取热度等级
        heat_level = topic.get("heat_level", "").lower()

        # 根据热度等级评分
        heat_scores = {
            "萌芽": 9.0,  # 最佳时机
            "上升": 8.0,  # 很好的时机
            "爆发": 6.0,  # 竞争激烈
            "衰退": 3.0,  # 已过时
        }

        score = heat_scores.get(heat_level, 5.0)

        # 如果有发现时间，可以进一步调整
        # TODO: 根据discovered_date计算时间衰减

        return score

    async def _score_differentiation(
        self, topic: Dict[str, Any], benchmark: Optional[List[Dict[str, Any]]]
    ) -> float:
        """差异化评分 (0-10).

        Args:
            topic: 热点数据
            benchmark: 对标数据

        Returns:
            评分 (0-10)
        """
        if not benchmark:
            # 没有对标数据，给中等分数
            return 5.0

        # 检查对标创作者是否已经覆盖这个热点
        topic_keywords = set(extract_keywords(topic.get("title", "")))

        covered_count = 0
        for creator in benchmark:
            top_content = creator.get("top_content", [])
            for content in top_content:
                content_keywords = set(extract_keywords(content.get("title", "")))
                # 如果关键词重叠度高，说明已被覆盖
                overlap = len(topic_keywords & content_keywords)
                if overlap >= 2:
                    covered_count += 1
                    break

        # 覆盖越少，差异化越高
        coverage_ratio = covered_count / len(benchmark) if benchmark else 0
        differentiation_score = (1 - coverage_ratio) * 10

        return round(differentiation_score, 2)

    def _score_risk(self, topic: Dict[str, Any]) -> float:
        """风险评分 (0-10，越低越好).

        Args:
            topic: 热点数据

        Returns:
            评分 (0-10)
        """
        risk_keywords = [
            "政治",
            "敏感",
            "争议",
            "负面",
            "违规",
            "封禁",
            "限流",
            "色情",
            "暴力",
            "赌博",
        ]

        topic_text = (
            topic.get("title", "") + " " + topic.get("description", "")
        ).lower()

        # 检查风险关键词
        risk_count = sum(1 for keyword in risk_keywords if keyword in topic_text)

        # 风险越高，分数越高（因为这是负面指标）
        risk_score = min(10, risk_count * 2.5)

        return risk_score

    def _weighted_score(self, scores: Dict[str, float]) -> float:
        """加权计算综合得分.

        Args:
            scores: 各维度评分

        Returns:
            综合得分 (0-10)
        """
        total = 0.0
        for dimension, weight in self.weights.items():
            score = scores.get(dimension, 0)
            # 风险是负面指标，需要反转
            if dimension == "risk":
                score = 10 - score
            total += score * weight

        return round(total, 2)

    async def _generate_recommendations(
        self, top_topics: List[Dict[str, Any]], profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成Top推荐.

        Args:
            top_topics: Top热点列表
            profile: 创作者画像

        Returns:
            推荐列表
        """
        recommendations = []

        for topic in top_topics:
            # 生成推荐切入角度
            angles = self._suggest_angles(topic, profile)

            # 生成内容形式建议
            content_forms = self._suggest_content_forms(topic, profile)

            # 生成发布窗口期
            publish_window = self._suggest_publish_window(topic)

            recommendation = {
                "topic": topic.get("title", ""),
                "platform": topic.get("platform", ""),
                "total_score": topic.get("total_score", 0),
                "scores": topic.get("scores", {}),
                "recommended_angles": angles,
                "content_forms": content_forms,
                "publish_window": publish_window,
                "risk_level": self._assess_risk_level(topic.get("scores", {})),
            }

            recommendations.append(recommendation)

        return recommendations

    def _suggest_angles(
        self, topic: Dict[str, Any], profile: Dict[str, Any]
    ) -> List[str]:
        """建议切入角度.

        Args:
            topic: 热点数据
            profile: 创作者画像

        Returns:
            角度列表
        """
        angles = []

        # 基于创作者的独特角度
        unique_angles = profile.get("differentiation", {}).get("unique_angles", [])

        if unique_angles:
            # 选择最相关的角度
            angles.append(unique_angles[0])

        # 通用角度建议
        angles.extend(
            [
                "从个人实践经验出发",
                "提供可执行的方法论",
                "挑战常见误区",
            ]
        )

        return angles[:3]

    def _suggest_content_forms(
        self, topic: Dict[str, Any], profile: Dict[str, Any]
    ) -> List[str]:
        """建议内容形式.

        Args:
            topic: 热点数据
            profile: 创作者画像

        Returns:
            内容形式列表
        """
        # 根据平台和热点类型建议
        platform = topic.get("platform", "")

        forms = {
            "douyin": ["短视频（60秒）", "系列短视频", "直播"],
            "xiaohongshu": ["图文笔记", "视频笔记", "合集"],
            "bilibili": ["中视频（5-10分钟）", "系列视频"],
            "weibo": ["长图文", "短视频"],
            "zhihu": ["深度文章", "问答"],
        }

        return forms.get(platform, ["短视频", "图文"])

    def _suggest_publish_window(self, topic: Dict[str, Any]) -> str:
        """建议发布窗口期.

        Args:
            topic: 热点数据

        Returns:
            窗口期描述
        """
        heat_level = topic.get("heat_level", "").lower()

        windows = {
            "萌芽": "立即发布（1-2天内）",
            "上升": "尽快发布（3-5天内）",
            "爆发": "谨慎发布（竞争激烈）",
            "衰退": "不建议发布",
        }

        return windows.get(heat_level, "根据情况决定")

    def _assess_risk_level(self, scores: Dict[str, float]) -> str:
        """评估风险等级.

        Args:
            scores: 评分字典

        Returns:
            风险等级
        """
        risk_score = scores.get("risk", 0)

        if risk_score >= 7:
            return "高风险"
        elif risk_score >= 4:
            return "需注意"
        else:
            return "安全"
