"""Format conversion utilities."""

import json
from typing import Any, Dict


def dict_to_markdown(data: Dict[str, Any], title: str = None) -> str:
    """Convert dictionary to markdown format.

    Args:
        data: Data dictionary
        title: Optional title

    Returns:
        Markdown formatted string
    """
    lines = []

    if title:
        lines.append(f"# {title}\n")

    for key, value in data.items():
        # Format key as header
        formatted_key = key.replace("_", " ").title()
        lines.append(f"## {formatted_key}\n")

        # Format value
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                lines.append(f"- **{sub_key}**: {sub_value}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
                else:
                    lines.append(f"- {item}")
        else:
            lines.append(f"{value}")

        lines.append("")  # Empty line

    return "\n".join(lines)


def markdown_to_dict(markdown: str) -> Dict[str, Any]:
    """Convert markdown to dictionary (simple parser).

    Args:
        markdown: Markdown formatted string

    Returns:
        Data dictionary
    """
    # This is a simplified parser
    # For production, consider using a proper markdown parser
    data = {}
    current_key = None

    for line in markdown.split("\n"):
        line = line.strip()

        if line.startswith("## "):
            # New section
            current_key = line[3:].strip().lower().replace(" ", "_")
            data[current_key] = []
        elif line.startswith("- ") and current_key:
            # List item
            item = line[2:].strip()
            data[current_key].append(item)
        elif line and current_key and not line.startswith("#"):
            # Regular content
            if not data[current_key]:
                data[current_key] = line
            elif isinstance(data[current_key], list):
                data[current_key].append(line)

    return data


def json_to_yaml_str(data: Dict[str, Any]) -> str:
    """Convert JSON/dict to YAML string (simple version).

    Args:
        data: Data dictionary

    Returns:
        YAML formatted string
    """
    import yaml

    return yaml.dump(data, allow_unicode=True, default_flow_style=False)
