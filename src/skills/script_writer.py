"""Script Writer Skill - 脚本生成."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_skill import BaseSkill, SkillInput, SkillOutput


class ScriptWriterInput(SkillInput):
    """Input for ScriptWriter."""

    topic: str = Field(description="选题话题")
    angle: str = Field(description="切入角度")
    platform: str = Field(description="目标平台")
    duration: int = Field(description="目标时长（秒）")
    creator_profile: Dict[str, Any] = Field(description="创作者人设")
    reference_content: Optional[Dict[str, Any]] = Field(
        default=None, description="参考内容（可选）"
    )


class ScriptWriterOutput(SkillOutput):
    """Output for ScriptWriter."""

    script: Dict[str, Any] = {}
    analysis: Dict[str, Any] = {}
    word_count: int = 0
    estimated_duration: int = 0


class ScriptWriter(BaseSkill):
    """脚本生成Skill.

    功能：
    1. 基于选题和人设生成结构化脚本
    2. 应用创作者风格约束
    3. 自动分析脚本质量
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize ScriptWriter.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # 脚本结构模板
        self.script_structure = {
            "hook": {
                "duration_ratio": 0.05,  # 前5%
                "purpose": "抓住注意力",
                "techniques": ["反常识问题", "个人真实经历", "数据颠覆认知", "痛点直击"],
            },
            "pain_point": {
                "duration_ratio": 0.15,  # 10-20%
                "purpose": "建立共鸣",
                "techniques": ["展示脆弱", "描述痛点", "引发共情"],
            },
            "core_content": {
                "duration_ratio": 0.60,  # 20-80%
                "purpose": "提供价值",
                "techniques": ["框架化呈现", "案例支撑", "方法论"],
            },
            "insight": {
                "duration_ratio": 0.15,  # 80-95%
                "purpose": "认知升级",
                "techniques": ["更高维度综合", "反转", "启发"],
            },
            "cta": {
                "duration_ratio": 0.05,  # 最后5%
                "purpose": "行动引导",
                "techniques": ["微行动", "给选项", "不说教"],
            },
        }

    def validate_input(
        self, input_data: ScriptWriterInput
    ) -> tuple[bool, Optional[str]]:
        """Validate input data.

        Args:
            input_data: Input data

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not input_data.topic:
            return False, "Topic is empty"

        if not input_data.angle:
            return False, "Angle is empty"

        if not input_data.platform:
            return False, "Platform is missing"

        if input_data.duration <= 0:
            return False, "Duration must be positive"

        if not input_data.creator_profile:
            return False, "Creator profile is missing"

        return True, None

    async def execute(self, input_data: ScriptWriterInput) -> ScriptWriterOutput:
        """Execute script generation.

        Args:
            input_data: Input data

        Returns:
            ScriptWriterOutput with generated script
        """
        try:
            self.logger.info(
                "Starting script generation",
                topic=input_data.topic,
                platform=input_data.platform,
                duration=input_data.duration,
            )

            # 1. 提取创作者风格参数
            style_params = self._extract_style_params(input_data.creator_profile)

            # 2. 生成脚本各部分
            script = await self._generate_script(
                input_data.topic,
                input_data.angle,
                input_data.platform,
                input_data.duration,
                style_params,
                input_data.reference_content,
            )

            # 3. 计算字数和预估时长
            word_count = self._count_words(script)
            estimated_duration = self._estimate_duration(word_count, input_data.platform)

            # 4. 分析脚本质量
            analysis = self._analyze_script(script, style_params, input_data.duration)

            self.logger.info(
                "Script generation completed",
                word_count=word_count,
                estimated_duration=estimated_duration,
            )

            return ScriptWriterOutput(
                success=True,
                script=script,
                analysis=analysis,
                word_count=word_count,
                estimated_duration=estimated_duration,
                metadata={
                    "topic": input_data.topic,
                    "platform": input_data.platform,
                    "target_duration": input_data.duration,
                },
            )

        except Exception as e:
            self.logger.error("Script generation failed", error=str(e))
            return ScriptWriterOutput(success=False, error=str(e))

    def _extract_style_params(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """提取创作者风格参数.

        Args:
            profile: 创作者画像

        Returns:
            风格参数字典
        """
        content_style = profile.get("content_style", {})
        content_prefs = profile.get("content_preferences", {})

        return {
            "tone": content_style.get("tone", "同路人"),
            "personality_type": content_style.get("personality_type", "ENTP"),
            "preferred_phrases": content_style.get("preferred_phrases", []),
            "avoid_phrases": content_style.get("avoid_phrases", []),
            "information_density": content_prefs.get("information_density", 8),
            "conversational_tone": content_prefs.get("conversational_tone", 8),
            "challenge_level": content_prefs.get("challenge_level", 7),
            "vulnerability_sharing": content_prefs.get("vulnerability_sharing", 7),
            "framework_thinking": content_prefs.get("framework_thinking", 9),
        }

    async def _generate_script(
        self,
        topic: str,
        angle: str,
        platform: str,
        duration: int,
        style_params: Dict[str, Any],
        reference: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成脚本.

        Args:
            topic: 选题
            angle: 切入角度
            platform: 平台
            duration: 时长
            style_params: 风格参数
            reference: 参考内容

        Returns:
            脚本字典
        """
        # 计算各部分的目标字数
        target_words = self._calculate_target_words(duration, platform)
        section_words = self._allocate_words(target_words)

        # 生成各部分内容
        script = {
            "title": self._generate_title(topic, angle, style_params),
            "hook": self._generate_hook(topic, angle, section_words["hook"], style_params),
            "pain_point": self._generate_pain_point(
                topic, angle, section_words["pain_point"], style_params
            ),
            "core_content": self._generate_core_content(
                topic, angle, section_words["core_content"], style_params, reference
            ),
            "insight": self._generate_insight(
                topic, angle, section_words["insight"], style_params
            ),
            "cta": self._generate_cta(
                topic, angle, section_words["cta"], style_params
            ),
        }

        return script

    def _calculate_target_words(self, duration: int, platform: str) -> int:
        """计算目标字数.

        Args:
            duration: 时长（秒）
            platform: 平台

        Returns:
            目标字数
        """
        # 不同平台的语速（字/秒）
        speech_rates = {
            "douyin": 4.5,  # 抖音语速较快
            "xiaohongshu": 4.0,
            "bilibili": 3.5,  # B站可以慢一点
            "weibo": 4.0,
            "zhihu": 3.5,
        }

        rate = speech_rates.get(platform, 4.0)
        return int(duration * rate)

    def _allocate_words(self, total_words: int) -> Dict[str, int]:
        """分配各部分字数.

        Args:
            total_words: 总字数

        Returns:
            各部分字数字典
        """
        return {
            "hook": int(total_words * 0.05),
            "pain_point": int(total_words * 0.15),
            "core_content": int(total_words * 0.60),
            "insight": int(total_words * 0.15),
            "cta": int(total_words * 0.05),
        }

    def _generate_title(
        self, topic: str, angle: str, style_params: Dict[str, Any]
    ) -> str:
        """生成标题.

        Args:
            topic: 选题
            angle: 切入角度
            style_params: 风格参数

        Returns:
            标题
        """
        # 简化版：组合topic和angle
        # 实际应用中可以使用更复杂的生成逻辑或调用LLM
        return f"{topic}：{angle}"

    def _generate_hook(
        self, topic: str, angle: str, target_words: int, style_params: Dict[str, Any]
    ) -> str:
        """生成Hook（前3秒）.

        Args:
            topic: 选题
            angle: 切入角度
            target_words: 目标字数
            style_params: 风格参数

        Returns:
            Hook文本
        """
        # 这里是简化版本，实际应用中应该调用LLM生成
        # 根据风格参数选择Hook类型
        hook_templates = {
            "反常识": f"你以为{topic}是这样的？其实完全相反。",
            "个人经历": f"说实话，我也曾经在{topic}上栽过跟头。",
            "数据颠覆": f"关于{topic}，有个数据可能会颠覆你的认知。",
            "痛点直击": f"如果你也在{topic}上感到焦虑，这条视频可能帮到你。",
        }

        # 选择第一个模板（实际应该根据topic和angle智能选择）
        hook = list(hook_templates.values())[0]

        return f"[Hook - 前3秒]\n{hook}\n\n> 设计原则：3秒内抓住注意力，体现认知挑战"

    def _generate_pain_point(
        self, topic: str, angle: str, target_words: int, style_params: Dict[str, Any]
    ) -> str:
        """生成痛点共鸣部分.

        Args:
            topic: 选题
            angle: 切入角度
            target_words: 目标字数
            style_params: 风格参数

        Returns:
            痛点文本
        """
        # 简化版本
        pain_point = f"""[痛点共鸣 - 3-15秒]
你是不是也有过这样的经历：想要在{topic}上有所突破，但总是感觉力不从心？

看着别人轻松做到，自己却怎么也找不到方法。

> 设计原则：展示脆弱建立共情，不说教"""

        return pain_point

    def _generate_core_content(
        self,
        topic: str,
        angle: str,
        target_words: int,
        style_params: Dict[str, Any],
        reference: Optional[Dict[str, Any]],
    ) -> str:
        """生成核心内容.

        Args:
            topic: 选题
            angle: 切入角度
            target_words: 目标字数
            style_params: 风格参数
            reference: 参考内容

        Returns:
            核心内容文本
        """
        # 简化版本 - 框架化呈现
        core = f"""[核心论点 - 15秒-X]

从{angle}来看，{topic}其实可以这样理解：

**第一，** [论点一]
举个例子，[具体案例或类比]

**第二，** [论点二]
这就像[类比说明]

**第三，** [论点三或辩证综合]
但这里有个反直觉的点：[反转]

> 设计原则：高信息密度+框架感，将个人经历提炼为可复制方法论"""

        return core

    def _generate_insight(
        self, topic: str, angle: str, target_words: int, style_params: Dict[str, Any]
    ) -> str:
        """生成启发/反转部分.

        Args:
            topic: 选题
            angle: 切入角度
            target_words: 目标字数
            style_params: 风格参数

        Returns:
            启发文本
        """
        # 简化版本
        insight = f"""[启发/反转 - 80-95%]

所以，{topic}的本质其实不是[表面现象]，而是[更高维度的理解]。

这个认知一旦建立，很多问题就迎刃而解了。

> 设计原则：提供认知增量，不是简单总结"""

        return insight

    def _generate_cta(
        self, topic: str, angle: str, target_words: int, style_params: Dict[str, Any]
    ) -> str:
        """生成CTA（行动召唤）.

        Args:
            topic: 选题
            angle: 切入角度
            target_words: 目标字数
            style_params: 风格参数

        Returns:
            CTA文本
        """
        # 使用创作者偏好的表述
        preferred = style_params.get("preferred_phrases", [])
        phrase = preferred[0] if preferred else "你可以试试"

        cta = f"""[CTA - 最后5-10秒]

{phrase}，今天就从[一个微行动]开始。

不用完美，先开始就好。

> 设计原则：不说教，给选项。"{phrase}..." 而非 "你应该..." """

        return cta

    def _count_words(self, script: Dict[str, Any]) -> int:
        """统计字数.

        Args:
            script: 脚本字典

        Returns:
            总字数
        """
        total = 0
        for section in ["hook", "pain_point", "core_content", "insight", "cta"]:
            text = script.get(section, "")
            # 只统计中文字符和英文单词
            chinese_chars = len([c for c in text if "一" <= c <= "鿿"])
            english_words = len(text.split())
            total += chinese_chars + english_words // 2  # 英文单词按0.5计

        return total

    def _estimate_duration(self, word_count: int, platform: str) -> int:
        """预估时长.

        Args:
            word_count: 字数
            platform: 平台

        Returns:
            预估时长（秒）
        """
        speech_rates = {
            "douyin": 4.5,
            "xiaohongshu": 4.0,
            "bilibili": 3.5,
            "weibo": 4.0,
            "zhihu": 3.5,
        }

        rate = speech_rates.get(platform, 4.0)
        return int(word_count / rate)

    def _analyze_script(
        self, script: Dict[str, Any], style_params: Dict[str, Any], target_duration: int
    ) -> Dict[str, Any]:
        """分析脚本质量.

        Args:
            script: 脚本字典
            style_params: 风格参数
            target_duration: 目标时长

        Returns:
            分析结果
        """
        analysis = {
            "information_density": self._check_information_density(script),
            "persona_consistency": self._check_persona_consistency(
                script, style_params
            ),
            "structure_balance": self._check_structure_balance(script),
            "improvement_suggestions": [],
        }

        # 生成改进建议
        if analysis["information_density"]["score"] < 7:
            analysis["improvement_suggestions"].append("增加信息密度，每段都要有增量")

        if not analysis["persona_consistency"]["consistent"]:
            analysis["improvement_suggestions"].append(
                f"调整语气，避免使用：{', '.join(analysis['persona_consistency']['violations'][:3])}"
            )

        if not analysis["structure_balance"]["balanced"]:
            analysis["improvement_suggestions"].append("调整各部分比例，保持结构平衡")

        return analysis

    def _check_information_density(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """检查信息密度.

        Args:
            script: 脚本字典

        Returns:
            检查结果
        """
        # 简化版：检查是否每个部分都有实质内容
        sections_with_content = 0
        total_sections = 5

        for section in ["hook", "pain_point", "core_content", "insight", "cta"]:
            text = script.get(section, "")
            if len(text) > 50:  # 简单判断：超过50字认为有内容
                sections_with_content += 1

        score = (sections_with_content / total_sections) * 10

        return {
            "score": round(score, 1),
            "sections_with_content": sections_with_content,
            "total_sections": total_sections,
        }

    def _check_persona_consistency(
        self, script: Dict[str, Any], style_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查人设一致性.

        Args:
            script: 脚本字典
            style_params: 风格参数

        Returns:
            检查结果
        """
        # 检查是否使用了应避免的表述
        avoid_phrases = style_params.get("avoid_phrases", [])
        violations = []

        full_text = " ".join(
            [script.get(s, "") for s in ["hook", "pain_point", "core_content", "insight", "cta"]]
        )

        for phrase in avoid_phrases:
            if phrase in full_text:
                violations.append(phrase)

        return {
            "consistent": len(violations) == 0,
            "violations": violations,
            "avoid_phrases_count": len(avoid_phrases),
        }

    def _check_structure_balance(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """检查结构平衡.

        Args:
            script: 脚本字典

        Returns:
            检查结果
        """
        # 检查各部分字数比例
        section_lengths = {}
        total_length = 0

        for section in ["hook", "pain_point", "core_content", "insight", "cta"]:
            length = len(script.get(section, ""))
            section_lengths[section] = length
            total_length += length

        # 计算比例
        ratios = {}
        for section, length in section_lengths.items():
            ratios[section] = length / total_length if total_length > 0 else 0

        # 检查是否平衡（核心内容应该占大头）
        balanced = ratios.get("core_content", 0) >= 0.5

        return {
            "balanced": balanced,
            "ratios": ratios,
            "section_lengths": section_lengths,
        }
