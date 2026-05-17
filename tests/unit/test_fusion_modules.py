"""融合模块测试 — RulesMonitor, CreatorPipeline, TrendAnalyzer."""

import json
import pytest
from pathlib import Path

from src.analyzers.rules_monitor import RulesMonitor
from src.analyzers.creator_pipeline import CreatorPipeline
from src.analyzers.trend_analyzer import TrendAnalyzer


# ==================== RulesMonitor ====================

class TestRulesMonitor:
    @pytest.fixture
    def monitor(self, tmp_path):
        rules_file = tmp_path / "rules.json"
        return RulesMonitor(str(rules_file))

    def test_init_default_rules(self, monitor):
        assert "douyin" in monitor.rules
        assert "xiaohongshu" in monitor.rules
        assert "bilibili" in monitor.rules

    def test_parse_changes_table(self, monitor):
        content = """## 变动清单
| 平台 | 变动类型 | 变动内容摘要 | 发现来源 | 可信度 | 影响范围 | 对我的影响 |
|------|---------|------------|---------|--------|---------|-----------|
| 抖音 | 算法调整 | 推荐机制调整，知识类内容权重上升 | 官方公告 | 确认 | 全量 | 大 |
| 小红书 | 社区规则 | 商业内容需标注广告 | 官方公告 | 高可信 | 部分赛道 | 中 |
"""
        changes = monitor._parse_changes_table(content)
        assert len(changes) == 2
        assert changes[0]["platform"] == "douyin"
        assert "推荐机制" in changes[0]["content"]

    def test_import_report(self, monitor, tmp_path):
        report = tmp_path / "rules_report.md"
        report.write_text("""## 变动清单
| 平台 | 变动类型 | 变动内容摘要 | 发现来源 | 可信度 | 影响范围 | 对我的影响 |
|------|---------|------------|---------|--------|---------|-----------|
| 抖音 | 算法调整 | 推荐机制变化 | 官方 | 确认 | 全量 | 大 |
""", encoding="utf-8")
        stats = monitor.import_report(str(report))
        assert stats.get("douyin", 0) > 0

    def test_check_content_finds_restricted(self, monitor):
        monitor.rules["douyin"]["content_policies"] = [{
            "content": "禁止使用「最」「第一」等绝对化用语",
            "date": "2026-05-01",
        }]
        risks = monitor.check_content(
            {"hook": "这是最好的AI工具"},
            "douyin"
        )
        assert len(risks) > 0

    def test_check_content_no_issue(self, monitor):
        monitor.rules["douyin"]["content_policies"] = []
        risks = monitor.check_content(
            {"hook": "我们来看看AI工具的选择"},
            "douyin"
        )
        assert len(risks) == 0

    def test_get_rule_context(self, monitor):
        monitor.rules["douyin"]["last_updated"] = "2026-05-17"
        monitor.rules["douyin"]["overall_stance"] = "tightening"
        monitor.rules["douyin"]["content_policies"] = [{
            "date": "2026-05-15", "type": "社区规则",
            "content": "禁止绝对化用语",
        }]
        ctx = monitor.get_rule_context("douyin")
        assert "收紧" in ctx
        assert "绝对化" in ctx

    def test_status(self, monitor):
        monitor.rules["douyin"]["overall_stance"] = "tightening"
        status = monitor.status("douyin")
        assert len(status) == 1
        assert status[0]["stance"] == "tightening"

    def test_resolve_platform(self, monitor):
        assert monitor._resolve_platform("抖音") == "douyin"
        assert monitor._resolve_platform("小红书平台") == "xiaohongshu"
        assert monitor._resolve_platform("B站视频") == "bilibili"
        assert monitor._resolve_platform("未知平台") == "douyin"

    def test_extract_restricted_keywords_quoted(self, monitor):
        kw = monitor._extract_restricted_keywords("禁止使用「最」「第一」「顶级」")
        assert "最" in kw
        assert "第一" in kw

    def test_extract_restricted_keywords_dunhao(self, monitor):
        kw = monitor._extract_restricted_keywords("限制话题：AI取代、裁员、失业")
        # 顿号分隔，第一个可能包含前缀
        assert any("AI取代" in k for k in kw)
        assert "裁员" in kw


