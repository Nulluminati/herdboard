"""Tell a started card's live work agent that the user changed the card's title, details or attachments."""

import os

from . import activity, start
from .model import HerdboardError
from .store import CardView


def edit_changes(before: CardView, after: CardView) -> list[str]:
    """The labels of the edit's changes that the card's agent must know: `title` and `details`."""
    changes = []
    if before.title != after.title:
        changes.append("title")
    if before.body != after.body:
        changes.append("details")
    return changes


def notify_card_agent(store, ref: str, changes: list[str], skip: bool = False) -> dict | None:
    """Prompt the card's live work agent to read the card again.

    None when there is nothing to tell: no changes, no start record or no live agent. Else the
    notice, with `status` sent, skipped (`reason` no_notify or self) or failed (with `error`).
    A failure never raises: the card change stays saved.
    """
    if not changes:
        return None
    try:
        found = start.find_record(ref)
    except HerdboardError:
        return None
    if found is None:
        return None
    record = found[1]
    agent = record.get("agent_name")
    notice = {
        "agent": agent,
        "pane_id": record.get("pane_id"),
        "changes": list(changes),
        "status": "sent",
        "reason": None,
        "error": None,
    }
    try:
        live = start.agent_live(record)
    except HerdboardError as error:
        return {**notice, "status": "failed", "error": str(error)}
    if not live:
        return None
    if skip:
        return {**notice, "status": "skipped", "reason": "no_notify"}
    if os.environ.get("HERDR_PANE_ID") == record["pane_id"]:
        return {**notice, "status": "skipped", "reason": "self"}
    labels = ", ".join(changes)
    text = f"Card {ref} changed: {labels}. Run `herdboard --json show {ref}` and read the changes before you go on."
    try:
        start.herdr("agent", "prompt", record["pane_id"], text)
    except HerdboardError as error:
        return {**notice, "status": "failed", "error": str(error)}
    try:
        activity.append(store, ref, f"Told agent {agent}: {labels}.", "herdboard")
    except HerdboardError as error:
        # The agent has the prompt; only the log entry is missing.
        notice["error"] = f"The agent has the prompt, but the log entry failed: {error}"
    return notice
