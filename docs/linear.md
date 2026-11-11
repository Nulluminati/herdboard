# Linear

Linear is optional. It turns on when `linear.api_key_command` is set or `LINEAR_API_KEY` holds a Linear personal API key. Set `linear.enabled = false` to keep it off.

| herdboard | Linear |
|---|---|
| Column | The workflow state of the issue's team |
| Card | Issue |
| Sub-card or checklist item | Sub-issue |
| Tag | Label |
| Type bug | The label `bug` (any letter case) |
| Due date | Due date |
| Card ID (`t7k2`) | Identifier (`ENG-123`) |

## Keep the key in a keyring

Use `api_key_command` to keep a distinct herdboard key in a secret store, outside the environment and config file.

For Fedora with GNOME Keyring:

1. Run this command and paste the key at the prompt:

   ```bash
   secret-tool store --label='herdboard Linear' service herdboard
   ```

2. Add this command under `[linear]` in `~/.config/herdboard/config.toml`:

   ```toml
   [linear]
   api_key_command = "secret-tool lookup service herdboard"
   ```

For macOS Keychain:

1. Run this command and enter the key at the prompt:

   ```bash
   security add-generic-password -s herdboard -a linear -w
   ```

2. Set the lookup command:

   ```toml
   [linear]
   api_key_command = "security find-generic-password -s herdboard -a linear -w"
   ```

For `pass`, set `api_key_command = "pass show linear/herdboard"` under `[linear]`.
`pass` prints the whole entry. Store only the key on one line, or use a script that prints only the key.

A command string uses shell-style word splitting. A list specifies the arguments directly:

```toml
[linear]
api_key_command = ["secret-tool", "lookup", "service", "herdboard"]
```

herdboard runs no shell: pipes and `$VAR` expansion do not work. It expands `~` only in the first word.
The command must print the key to standard output. herdboard removes surrounding whitespace.
The timeout is 30 seconds, which allows time for a keyring unlock prompt.
herdboard runs the command only when it first needs the key. It caches a successful result for the process lifetime.
Commands that do not use Linear do not run it. Failed commands can run again on the next attempt.
Restart herdboard after you rotate the key.

The command wins over `api_key_env`. Without a command, herdboard reads the environment variable named by `api_key_env` (default: `LINEAR_API_KEY`).
Command failures produce an authentication error with exit code 3. Error messages never include standard output.
Do not put the key itself in `config.toml` or command arguments.

## Link a repository to Linear projects

`herdboard link "API Platform" [--label repo:api]` links the current repository board to a Linear project. The repository view then shows every issue of that project. With labels, it shows only the issues that have one of the labels. `link --remove` removes the link. A project can serve several repositories, and a repository can have several projects.

On the board, `c` shows the linked projects. Press enter on a project to mark it for removal. Type a project name, and optional labels separated by commas, to link a project. Enter in the project field moves to the labels. ctrl+s, or enter in the labels field, writes the changes. A label name with a comma needs `herdboard link --label`. A link needs a Linear connection, so an offline board (`--offline`) cannot add one. A removal works offline.

## Pin single Linear issues

A Linear project can hold issues for many repositories, and a team can hold thousands. To show only the issues you work on, pin them one by one to the repository board. The board fetches pinned issues by ID, so a pin costs no team-wide fetch.

- `herdboard pin ENG-123` pins an issue to the current repository board. `--repo BOARD_OR_PATH` names another board. `pin --remove` removes the pin, also offline.
- `herdboard search "login timeout"` lists the open issues of your teams that match. An identifier such as `ENG-123` finds that issue in any team and any state.
- On the board, `I` opens a search. Type words and press enter: Linear allows only 30 searches per minute, so typing does not search. Press enter on a result to pin it. Outside a repository, the board first asks which repository board to pin to.
- `u` on a pinned card removes its pin. `c` lists the pinned issues: press enter on one to mark it for removal.
- `start` on a Linear issue pins it to the board of the repository it starts in. It does not pin an issue that a linked project of that board already shows. When the board cannot tell the repository of an issue (for example in the `mine` view), `s` asks where it runs: a repository board, or no repository. A Linear issue cannot create a new repository (`--new-repo` fails with `usage`).

A pinned issue goes off the board like other done issues, after `linear.done_days`. A canceled issue does not show. The pin stays in the board until you remove it. A pin does not bring the issue's sub-issues: pin each one by itself. The pins live in the `[[linear-issues]]` tables of the board's `board.toml`.

When Linear's GitHub integration attaches a pull request from this repository to an issue, the card shows `PR`.

## Workflow states

- Each state type maps to a column: backlog and triage to Backlog, unstarted to Todo, started to In progress, completed to Done, canceled to Done. `[linear.columns]` changes this. `[linear.state_names]` maps one state by name, for example `"In Review" = "Review"`.
- A move picks the state of the issue's team that maps to the column. A canceled state is used only when no other state matches, so `done` picks the completed state.
- When several states of one team match, herdboard asks once and stores the answer for that team. Without a terminal or with `--json`, the command fails with `ambiguous_state` and lists the states. `--state <name>` gives the answer.

## Offline use

herdboard caches Linear data per workspace and per user. When Linear is not reachable, the board shows the cache and marks it stale. Linear cards are read-only while you are offline. `--offline` on a command uses only the cache.

Completed issues show for `done_days` days (default 14). Archived issues do not show.

Before a write, herdboard fetches the issue again. When a write times out, it checks the result before it reports. When it cannot learn the result, it fails with `linear_unknown`. Check the issue in Linear before you try again.

## Card order

Linear cards follow Linear's manual order, after the local cards of the column. `move --position top|bottom` puts an issue below the lowest or above the highest order value of its team and state.

## promote

`herdboard promote <id> [--team ENG] [--project NAME] [--state NAME]` turns a todo into a Linear issue assigned to you:

- The title stays. Tags become labels when a label with that name exists. The type bug becomes the label `bug`. The due date stays.
- Top-level checklist items of the details and sub-cards become sub-issues. A sub-card cannot be promoted alone (`parent_not_promoted`).
- The issue starts in the state of the todo's column.
- Anything that herdboard cannot convert goes into the description as text.

After Linear confirms every issue, the todo moves to Done, and its card file gets `promoted = "ENG-123"`. The card shows `→ ENG-123`. The todo is not deleted. herdboard records each step first, so a second `promote` after a failure creates only the missing issues.

On the board, press `T` on a todo, or choose "Promote to Linear" in the card menu:

1. Choose a team. The form lists every team that your API key can see. No team is chosen at the start.
2. Choose a project of that team, or "No project". The board's linked project is not chosen for you, and its labels are not added. Projects with the same name show their teams and ID.
3. Press ctrl+s. Escape closes the form and creates nothing.

When the column matches more than one workflow state, the state dialog asks, as for a move. Escape there cancels the promotion. The board refuses Linear cards, sub-cards, archived todos, and a todo that has a worktree, or a sub-card with one: finish that card first. After a failure, press `T` on the todo again. herdboard finishes the recorded promotion. Another team or project on that second try is ignored, with a warning.