# ==================== CreatorPipeline ====================

class TestCreatorPipeline:
    @pytest.fixture
    def pipeline(self, tmp_path):
        data_file = tmp_path / "creators.json"
        return CreatorPipeline(str(data_file))

    def test_init_structure(self, pipeline):
        assert "creators" in pipeline.data
        assert "viral_patterns" in pipeline.data
        assert "differentiation" in pipeline.data

    def test_parse_discovery_table(self, pipeline):
        content = """## 创作者发现
| 平台 | 账号名称 | 粉丝数 | 层级 | 内容定位 | 更新频率 | 近期代表作 | 内容风格 | 对标价值 |
|------|---------|--------|------|---------|---------|-----------|---------|---------|
| 抖音 | AI小明 | 50万 | 学习标杆 | AI工具教程 | 日更 | 《10个AI工具》 | 轻松幽默 | 标题技巧 |
| 小红书 | 超级个体小王 | 5万 | 成长对标 | 一人企业 | 3天1更 | 《我的AI工作流》 | 深度干货 | 内容结构 |
"""
        creators = pipeline._parse_discovery_table(content)
        assert len(creators) == 2
        assert creators[0]["account_name"] == "AI小明"
        assert creators[0]["tier"] == "学习标杆"

    def test_upsert_creator(self, pipeline):
        c = {"account_name": "AI小明", "platform": "douyin", "followers": "50万"}
        pipeline._upsert_creator(c)
        assert len(pipeline.data["creators"]) == 1

        # 更新已有
        c["followers"] = "80万"
        pipeline._upsert_creator(c)
        assert pipeline.data["creators"][0]["followers"] == "80万"
        assert len(pipeline.data["creators"]) == 1

    def test_list_creators_by_tier(self, pipeline):
        pipeline.data["creators"] = [
            {"account_name": "A", "tier": "学习标杆"},
            {"account_name": "B", "tier": "成长对标"},
        ]
        result = pipeline.list_creators(tier="学习标杆")
        assert len(result) == 1
        assert result[0]["account_name"] == "A"

    def test_get_differentiation_signals(self, pipeline):
        pipeline.data["differentiation"] = {
            "content_whitespace": ["AI+哲学交叉话题"],
            "unique_strengths": ["前PM视角"],
        }
        pipeline.data["viral_patterns"] = [
            {"type": "hook_formula", "content": "反常识开头+数据支撑"},
        ]
        signals = pipeline.get_differentiation_signals()
        assert "AI+哲学" in str(signals["content_gaps"])
        assert len(signals["viral_patterns"]) > 0

    def test_get_script_references(self, pipeline):
        pipeline.data["creators"] = [{
            "account_name": "AI小明",
            "positioning": "AI工具教程博主",
            "learnable": "标题技巧和数据可视化",
            "style": "轻松幽默",
            "top_content": "《10个AI工具提升效率》",
        }]
        refs = pipeline.get_script_references("AI工具")
        assert len(refs) > 0

    def test_get_script_references_no_match(self, pipeline):
        pipeline.data["creators"] = [{
            "account_name": "AI小明",
            "positioning": "AI工具",
            "learnable": "标题技巧",
        }]
        refs = pipeline.get_script_references("养花技巧")
        assert len(refs) == 0

    def test_import_report(self, pipeline, tmp_path):
        report = tmp_path / "creator_report.md"
        report.write_text("""## 创作者发现
| 平台 | 账号名称 | 粉丝数 | 层级 | 内容定位 | 更新频率 | 近期代表作 | 内容风格 | 对标价值 |
|------|---------|--------|------|---------|---------|-----------|---------|---------|
| 抖音 | AI达人 | 100万 | 学习标杆 | AI教程 | 日更 | 《AI改变工作》 | 干货 | 选题角度 |
""", encoding="utf-8")
        stats = pipeline.import_report(str(report))
        assert stats["discovered"] >= 1


