"""Compare validated snapshots without reproducing their evidence passages."""

import argparse
import html
import re
import unicodedata
from pathlib import Path

from cli import abort, atomic_write, is_link, json_text, print_text
from state import StateError, compare_snapshots, load_snapshot, require


def markdown_text(value: str) -> str:
    clean = "".join(ch for ch in " ".join(value.split()) if not unicodedata.category(ch).startswith("C"))
    return re.sub(r"([\\`*_{}\[\]()!~])", r"\\\1", html.escape(clean))


def render_markdown(diff: dict) -> str:
    lines = ["# Assumption changes", ""]
    if not any(diff.values()):
        return "# Assumption changes\n\nNo assumption changes.\n"
    for group in ("added", "retired"):
        if diff[group]:
            lines.append(f"- {group.capitalize()} — {', '.join(diff[group])}")
    for entry in diff["changes"]:
        fields = ", ".join(markdown_text(field) for field in entry["fields"])
        reason = markdown_text(entry["reason"]) if entry["reason"] else "Reason unavailable."
        lines.append(f"- **{entry['id']}** — {fields}. {reason}")
        if "status" in entry:
            status = entry["status"]
            lines.append(f"  - Status moved from {status['before']} to {status['after']}.")
        if "priority" in entry:
            old, new = (entry["priority"][key] for key in ("before", "after"))
            lines.append(f"  - Triage score moved from {old['score']:g} to {new['score']:g}.")
            if old["critical_unresolved"] != new["critical_unresolved"]:
                flag = "set" if new["critical_unresolved"] else "cleared"
                lines.append(f"  - Critical unresolved flag {flag}.")
    return "\n".join(lines) + "\n"


def output_path(path: Path, use_json: bool) -> Path:
    expected = ".json" if use_json else ".md"
    require(not path.anchor and ".." not in path.parts and path.suffix.lower() == expected
            and all(":" not in part and not part.endswith((".", " ")) for part in path.parts),
            "--output", f"expected a relative {expected} path inside the working directory")
    root = Path.cwd().resolve()
    require(not any(is_link(parent) for parent in (path, *path.parents)), "--output",
            "symbolic links and junctions are unsupported")
    destination = (root / path).resolve()
    require(destination.is_relative_to(root) and not destination.exists(), "--output",
            "expected a new file inside the working directory")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--json", action="store_true", help="output JSON instead of Markdown")
    parser.add_argument("--output", type=Path, help="atomically create a new report in the working directory")
    args = parser.parse_args()
    try:
        diff = compare_snapshots(load_snapshot(args.old), load_snapshot(args.new))
        content = json_text(diff) if args.json else render_markdown(diff)
        if args.output:
            atomic_write(output_path(args.output, args.json), content.encode("utf-8"))
        else:
            print_text(content)
    except (OSError, StateError) as error:
        abort(parser, error)


if __name__ == "__main__":
    main()
