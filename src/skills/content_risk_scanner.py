"""Content Risk Scanner Skill - 内容合规审核."""

import re
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_skill import BaseSkill, SkillInput, SkillOutput


class ContentRiskInput(SkillInput):
    """Input for ContentRiskScanner."""

    content_text: str = Field(description="待检查的内容文本")
    platform: str = Field(description="目标平台")
    content_type: str = Field(default="script", description="内容类型：script/title/description")


class ContentRiskOutput(SkillOutput):
    """Output for ContentRiskScanner."""

    risk_level: str = "安全"  # 安全/需注意/高风险
    risk_points: List[Dict[str, Any]] = []
    suggestions: List[str] = []
    safe_to_publish: bool = True


class ContentRiskScanner(BaseSkill):
    """内容合规审核Skill.

    功能：
    1. 广告法合规检查
    2. 平台社区规范检查
    3. 版权风险检查
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize ContentRiskScanner.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # 广告法禁用词库
        self.ad_law_forbidden_words = {
            "极限词": [
                "最",
                "第一",
                "顶级",
                "唯一",
                "100%",
                "绝对",
                "完美",
                "极致",
                "终极",
                "首选",
                "最佳",
                "最优",
                "最好",
                "最大",
                "最小",
                "最高",
                "最低",
                "最强",
                "最新",
                "最先进",
                "最流行",
                "最受欢迎",
                "史上最",
                "全网最",
                "世界级",
                "国际级",
                "顶尖",
                "尖端",
                "巅峰",
            ],
            "虚假宣传": [
                "包治",
                "根治",
                "永久",
                "速效",
                "特效",
                "全效",
                "强效",
                "奇效",
                "高效",
                "神效",
                "超强",
                "万能",
                "包赚",
                "躺赚",
                "日赚",
                "月入",
                "保证",
                "确保",
                "承诺",
            ],
            "医疗禁区": [
                "治疗",
                "治愈",
                "疗效",
                "药效",
                "处方",
                "诊断",
                "医治",
                "根除",
                "防癌",
                "抗癌",
                "防病",
                "治病",
            ],
            "金融禁区": [
                "稳赚",
                "无风险",
                "保本",
                "保收益",
                "高回报",
                "暴利",
                "一夜暴富",
                "躺着赚钱",
            ],
        }

        # 平台规则库
        self.platform_rules = {
            "douyin": {
                "forbidden": [
                    "导流",
                    "加微信",
                    "加V",
                    "私信",
                    "链接",
                    "关注送",
                    "点赞送",
                    "评论送",
                    "搬运",
                    "抄袭",
                    "盗用",
                ],
                "sensitive": ["引流", "推广", "广告", "营销"],
            },
            "xiaohongshu": {
                "forbidden": [
                    "软广",
                    "恰饭",
                    "刷数据",
                    "买粉",
                    "互赞",
                    "互关",
                    "私信",
                    "加微信",
                ],
                "sensitive": ["推荐", "种草", "好物"],
            },
            "bilibili": {
                "forbidden": [
                    "恰饭未标注",
                    "标题党",
                    "引流",
                    "搬运",
                    "盗视频",
                ],
                "sensitive": ["推广", "广告"],
            },
            "weibo": {
                "forbidden": ["敏感话题", "虚假信息", "引战", "谣言"],
                "sensitive": ["政治", "社会事件"],
            },
            "zhihu": {
                "forbidden": ["软广", "引流", "低质内容", "灌水"],
                "sensitive": ["推广", "营销"],
            },
        }

        # 通用敏感词
        self.common_sensitive = [
            "政治",
            "敏感",
            "色情",
            "暴力",
            "赌博",
            "毒品",
            "血腥",
            "恐怖",
            "歧视",
            "仇恨",
            "未成年",
        ]

    def validate_input(
        self, input_data: ContentRiskInput
    ) -> tuple[bool, Optional[str]]:
        """Validate input data.

        Args:
            input_data: Input data

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not input_data.content_text:
            return False, "Content text is empty"

        if not input_data.platform:
            return False, "Platform is missing"

        valid_platforms = ["douyin", "xiaohongshu", "bilibili", "weibo", "zhihu"]
        if input_data.platform not in valid_platforms:
            return False, f"Invalid platform: {input_data.platform}"

        return True, None

    async def execute(self, input_data: ContentRiskInput) -> ContentRiskOutput:
        """Execute content risk scanning.

        Args:
            input_data: Input data

        Returns:
            ContentRiskOutput with risk assessment
        """
        try:
            self.logger.info(
                "Starting content risk scan",
                platform=input_data.platform,
                content_length=len(input_data.content_text),
            )

            risk_points = []

            # 1. 广告法合规检查
            ad_law_risks = self._check_ad_law(input_data.content_text)
            risk_points.extend(ad_law_risks)

            # 2. 平台规则检查
            platform_risks = self._check_platform_rules(
                input_data.content_text, input_data.platform
            )
            risk_points.extend(platform_risks)

            # 3. 通用敏感词检查
            sensitive_risks = self._check_sensitive_words(input_data.content_text)
            risk_points.extend(sensitive_risks)

            # 4. 版权风险检查
            copyright_risks = self._check_copyright(input_data.content_text)
            risk_points.extend(copyright_risks)

            # 5. 评估整体风险等级
            risk_level = self._assess_overall_risk(risk_points)

            # 6. 生成修改建议
            suggestions = self._generate_suggestions(risk_points)

            # 7. 判断是否可以发布
            safe_to_publish = risk_level != "高风险"

            self.logger.info(
                "Content risk scan completed",
                risk_level=risk_level,
                risk_count=len(risk_points),
                safe_to_publish=safe_to_publish,
            )

            return ContentRiskOutput(
                success=True,
                risk_level=risk_level,
                risk_points=risk_points,
                suggestions=suggestions,
                safe_to_publish=safe_to_publish,
                metadata={
                    "platform": input_data.platform,
                    "content_length": len(input_data.content_text),
                    "risk_count": len(risk_points),
                },
            )

        except Exception as e:
            self.logger.error("Content risk scan failed", error=str(e))
            return ContentRiskOutput(success=False, error=str(e))

    def _check_ad_law(self, text: str) -> List[Dict[str, Any]]:
        """检查广告法合规.

        Args:
            text: 内容文本

        Returns:
            风险点列表
        """
        risks = []

        for category, words in self.ad_law_forbidden_words.items():
            for word in words:
                # Simple string search for Chinese text (regex \b doesn't work with CJK)
                start = 0
                while True:
                    pos = text.find(word, start)
                    if pos == -1:
                        break
                    risks.append(
                        {
                            "type": "广告法违规",
                            "category": category,
                            "word": word,
                            "position": pos,
                            "context": self._get_context(text, pos),
                            "severity": "高" if category in ["极限词", "虚假宣传"] else "中",
                            "suggestion": f"删除或替换'{word}'",
                        }
                    )
                    start = pos + len(word)

        return risks

    def _check_platform_rules(self, text: str, platform: str) -> List[Dict[str, Any]]:
        """检查平台规则.

        Args:
            text: 内容文本
            platform: 平台名称

        Returns:
            风险点列表
        """
        risks = []

        if platform not in self.platform_rules:
            return risks

        rules = self.platform_rules[platform]

        # 检查禁用词
        for word in rules.get("forbidden", []):
            if word in text:
                position = text.find(word)
                risks.append(
                    {
                        "type": "平台规则违规",
                        "platform": platform,
                        "word": word,
                        "position": position,
                        "context": self._get_context(text, position),
                        "severity": "高",
                        "suggestion": f"删除'{word}'相关内容",
                    }
                )

        # 检查敏感词
        for word in rules.get("sensitive", []):
            if word in text:
                position = text.find(word)
                risks.append(
                    {
                        "type": "平台敏感词",
                        "platform": platform,
                        "word": word,
                        "position": position,
                        "context": self._get_context(text, position),
                        "severity": "中",
                        "suggestion": f"谨慎使用'{word}'，建议调整表述",
                    }
                )

        return risks

    def _check_sensitive_words(self, text: str) -> List[Dict[str, Any]]:
        """检查通用敏感词.

        Args:
            text: 内容文本

        Returns:
            风险点列表
        """
        risks = []

        for word in self.common_sensitive:
            if word in text:
                position = text.find(word)
                risks.append(
                    {
                        "type": "敏感内容",
                        "word": word,
                        "position": position,
                        "context": self._get_context(text, position),
                        "severity": "高",
                        "suggestion": f"删除或重新表述'{word}'相关内容",
                    }
                )

        return risks

    def _check_copyright(self, text: str) -> List[Dict[str, Any]]:
        """检查版权风险.

        Args:
            text: 内容文本

        Returns:
            风险点列表
        """
        risks = []

        # 检查是否提到BGM/音乐
        music_keywords = ["BGM", "背景音乐", "音乐", "歌曲", "歌名"]
        for keyword in music_keywords:
            if keyword in text:
                risks.append(
                    {
                        "type": "版权提醒",
                        "word": keyword,
                        "position": text.find(keyword),
                        "context": self._get_context(text, text.find(keyword)),
                        "severity": "低",
                        "suggestion": "确保使用的音乐有版权或使用免费音乐库",
                    }
                )
                break  # 只提醒一次

        # 检查是否引用他人内容
        quote_keywords = ["引用", "参考", "来源", "转载"]
        for keyword in quote_keywords:
            if keyword in text:
                risks.append(
                    {
                        "type": "版权提醒",
                        "word": keyword,
                        "position": text.find(keyword),
                        "context": self._get_context(text, text.find(keyword)),
                        "severity": "低",
                        "suggestion": "确保已标注来源并获得授权",
                    }
                )
                break  # 只提醒一次

        return risks

    def _get_context(self, text: str, position: int, window: int = 20) -> str:
        """获取上下文.

        Args:
            text: 完整文本
            position: 位置
            window: 窗口大小

        Returns:
            上下文字符串
        """
        start = max(0, position - window)
        end = min(len(text), position + window)
        context = text[start:end]

        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def _assess_overall_risk(self, risk_points: List[Dict[str, Any]]) -> str:
        """评估整体风险等级.

        Args:
            risk_points: 风险点列表

        Returns:
            风险等级：安全/需注意/高风险
        """
        if not risk_points:
            return "安全"

        # 统计各严重程度的数量
        high_count = sum(1 for r in risk_points if r.get("severity") == "高")
        medium_count = sum(1 for r in risk_points if r.get("severity") == "中")

        if high_count >= 3:
            return "高风险"
        elif high_count >= 1 or medium_count >= 3:
            return "需注意"
        else:
            return "安全"

    def _generate_suggestions(self, risk_points: List[Dict[str, Any]]) -> List[str]:
        """生成修改建议.

        Args:
            risk_points: 风险点列表

        Returns:
            建议列表
        """
        if not risk_points:
            return ["内容合规，可以发布"]

        suggestions = []

        # 按严重程度分组
        high_risks = [r for r in risk_points if r.get("severity") == "高"]
        medium_risks = [r for r in risk_points if r.get("severity") == "中"]
        low_risks = [r for r in risk_points if r.get("severity") == "低"]

        if high_risks:
            suggestions.append(
                f"⚠️ 发现{len(high_risks)}个高风险点，必须修改后才能发布"
            )
            for risk in high_risks[:3]:  # 只显示前3个
                suggestions.append(f"  • {risk.get('suggestion', '')}")

        if medium_risks:
            suggestions.append(f"⚡ 发现{len(medium_risks)}个需注意的点，建议优化")
            for risk in medium_risks[:2]:  # 只显示前2个
                suggestions.append(f"  • {risk.get('suggestion', '')}")

        if low_risks:
            suggestions.append(f"💡 {len(low_risks)}个提醒事项")

        # 通用建议
        if high_risks or medium_risks:
            suggestions.append("\n建议：")
            suggestions.append("  • 使用更中性、客观的表述")
            suggestions.append("  • 避免使用绝对化、夸张的词汇")
            suggestions.append("  • 确保内容真实、准确")

        return suggestions
