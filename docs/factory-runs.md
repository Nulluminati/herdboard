# Factory runs

A factory run chains the card stages: the planner, the work agent (the builder), lens reviewers, and an approver. Start one with `herdboard start <id> --factory`, or press `F` on the board. Choose Default, a named preset, or Custom….

1. Plan the card with `P` first. The plan is the spec. The planner adds a `Review lenses:` line under Decisions, such as `Review lenses: security, code`, and the verification contract under Testing: the acceptance criteria and the checks that prove them. A factory run does not start without a valid contract.
2. `start --factory` checks the plan's contract, then starts the builder as `start` does. A background worker (`herdboard factory-wait`) watches the run. The builder's brief says where to write its evidence.
3. While the run goes on, the card stays in In progress. When the builder runs `herdboard move <id> Review`, the column does not change: the move records a ready signal in the local start record. When the builder has signalled and is idle, the worker starts one review round. One sandboxed reviewer per lens opens in a split to the right of the builder, as `hb-<id>-<lens>`. Each lens gets its own instruction:
   - `security`: injection, authentication, secrets, unsafe file and shell use, sandbox escapes.
   - `ux`: flows, error messages, defaults, keyboard and mouse use, user documentation.
   - `ui`: layout, consistency with the existing interface, `mockup-*.png` attachments, themes.
   - `code`: bugs, missing tests, readability, the style of the surrounding code.
4. The worker merges the findings of all lenses into one round file. A lens that fails, or whose reviewer does not start, gets a section that says so. The round continues without it. When no reviewer of a round starts, the run stops.
5. The worker sends the round file to the builder. For each finding, the builder fixes it or logs why it disagrees, with the code path, test or evidence that supports it. It writes its answers as a table (`responses.md`), commits, runs the contract's checks again on the final commit, writes fresh evidence, and runs `move <id> Review` again to signal the next round.
6. The next round's reviewers read the earlier findings and answers. They do not raise a finding again that the builder disagreed with, unless they have new evidence.

The loop stops when one of these is true:

- A round has no confirmed problems and no lens failed. Risks and questions go to the builder, but they do not start another round.
- The builder made no new commits since the last round, and no lens failed. When uncommitted changes exist, the log says that the approver reviews them too.
- The round reached the run's limit: the preset's or Custom form's `rounds`, `--rounds N`, else `factory_max_rounds` (default 3).

A lens that failed did not review the change, so its round is not clean. When such a round has no findings for the builder, the next round starts at once.

A confirmed problem from a reviewer names its `path:line` and the failure or code path that shows it. An unproven concern goes under Risks and questions. What the reviewer could not check goes under Verification limits: it is not a finding and does not start another round.

Then herdboard checks the builder's evidence, and an approver checks the work against the plan's acceptance criteria and that evidence. The lens reviewers checked the code; the approver checks the requirements. It writes `verdict.md` (`Verdict: approve` or `Verdict: changes needed`, with an acceptance table, the requirements not met, the code findings left, the lenses that failed, and the testing) and a structured `approval.json`. herdboard then decides the effective verdict. Missing, malformed, stale or incomplete evidence, a dirty worktree, a failed check, a changed plan, or a blocked check without the approver's named exception makes it `changes needed`. herdboard never raises a verdict. It attaches the result to the card as `factory-verdict.md`, logs `Factory done: <verdict>.`, and shows a notification. Then it moves the card to Review. For a factory card, Review means that every round is done and the work is ready for you to inspect, also after `changes needed`. You merge it with `m`; the approver never merges.

See [Workflow verification](workflow-verification.md) for a complete contract, evidence report and approval, and for the limits of the check: it shows that the evidence is complete and current, not that an agent ran a command.

A branch with no change starts no reviewer, logs `Factory: no change to review, approver next.`, and still gets the evidence check and a verdict.

The contract errors:

- `verification_plan_required`: the card has no plan, or the plan has no `herdboard-verification` block.
- `verification_plan_invalid`: the block is malformed. The message names the field.

Nothing starts after either error. On the board, the `F` popup and the Custom form show the error and stay open: press escape, then `P` to update the plan. A factory automation whose plan has no valid contract adds no card: its last result is `plan_invalid`, and `doctor` reports `automation_plan_invalid`. When the copy on a spawned card fails the check, the card logs `Auto start failed: ...`, and the last result is `start_failed`.

A run started before this policy keeps its old approval and the old no-change shortcut. Plan the card again to add a contract. A plan that changes during a run makes the approval `changes needed`: start the factory again with the new plan.

A Linear issue runs the same way. The ready signal is local, so the rounds make no Linear calls. The worker reads the issue once when it starts, and writes to Linear once: the final move to Review. That move cannot ask which state to use. When no state maps to Review, or several do and you have not chosen one before, the move fails. The log then says `Factory: the card did not move to Review: <reason>`, the verdict stays attached, and you move the issue by hand. See [Workflow states](linear.md#workflow-states).

A stopped run leaves the card in In progress. A move on the board itself (not with `herdboard move`) still changes the column.

`herdboard factory <id>` shows the run's status, round and preset. `herdboard factory <id> --stop` stops it and closes its reviewers. `show --json` has a `factory` object. The run also stops when the builder's pane is gone, the card leaves the board or is finished, or the worktree is removed. The worker checks this during the reviews and the approval too, so a finished card does not move back to Review. When the worker process died, the next `move <id> Review` stops the stale run, closes its reviewers, logs `Factory stopped: its worker is gone.`, and moves the card. While a run goes on, `review --agent` and `merge` refuse with `factory_running`. `merge --force` still merges.

Default runs take their lens agents from `[factory.lenses]` in the config, see [Configuration](configuration.md). Each lens uses its configured agent, also when it is the builder's agent. The approver uses `[factory] approver`, else the card reviewer of the builder's agent (pi for Claude, Codex for pi, Claude for Codex).

Use `herdboard start <id> --factory --preset cheap` to select a named preset. Do not combine `--preset` with `--agent`, `--model`, `--thinking` or `--rounds`. Each preset defines the builder, all four lens reviewers, the approver and the round limit. Optional `lenses_on` replaces the plan's lens selection. Without it, the plan decides.

Presets and Custom runs choose the agents, the lenses and the rounds. The plan's contract applies to all of them: no preset turns it off. A run without the code lens, such as `lenses_on = ["security"]`, still gets the evidence gate. The approver does not replace a code review.

The `F` popup shows a summary of the highlighted run. Enter starts it. Default uses `start_agent` and its configured model and thinking level. To choose a different builder, open the Custom form. Press `c` to edit a copy in the Custom form. Set each role's agent, model and thinking level. Select the lenses, or let the plan choose them. Press `ctrl+s`, or Enter in the Rounds or save-name field, to start. Leave the save name empty for a one-off run. A name saves a preset first; replacing a preset needs confirmation. Escape returns to the popup.

Preset names use `a-z`, `0-9` and `-`. The names `default` and `custom` are reserved. Each preset needs all six role agents and a round limit from 1 to 10. Model and thinking are optional on each role. Unknown keys are errors. Edit or delete presets in the config file.

The start record stores the run settings. Later config changes do not replace those settings. An omitted model or thinking level keeps the agent's default; pi resolves omitted values through its usual model and thinking settings.

Limits: a factory run needs a card with a repository. It refuses `--no-agent`, `--no-repo`, `--new-repo`, and a card whose agent already runs. One round can start four reviewers at the same time.
