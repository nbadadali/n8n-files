"""Utility script to verify n8n workflow JSON files."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def validate_workflow(path: Path) -> list[str]:
    data = json.loads(path.read_text())
    nodes = data.get("nodes", [])
    missing: list[str] = []

    name_counts: Counter[str] = Counter()
    id_counts: Counter[str] = Counter()
    node_names: set[str] = set()

    for index, node in enumerate(nodes):
        name = node.get("name")
        if not name:
            missing.append(f"Node at index {index} is missing a 'name' field")
        else:
            name_counts[name] += 1
            node_names.add(name)

        if "id" not in node:
            identifier = name or f"index {index}"
            missing.append(f"Node '{identifier}' is missing an 'id' field")
        else:
            node_id = node.get("id")
            if node_id is None:
                identifier = name or f"index {index}"
                missing.append(f"Node '{identifier}' has a null 'id' value")
            else:
                id_counts[str(node_id)] += 1

    duplicates = [name for name, count in name_counts.items() if count > 1]
    for name in duplicates:
        missing.append(f"Duplicate node name detected: '{name}'")

    duplicate_ids = [node_id for node_id, count in id_counts.items() if count > 1]
    for node_id in duplicate_ids:
        missing.append(f"Duplicate node id detected: '{node_id}'")

    for source, connection_types in data.get("connections", {}).items():
        if source not in node_names:
            missing.append(f"Connection source '{source}' missing from nodes")
        for targets in connection_types.values():
            for branch in targets:
                for connection in branch:
                    target = connection.get("node")
                    if target not in node_names:
                        missing.append(
                            f"Connection from '{source}' references missing node '{target}'"
                        )
    return missing


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv] if argv else sorted(Path.cwd().glob("Gmail*.json"))
    exit_code = 0
    for path in paths:
        problems = validate_workflow(path)
        if problems:
            exit_code = 1
            print(f"{path.name}: FAIL")
            for issue in problems:
                print(f"  - {issue}")
        else:
            print(f"{path.name}: OK")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
