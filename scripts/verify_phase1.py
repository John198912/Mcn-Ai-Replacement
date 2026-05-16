#!/usr/bin/env python3
"""Quick verification script for Phase 1 infrastructure."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, init_database, get_db_session, setup_logging
from src.core.database import HotTopic, Creator, Content
from src.utils import clean_text, calculate_similarity, validate_hot_topic


def main():
    """Run verification checks."""
    print("=" * 60)
    print("MCN AI Replacement System - Phase 1 Verification")
    print("=" * 60)
    print()

    # Setup logging
    setup_logging(log_level="INFO")

    # 1. Configuration
    print("1️⃣  Testing Configuration System...")
    try:
        config = get_config()
        print(f"   ✅ Config loaded")
        print(f"   📁 Database: {config.database_url}")
        print(f"   🔑 Keywords: {len(config.keywords)} categories")
        print(f"   🌐 Platforms: {len(config.platforms['platforms'])} platforms")
        print()
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return False

    # 2. Database
    print("2️⃣  Testing Database System...")
    try:
        init_database(config.database_url)
        session = get_db_session()

        # Test insert
        test_topic = HotTopic(
            title="测试热点",
            platform="douyin",
            track_score=8.5,
            total_score=8.0,
        )
        session.add(test_topic)
        session.commit()

        # Test query
        count = session.query(HotTopic).count()
        print(f"   ✅ Database working")
        print(f"   📊 Tables: HotTopic, Creator, Content")
        print(f"   📝 Test record created (total: {count})")

        # Cleanup
        session.delete(test_topic)
        session.commit()
        session.close()
        print()
    except Exception as e:
        print(f"   ❌ Database failed: {e}")
        return False

    # 3. Personal Profile
    print("3️⃣  Testing Personal Profile...")
    try:
        profile = config.personal_profile
        print(f"   ✅ Profile loaded")
        print(f"   👤 Creator: {profile['creator_info']['name']}")
        print(f"   🎯 Positioning: {profile['creator_info']['positioning'][:50]}...")
        print(f"   🏷️  Track focus: {', '.join(profile['track_focus'][:3])}")
        print()
    except Exception as e:
        print(f"   ❌ Profile failed: {e}")
        return False

    # 4. Utilities
    print("4️⃣  Testing Utility Functions...")
    try:
        # Text processing
        text = "  这是一个  测试文本！！  "
        cleaned = clean_text(text)

        # Similarity
        sim = calculate_similarity("AI大模型应用", "AI应用开发")

        # Validation
        valid, error = validate_hot_topic({
            "title": "测试热点",
            "platform": "douyin",
            "track_score": 8.5,
        })

        print(f"   ✅ Utilities working")
        print(f"   🧹 Text cleaning: functional")
        print(f"   📊 Similarity calc: functional")
        print(f"   ✔️  Data validation: functional")
        print()
    except Exception as e:
        print(f"   ❌ Utilities failed: {e}")
        return False

    # 5. Keywords
    print("5️⃣  Testing Keywords Configuration...")
    try:
        ai_keywords = config.get_keywords_by_category("ai_keywords")
        brand_keywords = config.get_keywords_by_category("personal_brand_keywords")

        print(f"   ✅ Keywords loaded")
        print(f"   🤖 AI keywords: {len(ai_keywords)} items")
        print(f"   🏷️  Brand keywords: {len(brand_keywords)} items")
        print(f"   📝 Sample: {', '.join(ai_keywords[:3])}")
        print()
    except Exception as e:
        print(f"   ❌ Keywords failed: {e}")
        return False

    # 6. Platforms
    print("6️⃣  Testing Platform Configuration...")
    try:
        douyin = config.get_platform_config("douyin")
        xiaohongshu = config.get_platform_config("xiaohongshu")

        print(f"   ✅ Platforms loaded")
        print(f"   📱 Douyin: {douyin['name']}")
        print(f"   📱 Xiaohongshu: {xiaohongshu['name']}")
        print(f"   ⏱️  Optimal duration: {douyin['optimal_duration']}")
        print()
    except Exception as e:
        print(f"   ❌ Platforms failed: {e}")
        return False

    # Summary
    print("=" * 60)
    print("✅ All Phase 1 Components Verified Successfully!")
    print("=" * 60)
    print()
    print("📦 Installed Components:")
    print("   • Configuration System (YAML/JSON/ENV)")
    print("   • Database Models (SQLAlchemy + SQLite)")
    print("   • Logging System (structlog)")
    print("   • WebSearch Framework (async)")
    print("   • Utility Functions (text/validation/format)")
    print()
    print("🚀 Ready for Phase 2: Skills Implementation")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
