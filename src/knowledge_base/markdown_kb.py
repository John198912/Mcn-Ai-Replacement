"""Markdown knowledge base management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import get_logger

logger = get_logger(__name__)


class MarkdownKnowledgeBase:
    """Markdown-based knowledge base for non-structured content."""

    def __init__(self, base_path: Path):
        """Initialize markdown knowledge base.

        Args:
            base_path: Base path for markdown files
        """
        self.base_path = Path(base_path)
        self.logger = logger.bind(component="MarkdownKB")

        # Create directories
        self.trends_path = self.base_path / "trends"
        self.creators_path = self.base_path / "creators"
        self.scripts_path = self.base_path / "scripts"

        for path in [self.trends_path, self.creators_path, self.scripts_path]:
            path.mkdir(parents=True, exist_ok=True)

    def save_trend_report(
        self, title: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Save a trend report.

        Args:
            title: Report title
            content: Report content (markdown)
            metadata: Optional metadata

        Returns:
            Path to saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)
        filename = f"{timestamp}_{safe_title[:50]}.md"
        filepath = self.trends_path / filename

        # Prepare content with frontmatter
        frontmatter = self._generate_frontmatter(
            {"title": title, "type": "trend_report", "created_at": timestamp, **(metadata or {})}
        )

        full_content = f"{frontmatter}\n\n{content}"

        # Write file
        filepath.write_text(full_content, encoding="utf-8")

        self.logger.info("Trend report saved", filepath=str(filepath))
        return filepath

    def save_creator_analysis(
        self, creator_name: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Save creator analysis.

        Args:
            creator_name: Creator name
            content: Analysis content (markdown)
            metadata: Optional metadata

        Returns:
            Path to saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(
            c if c.isalnum() or c in "._-" else "_" for c in creator_name
        )
        filename = f"{safe_name}_{timestamp}.md"
        filepath = self.creators_path / filename

        # Prepare content with frontmatter
        frontmatter = self._generate_frontmatter(
            {
                "creator": creator_name,
                "type": "creator_analysis",
                "created_at": timestamp,
                **(metadata or {}),
            }
        )

        full_content = f"{frontmatter}\n\n{content}"

        # Write file
        filepath.write_text(full_content, encoding="utf-8")

        self.logger.info("Creator analysis saved", filepath=str(filepath))
        return filepath

    def save_script(
        self, title: str, script: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Save a script.

        Args:
            title: Script title
            script: Script dictionary
            metadata: Optional metadata

        Returns:
            Path to saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)
        filename = f"{timestamp}_{safe_title[:50]}.md"
        filepath = self.scripts_path / filename

        # Format script content
        content = self._format_script(script)

        # Prepare content with frontmatter
        frontmatter = self._generate_frontmatter(
            {
                "title": title,
                "type": "script",
                "created_at": timestamp,
                "word_count": metadata.get("word_count", 0) if metadata else 0,
                "platform": metadata.get("platform", "") if metadata else "",
                **(metadata or {}),
            }
        )

        full_content = f"{frontmatter}\n\n{content}"

        # Write file
        filepath.write_text(full_content, encoding="utf-8")

        self.logger.info("Script saved", filepath=str(filepath))
        return filepath

    def search(self, keyword: str, category: Optional[str] = None) -> List[Path]:
        """Search for files containing keyword.

        Args:
            keyword: Keyword to search
            category: Optional category (trends/creators/scripts)

        Returns:
            List of matching file paths
        """
        search_paths = []

        if category == "trends":
            search_paths = [self.trends_path]
        elif category == "creators":
            search_paths = [self.creators_path]
        elif category == "scripts":
            search_paths = [self.scripts_path]
        else:
            search_paths = [self.trends_path, self.creators_path, self.scripts_path]

        matches = []
        keyword_lower = keyword.lower()

        for search_path in search_paths:
            for filepath in search_path.glob("*.md"):
                try:
                    content = filepath.read_text(encoding="utf-8")
                    if keyword_lower in content.lower():
                        matches.append(filepath)
                except Exception as e:
                    self.logger.warning(
                        "Failed to read file", filepath=str(filepath), error=str(e)
                    )

        self.logger.info("Search completed", keyword=keyword, matches=len(matches))
        return matches

    def list_files(self, category: str, limit: int = 10) -> List[Path]:
        """List recent files in a category.

        Args:
            category: Category (trends/creators/scripts)
            limit: Maximum number of files

        Returns:
            List of file paths
        """
        if category == "trends":
            search_path = self.trends_path
        elif category == "creators":
            search_path = self.creators_path
        elif category == "scripts":
            search_path = self.scripts_path
        else:
            return []

        files = sorted(search_path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        return files[:limit]

    def _generate_frontmatter(self, metadata: Dict[str, Any]) -> str:
        """Generate YAML frontmatter.

        Args:
            metadata: Metadata dictionary

        Returns:
            Frontmatter string
        """
        lines = ["---"]
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")

        return "\n".join(lines)

    def _format_script(self, script: Dict[str, Any]) -> str:
        """Format script as markdown.

        Args:
            script: Script dictionary

        Returns:
            Formatted markdown
        """
        sections = []

        # Title
        if "title" in script:
            sections.append(f"# {script['title']}\n")

        # Hook
        if "hook" in script:
            sections.append(f"## Hook（前3秒）\n\n{script['hook']}\n")

        # Pain Point
        if "pain_point" in script:
            sections.append(f"## 痛点共鸣\n\n{script['pain_point']}\n")

        # Core Content
        if "core_content" in script:
            sections.append(f"## 核心内容\n\n{script['core_content']}\n")

        # Insight
        if "insight" in script:
            sections.append(f"## 启发/反转\n\n{script['insight']}\n")

        # CTA
        if "cta" in script:
            sections.append(f"## CTA\n\n{script['cta']}\n")

        # Analysis
        if "analysis" in script:
            sections.append(f"## 分析\n\n```json\n{json.dumps(script['analysis'], ensure_ascii=False, indent=2)}\n```\n")

        return "\n".join(sections)
