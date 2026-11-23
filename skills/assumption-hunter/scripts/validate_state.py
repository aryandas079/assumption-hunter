"""Validate an Assumption Hunter state file without resolving its citations."""

import argparse
from pathlib import Path

from cli import abort, print_text
from state import StateError, load_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    try:
        snapshot = load_snapshot(args.snapshot)
    except (OSError, StateError) as error:
        abort(parser, error)
    print_text(f"Valid snapshot ({len(snapshot['assumptions'])} assumptions).\n")


if __name__ == "__main__":
    main()
