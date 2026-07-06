
"""Spin up one pane per config entry, each running claude with
--append-system-prompt built from constitution + role.

By default, missing prompt files abort before anything is created.
Pass --force to launch anyway (with a red warning) for missing files."""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional

RED = "\033[31m"
RESET = "\033[0m"


def prompt_search_dirs(workdir: Path) -> list[Path]:
    return [workdir / ".claude" / "prompts", Path.home() / ".claude" / "prompts"]


def herdr(*args: str) -> dict:
    proc = subprocess.run(["herdr", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"herdr {' '.join(args)} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)["result"] if proc.stdout.strip() else {}


def find_prompt(filename: str, workdir: Path) -> Optional[Path]:
    for d in prompt_search_dirs(workdir):
        c = d / filename
        if c.is_file():
            return c
    return None


def searched_paths(filename: str, workdir: Path) -> str:
    return "\n    ".join(str(d / filename) for d in prompt_search_dirs(workdir))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="?", default="herdr-panes.json")
    parser.add_argument("workdir", nargs="?", default=".")
    parser.add_argument("--force", action="store_true",
                         help="launch panes even if prompt files are missing")
    args = parser.parse_args()

    config_path = Path(args.config)
    workdir = Path(args.workdir).resolve()

    entries = json.loads(config_path.read_text())
    if not entries:
        sys.exit("empty config")
    entries.sort(key=lambda e: e["pane"])

    # pre-flight: resolve every prompt file before creating anything
    resolved: dict[int, dict[str, Optional[Path]]] = {}
    missing: list[str] = []
    for entry in entries:
        default_file = find_prompt(entry["constitution"], workdir)
        prompt_file = find_prompt(entry["role"], workdir)
        resolved[entry["pane"]] = {"default": default_file, "prompt": prompt_file}
        if default_file is None:
            missing.append(f"{entry['name']}: {entry['constitution']}\n    {searched_paths(entry['constitution'], workdir)}")
        if prompt_file is None:
            missing.append(f"{entry['name']}: {entry['role']}\n    {searched_paths(entry['role'], workdir)}")

    if missing:
        msg = "\n  ".join(missing)
        if not args.force:
            sys.exit(f"{RED}missing prompt files, aborting (use --force to launch anyway):\n  {msg}{RESET}")
        print(f"{RED}warning: missing prompt files, launching anyway (--force):\n  {msg}{RESET}",
              file=sys.stderr)

    ws_result = herdr("workspace", "create", "--cwd", str(workdir), "--label", "claude-panes")
    if "root_pane" not in ws_result:
        panes = herdr("pane", "list")["panes"]
        prev_pane = panes[0]["pane_id"]
    else:
        prev_pane = ws_result["root_pane"]["pane_id"]
    pane_ids = [prev_pane]

    for _ in entries[1:]:
        split_result = herdr("pane", "split", prev_pane, "--direction", "down", "--no-focus")
        prev_pane = split_result["pane"]["pane_id"]
        pane_ids.append(prev_pane)

    for entry, pane in zip(entries, pane_ids):
        files = resolved[entry["pane"]]
        parts = [f.read_text() for f in (files["default"], files["prompt"]) if f is not None]

        herdr("pane", "rename", pane, entry["name"])  # unconfirmed CLI cmd — verify

        cmd = ["claude"]
        if parts:
            cmd += ["--append-system-prompt", "\n".join(parts)]
        herdr_cmd = shlex.join(cmd)
        subprocess.run(["herdr", "pane", "run", pane, herdr_cmd], check=True)


if __name__ == "__main__":
    main()
