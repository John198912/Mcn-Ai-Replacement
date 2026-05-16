"""Phase 1 模块单元测试."""

import os
import json
import csv
import tempfile
from pathlib import Path

import pytest

from src.adapters.manual_hotspot_importer import ManualHotspotImporter
from src.utils.data_quality_validator import DataQualityValidator
from src.knowledge.backup_manager import BackupManager
from src.knowledge.two_layer_manager import TwoLayerKnowledgeManager


class TestDataQualityValidator:
    """数据质量验证器测试."""

    @pytest.fixture
    def validator(self):
        return DataQualityValidator()

    def test_valid_hotspot(self, validator):
        """测试有效的热点数据."""
        hotspot = type("Hotspot", (), {
            "title": "AI大模型如何改变内容创作",
            "platform": "douyin",
            "heat_level": "上升",
            "tags": ["AI", "内容创作"],
        })
        is_valid, reason = validator.validate_hotspot(hotspot)
        assert is_valid, reason

    def test_empty_title(self, validator):
        """测试空标题."""
        hotspot = type("Hotspot", (), {
            "title": "",
            "platform": "douyin",
            "heat_level": "上升",
        })
        is_valid, reason = validator.validate_hotspot(hotspot)
        assert not is_valid
        assert "标题" in reason

    def test_short_title(self, validator):
        """测试过短的标题."""
        hotspot = type("Hotspot", (), {
            "title": "AB",
            "platform": "douyin",
            "heat_level": "上升",
        })
        is_valid, reason = validator.validate_hotspot(hotspot)
        assert not is_valid

    def test_invalid_platform(self, validator):
        """测试无效平台."""
        hotspot = type("Hotspot", (), {
            "title": "有效标题内容",
            "platform": "invalid_platform",
            "heat_level": "上升",
        })
        is_valid, reason = validator.validate_hotspot(hotspot)
        assert not is_valid
        assert "平台" in reason

    def test_invalid_heat_level(self, validator):
        """测试无效热度等级."""
        hotspot = type("Hotspot", (), {
            "title": "有效标题内容",
            "platform": "douyin",
            "heat_level": "超级热",
        })
        is_valid, reason = validator.validate_hotspot(hotspot)
        assert not is_valid

    def test_deduplicate(self, validator):
        """测试去重."""
        hotspots = [
            type("H", (), {"title": "同一个标题", "platform": "douyin"}),
            type("H", (), {"title": "同一个标题", "platform": "bilibili"}),
            type("H", (), {"title": "不同的标题", "platform": "douyin"}),
        ]
        unique, removed = validator.deduplicate(hotspots)
        assert len(unique) == 2
        assert removed == 1

    def test_filter_low_quality(self, validator):
        """测试过滤低质量数据."""
        hotspots = [
            type("H", (), {"title": "有效标题内容足够长", "platform": "douyin", "heat_level": "上升"}),
            type("H", (), {"title": "AB", "platform": "douyin", "heat_level": "上升"}),
        ]
        quality, filtered = validator.filter_low_quality(hotspots)
        assert len(quality) == 1
        assert len(filtered) == 1

    def test_validate_batch_report(self, validator):
        """测试批量验证报告."""
        hotspots = [
            type("H", (), {"title": f"热点{i}", "platform": "douyin", "heat_level": "上升"})
            for i in range(10)
        ]
        report = validator.validate_batch(hotspots)
        assert report["total_input"] == 10
        assert "pass_rate" in report


