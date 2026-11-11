# Automations

An automation is a task and a schedule. At each due time, herdboard adds a new card to the automation's board and starts an agent on it, as `start` does. Each run is its own card, with its own ID, log, worktree and branch. The agent moves the card to Review. You review, merge and finish it as any other card.

An example: every weekday, look at the repository's open security alerts and merge the Dependabot pull requests that need no change.

```bash
herdboard automation add --title "Merge safe Dependabot PRs" --board acme-api \
  --schedule "every weekday at 07:30" --type chore --tag security --may-merge-prs \
  --body "Read the open security alerts with gh. Merge each Dependabot PR whose checks pass."
herdboard automation timer install
```

## Schedules

Schedules are in local time. Each form takes an optional `at HH:MM`; the default time is 09:00.

| Schedule | Due |
|---|---|
| `every day` | Each day |
| `every weekday` | Monday to Friday |
| `every week on monday, thursday` | Those days. Names can be short (`mon`), and `and` also separates them |
| `every month on the 1st` | That day of each month. A month without the day (the 31st in April) uses its last day |
| `every N days`, `every N weeks` | Every N days (up to 365) or weeks (up to 52), counted from the day the automation was added |
| `every week` | Each week, on the weekday the automation was added |

A due time in the hour that daylight saving time skips runs one hour later. A due time in the hour that repeats runs once, the first time.

## The tick and the timer

`herdboard automation tick` does the work. For each automation that is on, it finds the last due time. When that time is new, it spawns one card and starts its agent. A tick never runs an automation twice for one due time, and a second tick that starts while one runs does nothing.

`herdboard automation timer install` sets up the OS scheduler to run the tick every 5 minutes, also when no board is open:

- Linux: a systemd user timer, `~/.config/systemd/user/herdboard-automations.timer`, and its service. `journalctl --user -u herdboard-automations` shows the output.
- macOS: a launchd agent, `~/Library/LaunchAgents/com.nulluminati.herdboard-automations.plist`. The output goes to `~/.local/state/herdboard/automations.log`. macOS shows a "Background item added" notice once.

The timer files hold absolute paths: the `herdboard` command, the `herdr` binary, the config file, `XDG_CONFIG_HOME` and `XDG_STATE_HOME` when they are set, and a `PATH` with the folders of `herdr`, `gh`, `git`, `uv`, `claude`, `pi` and `codex`. Run `timer install` again after one of them moves; it writes the files again. `timer status` shows whether the timer runs, and `timer remove` removes it. `herdboard doctor` warns when automations are on and the timer does not run.

## What a run does

- The card gets the automation's title after `Automation: `, details, type and tags, and a copy of every attachment of the automation. A `plan.md` attachment becomes the plan in the agent's brief.
- The board shows `↻` (or a Nerd Font repeat icon) after the state icon of a card whose title starts with `Automation: `.
- The card's log says which automation spawned it, and for which due time.
- An automation on the `inbox` board starts its cards without a repository, as `start --no-repo` does. On any other board, the board must name a repository: herdboard refuses a board without one, and `doctor` reports `automation_board_no_repo` for a saved one.
- The agent starts exactly as a manual `start` does: same permission mode, no extra allowed tools. When it waits at a prompt, the card shows a red `×`. herdboard shows a Herdr notification for each run.
- A run starts even when the card of the last run is not done.
- After sleep or power-off, the next tick spawns one card for the latest missed due time, and logs how many it skipped.
- When the start fails, the card stays in (or goes back to) its first column, its log says `Auto start failed: <reason>`, and herdboard shows a notification. No later tick retries it. Start the card by hand.
- A resumed automation, or one with a changed schedule, waits for its next due time. It does not catch up.

## Merge instruction

By default the agent follows the usual rules: it does not push or merge. With `--may-merge-prs`, or the form's "Tell the agent it may merge other PRs" checkbox, its brief also tells it that it may run `gh pr merge` on other pull requests whose checks pass and that need no code change. It logs each pull request it merged or left, and why. It still never pushes or merges its own card branch.

This is an instruction in the brief only. herdboard does not change the agent's tools or permissions, so the agent still asks before it runs `gh pr merge` when its permission mode asks for that command.

## Factory runs

With `--factory`, or the form's "Run as a factory" checkbox, each spawned card starts as a [factory run](factory-runs.md): lens reviewers, builder fixes and an approver's verdict. The automation's `plan.md` is copied to each card, so its `Review lenses:` line and its verification contract apply. The planner of a factory automation writes both. herdboard saves a factory automation without a plan, so that its planner can write one. A run whose plan has no valid contract adds no card, and its last result is `plan_invalid`. `doctor` reports such an automation as `automation_plan_invalid`. Default runs use `factory_max_rounds`. Add `--factory-preset cheap`, or choose a preset in the form, to use a named run. The definition stores `factory_preset = "cheap"`. A preset needs `factory = true` and cannot combine with `agent`, `model` or `thinking`. If the preset no longer exists, the run logs `start_failed`. `--no-factory` turns factory mode off and clears the automation's preset. Use `--factory-preset ''` to clear only the preset.

A factory automation needs a repository board: herdboard refuses it on `inbox`. Each run can start up to four reviewers in each round, and an approver, so it costs more than a plain run. `--factory` and `--may-merge-prs` work together.

## Plan an automation

`herdboard automation plan <id>`, or `P` in the Automations tab, starts a planner, as `plan` does for a card. For a repository board, it runs in a temporary worktree on the branch `auto/<id>-plan`, from the main checkout's branch. For an inbox automation, it runs in `.herdboard/work/<id>/`. The planner writes `plan.md` to the automation's attachments, so each run gets the plan. When the planner ends, herdboard removes the temporary worktree and branch if they are clean, and logs that it kept them if not. A second `plan` revises the plan.

## The Automations tab

The tab lists each automation: on or paused, ID, title, board, schedule, next run, and last run with its card and result.

When at least one automation is on and the timer is not active, the status line says that automations do not run on their own and gives the command that installs the timer. A status error, such as an unsupported platform, shows the same way. The tab checks the timer once when it opens and again when you come back to it, not on every reload.

| Key | Action |
|---|---|
| `enter` | Details: the fields, attachments and last result. `o` opens an attachment |
| `a` / `e` | Add or edit an automation. The form checks the schedule. The Model and Thinking fields offer the choices of the selected agent; "default" is `start_agent` |
| `P` | Plan the automation with an agent |
| `space` | Pause or resume |
| `n` | Run now: spawn and start one card, after you confirm |
| `i` | Install the automations timer, after you confirm. The key is dim when the timer runs |
| `x` | Remove the automation, after you confirm. Its cards stay |
| `r` | Read the automations again. The tab also reads them every 30 seconds |
| `escape`, `G` | Back to the board |

Limits:

- Automations are herdboard data in `.herdboard/automations.toml`. The spawned cards are normal board cards.
- Spawned cards are todos. An automation cannot target a Linear issue or spawn a sub-card.
- herdboard does not review, merge or finish a spawned card, and does not limit how many runs of one automation are open.
- A repository board needs a known checkout (`checkouts.json`). A run without one fails with `checkout_unknown`; run any herdboard command in the repository once.
