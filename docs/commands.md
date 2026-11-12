# Commands

| Command | Action |
|---|---|
| `herdboard board [--view NAME] [--project NAME]` | Open the board |
| `herdboard list [--view] [--project NAME] [--board] [--column] [--source todo\|linear] [--archived]` | List cards. `--archived` lists the archived todos |
| `herdboard add "title" [--body TEXT \| --body-file PATH] [--type NAME] [--tag NAME]... [--due YYYY-MM-DD] [--board] [--column] [--position top\|bottom] [--parent ID]` | Add a todo. Default board: the parent's board, else the repository board, else the inbox |
| `herdboard add --linear "title" [--body TEXT \| --body-file PATH] [--type NAME] [--team] [--project] [--label] [--column] [--state]` | Create a Linear issue assigned to you. In a repository with one linked project, that project and its labels are the default |
| `herdboard show <id> [--log]` | Show a card, its attachments and its last 10 log entries. `--log` shows them all |
| `herdboard move <id> <column> [--position top\|bottom] [--state]` | Move a card to a column |
| `herdboard move <id> --up\|--down` | Move a todo up or down in its column |
| `herdboard move <id> [column] --board NAME` | Move a todo, with its card folder, to another board. A started card cannot move |
| `herdboard done <id> [--state]` | Move a card to its board's done column |
| `herdboard edit <id> [--title] [--body \| --body-file] [--tag NAME... \| --no-tags] [--due YYYY-MM-DD \| --no-due] [--parent ID \| --no-parent] [--type NAME \| --no-type]` | Change a todo's title, details, tags, due date, parent or type. `--tag` replaces the tags. `--body ""` removes the details |
| `herdboard log <id> "text"` | Add an entry to the card's activity log |
| `herdboard attach <id> FILE [--name NAME]` / `attach <id> --remove NAME` | Add a file to the card's attachments, or remove one |
| `herdboard mockup <id> PROMPT... [--image FILE]... [--quality Q] [--no-show]` | Make UI mockup drafts with Codex, one per prompt (four at most), and show them in a pane |
| `herdboard details <id>` / `details --open [<id>] [--pane ID]` | Show the card's compact status, the view of the [details pane](work-on-a-card.md#details-pane); or open that pane in Herdr |
| `herdboard plan <id> [--agent claude\|pi\|codex] [--model] [--thinking] [--repo] [--no-repo] [--new-repo [PATH]] [--checkout PATH] [--base BRANCH]` | Plan the card with an agent in a tab in its worktree, or in its card folder when it has no repository |
| `herdboard sidebar-refresh` | Report the Herdr sidebar tokens of the started cards again. Herdr runs it at startup and when it finds an agent |
| `herdboard delete <id> [--yes]` | Delete a todo: its card folder, with its log and attachments. A started card cannot be deleted |
| `herdboard archive <id>` / `archive --done [--board NAME]` | Move a todo to its board's archive, or every card in the done column |
| `herdboard unarchive <id> [--yes]` | Move an archived todo back to its board's done column. `--yes` also moves an archived parent back without a question |
| `herdboard start <id> [--agent claude\|pi\|codex] [--model] [--thinking] [--no-agent] [--repo] [--no-repo] [--new-repo [PATH]] [--checkout PATH] [--base BRANCH] [--factory [--rounds N \| --preset NAME]]` | Start work on a card. Without a repository: `--no-repo` runs it in a card folder, `--new-repo` creates a repository first. `--factory` starts a [factory run](factory-runs.md) |
| `herdboard factory <id> [--stop]` | Show a card's factory run, or stop it |
| `herdboard review <id> [--human \| --agent \| --both] [--reviewer claude\|pi\|codex] [--model] [--thinking]` | Review a started card's work |
| `herdboard merge <id> [--local \| --pr] [--rewrite] [--force]` | Merge the card branch, or open a draft pull request |
| `herdboard pr-sync <id> [--fetch]` | Push the card branch, then replace the open pull request's title and description with `pr.md`. `--fetch` writes the GitHub text to a new `pr.md` instead, and changes nothing |
| `herdboard finish <id> [--force]` | Remove a merged card's worktree and branch, and move it to Done |
| `herdboard board --prs` | Open the board on its pull request list |
| `herdboard prs [--search TEXT] [--page N]` | List the open GitHub pull requests of the repository, 50 to a page, with review markers. `--search` takes GitHub search words and qualifiers |
| `herdboard pr-review <N> [--agent claude\|pi\|codex] [--model] [--thinking]` | Have an agent review PR `N` in its own workspace, with notes in Hunk. The defaults are `start_agent` and `start_model` |
| `herdboard pr-review-refresh <N>` | Fetch the PR's new commits, and open Hunk again with the old notes |
| `herdboard pr-review-go <N>` | Go to the PR's review workspace |
| `herdboard pr-review-finish <N> [--force]` | Close the review: the workspace, the worktree and `pr/<N>`. `--force` also drops your unsent notes and worktree changes |
| `herdboard promote <id> [--team] [--project] [--state]` | Turn a todo into a Linear issue |
| `herdboard link <project> [--label NAME] [--remove]` | Link the repository board to a Linear project |
| `herdboard pin <ENG-123> [--repo BOARD\|PATH] [--remove]` | Pin a Linear issue to a repository board, or remove the pin |
| `herdboard search <term>` | List the open Linear issues of your teams that match, or one issue by identifier |
| `herdboard init` | Create the board for the current repository |
| `herdboard migrate <TODO.md> [--board] [--yes]` | Convert a free-form `TODO.md` into cards |
| `herdboard doctor [--fix] [--offline]` | Check the boards, the config, Linear, the automations and the state files |
| `herdboard update` | Install the latest herdboard release, for the Herdr plugin and the `herdboard` command. Only a GitHub install updates; in a linked clone, run `git pull` |
| `herdboard convert-store [--dry-run]` | Convert the old Markdown boards to board folders, once. See [Convert old boards](files.md#convert-old-boards) |
| `herdboard automation list` | List the automations, with the next due time and the last run |
| `herdboard automation add --title T --schedule S [--board] [--body \| --body-file] [--type] [--tag ...] [--agent] [--model] [--thinking] [--may-merge-prs] [--factory [--factory-preset NAME]]` | Add an automation. Default board: `inbox`. `--agent` is claude, pi or codex; `--thinking` takes the agent's levels |
| `herdboard automation edit <aid> [the add options] [--no-merge-prs] [--no-factory]` | Change an automation. `--tag` replaces the tags; an empty `--type`, `--agent`, `--model`, `--thinking` or `--factory-preset` clears it |
| `herdboard automation remove <aid> [--yes]` | Remove an automation. Its cards stay |
| `herdboard automation pause\|resume <aid>` | Stop or restart the scheduled runs |
| `herdboard automation run <aid>` | Spawn and start one card now |
| `herdboard automation plan <aid> [--agent] [--model] [--thinking]` | Plan the automation with an agent |
| `herdboard automation attach <aid> FILE [--name]` / `attach <aid> --remove NAME` | Add or remove an automation attachment |
| `herdboard automation tick` | Spawn and start the due runs (the timer runs it) |
| `herdboard automation timer install\|remove\|status` | Set up, remove or check the timer that runs the tick |

- `<id>` is a todo ID (`t7k2`) or a Linear identifier (`ENG-123`). `<aid>` is an automation ID (`a7k2`).
- Every command takes `--json`, `--config FILE` and `-C DIR` (run as if in `DIR`).
- With `--json`, output goes to standard output as JSON. An error has the form `{"error": {"code": "…", "message": "…"}}`. The skill lists the error codes.
- Exit codes: 0 success, 1 user error, 2 conflict (the card changed, the lock is held, a rebase conflict), 3 Linear error.
- A command that asks a question in a terminal fails without a terminal or with `--json`. `delete --yes` and `migrate --yes` confirm without a question.

## Add card details

Use `add --body TEXT` to set details when you create a todo. Use `--body-file PATH` to read the details from a UTF-8 file. Do not use both options. Relative file paths start from the command directory (`-C`, if set).

```bash
herdboard add "Fix login timeout" --body "Check the retry limit"
herdboard add "Fix login timeout" --body-file docs/login.md
herdboard add --linear "Fix login timeout" --team ENG --body-file docs/login.md
```

With `--linear`, the body becomes the issue description. Started agents can create cards with details. They still cannot edit existing card titles or details.

## migrate

`herdboard migrate TODO.md` converts a free-form todo file. It reads Markdown and underlined headings, a plain line that ends with `:`, all common bullets, checkboxes, and tab or space indents.

- Each top-level item of a section becomes a card. Its deeper items become the card details.
- The section name becomes a tag: `Follow Ups:` becomes the tag `follow-ups`.
- A line that ends with `:` is a heading when a list item or a code fence comes after it before the next heading. Paragraph text between them does not change this. Otherwise the line is text.
- Text before the first card of a section becomes a card, as it does under a `#` heading.
- Open items go into the first column. Checked items go into the done column.
- A code fence stays in the details of the card above it. A fence before the first card of a section makes no card: the preview lists its lines as `skipped`.

herdboard shows the result and asks before it writes. The original file does not change.

## doctor

`herdboard doctor` reports problems with a level, a code and a fix when there is one. It checks:

- Boards and card files that do not parse, duplicate card IDs, and two boards with the same repository
- Cards that `board.toml` lists twice or does not list, listed cards without a folder, and the done column
- Old Markdown boards that `convert-store` did not convert yet, and config keys that herdboard no longer reads
- The config file, and Linear links, labels, pinned issues and the API key
- Sub-cards whose parent is missing
- Automations whose runs fail: a bad schedule, a missing board, a board without a repository, or a factory automation without a valid `herdboard-verification` block
- Unfinished `promote` records, old start records and old checkout paths
- Whether `herdr` and `gh` are on the path
- Whether `hunk` is on the path and has the `hunk-gh-review` extension. These are warnings: the board works without them

`--fix` repairs the card lists of `board.toml`: it removes a duplicate entry and an entry without a card folder, and adds a card folder that no column lists to the first column. `--offline` skips the Linear checks. `doctor` never changes Linear.