# ==================== TrendAnalyzer ====================

class TestTrendAnalyzer:
    @pytest.fixture
    def analyzer(self, tmp_path):
        data_file = tmp_path / "trends.json"
        return TrendAnalyzer(str(data_file))

    def test_init_structure(self, analyzer):
        assert "reports" in analyzer.data
        assert "sub_track_weights" in analyzer.data
        assert "scoring_params" in analyzer.data

    def test_parse_sub_track_trends(self, analyzer):
        content = """
AI工具教程类内容持续增长，成为赛道主力
超级个体方法论处于爆发期，各大平台都在扶持
AI副业赚钱类内容已趋于饱和，同质化严重
"""
        weights = analyzer._parse_sub_track_trends(content)
        assert weights.get("AI工具教程", 0) >= 0.8
        assert weights.get("超级个体", 0) >= 0.8
        assert weights.get("AI副业", 0) <= 0.3

    def test_parse_audience_migration(self, analyzer):
        content = """
AI焦虑情绪持续加剧，受众对未来的不确定感上升
同时寻找意义和精神自由的诉求明显增加
副业赚钱的实际需求趋于理性
"""
        trends = analyzer._parse_audience_migration(content)
        assert trends["anxiety_level"] == "rising"
        assert trends["meaning_seeking"] == "rising"

    def test_derive_scoring_params(self, analyzer):
        sub_tracks = {"AI工具教程": 0.9, "AI副业": 0.3, "认知升级": 0.6}
        audience = {"anxiety_level": "rising"}
        params = analyzer._derive_scoring_params(sub_tracks, audience)
        assert "AI工具教程" in params["boost_topics"]
        assert "AI副业" in params["penalize_topics"]

    def test_get_topic_weight(self, analyzer):
        analyzer.data["sub_track_weights"] = {"AI工具教程": 0.9}
        analyzer.data["scoring_params"] = {"boost_topics": ["AI工具教程"], "penalize_topics": []}
        weight = analyzer.get_topic_weight(["AI工具教程"])
        assert weight > 1.0

    def test_get_topic_weight_penalized(self, analyzer):
        analyzer.data["sub_track_weights"] = {"AI副业": 0.3}
        analyzer.data["scoring_params"] = {"boost_topics": [], "penalize_topics": ["AI副业"]}
        weight = analyzer.get_topic_weight(["AI副业"])
        assert weight < 1.0

    def test_generate_strategy(self, analyzer):
        sub_tracks = {"AI工具教程": 0.9, "AI副业": 0.3}
        platform = {"douyin": {"platform": "抖音", "short_video_weight": 0.8}}
        audience = {"anxiety_level": "rising", "meaning_seeking": "rising"}
        competition = {"saturation_signals": True}

        strategy = analyzer._generate_strategy(sub_tracks, platform, audience, competition)
        assert len(strategy["strategies"]) > 0
        assert "AI工具教程" in strategy["hot_tracks"]
        assert "AI副业" in strategy["cold_tracks"]

    def test_generate_monthly_strategy_empty(self, analyzer):
        result = analyzer.generate_monthly_strategy()
        assert "error" in result

    def test_import_report(self, analyzer, tmp_path):
        report = tmp_path / "trend_report.md"
        report.write_text("""# 趋势报告
AI工具教程持续增长，AI副业趋于饱和。
抖音知识类内容扶持力度加大。
受众焦虑上升，寻求意义的需求增加。
""", encoding="utf-8")
        result = analyzer.import_report(str(report))
        assert len(result["sub_tracks"]) > 0
        assert len(result["strategy"]["strategies"]) > 0
