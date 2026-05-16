"""SOUL Hot Topic Matcher — 基于SOUL框架的5维度热点适配评分."""

from typing import List, Dict, Any
from pydantic import Field
from .base_skill import BaseSkill, SkillInput, SkillOutput
from ..core.logger import get_logger

logger = get_logger(__name__)


class SOULHotTopicInput(SkillInput):
    """SOULHotTopicMatcher输入."""

    topics: List[Dict[str, Any]] = Field(description="热点列表")
    soul_framework: bool = Field(default=True, description="是否使用SOUL框架")


class SOULHotTopicOutput(SkillOutput):
    """SOULHotTopicMatcher输出."""

    ranked_topics: List[Dict[str, Any]] = []
    top_picks: List[Dict[str, Any]] = []
    soul_framework_applied: bool = False


class SOULHotTopicMatcher(BaseSkill):
    """基于SOUL框架的热点适配评分.

    五个评分维度：
    1. 有限性三角适配度 (0-10, 权重 30%)
       - 方向1：有限性智慧 — 选择、放弃、承担
       - 方向2：存在的偶然性 — 意义、独特性
       - 方向3：协议层协作 — 人机边界

    2. 核心受众匹配度 (0-10, 权重 25%)
       - Marcus（转型者，30-38岁）
       - Lily（探索者，25-30岁）— 最佳入口
       - Alex（觉醒者，32-40岁）
       - Z（年轻探索者，18-22岁）

    3. 三阶对话法可行性 (0-10, 权重 25%)
       - 是否有可爆破的场景
       - 是否有可拆解的结构
       - 是否有可重建的框架

    4. 差异化空间 (0-10, 权重 15%)
       - 对标创作者覆盖情况
       - SOUL独特视角的发挥空间

    5. 风险评估 (0-10, 权重 5%)
       - 合规性
       - 翻车概率
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

        # 有限性三角关键词
        self.finitude_keywords = {
            "direction1": {
                "name": "有限性智慧",
                "keywords": [
                    "选择", "放弃", "承担", "失去", "珍惜", "取舍",
                    "优先级", "有限", "专注", "减法", "代价", "牺牲",
                ],
                "hook": "AI能做一切，但你只能做一件事 — 这才是你存在的意义",
            },
            "direction2": {
                "name": "存在的偶然性",
                "keywords": [
                    "意义", "独特", "价值", "存在", "焦虑", "为什么",
                    "向死而生", "我是谁", "目的", "偶然", "身份", "迷茫",
                ],
                "hook": "AI的存在是被赋予的，你的存在是偶然的 — 这种偶然性才是价值",
            },
            "direction3": {
                "name": "协议层协作",
                "keywords": [
                    "边界", "协作", "人机", "协议", "工具", "代理",
                    "依赖", "平衡", "配合", "分工", "共生", "关系",
                ],
                "hook": "AI不需要理解你，你也不需要理解AI — 你们只需要约定规则",
            },
        }

        # 核心受众关键词（带权重）
        self.core_audiences = {
            "Marcus": {
                "label": "转型者（30-38岁）",
                "keywords": ["转型", "离职", "创业", "副业", "35岁", "职业", "裁员", "简历"],
                "weight": 0.85,
            },
            "Lily": {
                "label": "探索者（25-30岁）— 最佳入口",
                "keywords": ["成长", "学习", "选择", "迷茫", "焦虑", "方向", "尝试", "可能性"],
                "weight": 1.0,
            },
            "Alex": {
                "label": "觉醒者（32-40岁）",
                "keywords": ["意义", "自由", "精神", "价值", "996", "逃离", "觉醒", "真相"],
                "weight": 0.9,
            },
            "Z": {
                "label": "年轻探索者（18-22岁）",
                "keywords": ["AI", "未来", "学习", "技能", "方向", "无知", "好奇", "尝试"],
                "weight": 0.7,
            },
        }

    async def execute(self, input_data: SOULHotTopicInput) -> SOULHotTopicOutput:
        """执行SOUL框架评分.

        Args:
            input_data: 包含热点列表

        Returns:
            排序后的热点列表和Top推荐
        """
        self._log_execution_start(input_data)
        topics = input_data.topics

        ranked = []
        for topic in topics:
            title = topic.get("title", "").lower()
            description = topic.get("description", "").lower()
            content = title + " " + description

            # 五维度评分
            finitude_scores = self._score_finitude(content)
            best_finitude = max(finitude_scores, key=finitude_scores.get)

            audience_scores = self._score_audience(content)
            best_audience = max(audience_scores, key=audience_scores.get)

            dialogue_scores = self._score_dialogue(content)

            differentiation = self._score_differentiation(topic)

            risk = self._score_risk(topic)

            # 加权综合
            total = round(
                finitude_scores[best_finitude] * 0.30
                + audience_scores[best_audience] * 0.25
                + dialogue_scores["total"] * 0.25
                + differentiation * 0.15
                + risk * 0.05,
                2,
            )

            # 推荐切入角度
            angle = self._recommend_angle(best_finitude, best_audience, topic)

            ranked.append({
                "topic": topic,
                "total_score": total,
                "finitude_direction": best_finitude,
                "finitude_name": self.finitude_keywords[best_finitude]["name"],
                "finitude_hook": self.finitude_keywords[best_finitude]["hook"],
                "finitude_scores": finitude_scores,
                "target_audience": best_audience,
                "audience_label": self.core_audiences[best_audience]["label"],
                "audience_scores": audience_scores,
                "dialogue_scores": dialogue_scores,
                "differentiation_score": differentiation,
                "risk_score": risk,
                "recommended_angle": angle,
            })

        # 排序
        ranked.sort(key=lambda x: x["total_score"], reverse=True)

        # Top 5 推荐
        top_picks = ranked[:5]

        self._log_execution_end(True)
        logger.info(
            "SOUL评分完成",
            total=len(ranked),
            top_score=ranked[0]["total_score"] if ranked else 0,
        )

        return SOULHotTopicOutput(
            success=True,
            ranked_topics=ranked,
            top_picks=top_picks,
            soul_framework_applied=True,
        )

    # ==================== 评分方法 ====================

    def _score_finitude(self, content: str) -> Dict[str, float]:
        """计算有限性三角各方向匹配度."""
        scores = {}
        for direction, config in self.finitude_keywords.items():
            matches = sum(1 for kw in config["keywords"] if kw in content)
            scores[direction] = min(10.0, matches * 2.5)
        return scores

    def _score_audience(self, content: str) -> Dict[str, float]:
        """计算各受众匹配度."""
        scores = {}
        for name, config in self.core_audiences.items():
            matches = sum(1 for kw in config["keywords"] if kw in content)
            base = min(10.0, matches * 2.5)
            scores[name] = round(base * config["weight"], 2)
        return scores

    def _score_dialogue(self, content: str) -> Dict[str, float]:
        """评估三阶对话法的可行性."""
        tier1_keywords = [
            "日常", "场景", "习惯", "默认", "常识", "理所当然", "大家都说",
            "每个人", "普遍", "正常", "标准", "传统",
        ]
        tier2_keywords = [
            "逻辑", "本质", "原因", "结构", "框架", "原理", "模式",
            "机制", "驱动力", "底层", "根源",
        ]
        tier3_keywords = [
            "方法", "工具", "框架", "步骤", "思路", "路径", "方案",
            "练习", "行动", "实验", "验证",
        ]

        rupture = min(10.0, sum(1 for kw in tier1_keywords if kw in content) * 2.5)
        illuminate = min(10.0, sum(1 for kw in tier2_keywords if kw in content) * 2.5)
        rebuild = min(10.0, sum(1 for kw in tier3_keywords if kw in content) * 2.5)

        return {
            "rupture": rupture,
            "illuminate": illuminate,
            "rebuild": rebuild,
            "total": round((rupture + illuminate + rebuild) / 3, 2),
        }

    def _score_differentiation(self, topic: Dict) -> float:
        """评估差异化空间."""
        title = topic.get("title", "").lower()
        description = topic.get("description", "").lower()
        content = title + " " + description

        base = 6.0

        # 加分：有反常识或独特视角信号
        contrarian = ["反常识", "颠覆", "不同", "另类", "独特", "创新", "重新定义"]
        base += sum(1 for kw in contrarian if kw in content) * 1.0

        # 减分：被广泛覆盖
        crowded = ["都在说", "热门", "大家都在", "风口", "爆火", "刷屏"]
        base -= sum(1 for kw in crowded if kw in content) * 0.5

        return max(0.0, min(10.0, base))

    def _score_risk(self, topic: Dict) -> float:
        """评估风险（分数越高越安全）."""
        title = topic.get("title", "").lower()
        description = topic.get("description", "").lower()
        content = title + " " + description

        risk_signals = [
            "敏感", "政治", "歧视", "骂战", "争议", "翻车",
            "违规", "封禁", "限流", "审查", "举报",
        ]
        risk_count = sum(1 for kw in risk_signals if kw in content)
        return max(0.0, min(10.0, 10.0 - risk_count * 3.0))

    # ==================== 推荐算法 ====================

    def _recommend_angle(self, best_finitude: str, best_audience: str, topic: Dict) -> str:
        """基于SOUL框架推荐切入角度."""
        hook = self.finitude_keywords[best_finitude]["hook"]
        audience_label = self.core_audiences[best_audience]["label"]
        title = topic.get("title", "")

        angle_templates = {
            "direction1": f"从'有限性'重新审视{title}。{hook}",
            "direction2": f"追问{title}背后的意义。{hook}",
            "direction3": f"探讨人与AI在{title}中的新关系。{hook}",
        }

        base = angle_templates.get(best_finitude, f"从SOUL视角解读{title}")
        return f"{base}（目标：{audience_label}）"

    # ==================== 辅助方法 ====================

    def validate_input(self, input_data: SOULHotTopicInput) -> tuple:
        """验证输入."""
        if not input_data.topics:
            return False, "Topics list is empty"
        return True, None

    def score_single(self, topic: Dict) -> Dict[str, Any]:
        """快速评分单个热点（同步方法）."""
        input_data = SOULHotTopicInput(topics=[topic])
        # 同步执行
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self.execute(input_data))
            if result.success and result.ranked_topics:
                return result.ranked_topics[0]
            return {}
        finally:
            loop.close()

    def batch_score(self, topics: List[Dict]) -> List[Dict]:
        """批量快速评分（同步方法）."""
        input_data = SOULHotTopicInput(topics=topics)
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self.execute(input_data))
            return result.ranked_topics if result.success else []
        finally:
            loop.close()
