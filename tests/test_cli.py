import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "herdr-claude-panes.py"


def test_empty_config_aborts(tmp_path: Path) -> None:
    config = tmp_path / "panes.json"
    config.write_text(json.dumps([]))

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(config)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "empty config" in proc.stderr


def test_missing_prompt_files_abort_without_force(tmp_path: Path) -> None:
    config = tmp_path / "panes.json"
    config.write_text(json.dumps([
        {"pane": 1, "name": "architect", "constitution": "constitution.md", "role": "architect.md"},
    ]))

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(config), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "missing prompt files" in proc.stderr
