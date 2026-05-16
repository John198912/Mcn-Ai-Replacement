"""备份管理器 - 知识库备份/验证/恢复/清理."""

from pathlib import Path
from datetime import datetime
import shutil
import json
import sqlite3
from ..core.logger import get_logger

logger = get_logger(__name__)


class BackupManager:
    """备份管理器.

    功能：
    1. 创建备份（数据库 + Markdown + 配置）
    2. 验证备份完整性
    3. 从备份恢复
    4. 自动清理旧备份

    Usage:
        mgr = BackupManager()
        backup_id = mgr.create_backup()
        mgr.verify_backup(backup_id)
        mgr.restore_backup(backup_id)
    """

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.sources = {
            "database": Path("data/database.db"),
            "markdown": Path("data/markdown"),
            "config": Path("config"),
        }

    def create_backup(self, backup_name: str = None) -> str:
        """创建备份.

        Args:
            backup_name: 备份名称，默认使用时间戳

        Returns:
            备份ID
        """
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        files_count = 0
        total_size = 0

        # 备份数据库
        db_src = self.sources["database"]
        if db_src.exists():
            db_dst = backup_path / "database.db"
            shutil.copy2(db_src, db_dst)
            files_count += 1
            total_size += db_dst.stat().st_size
            logger.info("数据库已备份")

        # 备份Markdown
        md_src = self.sources["markdown"]
        if md_src.exists():
            md_dst = backup_path / "markdown"
            shutil.copytree(md_src, md_dst, dirs_exist_ok=True)
            for f in md_dst.rglob("*"):
                if f.is_file():
                    files_count += 1
                    total_size += f.stat().st_size
            logger.info("Markdown已备份")

        # 备份配置
        config_src = self.sources["config"]
        if config_src.exists():
            config_dst = backup_path / "config"
            shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
            for f in config_dst.rglob("*"):
                if f.is_file():
                    files_count += 1
                    total_size += f.stat().st_size
            logger.info("配置已备份")

        # 创建元数据
        size_mb = round(total_size / (1024 * 1024), 2)
        metadata = {
            "backup_id": backup_name,
            "created_at": datetime.now().isoformat(),
            "files_count": files_count,
            "size_bytes": total_size,
            "size_mb": size_mb,
        }
        metadata_file = backup_path / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))

        logger.info("备份创建完成", backup_id=backup_name, size=f"{size_mb}MB")
        return backup_name

    def verify_backup(self, backup_name: str) -> bool:
        """验证备份完整性.

        Args:
            backup_name: 备份名称

        Returns:
            是否完整
        """
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error("备份不存在", backup_id=backup_name)
            return False

        # 检查元数据
        metadata_file = backup_path / "metadata.json"
        if not metadata_file.exists():
            logger.error("缺少元数据文件")
            return False

        # 验证数据库
        db_file = backup_path / "database.db"
        if db_file.exists():
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in cursor]
                conn.close()
                logger.info("数据库验证通过", tables=len(tables))
                if not tables:
                    logger.warning("数据库无表")
            except Exception as e:
                logger.error("数据库验证失败", error=str(e))
                return False

        # 验证Markdown
        md_dir = backup_path / "markdown"
        if md_dir.exists():
            md_count = len(list(md_dir.rglob("*.md")))
            if md_count == 0:
                logger.warning("备份中无Markdown文件")
            else:
                logger.info("Markdown验证通过", files=md_count)

        return True

    def restore_backup(self, backup_name: str) -> bool:
        """从备份恢复.

        恢复前会自动创建当前状态的安全备份。

        Args:
            backup_name: 备份名称

        Returns:
            是否成功
        """
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error("备份不存在", backup_id=backup_name)
            return False

        # 先创建当前状态的备份
        safety_backup = self.create_backup(f"before_restore_{backup_name}")
        logger.info("安全备份已创建", backup_id=safety_backup)

        try:
            # 恢复数据库
            db_src = backup_path / "database.db"
            if db_src.exists():
                shutil.copy2(db_src, self.sources["database"])
                logger.info("数据库已恢复")

            # 恢复Markdown
            md_src = backup_path / "markdown"
            if md_src.exists():
                if self.sources["markdown"].exists():
                    shutil.rmtree(self.sources["markdown"])
                shutil.copytree(md_src, self.sources["markdown"])
                logger.info("Markdown已恢复")

            # 恢复配置（可选，默认不恢复）
            config_src = backup_path / "config"
            if config_src.exists():
                logger.info("配置备份存在但跳过恢复（保护当前配置）")

            logger.info("恢复完成", backup_id=backup_name)
            return True

        except Exception as e:
            logger.error("恢复失败", error=str(e))
            return False

    def list_backups(self) -> list:
        """列出所有备份."""
        backups = []
        for backup_path in sorted(
            self.backup_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            if backup_path.is_dir():
                metadata_file = backup_path / "metadata.json"
                if metadata_file.exists():
                    try:
                        metadata = json.loads(metadata_file.read_text())
                        backups.append(metadata)
                    except (json.JSONDecodeError, OSError):
                        backups.append({
                            "backup_id": backup_path.name,
                            "created_at": "unknown",
                            "files_count": "unknown",
                            "size_mb": "unknown",
                        })
        return backups

    def clean_old_backups(self, keep_last: int = 10):
        """清理旧备份，保留最近N个.

        Args:
            keep_last: 保留最近N个备份
        """
        backups = sorted(
            [p for p in self.backup_dir.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        removed = 0
        for backup_path in backups[keep_last:]:
            shutil.rmtree(backup_path)
            removed += 1
            logger.info("已清理旧备份", name=backup_path.name)

        kept = min(len(backups), keep_last)
        logger.info("备份清理完成", kept=kept, removed=removed)
