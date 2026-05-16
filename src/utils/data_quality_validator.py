"""数据质量验证和去重."""

from typing import List, Tuple, Dict
from datetime import datetime
from ..core.logger import get_logger

logger = get_logger(__name__)


class DataQualityValidator:
    """数据质量验证器.

    功能：
    1. 验证热点数据完整性和合理性
    2. 检测和移除重复数据
    3. 过滤低质量数据
    4. 生成质量报告

    支持 dict 和对象类型的输入。
    """

    def __init__(self):
        self.min_title_length = 5
        self.max_title_length = 100
        self.min_description_length = 10
        self.valid_platforms = {"douyin", "xiaohongshu", "bilibili", "weibo", "zhihu"}
        self.valid_heat_levels = {"爆发", "上升", "稳定", "衰退"}

    @staticmethod
    def _get_field(obj, field: str, default=""):
        """从dict或对象中获取字段值."""
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)

    def validate_hotspot(self, hotspot) -> Tuple[bool, str]:
        """验证单个热点数据质量."""
        checks = [
            (self._check_title, "标题"),
            (self._check_platform, "平台"),
            (self._check_heat_level, "热度等级"),
        ]
        for check_func, check_name in checks:
            is_valid, message = check_func(hotspot)
            if not is_valid:
                return False, f"[{check_name}] {message}"
        return True, "OK"

    def _check_title(self, hotspot) -> Tuple[bool, str]:
        title = self._get_field(hotspot, "title", "")
        if not title:
            return False, "标题为空"
        if len(title) < self.min_title_length:
            return False, f"标题过短（{len(title)} < {self.min_title_length}）"
        if len(title) > self.max_title_length:
            return False, f"标题过长（{len(title)} > {self.max_title_length}）"
        garbage_patterns = ["广告", "推广", "联系方式", "加微信"]
        for pattern in garbage_patterns:
            if pattern in title:
                return False, f"标题包含垃圾内容：{pattern}"
        return True, "OK"

    def _check_platform(self, hotspot) -> Tuple[bool, str]:
        platform = self._get_field(hotspot, "platform", "")
        if not platform:
            return False, "平台为空"
        if platform.lower() not in self.valid_platforms:
            return False, f"无效平台：{platform}（支持：{self.valid_platforms}）"
        return True, "OK"

    def _check_heat_level(self, hotspot) -> Tuple[bool, str]:
        heat_level = self._get_field(hotspot, "heat_level", "上升")
        if heat_level not in self.valid_heat_levels:
            return False, f"无效热度：{heat_level}（支持：{self.valid_heat_levels}）"
        return True, "OK"

    def deduplicate(self, hotspots: List) -> Tuple[List, int]:
        """去重.

        规则：
        1. 标题完全相同 → 重复
        2. 标题相似度 > 0.85 → 可能重复（保留第一个）
        """
        seen_titles = set()
        unique = []
        removed_count = 0

        for hotspot in hotspots:
            title = self._get_field(hotspot, "title", "")
            normalized = title.lower().strip()
            if normalized in seen_titles:
                removed_count += 1
                continue
            is_duplicate = False
            for seen_title in seen_titles:
                if self._title_similarity(normalized, seen_title) > 0.85:
                    is_duplicate = True
                    removed_count += 1
                    break
            if not is_duplicate:
                seen_titles.add(normalized)
                unique.append(hotspot)

        if removed_count > 0:
            logger.info("去重完成", removed=removed_count, kept=len(unique))
        return unique, removed_count

    @staticmethod
    def _title_similarity(title1: str, title2: str) -> float:
        """计算两个标题的相似度（基于bigram的Jaccard系数）."""
        def char_bigrams(s):
            return {s[i:i + 2] for i in range(len(s) - 1)}

        bigrams1 = char_bigrams(title1)
        bigrams2 = char_bigrams(title2)
        if not bigrams1 or not bigrams2:
            return 0.0
        intersection = len(bigrams1 & bigrams2)
        union = len(bigrams1 | bigrams2)
        return intersection / union if union > 0 else 0.0

    def filter_low_quality(self, hotspots: List) -> Tuple[List, List[Tuple]]:
        """过滤低质量数据."""
        quality = []
        filtered = []

        for hotspot in hotspots:
            is_valid, reason = self.validate_hotspot(hotspot)
            if is_valid:
                quality.append(hotspot)
            else:
                filtered.append((hotspot, reason))

        if filtered:
            logger.warning("过滤低质量数据", count=len(filtered))
        return quality, filtered

    def validate_batch(self, hotspots: List) -> Dict:
        """批量验证并生成质量报告."""
        unique, duplicates_removed = self.deduplicate(hotspots)
        quality, filtered = self.filter_low_quality(unique)

        report = {
            "total_input": len(hotspots),
            "duplicates_removed": duplicates_removed,
            "low_quality_filtered": len(filtered),
            "final_count": len(quality),
            "pass_rate": f"{len(quality) / max(len(hotspots), 1) * 100:.1f}%",
            "filtered_details": [
                {"title": self._get_field(h, "title", "N/A"), "reason": reason}
                for h, reason in filtered
            ],
            "validated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "质量报告",
            total=report["total_input"],
            final=report["final_count"],
            pass_rate=report["pass_rate"],
        )
        return report
