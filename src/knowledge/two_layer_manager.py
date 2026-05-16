"""两层知识库管理器 - 本地Markdown + GitHub备份."""

from pathlib import Path
from typing import List, Dict, Optional
import shutil
import subprocess
from datetime import datetime
from ..core.logger import get_logger

logger = get_logger(__name__)


class TwoLayerKnowledgeManager:
    """两层知识库管理器.

    第一层：本地Markdown + SQLite（主存储）
    第二层：GitHub仓库（备份 + 版本控制）

    特性：
    1. 本地为主，GitHub为备份
    2. 独立维护，互不干扰
    3. 冲突解决机制（local_wins / remote_wins / manual）
    4. 增量同步（只同步变更文件）
    """

    def __init__(self):
        self.local_markdown = Path("data/markdown")
        self.github_knowledge_dir = Path("knowledge")
        self.last_sync_file = Path(".last_sync")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保目录结构存在."""
        dirs = [
            self.local_markdown / "hotspots",
            self.local_markdown / "scripts",
            self.local_markdown / "creators",
            self.local_markdown / "analytics",
            self.github_knowledge_dir / "hotspots",
            self.github_knowledge_dir / "scripts",
            self.github_knowledge_dir / "creators",
            self.github_knowledge_dir / "analytics",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # ==================== 保存操作 ====================

    def save_hotspot_to_markdown(self, hotspot_data: Dict) -> str:
        """将热点保存为Markdown文件.

        Args:
            hotspot_data: 热点数据字典

        Returns:
            保存的文件路径
        """
        title = hotspot_data.get("title", "unknown")
        safe_name = self._safe_filename(title)
        md_path = self.local_markdown / "hotspots" / f"{safe_name}.md"

        content = self._hotspot_to_markdown(hotspot_data)
        md_path.write_text(content, encoding="utf-8")
        logger.info("热点已保存", title=title, path=str(md_path))
        return str(md_path)

    def save_script_to_markdown(self, script_data: Dict) -> str:
        """将脚本保存为Markdown文件.

        Args:
            script_data: 脚本数据字典，包含topic、hook、core_content等

        Returns:
            保存的文件路径
        """
        topic = script_data.get("topic", "unknown")
        safe_name = self._safe_filename(topic)
        md_path = self.local_markdown / "scripts" / f"{safe_name}.md"

        content = self._script_to_markdown(script_data)
        md_path.write_text(content, encoding="utf-8")
        logger.info("脚本已保存", topic=topic, path=str(md_path))
        return str(md_path)

    @staticmethod
    def _safe_filename(name: str) -> str:
        """生成安全的文件名."""
        safe = name.replace("/", "_").replace(" ", "_").replace("?", "")[:50]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{safe}_{timestamp}"

    def _hotspot_to_markdown(self, hotspot: Dict) -> str:
        """将热点数据转换为Markdown."""
        tags_str = ", ".join(hotspot.get("tags", []))
        return f"""# {hotspot.get('title', '')}

## 基本信息
- 来源：{hotspot.get('platform', '')}
- 热度：{hotspot.get('heat_level', '')}
- 标签：{tags_str}
- 优先级：{hotspot.get('priority', '')}

## SOUL框架分析
### 推荐切入角度
{hotspot.get('recommended_angle', '')}

## 状态
- 创建时间：{datetime.utcnow().isoformat()}
"""

    def _script_to_markdown(self, script: Dict) -> str:
        """将脚本数据转换为Markdown."""
        return f"""# {script.get('topic', '')}

## Hook (前5%)
{script.get('hook', '')}

## 痛点 (10-20%)
{script.get('pain_point', '')}

## 核心内容 (20-80%)
{script.get('core_content', '')}

## 启发 (80-95%)
{script.get('insight', '')}

## CTA (最后5%)
{script.get('cta', '')}

