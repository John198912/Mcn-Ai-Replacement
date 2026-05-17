"""赛道趋势分析引擎 — 解析趋势报告，驱动关键词库和评分权重更新."""

import json
import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from ..core.logger import get_logger

logger = get_logger(__name__)


class TrendAnalyzer:
    """赛道趋势分析引擎.

    功能：
    1. 解析 deepresearch-trend-report
    2. 更新 config/keywords.yaml 的子赛道权重
    3. 调整 SOULHotTopicMatcher 评分参数
    4. 生成月度内容策略建议

    数据存储：data/trend_data.json
    """

    def __init__(self, data_file: str = None):
        self.data_file = Path(data_file or "data/trend_data.json")
        self.keywords_file = Path("config/keywords.yaml")
        self.data = self._load_data()
        self._init_structure()

    def _load_data(self) -> Dict:
        if self.data_file.exists():
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        return {}

    def _save_data(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))

    def _init_structure(self):
        defaults = {
            "reports": [],           # 历史报告归档
            "sub_track_weights": {}, # 子赛道权重
            "audience_trends": {},   # 受众趋势
            "platform_trends": {},   # 平台趋势
            "scoring_params": {},    # 评分参数调整
            "monthly_strategies": [],# 月度策略
            "last_updated": None,
        }
        for key, val in defaults.items():
            if key not in self.data:
                self.data[key] = val

    # ==================== 报告导入 ====================

    def import_report(self, report_path: str) -> Dict:
        """导入 deepresearch-trend-report.

        解析四个维度：
        1. 赛道宏观趋势（子赛道增长/衰退判断）
        2. 内容形式演变（算法偏好变化）
        3. 受众需求迁移（焦虑→理性，副业→意义）
        4. 竞争格局变化（新进入者、方向调整）

        Returns:
            趋势摘要
        """
        content = Path(report_path).read_text(encoding="utf-8")
        report_date = datetime.now().strftime("%Y-%m-%d")

        # 保存原始报告
        self.data["reports"].append({
            "date": report_date,
            "path": str(report_path),
        })

        # 1. 解析子赛道趋势
        sub_tracks = self._parse_sub_track_trends(content)
        self.data["sub_track_weights"] = sub_tracks

        # 2. 解析内容形式演变
        platform_trends = self._parse_platform_trends(content)
        self.data["platform_trends"] = platform_trends

        # 3. 解析受众需求迁移
        audience_trends = self._parse_audience_migration(content)
        self.data["audience_trends"] = audience_trends

        # 4. 解析竞争格局
        competition = self._parse_competition(content)
        self.data["competition"] = competition

        # 5. 生成评分参数调整建议
        scoring = self._derive_scoring_params(sub_tracks, audience_trends)
        self.data["scoring_params"] = scoring

        # 6. 生成月度策略
        strategy = self._generate_strategy(sub_tracks, platform_trends, audience_trends, competition)
        self.data["monthly_strategies"].append({
            "date": report_date,
            "strategy": strategy,
        })

        self.data["last_updated"] = datetime.now().isoformat()
        self._save_data()

        # 7. 更新 keywords.yaml
        self._update_keywords_file(sub_tracks)

        logger.info("趋势报告已导入", sub_tracks=len(sub_tracks))
        return {
            "sub_tracks": sub_tracks,
            "platform_trends": platform_trends,
            "audience_trends": audience_trends,
            "strategy": strategy,
        }

    def _parse_sub_track_trends(self, content: str) -> Dict[str, float]:
        """解析子赛道趋势.

        识别增长↑/衰退↓/平稳→标记，提取权重建议。

        Returns:
            {子赛道名: 权重(0-1)}，如 {"AI工具教程": 0.6, "超级个体方法论": 0.9}
        """
        weights = {}

        # 常见子赛道关键词
        sub_tracks = [
            "AI工具教程", "AI副业", "超级个体", "一人企业",
            "个人品牌", "认知升级", "AI哲学", "AI人文",
            "职场转型", "自由职业", "数字游民", "内容创业",
        ]

        for track in sub_tracks:
            # 查找该子赛道的趋势描述
            pattern = rf"{track}.*?(?:增长|爆发|上升|看好|机会)"
            m_growth = re.search(pattern, content)
            pattern_decline = rf"{track}.*?(?:衰退|下降|饱和|过时|减少)"
            m_decline = re.search(pattern_decline, content)

            if m_growth:
                weights[track] = 0.9  # 增长趋势，高权重
            elif m_decline:
                weights[track] = 0.3  # 衰退趋势，低权重
            else:
                weights[track] = 0.6  # 默认中性权重

        return weights

    def _parse_platform_trends(self, content: str) -> Dict[str, Dict]:
        """解析平台内容形式趋势."""
        trends = {}
        platforms = {
            "douyin": "抖音",
            "xiaohongshu": "小红书",
            "bilibili": "B站",
        }

        for key, name in platforms.items():
            # 查找该平台的趋势分析
            pattern = rf"{name}.*?(?:推荐|流量|算法|权重|偏好).*?(?:([^。]+)(?:上升|增长|下降|变化))"
            m = re.search(pattern, content)
            trends[key] = {
                "platform": name,
                "trend": m.group(1).strip()[:100] if m else "无明确信号",
                "short_video_weight": self._estimate_weight(content, name, "短视频"),
                "long_video_weight": self._estimate_weight(content, name, "中长视频|长视频"),
                "text_weight": self._estimate_weight(content, name, "图文|文章"),
            }
        return trends

    def _estimate_weight(self, content: str, platform: str, content_type: str) -> float:
        """估计内容形式在某平台的权重."""
        pattern = rf"{platform}.*?{content_type}.*?(?:上升|增长|扶持|偏好|权重增加)"
        if re.search(pattern, content):
            return 0.8
        pattern_decline = rf"{platform}.*?{content_type}.*?(?:下降|减少|边缘化|权重降低)"
        if re.search(pattern_decline, content):
            return 0.3
        return 0.5

    def _parse_audience_migration(self, content: str) -> Dict:
        """解析受众需求迁移."""
        return {
            "anxiety_level": self._extract_trend_direction(content, "焦虑"),
            "meaning_seeking": self._extract_trend_direction(content, "意义|成长|精神"),
            "practical_needs": self._extract_trend_direction(content, "副业|赚钱|变现"),
            "emerging_pain_points": self._extract_list_after_keyword(content, "新的受众痛点"),
        }

    def _parse_competition(self, content: str) -> Dict:
        """解析竞争格局."""
        return {
            "new_entrants": self._extract_list_after_keyword(content, "新进入|新玩家|涌现"),
            "direction_shifts": self._extract_list_after_keyword(content, "方向调整|转型|转向"),
            "saturation_signals": "饱和" in content or "红海" in content,
        }

    # ==================== 评分参数推导 ====================

    def _derive_scoring_params(
        self,
        sub_tracks: Dict[str, float],
        audience_trends: Dict,
    ) -> Dict:
        """从趋势推导SOUL评分参数调整.

        Returns:
            {
              "finitude_weight": 0.30 (调整后),
              "audience_weight": 0.25,
              "dialogue_weight": 0.25,
              "differentiation_weight": 0.15,
              "risk_weight": 0.05,
              "boost_topics": [...],    # 加分话题
              "penalize_topics": [...], # 减分话题
            }
        """
        params = {
            "finitude_weight": 0.30,
            "audience_weight": 0.25,
            "dialogue_weight": 0.25,
            "differentiation_weight": 0.15,
            "risk_weight": 0.05,
            "boost_topics": [],
            "penalize_topics": [],
        }

        # 根据子赛道权重调整
        for track, weight in sub_tracks.items():
            if weight >= 0.8:
                params["boost_topics"].append(track)
            elif weight <= 0.3:
                params["penalize_topics"].append(track)

        # 如果焦虑在上升，提高差异化权重
        if audience_trends.get("anxiety_level") == "rising":
            params["differentiation_weight"] += 0.05
            params["dialogue_weight"] -= 0.05

        return params

    def get_scoring_params(self) -> Dict:
        """获取当前评分参数（供 SOULHotTopicMatcher 使用）."""
        return self.data.get("scoring_params", {})

    def get_topic_weight(self, topic_tags: List[str]) -> float:
        """获取某话题的趋势加权.

        Returns:
            1.0 为中性，>1.0 为加分，<1.0 为减分
        """
        weights = self.data.get("sub_track_weights", {})
        boost = self.data.get("scoring_params", {}).get("boost_topics", [])
        penalize = self.data.get("scoring_params", {}).get("penalize_topics", [])

        multiplier = 1.0
        for tag in topic_tags:
            if tag in boost:
                multiplier *= 1.2
            if tag in penalize:
                multiplier *= 0.8

        # 基于赛道权重调整
        for track, weight in weights.items():
            if track in topic_tags:
                multiplier *= (0.5 + weight)  # 映射 0.3→0.8, 0.9→1.4

        return round(multiplier, 2)

    # ==================== 月度策略 ====================

    def _generate_strategy(self, sub_tracks, platform_trends, audience_trends, competition) -> Dict:
        """生成月度内容策略."""
        strategies = []

        # 高权重子赛道
        hot_tracks = [t for t, w in sub_tracks.items() if w >= 0.8]
        if hot_tracks:
            strategies.append(f"🔥 重点赛道：{'、'.join(hot_tracks)}")

        # 衰退子赛道
        cold_tracks = [t for t, w in sub_tracks.items() if w <= 0.3]
        if cold_tracks:
            strategies.append(f"⚠️ 谨慎投入：{'、'.join(cold_tracks)}")

        # 平台策略
        for key, trend in platform_trends.items():
            if trend.get("short_video_weight", 0.5) > 0.6:
                strategies.append(f"📱 {trend['platform']}：增加短视频投入")
            if trend.get("long_video_weight", 0.5) > 0.6:
                strategies.append(f"📺 {trend['platform']}：重点布局中长视频")

        # 受众策略
        if audience_trends.get("meaning_seeking") == "rising":
            strategies.append("🧠 受众在寻求意义，增加哲学/认知类内容比例")
        if audience_trends.get("practical_needs") == "rising":
            strategies.append("🛠️ 受众偏重实用，增加工具教程+方法论内容")

        # 竞争策略
        if competition.get("saturation_signals"):
            strategies.append("⚡ 赛道趋近饱和，强调差异化，避免跟风热门话题")

        return {
            "strategies": strategies,
            "hot_tracks": hot_tracks,
            "cold_tracks": cold_tracks,
            "content_mix": self._estimate_content_mix(platform_trends, audience_trends),
        }

    def _estimate_content_mix(self, platform_trends, audience_trends) -> Dict:
        """估算推荐内容配比."""
        return {
            "tutorial": 0.25,
            "methodology": 0.30,
            "philosophy": 0.25,
            "trending": 0.20,
        }

    # ==================== keywords.yaml 更新 ====================

    def _update_keywords_file(self, sub_tracks: Dict[str, float]):
        """根据趋势更新 keywords.yaml 中的关键词权重."""
        if not self.keywords_file.exists():
            logger.warning("keywords.yaml not found")
            return

        with open(self.keywords_file, "r", encoding="utf-8") as f:
            keywords_data = yaml.safe_load(f) or {}

        # 在文件末尾追加趋势权重信息
        # 实际使用时不直接修改文件，而是保存到 trend_data.json
        # keywords.yaml 保持手动维护，趋势数据作为运行时叠加

    def generate_monthly_strategy(self) -> Dict:
        """生成当前月度内容策略报告."""
        if not self.data.get("last_updated"):
            return {"error": "尚未导入趋势报告"}

        latest = self.data["monthly_strategies"][-1] if self.data["monthly_strategies"] else {}
        scoring = self.data.get("scoring_params", {})

        return {
            "date": self.data["last_updated"],
            "strategies": latest.get("strategy", {}).get("strategies", []),
            "hot_tracks": scoring.get("boost_topics", []),
            "cold_tracks": scoring.get("penalize_topics", []),
            "scoring_weights": {
                k: v for k, v in scoring.items()
                if k.endswith("_weight")
            },
        }

    # ==================== 工具方法 ====================

    @staticmethod
    def _extract_trend_direction(content: str, keyword: str) -> str:
        """提取趋势方向：rising / declining / stable."""
        pattern_rise = rf"{keyword}.*?(?:上升|加剧|增强|增长|增加|扩大)"
        pattern_decline = rf"{keyword}.*?(?:下降|减弱|减少|缓解|缩小|趋于理性)"
        if re.search(pattern_rise, content):
            return "rising"
        if re.search(pattern_decline, content):
            return "declining"
        return "stable"

    @staticmethod
    def _extract_list_after_keyword(content: str, keyword: str) -> List[str]:
        """提取关键词后的列表项."""
        pattern = rf"{keyword}.*?\n((?:\s*[-*]\s*.+\n?)+)"
        m = re.search(pattern, content)
        if m:
            return [re.sub(r"^\s*[-*]\s*", "", i).strip()
                    for i in m.group(1).strip().split("\n") if i.strip()]
        return []
