"""Explicitly persist a validated snapshot under a project's .assumption-hunter/."""

import argparse
import json
from contextlib import contextmanager
from pathlib import Path

from cli import abort, atomic_write, is_link, print_text
from state import MAX_BYTES, StateError, canonical, load_snapshot, require, timestamp


@contextmanager
def project_lock(directory: Path):
    lock = directory / ".save.lock"
    try:
        lock.touch(exist_ok=False)
    except FileExistsError:
        raise StateError(
            "snapshot directory is locked; if an earlier writer crashed, "
            "confirm no writer is active before removing .save.lock"
        ) from None
    try:
        yield
    finally:
        lock.unlink()


def snapshot_bytes(snapshot: dict) -> bytes:
    try:
        content = (json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    except UnicodeError:
        content = (canonical(snapshot) + "\n").encode("ascii")
    require(len(content) <= MAX_BYTES, "JSON", "serialized snapshot exceeds the size limit")
    return content


def safe_load(path: Path) -> dict:
    require(not is_link(path) and path.is_file(), path.name, "expected a regular snapshot file")
    return load_snapshot(path)


def save_snapshot(snapshot: dict, project: Path, base: str | None = None) -> bool:
    payload = snapshot_bytes(snapshot)
    project = project.resolve(strict=True)
    require(project.is_dir(), "--project", "expected an existing project directory")
    directory = project / ".assumption-hunter"
    require(not is_link(directory), directory.name, "symbolic links and junctions are unsupported")
    directory.mkdir(exist_ok=True)
    current_file = directory / "assumptions.json"
    history = directory / "history"
    with project_lock(directory):
        require(not is_link(history) and not is_link(current_file), directory.name,
                "snapshot and history paths must not redirect")
        if not current_file.exists():
            require(base is None, "--base", "no current snapshot to match")
            require(not history.exists(), history.name, "current state is missing; check the saved history")
            atomic_write(current_file, payload)
            return True
        previous = safe_load(current_file)
        if canonical(previous) == canonical(snapshot):
            return False
        require(snapshot["project_id"] == previous["project_id"], "$.project_id",
                "does not match the saved project")
        previous_time = timestamp(previous["audited_at"], "$.audited_at")
        require(base is not None and timestamp(base, "--base") == previous_time,
                "--base", "expected the audited_at value of the current snapshot")
        require(timestamp(snapshot["audited_at"], "$.audited_at") > previous_time,
                "$.audited_at", "must be newer than the saved snapshot")
        history.mkdir(exist_ok=True)
        existing_ids = {item["id"] for item in previous["assumptions"]}
        introduced = {item["id"] for item in snapshot["assumptions"]} - existing_ids
        if introduced:
            for archived in history.glob("*.json"):
                archived_ids = {item["id"] for item in safe_load(archived)["assumptions"]}
                require(not introduced & archived_ids, "$.assumptions",
                        "a newly introduced ID was already used in the history")
        archive = history / (previous_time.isoformat(timespec="microseconds")
                             .removesuffix("+00:00").replace(":", "") + "Z.json")
        if archive.exists() or is_link(archive):
            require(canonical(safe_load(archive)) == canonical(previous), "history",
                    "archive at the prior timestamp contains different data")
        else:
            atomic_write(archive, snapshot_bytes(previous))
        atomic_write(current_file, payload, replace=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--project", type=Path, required=True, help="existing project directory for local state")
    parser.add_argument("--base", help="current snapshot's audited_at value when saving an update")
    args = parser.parse_args()
    try:
        changed = save_snapshot(load_snapshot(args.snapshot), args.project, args.base)
    except (OSError, StateError) as error:
        abort(parser, error)
    print_text("Snapshot saved.\n" if changed else "Snapshot already current.\n")


if __name__ == "__main__":
    main()
