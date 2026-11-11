# Pull request reviews

herdboard can have an agent review an open GitHub pull request of the current repository. The agent leaves notes in a live Hunk session and never submits a review. You read its notes and its chat, add your own notes, and submit the review yourself from Hunk.

The flow:

1. Press `G` on the board. The list shows the open PRs, 50 to a page, newest first. Each PR is a box. Its border is green when the checks passed, red when they failed and yellow while they run. A PR shows:
   - An open or draft icon, the number, and the title with its first two labels in their GitHub colors.
   - The author (yours in cyan) and the size (`+84 −31`), then the branch and its base (`fix-login → main`).
   - **CI**: the state of the last commit's checks: `passed`, `failed` or `pending`.
   - **GitHub review**: what GitHub says. `your review` when the PR asks you, and GitHub's review decision: `approved`, `changes requested` or `review required`.
   - **Agent review (local)**, under the GitHub review: what herdboard's agent did on this machine: `reviewing`, `reviewed` or `failed`, and `new commits` since then.
   - At the right: the comment count, the agent's note count, and when the PR was last updated.

   In a window narrower than about 115 columns, a PR keeps three rows: the GitHub and agent reviews move under the title, and CI, the counts and the update time go to the right.

   The lines above the list show the repository, the total, the page and the search, then count what needs you on the page, by GitHub, CI and agent.
2. Press `R` on a PR. Choose Claude, pi or Codex, then the model. For pi or Codex, also choose the thinking level. The pi dialog starts at the level that you last chose for that model. See [thinking levels](configuration.md#thinking-levels).
3. herdboard fetches `pull/<N>/head` from the base repository's remote into the local branch `pr/<N>`. This also works for a PR from a fork. It opens a Herdr worktree workspace `PR #<N> <title>` under the repository, in the background.
4. The workspace has the agent on the left and `hunk gh pr 'owner/repo#N'` on the right. The Hunk pane gets `GH_TOKEN`, `GH_PR_NUMBER` and `GH_PR_REPO` in its environment. The token does not show in the command.
5. The agent reads the PR with `gh pr view`, `gh pr diff` and `gh pr checks`, and adds its notes with `hunk session comment add`. It ends with a short summary in its chat.
6. A background worker waits up to 30 minutes for the agent to go idle. Then it marks the PR `reviewed` and shows a Herdr notification with the count of notes that this review added.
7. Press `g` to go to the workspace. Read the chat and the notes, add your own, and press `S` in Hunk to submit one GitHub review. Hunk's notes keep GitHub's diff positions, so the submit targets the right lines.
8. Press `f` when you are done. herdboard closes the workspace, removes the worktree and deletes `pr/<N>`. When notes of yours are not submitted, it asks again before it removes them. It checks the notes in Hunk, and the notes that a failed refresh saved.

When the author pushes new commits, the list shows `new commits` within a minute. Press `u`. herdboard moves `pr/<N>` to the new head, opens Hunk again on the new diff, and adds the old notes back. A note whose line is no longer in the diff is dropped, and the notice names it. Then herdboard offers a new review by the same agent. A running agent gets the new request in its chat. `u` stops when the worktree has changes.

Keys on the list:

| Key | Action |
|---|---|
| `enter` or a click | Show the PR's details: its branches, size and labels, each CI check (failed first), the issues it closes, the GitHub reviews by reviewer, the local agent review and the description. herdboard reads the checks, issues, reviews and description only then. The action keys below also work there |
| `R` | Choose an agent and a model, then review the PR |
| `g` | Go to the PR's review workspace |
| `u` | Fetch new commits, open Hunk again with the old notes, and offer a new agent review |
| `f` | Finish the review, after you confirm |
| `o` | Open the PR in the browser |
| `n` / `p` | The next or previous page |
| `/` | Search GitHub for open PRs: words match the title and the description, and GitHub qualifiers such as `author:octo`, `draft:true`, `label:bug` or `review-requested:@me` work. `enter` searches from page 1 |
| `r` | Read GitHub again. The list also reads the current page once a minute |
| `escape` | Close the search box, else clear the search, else go back to the board |
| `G` | Go to the Notes tab (see [Notes](notes.md)) |

The icons follow `icon_style` in the config: Nerd Font icons with `nerd`, plain symbols (● ◌ ◆ … ✓ ✗ ↑) otherwise. When the "Herdr Agent Icons Max" font of the [agent-icons](../agent-icons/README.md) plugin is installed, a local agent review shows the logo of its agent.

The Herdr action `nulluminati.herdboard.prs` opens the board on this list. A suggested key:

```toml
[[keys.command]]
key = "prefix+shift+r"
type = "plugin_action"
command = "nulluminati.herdboard.prs"
description = "herdboard: review pull requests"
```

What the reviewer can do:

- Every reviewer may run any read-only command in a sandbox that writes no file and keeps the PR checkout read-only. The shell reaches only GitHub and the local Hunk service. See [Agent permissions](agent-permissions.md).
- The reviewer gets no `terminal-browser`: it runs outside the sandbox and can read any file, and a PR can ask for that. Codex is the exception while its global `terminal-browser` rule is in `~/.codex/rules/`.
- The prompt treats the whole PR as untrusted, including its `AGENTS.md`, `CLAUDE.md` and agent config. It tells the reviewer to ignore instructions in the PR, to keep away from credentials and environment variables, and to flag a prompt injection as a high note. A prompt cannot stop the PR's agent config from loading when the reviewer starts.
- The prompt forbids code execution, Git changes and any submission to GitHub. The sandbox cannot block a submit through `gh`: it uses your token.
- No reviewer runs the tests or the code of the PR.

Limits:

- One reviewer agent per PR. A review with another agent kind, model or thinking level stops with `agent_running` while the first agent still runs. Close it first, or press `f` and review again.
- Old notes come back after `u` as agent notes, with their author kept. herdboard remembers which of them were yours, so `f` still stops at them.
- `u` waits for a reviewer that Herdr shows as working: it stops with `agent_running` until the review ends. A review that shows `reviewing` but has no working agent counts as failed, and `u` goes on. When Hunk cannot list the notes of a live session, `u` stops and Hunk stays open.
- A note on a line that is no longer in the diff is dropped. When Hunk refuses a note for another reason, herdboard keeps it in the saved notes and stops with `hunk_failed`. Press `u` to apply it again. `f` counts these saved notes too.
- When Git does not delete `pr/<N>`, `f` stops with `git_failed` and keeps the review. Fix the branch, then press `f` again.
- `u` saves the notes to `pr-reviews/<PR>.notes.json` in the state folder before it closes Hunk. When the new Hunk does not open, the next `u` or review puts them back.
- A review (`R`) of a PR whose worktree is behind the PR head stops with `new_commits`. On the list, herdboard then offers to fetch the new commits first.
- `f` removes the worktree first. When Herdr or Git refuses, Hunk and its notes stay open.
- Only github.com, and only PRs of the current repository.
- herdboard does not remove the workspaces of merged or closed PRs by itself. Use `f`.
