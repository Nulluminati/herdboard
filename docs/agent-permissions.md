# Agent permissions

Each role gets the same permissions in Claude, pi and Codex. The work agent and the planner run with you in the tab, so each agent's automatic judge decides on risky actions. Reviewers run unattended, so no judge runs: an operating system sandbox is the limit.

| Role | Claude | pi | Codex |
|---|---|---|---|
| Work agent (`start`) | `--permission-mode auto` | Approval Mode with `--approval-reject block`: Jev rejects go back to the agent, uncertain commands ask | `workspace-write` with network, approvals `on-request` with auto-review, `web_search="live"` |
| Planner (`plan`) | as the work agent, plus `--add-dir` for the attachments folder | as the work agent, with all its tools | as the work agent, plus `--add-dir` for the attachments folder |
| Card reviewer (`review --agent`) | sandbox, writes the review folder, browser | sandbox, writes the review folder, browser | sandbox, writes the review folder, browser |
| Factory builder (`start --factory`) | as the work agent, plus `--add-dir` for the factory folder | as the work agent | as the work agent, plus `--add-dir` for the factory folder |
| Factory lens reviewer and approver | as the card reviewer, writes its lens or approver folder | as the card reviewer | as the card reviewer |
| PR writer (`merge --pr`) | sandbox, writes the description folder | sandbox, writes the description folder | sandbox, writes the description folder |
| PR reviewer (`pr-review`) | sandbox, writes nothing, Hunk | sandbox, writes nothing, Hunk | sandbox, writes nothing, Hunk (the global `terminal-browser` rule still applies) |

The reviewer sandbox:

- The reviewer may run any shell command. The sandbox reads the whole disk except credentials and writes only the role's folder. The repository or PR checkout stays read-only.
- The credentials are `~/.ssh`, `~/.gnupg`, `~/.aws`, `~/.netrc`, `~/.docker/config.json`, `~/.local/share/keyrings`, `~/.password-store` and the Claude, Codex and pi auth files. Claude also gets `Read` deny rules for them, because its `Read`, `Grep` and `Glob` tools run outside the sandbox. `~/.config/gh` stays readable: `gh` needs its token for private PRs.
- The shell gets no environment variable whose name contains `KEY`, `SECRET`, `TOKEN` or `PASSWORD`, such as `OPENAI_API_KEY`. The agent itself keeps them. Claude's sandbox takes exact names, so herdboard lists the names in its own environment at launch. Codex uses its `shell_environment_policy` filter. pi's sandbox passes no such variable.
- The shell reaches only GitHub: `github.com`, its subdomains and `*.githubusercontent.com`. `gh` uses your token. Claude's and pi's sandboxes do not accept all hosts, so Codex gets the same list.
- Web tools run outside the sandbox and read other pages: Claude `WebFetch` and `WebSearch`, pi `web_fetch` and `web_search`, Codex live web search. The context7 and grep_app documentation tools (pi: the context7 tools and `code_search`) also run outside it.
- With the browser, `terminal-browser` runs outside the sandbox, because it splits panes through the Herdr socket. It can open `file://` addresses, so it reads any file. The PR reviewer gets no browser for this reason.
- The PR reviewer reaches the Hunk daemon on `127.0.0.1` (port `HUNK_MCP_PORT`, default 47657). Claude runs `hunk session` outside its sandbox instead, because its sandbox does not send `127.0.0.1` through its proxy. Only a plain `hunk session` command runs outside: with `cd`, an environment variable or another command joined to it, it stays in the sandbox and fails with "No active Hunk sessions". The prompt tells the reviewer to run each `hunk session` command alone.
- Claude runs in `dontAsk` mode with a `--settings` sandbox that fails when the sandbox is not available. Its allowed tools are `Read`, `Grep`, `Glob`, `Bash`, `WebFetch`, `WebSearch`, `Skill`, the `context7` and `grep_app` MCP servers, and `Edit` and `Write` in the role's folder.
- pi runs with `--approval-mode off` and a `--sandbox` policy. Without the `worker-sandbox` extension, the pi reviewer runs with no sandbox, and herdboard warns. Its tools are `read`, `grep`, `find`, `ls`, `bash`, `web_fetch`, `web_search`, the context7 tools, `code_search`, and `write` when the role has a folder.
- Codex runs with approvals `never` and a permission profile for one run (`hb-review` or `hb-pr-review`). herdboard does not change `~/.codex`.
- The prompts set the other limits: do not run the project's code, tests or builds, do not start a server, do not change Git state, and never submit to GitHub.

What each agent needs on your machine:

- pi: optionally, the `approval-mode` and `worker-sandbox` extensions from [pi-extensions](https://github.com/Nulluminati/pi-extensions). The reviewer tool list also names the context7 tools and `code_search`. pi ignores a tool name that no extension adds.
  - `approval-mode` adds `--approval-reject` and `--approval-mode`. Without it, the work agent and the planner start with no Jev command review, and reviewers start without `--approval-mode off`.
  - `worker-sandbox` adds `--sandbox`. Without it, reviewers (card reviewer, factory reviewers, PR writer and PR reviewer) run with no sandbox: they can write the repository, read your credentials and reach any host.
  - Before each pi start, plan and review, herdboard runs `pi --help` in the card's folder, because extensions can be project-local. It leaves out each flag that pi does not list. For each missing extension, it shows a Herdr notification, prints a warning on stderr and writes the warning to the card's log. A PR review has no card, so its warning has no log entry. When `pi --help` fails, herdboard passes all the flags.
  - Check with `pi --help | grep -E 'approval-reject|sandbox'`.
- Codex reviewers: a rule in `~/.codex/rules/` that runs `terminal-browser` outside the sandbox (`prefix_rule(pattern=["terminal-browser"], decision="allow")`), and the `context7` and `grep_app` MCP servers in `~/.codex/config.toml`.
- Codex work agents and planners: a rule in `~/.codex/rules/` that allows the safe `herdboard` subcommands (`show`, `list`, `log`, `attach`, `mockup`, `move`).
