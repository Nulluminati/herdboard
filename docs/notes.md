# Notes

The Notes tab is a scratchpad for quick notes and ideas next to the board. Each board has one note, and the inbox's note is the global note. Press `G` twice on the board, or click the Notes tab.

The notes are plain Markdown files, one in each board folder:

- `~/todos/boards/<board>/notes.md` for a board, such as `~/todos/boards/acme-api/notes.md`.
- `~/todos/boards/inbox/notes.md` for the global note.

herdboard creates a note file on its first save. It does not delete note files.

The tab shows the note of the board that the board tab shows. In the repo view, that is the repository's board. In the inbox view, it is the global note. In the all and mine views, it is the board of the selected card. Without a selected todo, such as on a Linear card, it is the global note.

The tab shows the note as Markdown. Press `e` to edit it as text. herdboard saves the edit 2 seconds after your last change, on `escape`, on `ctrl+s`, when you go to another tab and when you quit.

| Key | Action |
|---|---|
| `e` or enter | Edit the note |
| `t` | Show the global note, or go back to the board's note |
| `j` / `k` | Scroll |
| `r` | Read the file again |
| `escape` | In the editor: save and show the note. Else: back to the board |
| `ctrl+s` | In the editor: save now |
| `G` | Go to the Automations tab |

When you edit a note file in another application, such as a text editor, the tab shows the change within 2 seconds. In the editor, the tab does not read the file. When the file changed on disk during your edit, a save asks: `o` writes your edit over the file, `r` reads the file and drops your edit, and `escape` keeps editing.

When a save fails, for example because the disk is full, the error shows above the note and your edit stays. The tab stays open until the save works. `q` then asks before it quits without the edit.

Agents do not read or write the notes.
