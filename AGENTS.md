# AGENTS.md

herdboard: a kanban board inside Herdr for local todos and Linear issues, and a Herdr plugin that starts, reviews and merges card work with Claude Code, pi and Codex.

## Layout

```
herdr-plugin.toml          # Herdr manifest; id is "nulluminati.herdboard"
pyproject.toml, uv.lock    # the herdboard package and its dev tools
src/herdboard/             # the package
bin/                       # scripts that the manifest commands run
skills/herdboard/SKILL.md  # agent skill, installed with the skills CLI
docs/                      # design notes and live test checklists
tests/unit/                # tests with no Textual pilot
tests/ui/                  # Textual pilot tests (run_test)
tests/repo/                # tests of repository files, such as CI and Dependabot
tests/fixtures/            # test data
tests/support/             # shared helpers and base test cases; test modules import only from here
```

## How the plugin runs

- Herdr runs action commands from the repository root, which is the plugin root. Use paths relative to it, such as `bin/open_board.py`.
- Commands receive context in `HERDR_PLUGIN_CONTEXT_JSON`, `HERDR_PLUGIN_STATE_DIR`, `HERDR_PLUGIN_CONFIG_DIR`, `HERDR_PANE_ID` and `HERDR_BIN_PATH`.
- Drive Herdr through its CLI (`herdr agent ...`, `herdr pane ...`). The installed binary is the authority for syntax: run `herdr <group>` to list commands.
- herdboard is installed with `uv tool install` and declares its dependencies in `pyproject.toml`. Keep its core modules importable without them. Scripts in `bin/` use the Python 3.11 standard library only.

## Testing

```bash
uv run pytest -n auto              # full suite
uv run pytest -n auto tests/unit   # fast tests only
uv run ruff check .
uv run ruff format .
uv lock --check
uv run pre-commit install          # once per clone: ruff before each commit
```

- Tests load a `bin/` script with `load_script` from `tests/support/scripts.py` and replace `command` with a fake, so no test calls the real `herdr`.
- Unit tests do not catch Herdr or agent behavior. After a change to how herdboard drives Herdr, test it live in a Herdr pane with a throwaway Git repository.

## Gotchas

- Do not type prompts into a new agent pane. Text can land in a startup prompt, such as Claude's or Codex's folder trust check. Pass the first message on the agent's command line.
- `herdr agent start` can report `agent_not_ready` or `timeout` for an agent that works: one blocked at a startup prompt, or one busy with its first message.
- Claude's `--allowedTools` takes every value after it. Put a positional prompt before it.
- The user's machine is linked to this checkout with `herdr plugin link`, so edits are live.
- Claude's and pi's reviewer sandbox writes the working directory unless `denyWrite` names it. Name the repository there.
- `terminal-browser` splits panes through the Herdr socket, so it must run outside a reviewer sandbox. Claude and pi exclude it with `excludedCommands`. Codex runs it outside with a rule in `~/.codex/rules/`, not by allowing the socket: with the socket allowed, `herdr pane run` lets any command escape the sandbox.
- The reviewer sandbox options live in `src/herdboard/sandbox.py`. The peer-review plugin in `Nulluminati/herdr-extensions` keeps a hand copy in `plugins/peer-review/bin/peer_review.py`. No test checks that the two match, so change both.
