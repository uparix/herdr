#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "agent-messages.log"


def resolve_pane_id(target: str) -> str:
    proc = subprocess.run(
        ["herdr", "agent", "get", target],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"agent {target!r} not found")
    return json.loads(proc.stdout)["result"]["agent"]["pane_id"]


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <pane> <message>", file=sys.stderr)
        sys.exit(1)

    pane, message = sys.argv[1], sys.argv[2]

    try:
        pane_id = resolve_pane_id(pane)
    except RuntimeError as exc:
        print(f"herdr agent get failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # pane run types the text into the pane AND presses Enter, so the
    # receiving agent reacts immediately instead of waiting for a human
    # to submit the prompt.
    proc = subprocess.run(
        ["herdr", "pane", "run", pane_id, message],
        capture_output=True, text=True,
    )
    status = "delivered" if proc.returncode == 0 else f"delivery failed: {proc.stderr.strip()}"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"[{timestamp}] pane={pane}: {message} ({status})\n")

    if proc.returncode != 0:
        print(f"herdr pane run failed: {proc.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
