"""HTTP API. Every handler is `async def` so all game/DB access stays on the
event-loop thread."""

import asyncio
import contextlib
import hashlib
import hmac
import os
import re
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .claude import ClaudeRunner
from .game import Game, GameError
from .store import Store

SERVER_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = SERVER_DIR.parent           # nomic/ (index.html, app.js, style.css)
FRONTEND_FILES = {"index.html", "app.js", "style.css"}

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.'-]{0,22}[A-Za-z0-9_.'-]$|^[A-Za-z0-9]$")
RESERVED = ("claude", "anthropic", "root", "system", "admin", "everyone", "nobody", "game")
MAX_PLAYERS = 1000
LONG_POLL_SECONDS = 25
INITIAL_LOG_ENTRIES = 300


def hash_password(password):
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${h.hex()}"


def check_password(password, stored):
    _, salt, h = stored.split("$")
    got = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1)
    return hmac.compare_digest(got.hex(), h)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def validate_name(name):
    name = " ".join((name or "").split())
    if not NAME_RE.match(name):
        raise GameError("Names are 1–24 characters: letters, digits, spaces, and _ . ' -")
    if any(word in name.casefold() for word in RESERVED):
        raise GameError("That name is reserved.")
    return name


def create_app(data_dir=None, api_key=None, claude_runner=None):
    data_dir = Path(data_dir or os.environ.get("NOMIC_DATA_DIR", SERVER_DIR / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    store = Store(str(data_dir / "nomic.sqlite"))
    if claude_runner is None and api_key:
        claude_runner = ClaudeRunner(api_key)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        game = Game(store, data_dir, claude_runner)
        app.state.game = game
        task = asyncio.create_task(game.run())
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    app = FastAPI(title="Constitutional Promptocracy", lifespan=lifespan)
    app.state.store = store
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"],
                       allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(GameError)
    async def game_error(request, exc):
        return JSONResponse({"error": str(exc)}, status_code=400)

    def current_player(request: Request, required=True):
        auth = request.headers.get("authorization", "")
        player = None
        if auth.lower().startswith("bearer "):
            player = store.player_for_token(token_hash(auth[7:].strip()))
        if player is None and required:
            raise GameError("Please log in.")
        return player

    def require_root(request):
        player = current_player(request)
        if not player["is_root"]:
            raise GameError("Only the root player can do that.")
        return player

    async def body(request):
        try:
            data = await request.json()
        except Exception:
            raise GameError("Expected a JSON body.")
        if not isinstance(data, dict):
            raise GameError("Expected a JSON object.")
        return data

    def session_response(player):
        token = secrets.token_urlsafe(32)
        store.create_session(token_hash(token), player["id"])
        return {"token": token, "me": app.state.game.player_view(player)}

    # -- API ---------------------------------------------------------------------

    @app.get("/api/health")
    async def health():
        return {"ok": True}

    @app.get("/api/state")
    async def state(request: Request, v: int = -1, log_after: int = -1, wait: int = 0):
        game = app.state.game
        if wait and v == game.version:
            await game.wait_change(v, LONG_POLL_SECONDS)
        player = current_player(request, required=False)
        out = {"state": game.public_state()}
        if log_after < 0 or log_after > store.max_log_id():
            out["log"] = store.log_tail(INITIAL_LOG_ENTRIES)
            out["log_reset"] = True
        else:
            out["log"] = store.log_after(log_after, 1000)
            out["log_reset"] = False
        if player:
            out["me"] = game.player_view(player)
            if player["is_root"]:
                out["root"] = game.root_view()
        return out

    @app.get("/api/log")
    async def older_log(before: int, limit: int = 200):
        return {"log": store.log_before(before, max(1, min(limit, 1000)))}

    @app.post("/api/signup")
    async def signup(request: Request):
        data = await body(request)
        name = validate_name(data.get("name"))
        password = data.get("password") or ""
        if len(password) < 4:
            raise GameError("Passwords need at least 4 characters.")
        if store.player_by_name(name):
            raise GameError("That name is taken.")
        if store.player_count() >= MAX_PLAYERS:
            raise GameError("The game is full.")
        pw_hash = await asyncio.to_thread(hash_password, password)
        if store.player_by_name(name):  # re-check after the await
            raise GameError("That name is taken.")
        pid = store.create_player(name, pw_hash)
        app.state.game.player_joined(name)
        return session_response(store.player_by_id(pid))

    @app.post("/api/login")
    async def login(request: Request):
        data = await body(request)
        player = store.player_by_name(" ".join((data.get("name") or "").split()))
        ok = player and await asyncio.to_thread(check_password, data.get("password") or "",
                                                player["pw_hash"])
        if not ok:
            raise GameError("Wrong name or password.")
        return session_response(player)

    @app.post("/api/logout")
    async def logout(request: Request):
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            store.delete_session(token_hash(auth[7:].strip()))
        return {"ok": True}

    @app.post("/api/act")
    async def act(request: Request):
        player = current_player(request)
        data = await body(request)
        text = data.get("text") or ""
        if not isinstance(text, str):
            raise GameError("Text must be a string.")
        entry = app.state.game.take_action(player, str(data.get("action") or ""), text)
        return {"ok": True, "entry": entry}

    @app.post("/api/root/{command}")
    async def root(command: str, request: Request):
        player = require_root(request)
        game = app.state.game
        who = player["name"]
        data = await body(request)
        if command == "start":
            game.root_start()
        elif command == "pause":
            game.root_pause(who)
        elif command == "resume":
            game.root_resume(who)
        elif command == "end_phase":
            game.root_end_phase(who)
        elif command == "abort_claude":
            game.root_abort_claude(who)
        elif command == "announce":
            game.root_announce(who, str(data.get("text") or ""))
        elif command == "settings":
            game.root_settings(data)
        elif command == "reset":
            if data.get("confirm") != "RESET":
                raise GameError("Send confirm: RESET to reset the game.")
            game.root_reset(who)
        else:
            raise GameError(f"Unknown command {command!r}.")
        return {"ok": True}

    # -- frontend (also served on GitHub Pages; this copy is for local use) ------

    @app.get("/")
    async def index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{name}")
    async def frontend(name: str):
        if name not in FRONTEND_FILES:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return FileResponse(FRONTEND_DIR / name)

    return app
