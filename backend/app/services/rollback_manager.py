import shutil
from pathlib import Path
from typing import Dict, Any


def create_rollback_snapshot(workspace_dir: Path, snapshot_dir: Path) -> None:
    """Takes a full file-level backup snapshot of the workspace before modifying code."""
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir, ignore_errors=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(workspace_dir, snapshot_dir, dirs_exist_ok=True)


def restore_rollback_snapshot(snapshot_dir: Path, workspace_dir: Path) -> bool:
    """Restores workspace from pre-patch snapshot."""
    if not snapshot_dir.exists():
        return False
    shutil.rmtree(workspace_dir, ignore_errors=True)
    shutil.copytree(snapshot_dir, workspace_dir)
    return True

