# Configuration

The config file is `~/.config/herdboard/config.toml`. `HERDBOARD_CONFIG` or `--config` names another file. Every setting has a default, so the file is optional.

```toml
todos_dir = "~/todos"
projects_dir = "~/Projects"   # where `start --new-repo` creates a repository
columns = ["Backlog", "Todo", "In progress", "Review", "Done"]   # for new boards
start_agent = "claude"     # or "pi" or "codex"
# start_model = "openai-codex/gpt-6.1-sol"   # default: the agent's own default
# start_thinking = "medium"                  # pi uses it when the model has no [thinking] row
mockup_model = "gpt-6.1-sol"                 # the Codex model that `mockup` makes images with
# pi_models = ["zai/glm-5.3"]                # the board's pi model list; default: pi's enabledModels
# codex_models = ["gpt-5.2-codex"]           # default: visible models in ~/.codex/models_cache.json
# start_column = "In progress"               # default: linear.columns.started
merge = "local"            # or "pr"; a board's `merge` in board.toml wins
theme = "ansi-dark"        # the terminal's own colors; "ansi-light" or any Textual theme name
tag_style = "outline"      # tag text on a tint of its color; "round" (Nerd Font ends) or "block"
card_style = "full"        # cards with a border and a detail line; "compact" without both
icon_style = "plain"       # text labels; "nerd" adds Nerd Font icons
types = ["bug", "feature", "chore", "docs", "refactor"]   # card types: the `type` field of a card
details_pane = true        # a card details pane on top of each card agent and planner
details_pane_ratio = 0.25  # its share of the agent pane's height, from 0.1 to 0.6
factory_max_rounds = 3     # the most review rounds of a factory run, from 1 to 10

[factory]
# approver = "pi"          # default: the card reviewer of the builder's agent

[factory.lenses]           # the reviewer of each lens; model and thinking are optional
security = { agent = "codex" }
code = { agent = "pi" }
ux = { agent = "claude" }
ui = { agent = "claude" }   # such as { agent = "claude", model = "opus", thinking = "high" }

# A preset is complete: no roles or round limit fall back to the Default run.
[factory.presets.cheap]
rounds = 2
lenses_on = ["security", "code"]  # optional; absent means the plan decides
builder = { agent = "pi", model = "zai/glm-5.3", thinking = "high" }
approver = { agent = "claude", model = "opus" }

[factory.presets.cheap.lenses]
security = { agent = "codex" }
ux = { agent = "claude", model = "sonnet" }
ui = { agent = "claude", model = "sonnet" }
code = { agent = "pi", model = "zai/glm-5.3", thinking = "medium" }

[thinking]
# "zai/glm-5.3" = "high"   # pi only: the level that herdboard last chose for this model

[linear]
# enabled = true           # default: on when a key source is configured
api_key_env = "LINEAR_API_KEY"
# api_key_command = "secret-tool lookup service herdboard"   # wins over api_key_env
done_days = 14             # completed issues older than this are hidden

[linear.columns]
backlog = "Backlog"
triage = "Backlog"
unstarted = "Todo"
started = "In progress"
completed = "Done"
canceled = "Done"

[linear.state_names]
"In Review" = "Review"
```

To make pull requests the default for one repository, add `merge = "pr"` to its board's `board.toml`, or press `c` on the board and choose `pr`.

`doctor` warns about `complete_markers`, `archive_titles` and `vault_root`. They were settings of the old Markdown boards, and herdboard ignores them. Remove them from the file.

## The configuration dialog

Press `c` to open configuration. It has two tabs. Switch tabs with a click, or focus the tab row with shift+tab and press left or right.

