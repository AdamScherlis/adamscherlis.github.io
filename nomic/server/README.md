# Constitutional Promptocracy — game server

A Claude-powered Nomic. The frontend (`../index.html`, `../app.js`, `../style.css`)
is static and served by GitHub Pages at `adam.scherl.is/nomic`. Everything that
needs a server — accounts, the round timer, the Log, and calls to Claude — lives
here and runs on a laptop, exposed to the internet by a cloudflared quick tunnel.

```
phones / projector ──► adam.scherl.is/nomic (GitHub Pages, static)
        │                  └─ reads nomic/backend.json → current tunnel URL
        └──── API calls ──► https://<random>.trycloudflare.com ──► this server (127.0.0.1:8787)
                                                                    ├─ SQLite in data/
                                                                    └─ Claude API (key: ~/nomic_key)
```

## Running it

```bash
./start.sh     # server + tunnel as systemd user services (survive closing the terminal)
./status.sh    # are they up? what's the tunnel URL?
./stop.sh      # stop both; game state stays in data/
```

`start.sh` downloads `cloudflared` into `bin/` the first time. The tunnel
wrapper (`tunnel.py`) commits the tunnel URL to `nomic/backend.json` on the
default branch via the GitHub API (using `gh`) whenever it changes, i.e. every
time cloudflared restarts. Pages takes a minute or two to pick that up; open
pages re-read `backend.json` when they lose the server, so they recover on
their own. Pull before pushing other changes, since these commits land on the remote.
`NOMIC_PUBLISH=0 ./start.sh` skips publishing; the game is then reachable at the
tunnel URL itself (the server serves the frontend too) or via `?api=<tunnel URL>`.

Things that stop the game: the laptop sleeping, losing network, or logging out.

Local development without the tunnel:

```bash
uv run python -m nomic_server --data-dir /some/scratch/dir serve --port 8790
# then open http://127.0.0.1:8790/
```

Any page can be pointed at a specific server with `?api=https://...`.

## Accounts and the root player

Anyone can sign up with a name and password from the page. The root player can
start, pause/resume, end a Player Phase early, cut a Claude Phase short, post
announcements, change settings, and reset the game. Root is granted from the
command line:

```bash
uv run python -m nomic_server make-root NAME [--password PW]   # create or promote
uv run python -m nomic_server set-password NAME [--password PW] # for forgotten passwords
uv run python -m nomic_server unroot NAME
```

The root player is still an ordinary player in the game; Claude is told who
the host is but that they have no in-game powers unless the Constitution
grants them.

## How a round works

1. **Player Phase** (default 1 minute): players press Action buttons; each adds
   "`<player> did <Action>: <text>`" to the Log. Spam limits (Claude and root can
   both change them, within 1–100 Actions and 50–10,000 characters): 5 Actions per
   player per round, 1000 characters each.
2. **Claude Phase**: the server sends Claude (default `claude-opus-5-5`, effort
   `medium`) the Constitution, players and inventories, Actions, and the Log
   (this round in full, plus the previous 200 entries), and runs a tool loop.
   Claude's tools edit the Constitution, Inventories, Actions, Player Phase
   duration, and spam limits, and post to the Log; every edit is logged automatically and shows
   up live. Claude's summarized reasoning streams to the "Claude's notes" panel.
3. Next round.

If a Player Phase ends with no actions at all, its timer just restarts instead
of running a Claude Phase (root can turn this off in Settings). This keeps an
idle game from spending money all weekend; rules like "every round, X" don't
tick while nobody is playing.

Requests use the server-side refusal fallback (`fallbacks: "default"`), so a
safety-classifier decline is retried on another model instead of ending the turn.
If a Claude Phase fails or times out (10 minutes by default), the game logs it
and moves on to the next round.

## Views

- `adam.scherl.is/nomic` — player view (phones get tabs)
- `adam.scherl.is/nomic/?view=projector` — big-screen view with a join QR code

## Files

- `nomic_server/game.py` — game state, round loop, root controls, Claude's tool operations
- `nomic_server/claude.py` — system prompt, tool schemas, snapshot, streaming tool loop
- `nomic_server/app.py` — HTTP API (long-polling `GET /api/state`)
- `nomic_server/store.py` — SQLite
- `tunnel.py` — cloudflared wrapper that publishes `backend.json`
- `data/` (gitignored) — `nomic.sqlite`, `archive/` (a backup per reset), root password
- `tests/test_game.py` — API tests with a scripted Claude (`uv run pytest`)
- `tests/smoke_claude.py` — one real Claude Phase (costs cents)
- `tests/ui_check.py` — drives the UI in headless Chrome and saves screenshots
- `tests/ui_settings_check.py` — root Settings form stays in sync with Claude's edits
