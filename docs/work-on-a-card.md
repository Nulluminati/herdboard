# Work on a card

## Plan before the work

1. Select the card and press `P`, or run `herdboard plan t3m9`.
2. Choose the planner (claude, pi or codex) and its model. herdboard creates the card's worktree and branch when the card has none. A `plan <id>` tab opens in the worktree's workspace, in the background: you stay on the board.
3. The planner reads the card and the code. It may change code and run commands in the worktree to test ideas; it reverts its own changes and does not commit. It can show you a page, an HTML file or a server that already runs with `terminal-browser`, in a split next to its pane. It asks you about the unknowns, then writes the plan.
4. Answer its questions in the tab. Close the tab when the plan is complete.
5. Start the work with `s`. The agent starts in the same worktree and gets the plan in its brief.
6. To drop a planned card that will not be worked on, run `herdboard finish t3m9`. A branch with no commits counts as merged; add `--force` when the branch has commits.

## Cards into main

1. `herdboard add "Fix login timeout"` adds the card `t3m9`.
2. `herdboard start t3m9` creates the worktree and the branch `t3m9-fix-login-timeout` from `main`, moves the card to In progress and starts the agent.
3. The agent commits on its branch and records progress with `herdboard log`. When it is done, it moves the card to Review.
4. `herdboard review t3m9` opens the branch diff in Hunk next to the agent. Send your comments to the agent with the hunkdiff `send-review` action. The agent moves the card back to In progress, fixes the code, commits, and moves the card to Review again.
5. `herdboard merge t3m9` merges the branch into `main`, or opens a draft pull request.
6. `herdboard finish t3m9` removes the worktree and the branch, and moves the card to Done. A local merge runs `finish` itself.

## Cards into a feature branch

1. `herdboard add "Billing v2"` adds the parent card `t5aa`.
2. `herdboard add "Add invoice table" --parent t5aa` adds a sub-card. Add one for each part of the work.
3. `herdboard start` on a sub-card first starts the parent with no agent (branch `t5aa-billing-v2`, from `main`). Then it starts the sub-card from the parent's branch.
4. Each sub-card merges into the parent branch.
5. `herdboard review t5aa` shows all the merged sub-cards together. `herdboard merge t5aa` merges the parent branch into `main`.

A parent with sub-cards that are not done does not merge. `--force` merges it anyway.

## start

`herdboard start <id>` does these steps:

1. Find the repository. For a repository board, it is that repository. For a Linear issue, it is the repository of the current view, or `--repo`. An inbox todo needs a choice: `--repo` takes a board name or a path in a checkout, `--new-repo [PATH]` creates a repository, and `--no-repo` runs the card without one. See [Cards without a repository](#cards-without-a-repository).
2. Find the local checkout. herdboard records every main checkout that it runs in. When it knows none, it asks for a path, or `--checkout PATH` gives one.
3. Choose the branch. A Linear issue uses its own branch name. A todo uses its ID and a short name from its title, such as `t3m9-fix-login-timeout`. A typed todo's branch starts with the commit type, such as `fix/t3m9-fix-login-timeout`.
4. Choose the base: `--base`, else the recorded base of an earlier start, else the parent's branch for a sub-card, else the branch of the main checkout. A Linear sub-issue does not use its parent's branch, because the parent can belong to another repository.
5. Open the worktree with `herdr worktree create`, or reuse the card's worktree when it exists. The workspace opens in the background: you stay on the board. Press `g` to go to it. The base becomes the upstream of the card branch, so `git status` and Hunk compare the branch with its base.
6. Move the card to In progress (`start_column`). A Linear issue moves to its started state.
7. Start the agent in the worktree as `hb-<id>`. Its first message has the card and these rules: record progress with `herdboard log`, do not change the card text, commit with conventional commits, and do not push, merge or remove the worktree.

`--agent claude|pi|codex`, `--model` and `--thinking` choose the agent. `--no-agent` opens the worktree without one. herdboard does not start a second agent for a card whose agent still runs.

herdboard writes the card title and column to the `herdboard_card` token of the card's workspace and of its agent pane, such as `▶ Fix login timeout · In progress`. The token changes when the card moves. It also writes the repository's folder name, such as `herdr-extensions`, to the `herdboard_repo` token of the workspace. The workspace keeps the name that Herdr gives it, so the space switcher and notifications can tell cards apart. Herdr keeps these tokens in memory only. At Herdr startup, and when Herdr finds an agent in a pane, herdboard reports them again for every started card whose workspace is still open (`herdboard sidebar-refresh`). A Linear card's title then comes from the cache. Add the tokens to the Herdr sidebar rows to show them:

```toml
[ui.sidebar.spaces]
rows = [
  ["state_icon", "$herdboard_repo", "workspace"],
  ["$herdboard_card", "branch", "git_status"],
]

[ui.sidebar.agents]
rows = [
  ["state_icon", "agent"],
  ["workspace", "tab"],
  ["$herdboard_card"],
]
```

Without `--thinking`, pi uses the thinking level that you last chose for that model, from the `[thinking]` table of the config file. A model without a saved level uses `start_thinking`. See [thinking levels](configuration.md#thinking-levels).

A failed `start` reports the steps that worked. Run `start` again to continue from the first step that failed.

## plan

`herdboard plan <id>` starts a planner agent in a `plan <id>` tab in the card's worktree. It creates the worktree and the branch when the card has none, as `start` does, and finds the repository and the checkout the same way. It takes the same `--repo`, `--checkout` and `--base`. The card stays in its column, and the worktree stays open: `herdboard start <id>` later starts the work agent in the same worktree.

The planner gets a brief with the card, its attachments, its log and the current plan. It may change code and run commands in the worktree to test ideas. Before planning ends, it reverts its own changes, so the work agent starts clean; it does not commit. When the worktree is not clean, the brief names the changes that were already there, and when the card's work agent still runs, the brief says so. The planner has the work agent's permissions and can also write the card's attachments. See [Agent permissions](agent-permissions.md). The planner finds the facts in the repository itself and asks you only for decisions. It asks a few numbered questions at a time, each with its recommendation, and asks a question that depends on another answer in a later round. It agrees the test boundaries with you, and makes each step one small change with its own check. Then it writes the plan to the `plan.md` attachment, with these sections: Goal, Decisions, Steps, Testing, Out of scope and Open questions.

For a card with a repository, the Testing section has acceptance criteria (`AC1: <observable outcome>`) and a `herdboard-verification` block: the verification contract that a [factory run](factory-runs.md) needs. The planner writes the plan for one workflow: feature, defect, refactor or performance. See [Workflow verification](workflow-verification.md) for the contract fields and the workflows. A plan for a card without a repository has no contract.

A background worker watches the plan. Each time the planner saves it and is idle, the worker logs `Plan saved: <path>`. When the tab closes, the worker logs `Planning ended.` It stops watching after 8 hours, but a planner that still runs still blocks a second one.

When planning ends with a changed plan and the card's work agent still runs, the worker tells that agent to read the plan. The agent tells you how its work differs, and waits for you to decide.

`plan` on a card that has a plan gives the planner the current plan to revise. A second `plan` for a card whose planner still runs fails with `plan_running`.

Codex planners use `workspace-write` with network access and the attachments folder as an extra writable directory. Writes there and in the worktree need no approval. Other approval requests go to Codex's automatic reviewer (`approvals_reviewer = "auto_review"`), which uses extra model calls. You stay in the tab for requests it denies. Codex work agents use the same options without the attachments folder. Codex keeps every `.git` folder read-only in `workspace-write`, so each `git add` and `git commit` of a work agent goes to the automatic reviewer.

pi planners and work agents run Approval Mode with `--approval-reject block`. When Jev rejects a command, pi tells the agent that the command is blocked and shows no dialog. The agent takes another route. You still get the dialog for commands that Jev is uncertain about. pi has no sandbox in these sessions, so Approval Mode stays on. Approval Mode comes from the `approval-mode` extension in [pi-extensions](https://github.com/Nulluminati/pi-extensions). Without it, pi starts with no Jev command review, and herdboard shows a warning and writes it to the card's log. See [Agent permissions](agent-permissions.md).

`--agent claude|pi|codex`, `--model`, `--thinking` and `--base BRANCH` choose the planner and its base. On the board, `P` asks for them.

## Mockups

For work on a user interface, the planner offers a mockup image. It asks you before it makes one, because a mockup takes up to a few minutes and uses your ChatGPT subscription.

`herdboard mockup <id> "<prompt>" ["<prompt>"]...` runs `codex exec` once for each prompt, at the same time, and makes one draft per prompt. Give one prompt per option, four at most. Each prompt describes the screen: layout, components, text and style. `--image FILE` (up to five) gives Codex an image to revise or follow, such as an earlier draft or a screenshot. `--quality auto|low|medium|high` sets the image quality; the default is `medium`. A failed option does not stop the others: the JSON result lists it in `failed`.

The drafts go to `~/.local/state/herdboard/mockups/<id>/`, not to the attachments. The command logs the path of each draft. The planner attaches only the draft that you approve, with `herdboard attach <id> <draft> --name mockup-<slug>.png`. The work agent's brief tells it to open the `mockup-*.png` attachments before it builds the UI. `finish` and `archive` delete the drafts. Linear cards keep mockups in the local attachments only.

In Herdr, the drafts open in one pane to the right of the caller's pane. The pane shows one draft at a time, labeled "Option 1 of 3" and so on. Left and right arrows (or `h` and `l`) switch drafts, and Enter or `q` closes the pane. The pane draws the image with the kitty graphics protocol, so Herdr needs `kitty_graphics = true` in its `[terminal]` settings, in a terminal that shows images, such as Ghostty or kitty. When the terminal does not answer the graphics query, or outside Herdr, the drafts open with `xdg-open` (`open` on macOS). `--no-show` only makes the drafts.

`mockup` needs the `codex` CLI, logged in with a ChatGPT account. The `mockup_model` setting names the Codex model, because the model in your Codex config may not make images on a ChatGPT account. When Codex reports `model_not_found`, change `mockup_model`.

A planned card that will not be worked on is dropped with `herdboard finish <id>`: a branch with no commits counts as merged. Add `--force` when the branch has commits.

## Cards without a repository

An inbox card is sometimes research, or the start of a new project, and it has no repository. `start` and `plan` then fail with `repo_required`. There are three ways to continue:

- **A repository board.** `--repo BOARD` starts the card in that board's repository. On the board, the question lists the repository boards first.
- **A new repository.** `--new-repo [PATH]` creates a local Git repository, its board, and then starts the card as usual. Without PATH, herdboard uses `<projects_dir>/<title>`, such as `~/Projects/corvid-tracker`. The path must not exist, or must be an empty folder. A folder that a stopped start left with only an unborn repository is reused. herdboard runs `git init -b main` and makes one empty first commit. The new board merges locally (`local`) and has no remote: add one with `git remote add origin` when you have it. Only todos can create a repository, and not a card with a parent or sub-cards: their cards must stay on one board.
- **No repository.** `--no-repo` runs the card in `<todos_dir>/.herdboard/work/<id>/`, a plain folder with no Git, no branch and no worktree. herdboard opens a Herdr workspace there, in front of you, because there is no worktree to visit later. The brief tells the agent to write its result to the card's attachments, such as `findings.md`: press `o` on the card to read them.

A card that already has a worktree refuses `--no-repo` and `--new-repo` with `usage`, so a start record is never replaced by accident. Finish the card first. `--checkout` and `--base` need a repository that the card already has, so `--no-repo` and `--new-repo` refuse them too.

The choice is kept in the card's start record, so a later `start` or `plan` does not ask again. On the board, `s`, `S` and `P` ask the question in a dialog. In a terminal, `start` and `plan` ask too, unless `--json` is set.

A repoless card has limits. `review` opens nothing: only `review --agent` works, and the reviewer checks the attachments against `plan.md`. `merge` fails with `no_repository`. `finish` closes the workspace, deletes the card folder even when it is not empty, and moves the card to Done. The brief says so, so the agent copies everything worth keeping into the attachments.

## Attachments

Attachments hold documents that are too large for the card text, such as a specification. They are files in the `attachments/` folder of the card folder, next to the log. A Linear card keeps them in `<todos_dir>/.herdboard/linear/<ENG-123>/attachments/`, and herdboard posts nothing to Linear.

- `herdboard attach <id> FILE [--name NAME]` copies a file into the card's attachments and logs it. An attachment with the same name is replaced.
- `herdboard attach <id> --remove NAME` removes an attachment.
- `herdboard show <id>` lists the attachments.

The card detail on the board lists the attachments with their sizes. Press `o` to open one. With more than one attachment, you choose it from a list. herdboard shows a UTF-8 text file of 1 MB or less itself, and draws a `.md` file as Markdown. Other files open in the default application, with `xdg-open` on Linux or `open` on macOS.

When the card has a pull request, the detail shows its link above the attachments. A click or `o` opens it in the default browser. With attachments too, `o` lists the pull request first.

The detail of a Linear card also lists the issue's Linear attachments, such as pull requests and links, with their titles and URLs. `o` and a click open them in the default browser. Only `http` and `https` addresses open. herdboard shows them only: `show` and `--json` leave them out, and `attach` does not change them.

When `start` starts the work agent, its brief includes the `plan.md` attachment in full, and lists the other attachments by path. `review` and a rebase conflict give a brief only to a new agent, when the card's agent is gone. A running agent gets no new brief. An agent review gets the path of each attachment, and checks the work against the plan.

## Activity log

Each card has a log in `log.md` in its card folder. A Linear card's log is in `<todos_dir>/.herdboard/linear/<ENG-123>/log.md`. One entry is one line:

```markdown
- 2026-10-12 14:03 · pi · Ready for review: 3 commits.
- 2026-10-12 14:20 · herdboard · Rebase conflict in src/auth.py. Sent to the agent.
```

herdboard sets the author. In a card's agent pane, the author is the agent kind (`claude`, `pi` or `codex`). Some agents run their tool commands in a sandbox that cannot reach Herdr; there, herdboard names the agent that it last started in that pane. Entries that herdboard writes have the author `herdboard`. All other entries have the author `user`. The log works for Linear cards too, without a connection, and herdboard posts nothing to Linear.

Agents record progress in the log, not in the card. `edit` fails with `agent_edit_denied` in a card's agent pane. This guards against mistakes. It is not a security boundary.

## Details pane

Each card agent and each planner gets a small read-only pane on top, labeled `details - <id>`. Herdr draws its border and label, so the pane draws none of its own. It shows the card without going back to the board:

```text
tr88 │ Some kind of details pane in workspaces  In progress      feature
claude opus (high) · tr88-details-pane → main · PR #12 open
☑ 2/5  mockup-details-pane.png  plan.md
── log ─────────────────────────────────────────────────────────────────
10-29 14:02  herdboard  Plan saved: …/attachments/tr88/plan.md
10-29 15:10  claude     Moved to Review
```

- The first line has the card ID, the title without tags, the column (a Linear card's state) and the type.
- The second line has the agent, its model and thinking level, the branch and its base, and the pull request. A card without a repository shows `no repository`. A card without a start record, such as one that only has a planner, shows `no start record`.
- The third line has the checklist count and the attachment names. Without both, the line is left out.
- The newest log entries fill the rest of the pane, newest at the bottom.

The pane reads only herdboard's files, so it shows no live Herdr agent state; the sidebar shows that. It checks the files every two seconds and draws again after a change. A Linear card asks Linear at most once a minute.

`start` opens the pane in the card's workspace, also when `review` or a rebase conflict starts a new agent. `plan` opens it in the planner tab, and the tab closes when the planner ends. The agent keeps the focus, and your own focus stays where it was. An agent review opens to the right of the agent, under the full-width details pane.

Two global settings control it. The configuration dialog (`c`) has both:

- `details_pane = false` opens no pane.
- `details_pane_ratio` is the pane's share of the agent pane's height, from 0.1 to 0.6 (default 0.25). Herdr sets a split size only as a ratio.

After you close the pane, the Herdr action `nulluminati.herdboard.details` opens it again for the focused pane's workspace: the planner of that tab, else the started card of the workspace. It opens no second pane. `herdboard details --open [<id>] [--pane ID]` does the same from a shell. A suggested key:

```toml
[[keys.command]]
key = "prefix+shift+d"
type = "plugin_action"
command = "nulluminati.herdboard.details"
description = "herdboard: show card details"
```

Herdr does not keep the pane after a restart. Use the action to open it again.

## review

`herdboard review <id>` has three modes:

- `--human` (the default) opens the branch diff in Hunk, in a split next to the card's agent. Your Hunk comments go to that agent. A second `review` reuses the open Hunk pane. Hunk uses much memory, so herdboard closes the pane when the card leaves Review.
- `--agent` has a second agent review the work. By default, pi reviews Claude's work, Codex reviews pi's work, and Claude reviews Codex's work. `--reviewer`, `--model` and `--thinking` change this. Without `--thinking`, a pi reviewer uses the saved level of its model.
- `--both` runs the agent review first, and opens Hunk when the findings are ready.

When the card's agent no longer runs, `review` starts a new one of the same kind. Its first message has the card and the full log.

The agent reviewer gets the commits since the base, the uncommitted changes and the untracked files. It starts in a split as `hb-<id>-review`, in the background: herdboard does not move you to the card's workspace. It may run any read-only command in a sandbox that writes only its review folder and reaches only GitHub. See [Agent permissions](agent-permissions.md). No card reviewer may run project code, tests or builds from the shell, or start servers. Every reviewer may use `terminal-browser` to check pages, HTML files and servers that already run. A background worker waits up to 30 minutes for the findings. Then it closes the reviewer pane and sends the findings to the card's agent. The agent answers with a table: one row for each finding, with its number, a short description, its severity, and whether the agent agrees or disagrees, and why. The agent logs its answer, changes no code, and waits for you. A Herdr notification tells you when the review is done or failed.

On the board, `R` asks for Human, Agent or Both. For an agent review, it then asks for the reviewer and the model: `fable`, `opus`, `sonnet` or `haiku` for Claude, the pi model list for pi, or the Codex model list for Codex.

## merge

The mode comes from `--local` or `--pr`, else from `merge` in the board's `board.toml`, else from `merge` in the config. The default is `local`. On the board, `c` sets the board's mode.

Both modes stop when the worktree has uncommitted or untracked files (`worktree_dirty`), or when the branch has no commits ahead of its base (`nothing_to_merge`).

Local merge:

1. Rebase the branch onto the base in the worktree. On a conflict, herdboard aborts the rebase, moves the card to In progress, and sends the conflicting files to the card's agent. The command exits with `rebase_conflict`.
2. Fast-forward the base to the branch. A checkout that has the base checked out must have no uncommitted changes to tracked files (`base_dirty`).
3. Log `Merged into <base> at <commit>.` and run `finish`.

herdboard does not push the base.

Pull request:

1. herdboard writes a request for the card's agent: the card, its log, the branch diff, and the repository's pull request templates. When the card's agent no longer runs, a sandboxed writer agent of the same kind starts in a split as `hb-<id>-pr`.
2. The agent writes the title and the description. The title is a conventional commit, such as `feat(auth): add magic links`. With a template, the description follows its headings in the same order. Without one, it uses Why, What changed, Trade-offs (only when there are some) and Testing. The agent describes only the testing that the log or the change shows. The text does not name herdboard, the agent or the card.
3. A background worker waits up to 30 minutes for the text. Then it pushes the branch to `origin` and runs `gh pr create --draft`. For a Linear card, it adds the issue link at the end of the description.
4. The worker logs `PR opened: <url>` and shows a Herdr notification. The card stays in Review.

When the branch already has an open pull request, `merge --pr` only pushes the new commits. `--rewrite` also has an agent write the title and description again, which replaces edits made on GitHub. On the board, `m` asks before it rewrites.

A failure logs `PR not opened: <reason>` and shows a notification.

## pr-sync

`herdboard pr-sync <id>` sends a started card's written description to its open pull request. It runs `merge.push_branch`, then replaces the GitHub title and description with the card's `pr.md`. The card's agent may run it for its own card, so the user can ask the agent for text changes after `m` opened the draft. The agent edits `pr.md` and runs `pr-sync`.

The start record keeps the folder of the last written `pr.md`. Without one, the command fails with `no_description`. `herdboard pr-sync <id> --fetch` writes the current GitHub title and body to a new `pr.md` first, and prints its path: the agent edits that file and runs `pr-sync` again. `--fetch` changes nothing on GitHub. It covers a pull request that opened before this command existed, or one opened by hand.

A sync replaces the GitHub title and body, and so overwrites edits made on the GitHub web page. A sync stops when the worktree has uncommitted or untracked files (`worktree_dirty`). Both modes stop when an agent still writes the description (`pr_writing`), and when the branch has no open pull request (`no_pr`). `--fetch` reads GitHub only: a dirty worktree does not stop it.

## finish

`herdboard finish <id>` checks that the work is merged: the base contains the branch, or `gh` reports the pull request merged. Then it does these steps:

1. Close the Hunk pane.
2. Remove the worktree with `herdr worktree remove`.
3. Delete the branch. After a merged pull request, it also deletes the branch on `origin` if GitHub did not.
4. Move the card to its done column and log `Finished.`

A worktree with uncommitted or untracked files always stops `finish`. `--force` finishes a card that is not merged, but keeps its branch.

For a card without a repository, `finish` closes the card's workspace, deletes the card folder with everything in it, and moves the card to Done. There is no branch to check. This also drops a card that was planned with `--new-repo` before its repository exists.

The board never runs `finish` itself.