- **Global (all boards)** sets values in the config file: theme, agent, model, thinking level, merge mode, icons, tags, cards and the [details pane](work-on-a-card.md#details-pane). It works outside a repository too.
- **Current board** shows the board name. It sets the board's merge mode, linked Linear projects and pinned issues in the board's `board.toml`. Without a repository board, it tells you how to create one.

The model list is the list that a start offers. Claude offers fable, opus, sonnet and haiku. pi offers `pi_models`, else pi's `enabledModels`. Codex offers `codex_models`, else models with `visibility = "list"` in `~/.codex/models_cache.json`. Its default label reads `model` and `model_reasoning_effort` from `~/.codex/config.toml`.

"Agent default" removes `start_model`, so the agent uses its own default. A saved model outside the list stays as "current configured model". A change of agent resets the model to "Agent default". The thinking control follows the agent's levels.

pi accepts `off`, `minimal`, `low`, `medium`, `high`, `xhigh` and `max`. Codex accepts `low`, `medium`, `high`, `xhigh`, `max` and `ultra`; model support varies. Claude accepts `low`, `medium`, `high`, `xhigh` and `max`, which herdboard passes as `claude --effort`. An explicit invalid level returns a `usage` error. herdboard drops a configured level that the chosen agent does not accept.

The Thinking field follows the selected model. A named model shows its own level, from the `[thinking]` table. With "Agent default" as the model, the field shows `start_thinking`. "Agent default" in the field clears the level of the selected model, so that model uses `start_thinking` again. See [thinking levels](#thinking-levels).

The board's merge option "Global default" shows the global mode. A board without `merge` follows the global mode; a board with `merge` keeps it.

Press `ctrl+s` in either tab to save the changes of both tabs. Press `escape` to cancel without saving. Herdboard saves global changes in the active configuration file, including files selected with `--config` or `HERDBOARD_CONFIG`. They apply at once in this board: the theme, the cards and the next start, plan, review or merge. Other open herdboard processes read the saved values when they start again. A running agent does not change.

The board file and the config file save separately. If the board saves and the config file does not, the dialog says "Board settings saved; global settings not saved" and stays open. Fix the cause and press `ctrl+s` again.

Saves keep a `.<config name>.lock` file beside the configuration file (`.config.toml.lock` by default). Leave it in place; it coordinates concurrent saves.

## Thinking levels

A thinking level is a pi setting: off, minimal, low, medium, high, xhigh or max. herdboard keeps one level for each model in the `[thinking]` table of the config file:

```toml
[thinking]
"zai/glm-5.3" = "high"
"openai-codex/gpt-6.1-sol" = "max"
```

When you choose a thinking level in the model dialog of `S`, `P` or `R`, herdboard saves it for the model that the dialog starts. The dialog shows the saved level of the model under the cursor, until you change the field; after that, your choice stays. So a careful level for one model does not change the level of another model.

A start, plan, agent review or pull request review without `--thinking` uses the saved level of its model. A model without a row in the table uses `start_thinking`, else pi's own `defaultThinkingLevel`. `--thinking` on the command line always wins.

When `start`, `plan` or `review` names no model, herdboard uses `start_model`, else pi's own default model. The dialog's "pi default" row is that same model. So the level always belongs to the model that runs. pi's own default has a name only in its `settings.json`, from `defaultProvider` and `defaultModel`; herdboard saves that model's level under that name.

Remove a row by hand, or press `c` and choose "Agent default" for that model. herdboard keeps the table when it saves other settings.

## Display icons

`icon_style = "plain"` is the default. Dates use a `Due` label, and cards with attachments show `files` at the right edge.

Set `icon_style = "nerd"` to add icons beside text labels on board cards and detail screens. Icons identify default card types, dates, attachments, worktree status and pull requests. Custom types keep their text when no icon exists.

Use a **Nerd Font Mono** font in your terminal for `nerd` mode. Other Nerd Font variants can draw wider icons and disrupt spacing. Herdboard does not detect font support. See the [Nerd Fonts troubleshooting guide](https://github.com/ryanoasis/nerd-fonts/wiki/FAQ-and-Troubleshooting).

To disable these icons, select `plain` in the menu. Alternatively, set `icon_style = "plain"` in the file and restart Herdboard. The separate `tag_style` setting still controls tag shapes. The default `outline` and `block` need no Nerd Font; `round` draws Nerd Font tag ends. Existing structural symbols, such as checklist marks, remain in both modes.

These settings affect display only. Card files, filters and command-line output do not change.