## 状态
- 创建时间：{datetime.utcnow().isoformat()}
"""

    # ==================== GitHub同步 ====================

    async def sync_to_github(
        self,
        strategy: str = "local_wins",
        incremental: bool = True,
    ):
        """同步到GitHub.

        Args:
            strategy: 冲突解决策略（local_wins / remote_wins / manual）
            incremental: 是否增量同步（只同步变更文件）
        """
        logger.info("开始GitHub同步", strategy=strategy, incremental=incremental)

        # 1. 检查远程变更
        remote_changes = self._check_remote_changes()

        if remote_changes:
            logger.warning("检测到远程变更", count=len(remote_changes))
            self._resolve_conflicts(remote_changes, strategy)

        # 2. 同步本地变更
        if incremental:
            self._sync_incremental()
        else:
            self._sync_full()

        logger.info("GitHub同步完成")

    def _check_remote_changes(self) -> List[Dict]:
        """检查远程变更."""
        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                check=True,
                capture_output=True,
            )
            result = subprocess.run(
                ["git", "diff", "HEAD", "origin/main", "--name-only"],
                check=True,
                capture_output=True,
                text=True,
            )
            changed_files = result.stdout.strip().split("\n")
            return [
                {"file": f}
                for f in changed_files
                if f and f.startswith("knowledge/")
            ]
        except subprocess.CalledProcessError as e:
            logger.error("检查远程变更失败", error=str(e))
            return []

    def _resolve_conflicts(self, changes: List[Dict], strategy: str):
        """解决冲突."""
        if strategy == "local_wins":
            logger.info("冲突策略：本地优先")
            return

        if strategy == "remote_wins":
            logger.info("冲突策略：远程优先")
            try:
                subprocess.run(["git", "pull", "origin", "main"], check=True)
            except subprocess.CalledProcessError:
                logger.warning("Git pull 失败，使用本地版本")
            return

        if strategy == "manual":
            print("\n⚠️  检测到以下远程变更：")
            for change in changes:
                print(f"  - {change['file']}")
            print("\n选择策略：")
            print("1. 本地优先（覆盖远程）")
            print("2. 远程优先（覆盖本地）")
            choice = input("请选择 (1/2): ").strip()
            if choice == "1":
                self._resolve_conflicts(changes, "local_wins")
            elif choice == "2":
                self._resolve_conflicts(changes, "remote_wins")

    def _sync_incremental(self):
        """增量同步：只同步变更的文件."""
        if self.last_sync_file.exists():
            try:
                last_sync_time = datetime.fromisoformat(
                    self.last_sync_file.read_text().strip()
                )
            except (ValueError, OSError):
                last_sync_time = datetime.min
        else:
            last_sync_time = datetime.min

        changed_files = []
        for md_file in self.local_markdown.rglob("*.md"):
            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
            if mtime > last_sync_time:
                changed_files.append(md_file)

        if not changed_files:
            logger.info("无变更文件需要同步")
            return

        logger.info("增量同步", count=len(changed_files))

        for src_file in changed_files:
            rel_path = src_file.relative_to(self.local_markdown)
            dst_file = self.github_knowledge_dir / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

        self._git_commit_and_push(f"增量同步: {len(changed_files)} 个文件")
        self.last_sync_file.write_text(datetime.now().isoformat())

    def _sync_full(self):
        """全量同步."""
        logger.info("全量同步")

        # 清理旧文件
        if self.github_knowledge_dir.exists():
            shutil.rmtree(self.github_knowledge_dir)

        # 复制所有文件
        shutil.copytree(self.local_markdown, self.github_knowledge_dir)

        self._git_commit_and_push("全量同步")
        self.last_sync_file.write_text(datetime.now().isoformat())

    def _git_commit_and_push(self, message: str):
        """Git提交和推送."""
        try:
            subprocess.run(["git", "add", "knowledge/"], check=True)
            commit_msg = f"{message} - {datetime.utcnow().isoformat()}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            logger.info("Git推送成功")
        except subprocess.CalledProcessError as e:
            logger.error("Git操作失败", error=str(e))

    # ==================== 预览和查询 ====================

    def list_hotspot_files(self) -> List[Path]:
        """列出所有热点文件."""
        hotspot_dir = self.local_markdown / "hotspots"
        if hotspot_dir.exists():
            return sorted(hotspot_dir.glob("*.md"), reverse=True)
        return []

    def list_script_files(self) -> List[Path]:
        """列出所有脚本文件."""
        script_dir = self.local_markdown / "scripts"
        if script_dir.exists():
            return sorted(script_dir.glob("*.md"), reverse=True)
        return []

    def read_markdown(self, file_name: str, category: str = "hotspots") -> Optional[str]:
        """读取指定Markdown文件.

        Args:
            file_name: 文件名
            category: 分类（hotspots/scripts/creators/analytics）

        Returns:
            文件内容，或None
        """
        file_path = self.local_markdown / category / file_name
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return None
