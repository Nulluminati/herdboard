# Board files

```
~/todos/                            # todos_dir
  boards/
    inbox/                          # todos that belong to no repository
    acme-api/                       # one board per repository
      board.toml                    # the settings, the columns and the card order
      notes.md                      # the board's note
      cards/
        t3m9/                       # one folder per card; the folder name is the card ID
          card.md                   # the title, fields and details
          log.md                    # the activity log
          attachments/              # the attachments, such as plan.md
      archive/
        t2a6/                       # an archived card, with the same files
  .herdboard/automations.toml       # the automations
  .herdboard/automations/<aid>/     # an automation's log.md and attachments/
  .herdboard/linear/<ENG-123>/      # a Linear card's log.md and attachments/
  .herdboard/work/<id>/             # the folder of a card without a repository; deleted at `finish`
  .herdboard.lock                   # the store lock
```

`board.toml` holds the board settings and the columns. Only `board.toml` says which column holds a card, and in which order:

```toml
format = 1
repo = "github.com/acme/api"
merge = "pr"

[[linear-projects]]
id = "p-plat"
name = "Platform"

[[column]]
name = "Backlog"
cards = ["t3m9"]

[[column]]
name = "Todo"
limit = 5
cards = ["t7k2", "t4b1"]

[[column]]
name = "Done"
done = true
cards = ["t2a6"]
```

- `format` is the version of the store format.
- `repo` and `merge` are optional. `[[linear-projects]]` and `[[linear-issues]]` hold the linked Linear projects and the pinned issues.
- Each `[[column]]` has a `name`, an optional card `limit`, and the IDs of its cards in order. At most one column has `done = true`. Without it, a column named Done is the done column. A move into the done column checks the card, and a move out clears it.

`card.md` is TOML frontmatter between `+++` lines, then the details as plain Markdown:

```markdown
+++
title = "Add invoice table"
type = "feature"
tags = ["billing"]
due = 2026-10-20
parent = "t5aa"
created = 2026-10-12T14:03:00-07:00
+++

Ask finance for the columns.

- [ ] Draft the schema
- [ ] Add the migration
```

- `title` is the only field that a card must have.
- `type`, `tags` and `due` are the card's type, tags and due date.
- `parent` makes the card a sub-card of another card on the same board. Sub-cards go one level deep.
- `promoted` is the Linear identifier after `promote`. `archived` is the time of the archive. `created` is the time of the add. Both times need a UTC offset, such as `2026-11-15T09:30:00+01:00`.
- A top-level `- [ ]` line of the details is a checklist item.
- IDs are unique across all boards, in `cards/` and `archive/`.
- herdboard keeps keys and comments of `board.toml` and `card.md` that it does not know.

## Convert old boards

Earlier versions of herdboard kept boards as Markdown files in the Obsidian Kanban format: `inbox.md` and `projects/<name>.md`, with logs in `.herdboard/log/` and attachments in `.herdboard/attachments/`. `herdboard convert-store` converts them to board folders, once. Other commands refuse the old files with `old_format`.

- `--dry-run` reports what the conversion does, and writes nothing.
- The command builds the new boards in `boards.tmp/` and copies the old files to `~/.local/state/herdboard/backup-<time>/`. Then it renames `boards.tmp/` to `boards/` and removes the old files. A failure before the rename leaves the old files as they were. The command stops when `boards/` already exists.
- Cards without an ID, or with an ID that another card already has, get a new ID. Their sub-cards follow the new ID. The report lists them. The log and attachments of a shared ID go to the card that keeps the ID, and the report names that card.
- The report lists logs and attachments that have no card. They stay in the backup.
- The command refuses `projects/inbox.md`, because the inbox has that name. Rename the file first.
- The command refuses to run while an agent, planner or reviewer works on a card, a Linear issue or an automation.

Convert your real todos in this order:

1. Close every board view.
2. Stop the automations timer: `systemctl --user stop herdboard-automations.timer`.
3. Install the new version: `uv tool install --reinstall <path to the herdboard clone>`.
4. Run `herdboard convert-store --dry-run` and read the report.
5. Run `herdboard convert-store`.
6. Run `herdboard doctor`.
7. Start the timer again: `systemctl --user start herdboard-automations.timer`.

## Repository identity

herdboard finds a repository's board from its `origin` remote, as `host/owner/repo`. SSH and HTTPS remotes give the same identity. The board stores it in `repo` in `board.toml`. All worktrees of a repository share its board. A repository without a remote uses the path of its main checkout.

## Writes

- Agents and scripts change boards only through the CLI.
- Every write takes one lock for the store (`<todos_dir>/.herdboard.lock`), reads the files again, and replaces each file in one step. When the card changed since the command read it, the command stops with exit code 2. Changes to other cards stay.
- A text editor does not use the lock. The check above catches most conflicts with an edit by hand.
- Multi-file changes write in an order that leaves no lost card after a crash. A crash can leave a card folder that no column lists. The board shows such a card in the first column, and `doctor --fix` adds it to that column.

## Files outside the board

herdboard keeps its state in `~/.local/state/herdboard/`:

| Path | Content |
|---|---|
| `starts.json` | The worktree, branch, base, agent pane and pull request of each started card, and the HEAD commit of its last agent review |
| `checkouts.json` | The known main checkouts of each repository |
| `plans.json`, `plans/<id>.log` | The running planner of each card and automation, and the plan worker's output |
| `automations.json` | The last handled due time, last run, last card and last result of each automation |
| `automations.log` | The tick's output on macOS |
| `reviews/<id>-<time>-<random>/` | Agent review requests and findings |
| `prs/<id>-<time>-<random>/` | Pull request requests and the written description |
| `pr_reviews.json` | The workspace, Hunk session, agent and review state of each pull request review, keyed `owner/repo#N` |
| `pr-reviews/` | The request for each pull request reviewer, and its worker's output |
| `<workspace>/<user>/` | The Linear cache, state choices and `promote` records, per Linear account |
