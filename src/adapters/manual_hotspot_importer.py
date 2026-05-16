"""手动热点导入器 - 支持CSV/JSON/Markdown格式."""

from pathlib import Path
from typing import List, Dict
import csv
import json
from ..core.logger import get_logger

logger = get_logger(__name__)


class ManualHotspotImporter:
    """手动热点导入器.

    支持三种格式：
    1. CSV文件
    2. JSON文件
    3. Markdown表格

    当Hermes报告不可用时使用。
    """

    def import_from_file(self, file_path: str) -> List[Dict]:
        """从文件导入热点，自动识别格式.

        Args:
            file_path: 文件路径

        Returns:
            热点字典列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            return self.import_from_csv(file_path)
        elif suffix == ".json":
            return self.import_from_json(file_path)
        elif suffix == ".md":
            return self.import_from_markdown(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}（支持 .csv / .json / .md）")

    def import_from_csv(self, file_path: str) -> List[Dict]:
        """从CSV导入.

        CSV格式（第一行为表头）：
        标题,平台,热度,标签,描述
        AI焦虑,douyin,上升,"AI,超级个体",探讨AI时代的焦虑
        """
        hotspots = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tags_str = row.get("标签", "")
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    hotspot = {
                        "title": row.get("标题", ""),
                        "platform": row.get("平台", ""),
                        "heat_level": row.get("热度", "上升"),
                        "tags": tags,
                        "description": row.get("描述", ""),
                        "recommended_angle": row.get("推荐角度", ""),
                        "priority": row.get("优先级", "P1"),
                        "source": "manual_csv",
                    }
                    hotspots.append(hotspot)
            logger.info("CSV导入完成", file=file_path, count=len(hotspots))
        except Exception as e:
            logger.error("CSV导入失败", file=file_path, error=str(e))
            raise
        return hotspots

    def import_from_json(self, file_path: str) -> List[Dict]:
        """从JSON导入.

        JSON格式：
        [
            {
                "title": "AI焦虑",
                "platform": "douyin",
                "heat_level": "上升",
                "tags": ["AI", "超级个体"],
                "description": "探讨AI时代的焦虑"
            }
        ]
        """
        hotspots = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 支持单个对象或数组
            if isinstance(data, dict):
                data = [data]

            for item in data:
                hotspot = {
                    "title": item.get("title", ""),
                    "platform": item.get("platform", ""),
                    "heat_level": item.get("heat_level", "上升"),
                    "tags": item.get("tags", []),
                    "description": item.get("description", ""),
                    "recommended_angle": item.get("recommended_angle", ""),
                    "priority": item.get("priority", "P1"),
                    "source": "manual_json",
                }
                hotspots.append(hotspot)
            logger.info("JSON导入完成", file=file_path, count=len(hotspots))
        except Exception as e:
            logger.error("JSON导入失败", file=file_path, error=str(e))
            raise
        return hotspots

    def import_from_markdown(self, file_path: str) -> List[Dict]:
        """从Markdown表格导入.

        Markdown格式：
        | 标题 | 平台 | 热度 | 标签 | 描述 |
        |------|------|------|------|------|
        | AI焦虑 | douyin | 上升 | AI,超级个体 | 探讨AI时代的焦虑 |
        """
        hotspots = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.strip().split("\n")

            # 找到表格头
            header_idx = -1
            for i, line in enumerate(lines):
                if "标题" in line and "平台" in line:
                    header_idx = i
                    break
            if header_idx == -1:
                logger.warning("Markdown中未找到表格", file=file_path)
                return hotspots

            # 解析表头
            header = lines[header_idx]
            columns = [col.strip() for col in header.split("|") if col.strip()]

            # 解析数据行（跳过表头和分隔线）
            for line in lines[header_idx + 2:]:
                if not line.strip():
                    break
                cells = [cell.strip() for cell in line.split("|") if cell.strip()]
                if len(cells) < len(columns):
                    continue

                row = dict(zip(columns, cells))
                tags_str = row.get("标签", "")
                tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

                hotspot = {
                    "title": row.get("标题", ""),
                    "platform": row.get("平台", ""),
                    "heat_level": row.get("热度", "上升"),
                    "tags": tags,
                    "description": row.get("描述", ""),
                    "recommended_angle": row.get("推荐角度", ""),
                    "priority": row.get("优先级", "P1"),
                    "source": "manual_markdown",
                }
                hotspots.append(hotspot)
            logger.info("Markdown导入完成", file=file_path, count=len(hotspots))
        except Exception as e:
            logger.error("Markdown导入失败", file=file_path, error=str(e))
            raise
        return hotspots

    def generate_template_csv(self, output_path: str):
        """生成CSV导入模板."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["标题", "平台", "热度", "标签", "描述", "推荐角度", "优先级"])
            writer.writerow([
                "AI时代如何重新学会选择和放弃的能力",
                "douyin",
                "上升",
                "AI,超级个体,有限性",
                "AI能做一切但你只能做一件事，探讨AI时代的选择与放弃",
                "从有限性视角解读AI焦虑",
                "P0",
            ])
            writer.writerow([
                "超级个体如何打造一人企业实现自由职业转型",
                "xiaohongshu",
                "爆发",
                "超级个体,创业,自由职业",
                "探讨如何在AI时代构建一人企业，从打工人向超级个体转型",
                "超级个体的生存法则",
                "P1",
            ])
        logger.info("CSV模板已生成", path=output_path)

    def generate_template_json(self, output_path: str):
        """生成JSON导入模板."""
        template = [
            {
                "title": "AI时代如何重新学会选择和放弃的能力",
                "platform": "douyin",
                "heat_level": "上升",
                "tags": ["AI", "超级个体", "有限性"],
                "description": "AI能做一切但你只能做一件事，探讨AI时代的选择与放弃",
                "recommended_angle": "从有限性视角解读AI焦虑",
                "priority": "P0",
            },
            {
                "title": "超级个体如何打造一人企业实现自由职业转型",
                "platform": "xiaohongshu",
                "heat_level": "爆发",
                "tags": ["超级个体", "创业", "自由职业"],
                "description": "探讨如何在AI时代构建一人企业，从打工人向超级个体转型",
                "recommended_angle": "超级个体的生存法则",
                "priority": "P1",
            },
        ]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        logger.info("JSON模板已生成", path=output_path)
