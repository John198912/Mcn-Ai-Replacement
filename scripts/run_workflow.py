#!/usr/bin/env python3
"""Command-line interface for running workflows."""

import asyncio
import os
import sys
from pathlib import Path

import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, init_database, setup_logging
from src.workflows import (
    run_hot_topic_workflow,
    run_content_creation_workflow,
    run_creator_analysis_workflow,
)
from src.adapters import HotspotCollector, ManualHotspotImporter
from src.knowledge import TwoLayerKnowledgeManager, BackupManager
from src.scheduler import MCNScheduler
from src.integrations import HermesTaskBridge
from src.skills import (
    SOULScriptWriter,
    SOULScriptWriterInput,
    SOULHotTopicMatcher,
    SOULHotTopicInput,
)


@click.group()
def cli():
    """MCN AI Replacement System - Workflow Runner.

    Execute automated workflows for content creation assistance.
    """
    pass


@cli.command()
@click.option(
    "--keywords",
    "-k",
    multiple=True,
    help="Keyword categories to search (e.g., ai_keywords, personal_brand_keywords)",
)
def hot_topic(keywords):
    """Run hot topic collection workflow.

    Collects hot topics, scores them based on creator profile,
    and stores results to database.

    Example:
        python scripts/run_workflow.py hot-topic
        python scripts/run_workflow.py hot-topic -k ai_keywords -k job_keywords
    """
    click.echo("🔥 Starting Hot Topic Workflow...")
    click.echo()

    # Setup
    setup_logging(log_level="INFO")
    config = get_config()
    init_database(config.database_url)

    # Convert keywords tuple to list
    keyword_list = list(keywords) if keywords else None

    # Run workflow
    result = asyncio.run(run_hot_topic_workflow(keywords=keyword_list))

    # Display results
    if result.get("success"):
        click.echo("✅ Workflow completed successfully!")
        click.echo()
        click.echo(f"📊 Statistics:")
        click.echo(f"   • Topics collected: {result.get('collected', 0)}")
        click.echo(f"   • Topics ranked: {result.get('ranked', 0)}")
        click.echo(f"   • Topics stored: {result.get('stored', 0)}")
        click.echo()

        top_topics = result.get("top_topics", [])
        if top_topics:
            click.echo(f"🏆 Top {len(top_topics)} Recommendations:")
            for i, topic in enumerate(top_topics, 1):
                click.echo(f"\n   {i}. {topic.get('topic', '')}")
                click.echo(f"      Score: {topic.get('total_score', 0):.2f}/10")
                click.echo(f"      Platform: {topic.get('platform', '')}")
                click.echo(f"      Window: {topic.get('publish_window', '')}")
    else:
        click.echo(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


@cli.command()
@click.option("--topic", "-t", required=True, help="Content topic")
@click.option("--angle", "-a", required=True, help="Content angle")
@click.option(
    "--platform",
    "-p",
    default="douyin",
    type=click.Choice(["douyin", "xiaohongshu", "bilibili", "weibo", "zhihu"]),
    help="Target platform",
)
@click.option(
    "--duration", "-d", default=180, type=int, help="Target duration in seconds"
)
def create_content(topic, angle, platform, duration):
    """Run content creation workflow.

    Generates script, optimizes titles, and performs risk assessment.

    Example:
        python scripts/run_workflow.py create-content -t "AI工具" -a "从PM视角"
        python scripts/run_workflow.py create-content -t "职场焦虑" -a "35岁危机" -p xiaohongshu -d 120
    """
    click.echo("✍️  Starting Content Creation Workflow...")
    click.echo()
    click.echo(f"📝 Topic: {topic}")
    click.echo(f"🎯 Angle: {angle}")
    click.echo(f"📱 Platform: {platform}")
    click.echo(f"⏱️  Duration: {duration}s")
    click.echo()

    # Setup
    setup_logging(log_level="INFO")

    # Run workflow
    result = asyncio.run(
        run_content_creation_workflow(
            topic=topic, angle=angle, platform=platform, duration=duration
        )
    )

    # Display results
    if result.get("success"):
        click.echo("✅ Workflow completed successfully!")
        click.echo()

        # Script info
        script = result.get("script", {})
        click.echo("📄 Script Generated:")
        click.echo(f"   • Title: {script.get('title', '')}")
        click.echo(f"   • Word count: {script.get('word_count', 0)}")
        click.echo(f"   • Estimated duration: {script.get('estimated_duration', 0)}s")
        click.echo()

        # Titles
        titles = result.get("titles", [])
        if titles:
            click.echo(f"🏷️  Top {len(titles)} Title Candidates:")
            for i, title_info in enumerate(titles, 1):
                click.echo(
                    f"   {i}. {title_info.get('title', '')} (CTR: {title_info.get('estimated_ctr', 0):.1f})"
                )
            click.echo()

        # Risk assessment
        risk = result.get("risk_assessment", {})
        risk_level = risk.get("risk_level", "未知")
        safe = risk.get("safe_to_publish", False)

        risk_emoji = "🟢" if safe else "🔴" if risk_level == "高风险" else "🟡"
        click.echo(f"{risk_emoji} Risk Assessment: {risk_level}")

        if not safe:
            click.echo("   ⚠️  Not safe to publish - review required")
            suggestions = risk.get("suggestions", [])
            if suggestions:
                click.echo("   Suggestions:")
                for suggestion in suggestions[:3]:
                    click.echo(f"      • {suggestion}")
        else:
            click.echo("   ✅ Safe to publish")

        click.echo()
        click.echo(
            f"🚀 Ready to publish: {'Yes' if result.get('ready_to_publish') else 'No'}"
        )

    else:
        click.echo(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


@cli.command()
@click.argument("creators_file", type=click.Path(exists=True))
def creator_analysis(creators_file):
    """Run creator analysis workflow.

    Profiles creators and analyzes their viral content.

    Expects a JSON file with creator data.

    Example:
        python scripts/run_workflow.py creator-analysis creators.json
    """
    import json

    click.echo("👥 Starting Creator Analysis Workflow...")
    click.echo()

    # Setup
    setup_logging(log_level="INFO")
    config = get_config()
    init_database(config.database_url)

    # Load creators data
    try:
        with open(creators_file, "r", encoding="utf-8") as f:
            creators_data = json.load(f)

        if not isinstance(creators_data, list):
            creators_data = [creators_data]

        click.echo(f"📂 Loaded {len(creators_data)} creator(s) from {creators_file}")
        click.echo()

    except Exception as e:
        click.echo(f"❌ Failed to load file: {e}")
        sys.exit(1)

    # Run workflow
    result = asyncio.run(run_creator_analysis_workflow(creators_data))

    # Display results
    if result.get("success"):
        click.echo("✅ Workflow completed successfully!")
        click.echo()
        click.echo(f"📊 Statistics:")
        click.echo(f"   • Creators processed: {result.get('total_processed', 0)}")
        click.echo(f"   • Creators profiled: {result.get('total_profiled', 0)}")
        click.echo(
            f"   • Content analyzed: {len(result.get('analyzed_content', []))}"
        )
        click.echo()

        profiled = result.get("profiled_creators", [])
        if profiled:
            click.echo(f"👤 Profiled Creators:")
            for creator in profiled:
                click.echo(f"   • {creator.get('account_name', '')} ({creator.get('platform', '')})")
                click.echo(f"     Followers: {creator.get('followers', 0):,}")

    else:
        click.echo(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


@cli.command()
def list_workflows():
    """List all available workflows."""
    click.echo("📋 Available Workflows:")
    click.echo()
    click.echo("1. hot-topic")
    click.echo("   Collect and score hot topics")
    click.echo()
    click.echo("2. create-content")
    click.echo("   Generate script, titles, and risk assessment")
    click.echo()
    click.echo("3. creator-analysis")
    click.echo("   Profile creators and analyze viral content")
    click.echo()
    click.echo("Use --help with any command for more details.")


@cli.command()
@click.option("--use-hermes", is_flag=True, default=True, help="使用Hermes热点数据")
@click.option("--manual-file", type=str, help="手动导入文件路径")
@click.option("--days", default=7, help="读取最近N天的热点")
@click.option("--no-validate", is_flag=True, help="跳过数据质量验证")
def collect_hotspots(use_hermes, manual_file, days, no_validate):
    """采集热点数据（Hermes报告 + 手动导入）.

    示例：
        python scripts/run_workflow.py collect-hotspots
        python scripts/run_workflow.py collect-hotspots --manual-file hotspots.csv
    """
    click.echo("🔍 开始采集热点...")
    click.echo()

    collector = HotspotCollector()
    hotspots = asyncio.run(
        collector.collect(
            use_hermes=use_hermes,
            manual_file=manual_file,
            days=days,
            validate=not no_validate,
        )
    )

    if hotspots:
        click.echo(f"✅ 采集完成，共 {len(hotspots)} 个热点")
        click.echo()
        click.echo("📊 Top 10 热点：")
        for i, h in enumerate(hotspots[:10], 1):
            click.echo(f"  {i}. {h.get('title', '')} ({h.get('platform', '')})")
    else:
        click.echo("❌ 未采集到热点数据")
        click.echo("试试：python scripts/run_workflow.py generate-template")


@cli.command()
@click.option("--strategy", default="local_wins",
              type=click.Choice(["local_wins", "remote_wins", "manual"]),
              help="冲突解决策略")
@click.option("--incremental/--full", default=True, help="增量同步 / 全量同步")
def sync_github(strategy, incremental):
    """同步本地知识库到GitHub.

    示例：
        python scripts/run_workflow.py sync-github
        python scripts/run_workflow.py sync-github --strategy remote_wins
        python scripts/run_workflow.py sync-github --full
    """
    click.echo("🔄 同步知识库到GitHub...")
    manager = TwoLayerKnowledgeManager()
    asyncio.run(manager.sync_to_github(strategy=strategy, incremental=incremental))
    click.echo("✅ GitHub同步完成")


@cli.command()
@click.option("--keep", default=10, help="保留最近N个备份")
def backup(keep):
    """备份知识库（数据库 + Markdown + 配置）.

    示例：
        python scripts/run_workflow.py backup
        python scripts/run_workflow.py backup --keep 20
    """
    click.echo("💾 创建备份...")
    mgr = BackupManager()
    backup_id = mgr.create_backup()
    click.echo(f"✅ 备份完成: {backup_id}")

    if keep > 0:
        mgr.clean_old_backups(keep_last=keep)

    # 列出所有备份
    backups = mgr.list_backups()
    click.echo(f"\n📂 当前共 {len(backups)} 个备份")
    for b in backups[:5]:
        click.echo(f"  • {b['backup_id']} ({b.get('size_mb', '?')}MB)")


@cli.command()
@click.argument("backup_id")
def restore(backup_id):
    """从备份恢复.

    示例：
        python scripts/run_workflow.py restore backup_20260517_100000
    """
    click.echo(f"🔄 从备份恢复: {backup_id}")
    mgr = BackupManager()

    if not mgr.verify_backup(backup_id):
        click.echo("❌ 备份不完整，无法恢复")
        return

    if mgr.restore_backup(backup_id):
        click.echo("✅ 恢复完成")
    else:
        click.echo("❌ 恢复失败")


@cli.command()
def list_backups():
    """列出所有备份.

    示例：
        python scripts/run_workflow.py list-backups
    """
    mgr = BackupManager()
    backups = mgr.list_backups()

    if backups:
        click.echo(f"📂 共 {len(backups)} 个备份：\n")
        for b in backups:
            click.echo(f"  • {b['backup_id']}")
            click.echo(f"    时间：{b.get('created_at', '?')}")
            click.echo(f"    大小：{b.get('size_mb', '?')}MB")
            click.echo(f"    文件：{b.get('files_count', '?')}")
            click.echo()
    else:
        click.echo("📂 暂无备份")


@cli.command()
def start_scheduler():
    """启动定时任务调度器.

    示例：
        python scripts/run_workflow.py start-scheduler
    """
    scheduler = MCNScheduler()

    # 设置回调
    def collect_hotspots_job():
        collector = HotspotCollector()
        hotspots = asyncio.run(collector.collect(use_hermes=True, days=7))
        if hotspots:
            manager = TwoLayerKnowledgeManager()
            for h in hotspots:
                manager.save_hotspot_to_markdown(h)

    def backup_job():
        mgr = BackupManager()
        backup_id = mgr.create_backup()
        mgr.clean_old_backups(keep_last=10)

    def sync_job():
        manager = TwoLayerKnowledgeManager()
        asyncio.run(manager.sync_to_github(incremental=True))

    scheduler.set_hotspot_callback(collect_hotspots_job)
    scheduler.set_backup_callback(backup_job)
    scheduler.set_sync_callback(sync_job)

    scheduler.start()


@cli.command()
def generate_launchd():
    """生成 macOS launchd 配置.

    示例：
        python scripts/run_workflow.py generate-launchd > ~/Library/LaunchAgents/com.mcn.scheduler.plist
        launchctl load ~/Library/LaunchAgents/com.mcn.scheduler.plist
    """
    plist = MCNScheduler.get_launchd_plist()
    click.echo(plist)


@cli.command()
@click.option("--host", default="127.0.0.1", help="监听地址（默认仅本地）")
@click.option("--port", default=8000, help="监听端口")
def start_api(host, port):
    """启动HTTP API（用于Hermes调用）.

    示例：
        # 本地运行（无需认证）
        python scripts/run_workflow.py start-api

        # 远程访问（需要设置 MCN_API_KEY 环境变量）
        python scripts/run_workflow.py start-api --host 0.0.0.0
    """
    if host != "127.0.0.1" and not os.getenv("MCN_API_KEY"):
        click.echo("❌ 远程访问必须设置 MCN_API_KEY 环境变量")
        return

    from fastapi import FastAPI, HTTPException, Request
    import uvicorn

    app = FastAPI(title="MCN AI Replacement API")
    bridge = HermesTaskBridge()

    # 注册工作流
    bridge.register_workflow("hot_topic", run_hot_topic_workflow)
    bridge.register_workflow("create_content", run_content_creation_workflow)
    bridge.register_workflow("creator_analysis", run_creator_analysis_workflow)

    @app.post("/tasks")
    async def create_task(request: Request, task: dict):
        if host != "127.0.0.1":
            api_key = request.headers.get("X-API-Key")
            if api_key != os.getenv("MCN_API_KEY"):
                raise HTTPException(401, "Invalid API key")
        task_id = await bridge.receive_task(task)
        return {"task_id": task_id, "status": "accepted"}

    @app.get("/tasks/{task_id}")
    async def get_task_status(task_id: str):
        return bridge.get_task_status(task_id)

    @app.get("/tasks")
    async def list_tasks(status: str = None):
        return bridge.list_tasks(status_filter=status)

    click.echo(f"🚀 API服务已启动: http://{host}:{port}")
    if host == "127.0.0.1":
        click.echo("✅ 本地运行，无需API认证")
    else:
        click.echo("🔒 远程模式，需要API密钥")

    uvicorn.run(app, host=host, port=port, log_level="info")


@cli.command()
def generate_template():
    """生成数据导入模板.

    示例：
        python scripts/run_workflow.py generate-template
    """
    importer = ManualHotspotImporter()
    importer.generate_template_csv("hotspots_template.csv")
    importer.generate_template_json("hotspots_template.json")
    click.echo("✅ 模板已生成:")
    click.echo("  - hotspots_template.csv")
    click.echo("  - hotspots_template.json")
    click.echo()
    click.echo("填写模板后使用以下命令导入：")
    click.echo("  python scripts/run_workflow.py collect-hotspots --manual-file hotspots_template.csv")


@cli.command()
@click.option("--topic", "-t", required=True, help="选题")
@click.option("--angle", "-a", required=True, help="切入角度")
@click.option("--platform", "-p", default="douyin",
              type=click.Choice(["douyin", "xiaohongshu", "bilibili"]),
              help="目标平台")
@click.option("--duration", "-d", default=180, type=int,
              help="目标时长（秒）")
@click.option("--prompt-only", is_flag=True,
              help="仅生成提示词，不进入等待流程")
def soul_script(topic, angle, platform, duration, prompt_only):
    """SOUL驱动脚本生成.

    示例：
        python scripts/run_workflow.py soul-script -t "AI焦虑" -a "从有限性视角"
        python scripts/run_workflow.py soul-script -t "AI焦虑" -a "从有限性视角" --prompt-only
    """
    if prompt_only:
        prompt = SOULScriptWriter.generate_prompt_only(topic, angle, platform, duration)
        click.echo(prompt)
        click.echo()
        click.echo("=" * 60)
        click.echo("将上述提示词复制到 Claude Code 中执行")
    else:
        click.echo(f"📝 SOUL脚本生成")
        click.echo(f"   选题：{topic}")
        click.echo(f"   角度：{angle}")
        click.echo(f"   平台：{platform}")
        click.echo()
        writer = SOULScriptWriter()
        input_data = SOULScriptWriterInput(
            topic=topic, angle=angle, platform=platform, duration=duration
        )
        result = asyncio.run(writer.execute(input_data))
        if result.success:
            click.echo("✅ 脚本生成完成")
            script = result.script
            click.echo("\n" + "=" * 60)
            click.echo("Hook：")
            click.echo(f"  {script.get('hook', '')}")
            click.echo("-" * 60)
            click.echo("痛点：")
            click.echo(f"  {script.get('pain_point', '')}")
            click.echo("-" * 60)
            click.echo("核心内容：")
            click.echo(f"  {script.get('core_content', '')}")
            click.echo("-" * 60)
            click.echo("启发：")
            click.echo(f"  {script.get('insight', '')}")
            click.echo("-" * 60)
            click.echo("CTA：")
            click.echo(f"  {script.get('cta', '')}")
            click.echo("=" * 60)
            if script.get("soul_alignment_issues"):
                click.echo("\n⚠️  SOUL人设提醒：")
                for issue in script["soul_alignment_issues"]:
                    click.echo(f"  • {issue}")
        else:
            click.echo(f"❌ 失败：{result.error}")


@cli.command()
@click.option("--use-hermes", is_flag=True, default=True,
              help="使用Hermes热点数据")
@click.option("--manual-file", type=str, help="手动导入文件路径")
@click.option("--days", default=7, help="读取最近N天的热点")
@click.option("--top", default=10, help="显示Top N")
def soul_rank(use_hermes, manual_file, days, top):
    """SOUL框架热点评分排序.

    示例：
        python scripts/run_workflow.py soul-rank
        python scripts/run_workflow.py soul-rank --manual-file hotspots.csv
        python scripts/run_workflow.py soul-rank --top 10
    """
    click.echo("🔍 采集热点...")
    collector = HotspotCollector()
    hotspots = asyncio.run(
        collector.collect(use_hermes=use_hermes, manual_file=manual_file, days=days)
    )

    if not hotspots:
        click.echo("❌ 未采集到热点数据")
        return

    click.echo(f"📊 共 {len(hotspots)} 个热点")
    click.echo()

    click.echo("🧠 SOUL框架评分中...")
    matcher = SOULHotTopicMatcher()
    # 同步评分
    ranked = matcher.batch_score(hotspots)

    click.echo(f"\n🏆 SOUL适配度排名（Top {min(top, len(ranked))}）：\n")
    for i, topic in enumerate(ranked[:top], 1):
        click.echo(f"{i:2}. [{topic['total_score']:.1f}] {topic['topic']['title']}")
        click.echo(f"    方向：{topic['finitude_name']}  |  "
                    f"受众：{topic['audience_label']}")
        click.echo(f"    角度：{topic['recommended_angle']}")
        click.echo()

    click.echo("=" * 60)
    click.echo("💡 使用以下命令为Top 1生成脚本：")
    top1 = ranked[0]
    click.echo(f"  python scripts/run_workflow.py soul-script \\")
    click.echo(f"    -t \"{top1['topic']['title']}\" \\")
    click.echo(f"    -a \"{top1['recommended_angle'][:50]}...\"")


if __name__ == "__main__":
    cli()
