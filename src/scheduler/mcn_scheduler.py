"""MCN定时任务调度器."""

import schedule
import time
import asyncio
from datetime import datetime
from ..core.logger import get_logger

logger = get_logger(__name__)


class MCNScheduler:
    """MCN定时任务调度器.

    任务：
    1. 每周一 10:00 - 采集热点
    2. 每天 02:00 - 备份知识库
    3. 每天 03:00 - 同步GitHub

    Usage:
        scheduler = MCNScheduler()
        scheduler.start()  # 阻塞运行
        或
        scheduler.run_once("backup")  # 单次执行
    """

    def __init__(self):
        self.running = False
        self._hotspot_func = None
        self._backup_func = None
        self._sync_func = None

    def set_hotspot_callback(self, func):
        """设置热点采集回调."""
        self._hotspot_func = func

    def set_backup_callback(self, func):
        """设置备份回调."""
        self._backup_func = func

    def set_sync_callback(self, func):
        """设置同步回调."""
        self._sync_func = func

    def start(self):
        """启动调度器（阻塞运行）."""
        # 每周一 10:00 采集热点
        schedule.every().monday.at("10:00").do(self._run_hotspot)

        # 每天 02:00 备份
        schedule.every().day.at("02:00").do(self._run_backup)

        # 每天 03:00 同步GitHub
        schedule.every().day.at("03:00").do(self._run_sync)

        self.running = True
        logger.info("MCN调度器已启动")

        print("\n" + "=" * 60)
        print("🚀 MCN定时任务调度器已启动")
        print("=" * 60)
        print("\n定时任务：")
        print("  • 每周一 10:00 — 采集热点")
        print("  • 每天   02:00 — 备份知识库")
        print("  • 每天   03:00 — 同步GitHub")
        print("\n按 Ctrl+C 停止")
        print("=" * 60 + "\n")

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """停止调度器."""
        self.running = False
        logger.info("MCN调度器已停止")
        print("\n✅ 调度器已停止")

    def _run_hotspot(self):
        """执行热点采集."""
        logger.info("定时任务：采集热点")
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始采集热点...")
        try:
            if self._hotspot_func:
                self._hotspot_func()
                print("✅ 热点采集完成")
            else:
                print("⚠️  未设置热点采集回调")
        except Exception as e:
            logger.error("热点采集失败", error=str(e))
            print(f"❌ 热点采集失败: {e}")

    def _run_backup(self):
        """执行备份."""
        logger.info("定时任务：备份知识库")
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始备份知识库...")
        try:
            if self._backup_func:
                self._backup_func()
                print("✅ 备份完成")
            else:
                print("⚠️  未设置备份回调")
        except Exception as e:
            logger.error("备份失败", error=str(e))
            print(f"❌ 备份失败: {e}")

    def _run_sync(self):
        """执行同步."""
        logger.info("定时任务：同步GitHub")
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始同步GitHub...")
        try:
            if self._sync_func:
                self._sync_func()
                print("✅ GitHub同步完成")
            else:
                print("⚠️  未设置同步回调")
        except Exception as e:
            logger.error("GitHub同步失败", error=str(e))
            print(f"❌ GitHub同步失败: {e}")

    def run_once(self, task_name: str):
        """单次执行任务（用于测试）.

        Args:
            task_name: 任务名称（hotspot / backup / sync）
        """
        tasks = {
            "hotspot": self._run_hotspot,
            "backup": self._run_backup,
            "sync": self._run_sync,
        }
        func = tasks.get(task_name)
        if func:
            func()
        else:
            print(f"未知任务: {task_name}（支持：hotspot / backup / sync）")

    @staticmethod
    def get_launchd_plist() -> str:
        """生成macOS launchd配置.

        Returns:
            plist XML内容
        """
        import os

        home = os.path.expanduser("~")
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mcn.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{home}/mcn-ai-replacement/scripts/run_workflow.py</string>
        <string>start-scheduler</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{home}/mcn-ai-replacement</string>
    <key>StandardOutPath</key>
    <string>{home}/mcn-ai-replacement/logs/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>{home}/mcn-ai-replacement/logs/scheduler_error.log</string>
</dict>
</plist>'''
