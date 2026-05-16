"""Data validation utilities."""

from typing import Any, Dict, List, Optional


def validate_hot_topic(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate hot topic data.

    Args:
        data: Hot topic data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["title", "platform"]

    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"

    # Validate title length
    if len(data["title"]) > 500:
        return False, "Title too long (max 500 characters)"

    # Validate platform
    valid_platforms = ["douyin", "xiaohongshu", "bilibili", "weibo", "zhihu"]
    if data["platform"] not in valid_platforms:
        return False, f"Invalid platform: {data['platform']}"

    # Validate scores if present
    score_fields = [
        "track_score",
        "persona_score",
        "timeliness_score",
        "differentiation_score",
        "risk_score",
        "total_score",
    ]
    for field in score_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], (int, float)):
                return False, f"Invalid score type for {field}"
            if not 0 <= data[field] <= 10:
                return False, f"Score out of range for {field} (must be 0-10)"

    return True, None


def validate_creator(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate creator data.

    Args:
        data: Creator data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["account_name", "platform"]

    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"

    # Validate account name length
    if len(data["account_name"]) > 200:
        return False, "Account name too long (max 200 characters)"

    # Validate platform
    valid_platforms = ["douyin", "xiaohongshu", "bilibili", "weibo", "zhihu"]
    if data["platform"] not in valid_platforms:
        return False, f"Invalid platform: {data['platform']}"

    # Validate followers if present
    if "followers" in data and data["followers"] is not None:
        if not isinstance(data["followers"], int) or data["followers"] < 0:
            return False, "Invalid followers count"

    return True, None


def validate_content(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate content data.

    Args:
        data: Content data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["title", "platform"]

    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"

    # Validate title length
    if len(data["title"]) > 500:
        return False, "Title too long (max 500 characters)"

    # Validate platform
    valid_platforms = ["douyin", "xiaohongshu", "bilibili", "weibo", "zhihu"]
    if data["platform"] not in valid_platforms:
        return False, f"Invalid platform: {data['platform']}"

    # Validate numeric fields if present
    numeric_fields = ["views", "likes", "comments", "shares", "favorites", "new_followers"]
    for field in numeric_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], int) or data[field] < 0:
                return False, f"Invalid value for {field}"

    # Validate rate fields if present
    rate_fields = [
        "completion_rate",
        "five_sec_retention",
        "engagement_rate",
        "follower_conversion_rate",
        "favorite_like_ratio",
    ]
    for field in rate_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], (int, float)):
                return False, f"Invalid rate type for {field}"
            if not 0 <= data[field] <= 1:
                return False, f"Rate out of range for {field} (must be 0-1)"

    return True, None
