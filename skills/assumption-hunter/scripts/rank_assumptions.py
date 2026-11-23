"""Rank assumptions using the documented triage heuristic."""

import argparse
from pathlib import Path

from cli import abort, json_text, print_text
from state import StateError, load_snapshot, rank_assumptions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()
    try:
        ranked = rank_assumptions(load_snapshot(args.snapshot))
    except (OSError, StateError) as error:
        abort(parser, error)
    if args.json:
        print_text(json_text(ranked))
        return
    lines = ["ID\tScore\tStatus\tFlag"]
    for row in ranked:
        flag = "critical, unresolved" if row["critical_unresolved"] else ""
        lines.append(f"{row['id']}\t{row['score']:g}\t{row['status']}\t{flag}")
    print_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