class TestManualHotspotImporter:
    """手动导入器测试."""

    @pytest.fixture
    def importer(self):
        return ManualHotspotImporter()

    def test_import_from_json(self, importer):
        """测试JSON导入."""
        json_data = [
            {
                "title": "AI焦虑",
                "platform": "douyin",
                "heat_level": "上升",
                "tags": ["AI", "超级个体"],
                "description": "探讨AI时代的焦虑",
                "priority": "P0",
            }
        ]
        file_path = "/tmp/test_hotspots.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False)

        hotspots = importer.import_from_json(file_path)
        assert len(hotspots) == 1
        assert hotspots[0]["title"] == "AI焦虑"
        assert hotspots[0]["platform"] == "douyin"
        assert "AI" in hotspots[0]["tags"]

    def test_import_single_object_json(self, importer):
        """测试单个对象的JSON导入."""
        json_data = {"title": "单条热点", "platform": "bilibili"}
        file_path = "/tmp/test_single_hotspot.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f)

        hotspots = importer.import_from_json(file_path)
        assert len(hotspots) == 1
        assert hotspots[0]["title"] == "单条热点"

    def test_import_from_csv(self, importer):
        """测试CSV导入."""
        file_path = "/tmp/test_hotspots.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["标题", "平台", "热度", "标签", "描述"])
            writer.writerow(["AI焦虑", "douyin", "上升", "AI,超级个体", "探讨AI时代的焦虑"])

        hotspots = importer.import_from_csv(file_path)
        assert len(hotspots) == 1
        assert hotspots[0]["title"] == "AI焦虑"
        assert len(hotspots[0]["tags"]) == 2

    def test_generate_template_csv(self, importer):
        """测试CSV模板生成."""
        file_path = "/tmp/template.csv"
        importer.generate_template_csv(file_path)
        assert Path(file_path).exists()
        content = Path(file_path).read_text()
        assert "标题" in content
        assert "平台" in content

    def test_generate_template_json(self, importer):
        """测试JSON模板生成."""
        file_path = "/tmp/template.json"
        importer.generate_template_json(file_path)
        assert Path(file_path).exists()
        data = json.loads(Path(file_path).read_text())
        assert isinstance(data, list)
        assert len(data) > 0

    def test_nonexistent_file(self, importer):
        """测试不存在的文件."""
        with pytest.raises(FileNotFoundError):
            importer.import_from_file("/tmp/nonexistent_file.csv")

    def test_unsupported_format(self, importer):
        """测试不支持的格式."""
        file_path = "/tmp/test.txt"
        Path(file_path).write_text("hello")
        with pytest.raises(ValueError, match="不支持"):
            importer.import_from_file(file_path)


class TestTwoLayerKnowledgeManager:
    """知识库管理器测试."""

    @pytest.fixture
    def manager(self):
        return TwoLayerKnowledgeManager()

    def test_save_and_read_hotspot(self, manager):
        """测试保存和读取热点."""
        hotspot = {
            "title": "测试热点",
            "platform": "douyin",
            "heat_level": "上升",
            "tags": ["AI", "测试"],
            "priority": "P0",
            "recommended_angle": "从有限性视角",
        }
        path = manager.save_hotspot_to_markdown(hotspot)
        assert Path(path).exists()

        content = Path(path).read_text()
        assert "测试热点" in content
        assert "douyin" in content

    def test_save_and_read_script(self, manager):
        """测试保存和读取脚本."""
        script = {
            "topic": "AI焦虑",
            "hook": "测试Hook",
            "pain_point": "测试痛点",
            "core_content": "测试核心内容",
            "insight": "测试启发",
            "cta": "测试CTA",
        }
        path = manager.save_script_to_markdown(script)
        assert Path(path).exists()

        content = Path(path).read_text()
        assert "AI焦虑" in content
        assert "测试Hook" in content

    def test_list_files(self, manager):
        """测试列出文件."""
        manager.save_hotspot_to_markdown({
            "title": "列表演示", "platform": "douyin", "tags": []
        })
        files = manager.list_hotspot_files()
        assert len(files) > 0

    def test_nonexistent_file(self, manager):
        """测试读取不存在的文件."""
        result = manager.read_markdown("nonexistent.md", "hotspots")
        assert result is None


class TestBackupManager:
    """备份管理器测试."""

    @pytest.fixture
    def backup_mgr(self):
        return BackupManager(backup_dir="/tmp/mcn_test_backups")

    def test_create_and_verify_backup(self, backup_mgr):
        """测试创建和验证备份."""
        backup_id = backup_mgr.create_backup("test_backup")
        assert backup_id == "test_backup"

        is_valid = backup_mgr.verify_backup("test_backup")
        assert is_valid

    def test_list_backups(self, backup_mgr):
        """测试列出备份."""
        backup_mgr.create_backup("test_list")
        backups = backup_mgr.list_backups()
        assert len(backups) > 0

    def test_invalid_backup(self, backup_mgr):
        """测试无效备份."""
        is_valid = backup_mgr.verify_backup("nonexistent_backup")
        assert not is_valid

    def test_clean_old_backups(self, backup_mgr):
        """测试清理旧备份."""
        for i in range(15):
            backup_mgr.create_backup(f"old_backup_{i}")
        backup_mgr.clean_old_backups(keep_last=10)
        backups = backup_mgr.list_backups()
        # 最多保留10个（加上之前创建的test_backup和test_list）
        assert len(backups) <= 12
