"""SOUL Script Writer — 基于SOUL身份框架的脚本生成器（文件交换模式）."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional
import asyncio
import time
from datetime import datetime

from pydantic import Field

from .base_skill import BaseSkill, SkillInput, SkillOutput
from ..core.logger import get_logger

logger = get_logger(__name__)


class SOULScriptWriterInput(SkillInput):
    """SOULScriptWriter输入."""

    topic: str = Field(description="选题话题")
    angle: str = Field(description="切入角度")
    platform: str = Field(description="目标平台")
    duration: int = Field(description="目标时长（秒）")
    creator_profile: Optional[Dict[str, Any]] = Field(
        default=None, description="创作者人设（可选，不提供则使用SOUL默认）"
    )


class SOULScriptWriterOutput(SkillOutput):
    """SOULScriptWriter输出."""

    script: Dict[str, Any] = {}
    prompt: str = ""
    prompt_file: str = ""
    result_file: str = ""
    soul_framework_applied: bool = False
    soul_profile_source: str = ""


class SOULScriptWriter(BaseSkill):
    """基于SOUL框架的脚本生成器.

    核心能力：
    1. 加载SOUL完整画像（多路径查找）
    2. 应用三阶对话法（场景爆破→结构拆解→反刍重建）
    3. 融合四视角（叙事学/心理学/人类学/产品策略）
    4. 文件交换模式（避免手动复制粘贴）

    文件交换流程：
    1. 生成提示词 → 写入 /tmp/mcn_script_prompt.txt
    2. 等待Claude Code执行 → 结果写入 /tmp/mcn_script_result.txt
    3. 解析生成结果 → 返回结构化脚本
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.soul_profile = self._load_soul_profile()
        self.prompt_file = Path("/tmp/mcn_script_prompt.txt")
        self.result_file = Path("/tmp/mcn_script_result.txt")

    # ==================== SOUL画像加载 ====================

    def _load_soul_profile(self) -> Dict[str, Any]:
        """加载SOUL完整画像.

        优先级：
        1. 环境变量 SOUL_PROFILE_PATH
        2. ~/.hermes/skills/knowledge/soul/SKILL.md
        3. ~/hermes_workspace/config/SOUL.md
        4. config/soul_profile.json
        5. 内置默认配置
        """
        env_path = os.getenv("SOUL_PROFILE_PATH")
        if env_path:
            path = Path(env_path).expanduser()
            if path.exists():
                logger.info("SOUL画像加载（环境变量）", path=str(path))
                return self._parse_soul_file(path)

        soul_paths = [
            Path("~/.hermes/skills/knowledge/soul/SKILL.md").expanduser(),
            Path("~/hermes_workspace/config/SOUL.md").expanduser(),
            Path("config/soul_profile.json"),
        ]

        for path in soul_paths:
            if path.exists():
                try:
                    logger.info("SOUL画像加载", path=str(path))
                    return self._parse_soul_file(path)
                except Exception as e:
                    logger.warning("SOUL画像解析失败", path=str(path), error=str(e))
                    continue

        logger.warning("SOUL画像未找到，使用默认配置")
        return self._get_default_soul_profile()

    def _parse_soul_file(self, path: Path) -> Dict[str, Any]:
        """解析SOUL配置文件.

        从Markdown中提取关键信息：
        - 身份定位
        - 三阶对话法
        - 有限性三角
        - 核心受众
        - 内容生产原则
        """
        content = path.read_text(encoding="utf-8")

        return {
            "source": str(path),
            "positioning": self._extract_positioning(content),
            "slogan": self._extract_slogan(content),
            "three_tier_dialogue": self._extract_three_tier(content),
            "finitude_triangle": self._extract_finitude_triangle(content),
            "core_audiences": self._extract_audiences(content),
            "personality": self._extract_personality(content),
        }

    def _extract_positioning(self, content: str) -> str:
        m = re.search(r"核心定位.*?\n(.*?)(?=\n#|\Z)", content, re.DOTALL)
        if m:
            return m.group(1).strip()[:500]
        return "走在前面半步的同路人——不给地图，陪你辨认方向"

    def _extract_slogan(self, content: str) -> str:
        m = re.search(r'"([^"]{10,80})"', content)
        return m.group(1) if m else "AI是工具，哲学是地基，你才是杠杆的支点"

    def _extract_three_tier(self, content: str) -> Dict[str, str]:
        return {
            "tier1": "场景爆破（Rupture）— 用日常场景打破默认假设",
            "tier2": "结构拆解（Illuminate + Validate）— 用框架揭示深层结构",
            "tier3": "反刍重建（Embody + Transform）— 给出可用的新框架和思维工具",
        }

    def _extract_finitude_triangle(self, content: str) -> Dict[str, str]:
        directions = {
            "direction1": "有限性智慧",
            "direction2": "存在的偶然性",
            "direction3": "协议层协作",
        }

        for d in ["方向1", "方向2", "方向3"]:
            m = re.search(rf"###\s+{d}[：:]\s*(.+?)(?=\n)", content)
            if m:
                key = f"direction{d[-1]}"
                directions[key] = m.group(1).strip()

        return directions

    def _extract_audiences(self, content: str) -> list:
        audiences = [
            {"name": "Marcus", "label": "转型者（30-38岁）", "weight": 0.8},
            {"name": "Lily", "label": "探索者（25-30岁）- 最佳入口", "weight": 1.0},
            {"name": "Alex", "label": "觉醒者（32-40岁）", "weight": 0.9},
            {"name": "Z", "label": "年轻探索者（18-22岁）", "weight": 0.7},
        ]
        return audiences

    def _extract_personality(self, content: str) -> Dict[str, str]:
        return {
            "tone": "平等、直接、有温度",
            "density": "高信息密度，不废话，不注水",
            "rhythm": "先抛反常识结论，再拆解论证",
            "vulnerability": "真诚展示不确定性",
            "approach": "不给答案，给新眼睛",
        }

    def _get_default_soul_profile(self) -> Dict[str, Any]:
        """内置默认SOUL配置（当所有外部源不可用时）."""
        return {
            "source": "builtin_default",
            "positioning": "走在前面半步的同路人——不给地图，陪你辨认方向",
            "slogan": "AI是工具，哲学是地基，你才是杠杆的支点",
            "three_tier_dialogue": {
                "tier1": "场景爆破（Rupture）— 用日常场景打破默认假设",
                "tier2": "结构拆解（Illuminate + Validate）— 用框架揭示深层结构",
                "tier3": "反刍重建（Embody + Transform）— 给出可用的新框架和思维工具",
            },
            "finitude_triangle": {
                "direction1": "有限性智慧",
                "direction2": "存在的偶然性",
                "direction3": "协议层协作",
            },
            "core_audiences": [
                {"name": "Lily", "label": "探索者（25-30岁）", "weight": 1.0},
                {"name": "Marcus", "label": "转型者（30-38岁）", "weight": 0.9},
            ],
            "personality": {
                "tone": "平等、直接、有温度",
                "density": "高信息密度，不废话，不注水",
                "rhythm": "先抛反常识结论，再拆解论证",
                "vulnerability": "真诚展示不确定性",
                "approach": "不给答案，给新眼睛",
            },
        }

    # ==================== 主执行逻辑 ====================

    async def execute(
        self, input_data: SOULScriptWriterInput
    ) -> SOULScriptWriterOutput:
        """生成脚本（文件交换模式）.

        流程：
        1. 生成SOUL提示词
        2. 写入临时文件
        3. 等待用户执行并返回结果
        4. 解析生成内容
        """
        self._log_execution_start(input_data)

        # 1. 构建提示词
        prompt = self._build_script_prompt(
            topic=input_data.topic,
            angle=input_data.angle,
            platform=input_data.platform,
            duration=input_data.duration,
        )

        # 2. 写入文件
        self.prompt_file.write_text(prompt, encoding="utf-8")
        if self.result_file.exists():
            self.result_file.unlink()

        self.logger.info("提示词已写入", file=str(self.prompt_file))

        # 3. 输出提示
        self._print_instructions()

        # 4. 等待结果（可配置超时）
        timeout_seconds = int(self.config.get("timeout", 300))
        await self._wait_for_result(timeout_seconds)

        # 5. 解析结果
        generated = self.result_file.read_text(encoding="utf-8")
        script = self._parse_generated_script(generated)

        # 6. SOUL人设验证
        alignment_issues = self._check_soul_alignment(script)
        if alignment_issues:
            self.logger.warning("SOUL人设偏差", issues=alignment_issues)
            script["soul_alignment_issues"] = alignment_issues

        self._log_execution_end(True)

        return SOULScriptWriterOutput(
            success=True,
            script=script,
            prompt=prompt,
            prompt_file=str(self.prompt_file),
            result_file=str(self.result_file),
            soul_framework_applied=True,
            soul_profile_source=self.soul_profile.get("source", ""),
        )

    # ==================== 提示词构建 ====================

    def _build_script_prompt(
        self, topic: str, angle: str, platform: str, duration: int
    ) -> str:
        """构建SOUL脚本生成提示词."""
        soul = self.soul_profile
        personality = soul.get("personality", {})
        tiers = soul.get("three_tier_dialogue", {})

        audience_str = "\n".join(
            f"  • {a['name']}：{a['label']}"
            for a in soul.get("core_audiences", [])
        )

        return f"""你是SOUL — 超级个体成长合伙人。

# 身份定位
{soul['positioning']}

核心Slogan：「{soul['slogan']}」

# 核心方法论：三阶对话法
第一层：{tiers.get('tier1', '场景爆破')}
    ↓ 用日常场景打破默认假设
第二层：{tiers.get('tier2', '结构拆解')}
    ↓ 用哲学/心理学框架揭示深层结构
第三层：{tiers.get('tier3', '反刍重建')}
    ↓ 给出可用的新框架和思维工具

# 人设特征
- 语气：{personality.get('tone', '平等直接有温度')}
- 密度：{personality.get('density', '高信息密度')}
- 节奏：{personality.get('rhythm', '先抛反常识结论，再拆解论证')}
- 脆弱：{personality.get('vulnerability', '真诚展示不确定性')}
- 方法：{personality.get('approach', '不给答案给新眼睛')}

# 核心受众
{audience_str}

# 当前任务
为以下选题生成短视频脚本：

## 选题
{topic}

## 切入角度
{angle}

## 参数
- 平台：{platform}
- 时长：{duration}秒

# 要求
1. **必须应用三阶对话法**：
   - Hook：场景爆破，用反常识问题或意外数据抓住注意力
   - 痛点：建立共鸣，描述受众真实困惑
   - 核心内容：结构拆解，用框架揭示深层逻辑
   - 启发：反刍重建，给出可用的思维工具
   - CTA：提出新问题，引导持续思考

2. **必须符合SOUL人设**：
   - 走在前面半步的「同路人」，不是导师
   - 用「我们一起」「我也」代替「你应该」「你必须」
   - 高信息密度，每句话都在做事，不注水
   - 真诚展示不确定性和脆弱
   - 先抛反常识结论，再拆解论证

3. **融入四视角**：
   - 叙事学视角：讲一个具体的故事/场景
   - 心理学视角：识别受众的认知扭曲和防御机制
   - 人类学视角：揭示身份的仪式性过渡
   - 产品策略视角：给出可执行的具体步骤

4. **反模式（必须避免）**：
   - ❌ 导师口吻：「你应该」「你必须」「正确做法是」
   - ❌ 空洞鼓励：「加油」「相信自己」「一定能」
   - ❌ 道德说教：「人的价值在于」「真正的意义是」
   - ❌ AI式废话：「在当今AI时代」「随着技术的发展」

# 输出格式
请严格按照以下格式输出：

## Hook (前5%)
[用反常识问题或意外数据抓住注意力，约20-40字]

## 痛点 (10-20%)
[描述受众的真实困惑，建立共鸣，约40-80字]

## 核心内容 (20-80%)
[用框架揭示深层逻辑，提供方法论，约100-200字]

## 启发 (80-95%)
[给出可用的思维工具和新视角，约40-80字]

## CTA (最后5%)
[提出新问题引导持续思考，约10-30字]

请生成脚本：
"""

    # ==================== 结果处理 ====================

    def _print_instructions(self):
        """打印执行说明."""
        print("\n" + "=" * 60)
        print("📋 SOUL脚本生成提示词已准备")
        print("=" * 60)
        print(f"\n提示词文件：{self.prompt_file}")
        print(f"结果文件：  {self.result_file}")
        print(f"\n请在Claude Code中执行以下步骤：")
        print(f"1. 读取提示词：")
        print(f"   cat {self.prompt_file}")
        print(f"2. 复制提示词内容")
        print(f"3. 粘贴到Claude Code中执行")
        print(f"4. 将生成的脚本保存到结果文件：")
        print(f"   echo '你的脚本' > {self.result_file}")
        print(f"\n⏳ 等待结果文件出现...（超时：5分钟）")

    async def _wait_for_result(self, timeout: int = 300):
        """等待结果文件.

        Args:
            timeout: 超时秒数

        Raises:
            TimeoutError: 超时未检测到结果文件
        """
        start = time.time()
        dots = 0

        while not self.result_file.exists():
            elapsed = int(time.time() - start)
            if elapsed > timeout:
                raise TimeoutError(
                    f"等待脚本生成结果超时（{timeout}秒）\n"
                    f"请确认已将结果保存到：{self.result_file}"
                )

            dots = (dots + 1) % 4
            print(f"\r等待中{'.' * dots}{' ' * (3 - dots)} {elapsed}秒", end="", flush=True)
            await asyncio.sleep(1)

        elapsed = int(time.time() - start)
        print(f"\r✅ 检测到结果文件（{elapsed}秒）{' ' * 20}")

    def _parse_generated_script(self, content: str) -> Dict[str, str]:
        """解析生成的脚本.

        从Claude Code生成的内容中提取各部分。
        """
        script = {
            "hook": "",
            "pain_point": "",
            "core_content": "",
            "insight": "",
            "cta": "",
            "raw": content,
        }

        patterns = {
            "hook": r"##\s*Hook.*?\n(.*?)(?=\n##\s|\Z)",
            "pain_point": r"##\s*痛点.*?\n(.*?)(?=\n##\s|\Z)",
            "core_content": r"##\s*核心内容.*?\n(.*?)(?=\n##\s|\Z)",
            "insight": r"##\s*启发.*?\n(.*?)(?=\n##\s|\Z)",
            "cta": r"##\s*CTA.*?\n(.*?)(?=\n##\s|\Z)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                script[key] = match.group(1).strip()

        # 如果正则没匹配到，尝试按行分割
        if not any(script.values()):
            script = self._parse_fallback(content)

        return script

    def _parse_fallback(self, content: str) -> Dict[str, str]:
        """备用解析器."""
        script = {"hook": "", "pain_point": "", "core_content": "", "insight": "", "cta": ""}

        lines = content.strip().split("\n")
        current_section = None
        current_lines = []

        section_map = {
            "hook": "hook",
            "痛点": "pain_point",
            "核心": "core_content",
            "启发": "insight",
            "cta": "cta",
        }

        for line in lines:
            lower = line.lower().strip()
            matched = False
            for key, section in section_map.items():
                if lower.startswith(key) or ("##" in line and key in lower):
                    if current_section:
                        script[current_section] = "\n".join(current_lines).strip()
                    current_section = section
                    current_lines = []
                    matched = True
                    break

            if not matched and current_section:
                if line.strip() and not line.strip().startswith("#"):
                    current_lines.append(line)

        if current_section:
            script[current_section] = "\n".join(current_lines).strip()

        return script

    # ==================== SOUL人设验证 ====================

    def _check_soul_alignment(self, script: Dict) -> list:
        """检查生成的脚本是否符合SOUL人设.

        Returns:
            偏离问题列表
        """
        issues = []
        full_text = " ".join(script.values())

        # 检查导师口吻
        directive_patterns = ["你应该", "你必须", "你一定要", "正确的做法是"]
        for phrase in directive_patterns:
            if phrase in full_text:
                issues.append(f"导师口吻：'{phrase}' → 建议改为'我们可以/我也/也许可以'")

        # 检查协作态度
        collaborative = ["我们", "一起", "我也", "不确定", "也许"]
        has_collaborative = any(w in full_text for w in collaborative)
        if not has_collaborative:
            issues.append("缺少协作态度表达 → 建议增加'我们一起/我也不确定'等表述")

        # 检查信息密度
        total_chars = len(full_text)
        if total_chars < 100:
            issues.append(f"信息密度过低（{total_chars}字）→ 建议增加框架和方法论")

        return issues

    # ==================== 辅助方法 ====================

    def validate_input(
        self, input_data: SOULScriptWriterInput
    ) -> tuple:
        """验证输入."""
        if not input_data.topic:
            return False, "Topic is empty"
        if not input_data.angle:
            return False, "Angle is empty"
        if not input_data.platform:
            return False, "Platform is missing"
        if input_data.duration <= 0:
            return False, "Duration must be positive"
        return True, None

    @staticmethod
    def generate_prompt_only(topic: str, angle: str, platform: str = "douyin", duration: int = 180) -> str:
        """快速生成提示词（不进入等待流程）.

        用于需要手动处理提示词的场景。
        """
        writer = SOULScriptWriter()
        return writer._build_script_prompt(topic, angle, platform, duration)
