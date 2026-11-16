# Changelog

All notable changes to herdboard are in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and herdboard uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). See [docs/releasing.md](docs/releasing.md).

## [Unreleased]

### Changed

- `S` with Claude now asks for the model and the effort level, as it does for
  pi and Codex. The Claude model lists offer `fable`.

### Fixed

- `herdboard update` now updates a Herdr plugin that is older than the
  `herdboard` command. It compared only the command's version with the release.
- `herdboard automation pause`, `resume` and `edit` now work on an automation
  whose board has no repository or is gone. herdboard checks the board only
  when a change sets the board or turns on factory mode.
- herdboard now reads pi's flags with `pi --help` in an empty folder. In the
  folder of a card or a pull request, `pi --help` ran that folder's
  `.pi/extensions/` outside the reviewer sandbox, before the review.

## [0.2.0] - 2026-11-11

The first public release.

### Added

- A kanban board in a Herdr tab for local todos and Linear issues, with the
  `herdboard` command to list, add, edit, move, finish, archive and delete cards.
- Card types, tags, checklists, sub-cards, attachments, an activity log and a
  styled detail view. Mouse support, Nerd Font icons and themes.
- Start a card with `s`: herdboard opens a Git worktree and branch and hands the
  card to Claude Code, pi or Codex. Cards can also run without a repository.
- Plan a card with an agent that writes the plan as an attachment, with optional
  UI mockups from Codex.
- Review work in Hunk or with a second agent, then merge locally or open a draft
  GitHub pull request with an agent-written description.
- A Pull requests tab that lists, searches and reviews GitHub pull requests.
- Promote a todo to a Linear issue with `T`, and show Linear sub-issues,
  attachments and types on the board.
- A Triage column, a Notes tab with a Markdown scratchpad per board, and a
  details pane beside each card agent.
- Automations that spawn and start cards on a systemd or launchd timer.
- Factory runs: a builder agent works through rounds of lens reviewers and an
  approver, gated on a verification contract and current evidence.
- A config dialog with Global and Current board tabs, and Linear API keys from
  secret-store commands.
- `herdboard doctor`, and `herdboard migrate` for `TODO.md` files.
- The board header shows `↑ update` when a newer release exists, and
  `herdboard update` installs it.
