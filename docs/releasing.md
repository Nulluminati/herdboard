# Releasing

A release is a `vX.Y.Z` tag on `main` and a GitHub Release with the `CHANGELOG.md` section as its notes. The board compares its version with the latest GitHub Release and shows `↑ update` when that release is newer. `herdboard update` installs it.

The version is in three files: `pyproject.toml`, `herdr-plugin.toml` and `uv.lock`. Do not change them by hand.

## Cut a release

Ask an agent to release herdboard. The `herdboard-release` skill (`skills/herdboard-release/SKILL.md`) tells it to:

1. List the commits since the last tag.
2. Choose the next version from the Conventional Commit types: `feat` is a minor bump, `fix` and `perf` are a patch bump, and a breaking change is a major bump. While the version is `0.x`, a breaking change is a minor bump.
3. Write the `## [X.Y.Z] - YYYY-MM-DD` section in `CHANGELOG.md`.
4. Show you the version and the section, and wait for your approval.
5. Run `python3 bin/release.py X.Y.Z`.

Install the skill for a maintainer with `npx skills add Nulluminati/herdboard@herdboard-release -g -y`, or point the agent at the file.

To release without an agent, write the CHANGELOG section yourself and run the script.

## bin/release.py

```bash
python3 bin/release.py 0.3.0             # bump, commit, tag and push
python3 bin/release.py 0.3.0 --no-push   # bump, commit and tag only
```

The script checks first and changes nothing when a check fails:

- The version is `X.Y.Z` and higher than the version in `pyproject.toml`.
- The working tree has no change other than `CHANGELOG.md`.
- The branch is `main`, and `main` equals `origin/main` after a fetch.
- The tag `vX.Y.Z` does not exist.
- `CHANGELOG.md` has the section `## [X.Y.Z] - YYYY-MM-DD`.

Then it writes the version in `pyproject.toml` and `herdr-plugin.toml`, runs `uv lock`, and commits the three files and `CHANGELOG.md` as `chore(release): vX.Y.Z`. It creates the annotated tag `vX.Y.Z` and pushes `main` and the tag. When a push fails, the commit and the tag stay; the message gives the push command to finish.

## The Release workflow

The tag push starts `.github/workflows/release.yml`. It runs `bin/release_notes.py`, which fails when the tag differs from the version in `pyproject.toml` or `herdr-plugin.toml`, or when the CHANGELOG section is missing or empty. Then `gh release create` publishes the release with that section as its notes.

The workflow has `contents: write` and no other permission. It does not install herdboard and does not run the tests; CI ran them on `main`.
