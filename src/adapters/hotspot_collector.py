"""热点采集协调器 - 协调多种数据源，提供统一接口."""

from typing import List, Dict
from ..core.logger import get_logger
from ..utils.data_quality_validator import DataQualityValidator
from .hermes_hotspot_adapter import HermesHotspotAdapter
from .manual_hotspot_importer import ManualHotspotImporter

logger = get_logger(__name__)


class HotspotCollector:
    """热点采集协调器.

    协调三种数据源（按优先级）：
    1. Hermes报告（推荐）——真正的"引用Hermes已有能力"
    2. 手动导入（降级）——CSV/JSON/Markdown
    3. 提示用户（兜底）——引导用户手动处理

    Usage:
        collector = HotspotCollector()
        hotspots = await collector.collect(use_hermes=True, days=7)
    """

    def __init__(self):
        self.hermes_adapter = HermesHotspotAdapter()
        self.manual_importer = ManualHotspotImporter()
        self.quality_validator = DataQualityValidator()

    async def collect(
        self,
        use_hermes: bool = True,
        manual_file: str = None,
        days: int = 7,
        validate: bool = True,
    ) -> List[Dict]:
        """采集热点（多源协调）.

        Args:
            use_hermes: 是否尝试使用Hermes报告
            manual_file: 手动导入文件路径
            days: 读取最近N天的Hermes报告
            validate: 是否进行质量验证

        Returns:
            经过验证的热点列表
        """
        hotspots = []

        # 方案1：读取Hermes报告（推荐）
        if use_hermes and self.hermes_adapter.available:
            logger.info("尝试从Hermes报告加载热点")
            hermes_hotspots = await self.hermes_adapter.fetch_latest_hotspots(days=days)

            if hermes_hotspots:
                logger.info(f"✅ Hermes报告加载成功", count=len(hermes_hotspots))
                hotspots = hermes_hotspots
            else:
                logger.warning("Hermes报告为空，尝试其他方案")

        # 方案2：手动导入（降级）
        if not hotspots and manual_file:
            logger.info("尝试手动导入", file=manual_file)
            try:
                imported = self.manual_importer.import_from_file(manual_file)
                if imported:
                    logger.info(f"✅ 手动导入成功", count=len(imported))
                    hotspots = imported
            except Exception as e:
                logger.error("手动导入失败", error=str(e))

        # 方案3：提示用户
        if not hotspots:
            logger.warning("所有数据源均无数据")
            self._prompt_user_for_data()
            return []

        # 质量验证
        if validate and hotspots:
            quality_report = self.quality_validator.validate_batch(hotspots)
            logger.info(
                "质量验证完成",
                input_count=quality_report["total_input"],
                output_count=quality_report["final_count"],
                pass_rate=quality_report["pass_rate"],
            )
            # 返回通过验证的数据
            hotspots, _ = self.quality_validator.filter_low_quality(hotspots)

        return hotspots

    def _prompt_user_for_data(self):
        """提示用户提供数据."""
        print("\n" + "=" * 60)
        print("⚠️  无法获取热点数据")
        print("=" * 60)
        print("\n可选方案：")
        print("1. 等待Hermes热点采集系统运行（每日08:00）")
        print("2. 手动导入数据文件（CSV/JSON/Markdown）")
        print("3. 生成导入模板")
        print("\n使用以下命令：")
        print("  # 手动导入")
        print("  python scripts/run_workflow.py soul-create --manual-file hotspots.csv")
        print()
        print("  # 生成模板")
        print("  python scripts/run_workflow.py generate-template")

    def quick_import(self, file_path: str) -> List[Dict]:
        """快速导入（同步方法，用于简单场景）.

        Args:
            file_path: 数据文件路径

        Returns:
            热点列表
        """
        try:
            hotspots = self.manual_importer.import_from_file(file_path)
            if hotspots:
                hotspots, _ = self.quality_validator.filter_low_quality(hotspots)
            return hotspots
        except Exception as e:
            logger.error("快速导入失败", error=str(e))
            return []
