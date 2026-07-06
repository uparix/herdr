# herdr-claude-panes

Spins up one [herdr](https://github.com/) pane per entry in a JSON config, each
running `claude` with `--append-system-prompt` built from a constitution file
and a role file.

## Requirements

- Python >= 3.9
- The `herdr` and `claude` CLIs on `PATH`

## Dev setup

```sh
uv venv
uv pip install pytest
```

## Usage

```sh
python herdr-claude-panes.py [config] [workdir] [--force]
```

- `config` — path to the panes config JSON (default: `herdr-panes.json`)
- `workdir` — working directory for the herdr workspace (default: `.`)
- `--force` — launch panes even if prompt files are missing

Prompt files (`constitution` / `role` entries in the config) are looked up in
`<workdir>/.claude/prompts/` and then `~/.claude/prompts/`.

### Config format

See [herdr-panes.json](herdr-panes.json) for an example:

```json
[
  { "pane": 1, "name": "architect", "constitution": "constitution.md", "role": "architect.md" }
]
```
