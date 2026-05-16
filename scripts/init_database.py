"""Initialize database script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, init_database, get_logger

logger = get_logger(__name__)


def main():
    """Initialize database with tables."""
    try:
        # Load configuration
        config = get_config()

        logger.info("Initializing database", url=config.database_url)

        # Ensure data directory exists
        db_path = Path(config.database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        init_database(config.database_url)

        logger.info("Database initialized successfully", path=str(db_path))
        print(f"✅ Database initialized successfully at: {db_path}")

    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
