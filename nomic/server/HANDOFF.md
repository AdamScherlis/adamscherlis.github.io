# Handoff: moving the Nomic server to a new machine

Read `README.md` in this directory first; it covers the architecture, how a
round works, and the scripts. This file covers what lives outside the repo and
how to bring the game up somewhere else.

## Where things stand (2026-11-05)

- The code is complete and on `master`, under `nomic/` only. The rest of the site
  is untouched, and the homepage doesn't link to the game.
- On the old machine the server and tunnel are **stopped** (systemd user units
  `nomic-server` / `nomic-tunnel` are inactive). `nomic/backend.json` still points
  at a dead `trycloudflare.com` URL, so `adam.scherl.is/nomic` shows "Can't reach
  the game server" until the new machine publishes a fresh one.
- The old machine's `data/` holds a playtest game: 3 accounts, the game running at
  round 8, 88 Log entries. Bring it over only if you want to keep that game and
  those accounts. Otherwise start fresh and recreate root (see below).

## What isn't in the repo

| What | Old location | Needed? | Notes |
|---|---|---|---|
| Claude API key | `~/nomic_key` | **Yes** | One line, `sk-ant-...`. Secret: copy it over a private channel, never commit it. Override the path with `--key-file` or `NOMIC_KEY_FILE`. |
| Game database | `nomic/server/data/nomic.sqlite` (+ `-wal`, `-shm`) | Optional | Most recent writes may still be in the `-wal` file. Stop the server first, then copy all three files, or make one clean file with `sqlite3 nomic.sqlite ".backup /path/nomic.sqlite"`. |
| Root password | `nomic/server/data/root_password.txt` | Optional | Root account is `Adam`. To reset it: `uv run python -m nomic_server set-password Adam`. |
| Reset backups | `nomic/server/data/archive/` | Optional | One SQLite file per root "Reset game". |
| cloudflared | `nomic/server/bin/cloudflared` | No | `start.sh` downloads it, but only the **linux-amd64** build (see below). |
| Python env | `nomic/server/.venv` | No | `uv sync` recreates it. |
| Side worktree | `~/personal/adamscherlis.github.io.nomic` (branch `nomic`) | No | Same commit as `master`; nothing unique in it. |

## Machine prerequisites

- **Linux with a systemd user session**: `start.sh` uses `systemd-run --user`.
  On macOS, run the two commands from `start.sh` under launchd or in a terminal
  multiplexer.
- **`uv`, `git`, `curl`.** `uv` installs the Python version it needs.
- **`gh` logged in** as an account that can push to
  `AdamScherlis/adamscherlis.github.io`. `tunnel.py` uses it to commit each new
  tunnel URL to `nomic/backend.json` on the default branch. Check with
  `gh auth status`. Without it, start with `NOMIC_PUBLISH=0` and update
  `backend.json` by hand.
- **CPU architecture**: on ARM (or macOS), change the download URL in `start.sh`
  to the matching cloudflared build (`cloudflared-linux-arm64`, or install it with
  Homebrew), or put a binary at `bin/cloudflared` yourself.
- **Optional**: Google Chrome, for `tests/ui_check.py` and
  `tests/ui_settings_check.py` (Playwright drives the system Chrome via
  `channel="chrome"`; no browser download needed).

## Bring-up on the new machine

```bash
git clone git@github.com:AdamScherlis/adamscherlis.github.io.git ~/personal/adamscherlis.github.io
cd ~/personal/adamscherlis.github.io/nomic/server
# put the API key at ~/nomic_key, and the data/ files here if you're keeping the old game
uv sync
uv run pytest -q tests                                   # 7 tests, no API calls
uv run python -m nomic_server make-root Adam             # only for a fresh data/; prints a password
./start.sh
./status.sh                                              # shows the tunnel URL, then "Published ..."
```

After about a minute (GitHub Pages rebuild), `adam.scherl.is/nomic` should
connect. Open pages re-read `backend.json` on their own when they lose the
server. To check Claude end to end (costs a few cents and uses a throwaway
database): `PYTHONPATH=. uv run python tests/smoke_claude.py`.

Keep the old machine's server stopped once the new one is up. Two tunnels would
keep overwriting `backend.json` with each other's URLs.

## Things to know

- **The machine has to stay awake and online.** If it sleeps, is offline, or the
  user logs out, the game stops. The systemd units don't survive reboots; run
  `./start.sh` again. Restarting cloudflared gives a new URL, which is
  republished automatically.
- **`tunnel.py` commits to the remote default branch** through the GitHub API, not
  `git push`. Pull before pushing other changes.
- **Claude Code can't push here.** A global pre-push hook in the owner's dotfiles
  (`~/.config/git/hooks/pre-push`) blocks pushes from Claude, so the owner pushes.
  Work on a side branch and ask before merging to `master`.
- **Restarting the server mid-Claude-Phase cuts that phase short.** It is logged,
  and the game moves on to the next round. Check `/api/state` first if you can.
- **Cost controls:** idle Player Phases don't call Claude (the root setting
  "Skip Claude Phase when nobody acted"), and root's Settings panel shows running
  token usage and an approximate dollar cost.

## Open ideas (not started)

- Sockpuppet protection: sign-up is open; there's a 1000-account cap and nothing else.
- A stable URL instead of quick tunnels: a named Cloudflare tunnel (needs a
  Cloudflare account) or a small always-on host would remove the
  `backend.json` republishing and the dependence on one machine staying awake.
- Linking the game from the homepage was left for the owner to decide.
