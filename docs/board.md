# The board

## Board setup

Repository commands create a missing board automatically. On a terminal, `board`, `list`, and `add` ask for the merge method. `local` merges into the base branch. `pr` opens a draft pull request. Press Enter to use the global merge setting.

When Linear is enabled and the command runs online, setup offers an optional Linear project name or identifier. After you select a project, you can enter comma-separated labels to filter its issues. An invalid project or label repeats the project question and keeps your merge choice. Press Enter at the project question to skip linking. Press Control+C to cancel setup before herdboard creates the board.

Other commands, commands with `--json`, and commands without an interactive terminal create the board with global defaults and no Linear links. They do not ask questions. Open the board and press `c` to change these settings later. Existing boards keep their settings. If another process creates the board during setup, herdboard reports that your setup answers did not apply. Outside a Git repository, commands continue to use the inbox. `herdboard init` remains available for explicit creation. Migration creates its target board after confirmation; previews write no files. `doctor` only checks files unless you request repairs.

The top row shows `herdboard`, the board names and the Linear state at the left, and the view and the herdboard version at the right. Under it are four tabs: **Board**, **Pull requests**, **Notes** and **Automations**. Each tab is as wide as the widest label plus its box, so no label is cut, and its icon and label sit in the middle of its box. `G` goes to the next tab, and from Automations back to the board. The right end of the tab row shows a yellow `G next tab`, outside the tabs, so the tabs never change size when the tab that `G` goes to changes. A click on a tab opens it. The Pull requests tab shows the open PR count after the list reads GitHub. A search does not change the count. The bottom row shows the keys of the current tab as keycaps. It wraps between two keys when they do not fit. A click on a key presses it. A dialog, such as the card detail, shows its own keys there. A key that has nothing to act on is dimmed: for example Merge on a card without a worktree, Check on a card without a checklist, or Go on a PR without a local review. A dimmed key still runs and says why it did nothing.

Each column takes a color in turn: blue, magenta, yellow, cyan and green. The column's scrollbar has its color too. The done column is always green with a `✓`, and the start column has a `●`. The current column has a heavy border and an underlined header. The selected card has a heavy border in the text color.

A card shows, from top to bottom:

- A state icon (`○` not started, yellow `●` a worktree or an agent works on it, green `✓` in the done column), then the plan and review markers, then the card ID at the right. While the work agent's pane lives, the state icon is the agent's Herdr state instead (see [Agent states](#agent-states)). The done column always shows the green `✓`. A Linear card shows `◆` and its identifier.
- The title.
- The first detail line that is not a checklist item, in at most two rows. Cards in the done column strike the title and this line through.
- The type and the tags.
- The sub-card count (`2/5 done`) at the left and the due date at the right.
- The other markers below, when the card has any.

A card that is too narrow for its plan and review markers cuts them with `…`. The ID stays whole.

Set `card_style = "compact"` for cards without a border and without the detail line. A compact card has the state icon, the title, the plan and review markers and the ID in one row.

| Key | Action |
|---|---|
| `h` `j` `k` `l` or the arrow keys | Select a column or a card |
| `H` / `L` (or shift+left / shift+right) | Move the card to the previous or next column |
| `K` / `J` (or shift+up / shift+down) | Move a todo up or down in its column |
| `/` | Filter. Words match the title, tags and details. `#tag` matches a tag, and `#type/bug` a type. `^t5aa` shows `t5aa` and its sub-cards. Escape clears the filter |
| enter | Card detail, with the attachments and the last 10 log entries. In the detail, `o` opens an attachment |
| `a` | Add a card to the selected column |
| `e` | Edit the todo: title, type, tags, due date and details. ctrl+s saves |
| `d` | Mark the card done |
| `b` | Move the todo to another board, for example from the inbox to this repository |
| `x` | Delete the todo, after you confirm |
| `A` | Archive the todo. In the archive column, move it back to the done column |
| `D` | Archive every card in the done column, after you confirm |
| `z` | Show or hide the archive column |
| `T` | Promote the todo to a Linear issue: choose its team and project. See [promote](linear.md#promote) |
| `p` | Set or remove the todo's parent |
| `s` | Start work with the default agent. A card without a repository asks where it runs |
| `S` | Choose claude, pi or codex, the model and the thinking level, then start work. Each pi model keeps the thinking level that you chose for it |
| `P` | Plan the card: choose claude, pi or codex and the model |
| `g` | Go to the started card's Herdr workspace, when Herdr has it open |
| `R` | Review a started card: in Hunk, by another agent, or both. A repoless card offers the agent review only |
| `m` | Merge the card, after you confirm. A repoless card has nothing to merge |
| `f` | Finish a merged card, after you confirm |
| `v` | Change the view: repo, inbox, all, mine |
| `t` | Hide or show Linear cards |
| `i` | Create the board for this repository |
| `I` | Search Linear and pin an issue to this repository's board. The search runs when you press enter |
| `u` | Remove the pin of a pinned Linear issue (repo view) |
| `c` | Configure the global settings of all boards, and this board's merge mode, linked Linear projects and pinned issues. ctrl+s saves both tabs |
| `r` | Reload, and fetch Linear again |
| `G` | Go to the next tab: the list of the repository's open GitHub pull requests (see [Pull request reviews](pull-request-reviews.md)), then the [notes](notes.md) and the [automations](automations.md) |
| `?` | Help |
| `q` | Quit |

## Mouse

The keys stay the main input. Each mouse action runs an action that a key also runs.

| Mouse | Action |
|---|---|
| Click a card | Select the card |
| Click a column header, or the empty part of a column | Select the column |
| Double-click a card | Card detail (enter) |
| Right-click a card | A menu of the actions that apply to the card |
| Drag a card to another column | Move the card to the bottom of that column (`H` / `L`) |
| Click a checklist item in the card detail | Check or clear the item (space) |
| Click an attachment in the card detail | Open the attachment (`o`) |
| Wheel | Scroll a column, or the columns |

- Herdr keeps right-click for its own menu. To send right-clicks to the board, turn on "send right clicks to pane" in Herdr's right-click menu. Without it, use the keys of the actions.
- The menu uses only what the board knows, such as a worktree that exists. An action still makes its own checks, so it can refuse with its usual notice.
- A drop always puts the card at the bottom of the column. Use `K` / `J` to change the order.
- The wheel only scrolls. It does not change the selected card.

## Views

| View | Shows |
|---|---|
| repo (default inside a repository) | The repository's todos, the issues of its linked Linear projects and its pinned Linear issues |
| inbox (default outside a repository) | The `inbox` board: todos that belong to no repository |
| all | Every board and your Linear issues |
| mine | Linear issues assigned to you, from every team |
| project (`--view project --project NAME`) | One Linear project's issues and the todos of every repository linked to it |

In a view with several boards, columns with the same name merge. Each card keeps its own board, so a move writes to the correct board.

## Triage

Triage is the column where a new report lands before you sort it. Agents use it to file harness problems and project bugs.

- Triage is the first column of the board. It does not show while it has no cards: herdboard hides it, then shows it again as soon as a card lands there.
- A plain `add` skips Triage. The card goes to the first column that is not Triage, normally Backlog.
- `herdboard add "Report" --column Triage` and `herdboard move <id> Triage` file the card in Triage, and a board without the column gets it first. `H`/`L` moves a card into Triage while the column shows, which is while it has cards. Any other unknown column name still fails with `not_found`.
- A card moved to another board with `b` keeps its column name. A card that leaves Triage lands in the Triage column of the new board, which gets one when it has none.
- New boards do not get a Triage column. It appears the first time a card needs it.
- The Linear state type `triage` still maps to Backlog. A Linear issue cannot move to a column without a state.

## Card types

A card can have one type, such as bug or feature. The type is the `type` field of the card file.

- `herdboard add "Fix login timeout" --type bug` adds a card with the type bug. `edit <id> --type feature` changes the type, and `--no-type` removes it.
- On the board, the add and edit forms have a Type field. The card shows the type before its tags. Bug is red, feature green, docs cyan and refactor magenta.
- The `types` setting lists the allowed types. The default is bug, feature, chore, docs and refactor. herdboard refuses another type with `unknown_type`. A type that you write in a card file yourself always counts.
- JSON output has the type in `type`, apart from `tags`.
- `start` puts the conventional commit type in front of the branch name: `fix/t3m9-fix-login-timeout` for a bug, `feat/` for a feature. Other types use their own name, such as `chore/`. A Linear issue keeps its own branch name.
- The agent brief names the type and its commit type. The pull request title uses that commit type.
- A Linear issue's type is its first label that names a type, in any letter case. `Bug` is the type bug. `add --linear --type bug` and `promote` of a todo with the type bug add the label `bug` of the issue's team, else the workspace label `bug`. Without such a label, `add --linear` creates no issue.

## Archive

The archive keeps old todos off the board. An archived card's folder moves from `cards/` to `archive/` in the board folder, and its card file gets an `archived` time.

- `A`, or `herdboard archive <id>`, moves a todo to the archive. `L` on the last column does the same when the archive column shows.
- `D`, or `herdboard archive --done`, archives every card in the done column. In a view with several boards, `D` archives the done column of each board, and skips a board without one. In a repository without a board, `archive --done` needs `--board inbox` to archive the inbox.
- `z` shows the archive column at the end of the board. The board hides it again on the next `z`. `a` does not add cards to the archive column.
- `A` on an archived card, or `herdboard unarchive <id>`, moves it back to the done column.
- A sub-card whose parent is archived too brings its parent back with it. The board asks first. The command asks in a terminal, and needs `--yes` without one.

herdboard does not archive a card whose worktree still exists, or whose agent or planner still runs. `finish` the card, or close the planner tab, first. A parent whose sub-cards stay on the board does not archive either. `archive --done` keeps these cards in the done column and reports why.

An archived card keeps its ID, its log and its attachments. `show` and `log` work on it. Other commands, such as `start`, `plan`, `review`, `merge` and `attach`, refuse it with `archived` before they change anything. Linear issues are not archived here.

## Card markers

The markers after the state icon are the plan and review markers:

| Marker | Meaning |
|---|---|
| `✎ ◐ pi` | The card's planner runs: the planning icon, the planner's Herdr state and its agent. The card keeps its current column. It goes away when the planner pane closes |
| `▤` | The card has a plan (`plan.md` attachment) and no planner runs. It stays until the plan is removed, and does not show in the done column |
| `⌕ ◐ claude` | An agent review runs: the reviewing icon, the reviewer's Herdr state and its agent |
| `✔` | The agent review findings are ready, and the branch has no commits since that review |
| `↑` | The branch has new commits since the agent review. A new agent review replaces it |
| `⠋ starting` | The board runs an action on the card: a spinner and the action, such as `starting`, `planning`, `reviewing`, `merging` or `writing`. Another action on the card, or on its parent, waits with a Busy notice until it ends. Other cards stay free |

The markers below the card are:

| Marker | Meaning |
|---|---|
| `↳ <parent>` | A sub-card. For a Linear sub-issue whose parent is not in the view, the marker shows the parent's identifier, such as `↳ ENG-12` |
| `2/5 done` | A parent card and the progress of its sub-cards |
| `≡` (top-right corner) | The card has attachments. Open the card detail to see them. With `icon_style = "nerd"`, a paperclip icon alone |
| `PR: writing` | An agent writes the pull request description. The writer's Herdr state follows, such as `PR: writing ◐` |
| `PR open`, `PR merged`, `PR closed` | The state of the card's pull request. The board reads it at most once a minute |
| `worktree removed` | The card's worktree folder is gone |
| `worktree still exists` | The card is in Done, but its worktree is still there. Run `finish` |

The board checks planner panes every two seconds. If Herdr cannot answer, the marker keeps the recorded planner type. A missing or unreadable planning state file hides only the planning markers, not the cards.

The board checks the attachments folder at the same interval. A folder that cannot be read hides only the `≡` markers.

## Agent states

The board shows the state of each agent on a card with the glyphs and colors of the Herdr sidebar (Herdr's `symbols` status indicators). The work agent's state replaces the state icon. The planner, the agent reviewer and the pull request writer each show their state in their status marker.

| Glyph | Agent state |
|---|---|
| yellow `◐` | working |
| red `×` | blocked: it waits for you, such as for a permission |
| cyan `✓` | done: it finished, and you did not focus its pane yet. Herdr shows teal; the terminal palette has no teal |
| green `○` | idle |
| dim `·` | Herdr does not know the state |

The board reads all agent states with one `herdr agent list` call at each check, every two seconds. A board with no agent panes does not call Herdr. When Herdr cannot answer, the board shows no agent glyphs: started cards show `●` and the other markers keep their words. The glyphs are the same for both `icon_style` values.

With `icon_style = "nerd"`, the phase icons are Nerd Font glyphs: a pencil (planning), a checked box (planned), a magnifier (reviewing), a check in a circle (reviewed) and an up arrow (new commits). The card detail gives each state in words, such as `Agent  ◐ claude: working`. The help screen (`?`) lists every glyph.

To find "reviewed", herdboard saves the branch HEAD when an agent review starts, and keeps it when the findings are ready. A failed review saves nothing.
