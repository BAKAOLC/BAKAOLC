"""Reject missing, malformed, or error cards before they reach the README."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_card(path, required_ids):
    root = ET.parse(path).getroot()
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("not an SVG document")
    elements = {node.get("data-testid"): node for node in root.iter()}
    if "message" in elements:
        message = " ".join(" ".join(elements["message"].itertext()).split())
        raise ValueError(f"generator returned an error card: {message}")
    for test_id in required_ids:
        node = elements.get(test_id)
        if node is None or not "".join(node.itertext()).strip():
            raise ValueError(f"missing card content: {test_id}")


def main(directory):
    errors = []
    for theme in ("light", "dark"):
        for card, required in (
            ("stats", ("stars", "commits", "prs", "issues", "contribs")),
            ("top-langs", ("lang-name",)),
        ):
            path = directory / f"{card}-{theme}.svg"
            try:
                validate_card(path, required)
            except (OSError, ET.ParseError, ValueError) as exc:
                errors.append(f"{path}: {exc}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Validated all four README stats cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "profile")))
