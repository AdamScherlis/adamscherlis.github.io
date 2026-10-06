"""SQLite persistence: accounts, sessions, the append-only log, Claude turns,
and a key/value table holding the game state as one JSON document.

All access happens on the asyncio event-loop thread (the app only uses
`async def` handlers), so a single connection is safe.
"""

import json
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    name_key   TEXT NOT NULL UNIQUE,
    pw_hash    TEXT NOT NULL,
    is_root    INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    player_id  INTEGER NOT NULL REFERENCES players(id),
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS log (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts     REAL NOT NULL,
    round  INTEGER NOT NULL,
    kind   TEXT NOT NULL,
    actor  TEXT,
    action TEXT,
    text   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS log_round ON log(round, kind, actor);
CREATE TABLE IF NOT EXISTS claude_turns (
    round    INTEGER PRIMARY KEY,
    started  REAL NOT NULL,
    finished REAL,
    status   TEXT NOT NULL,
    notes    TEXT NOT NULL DEFAULT '[]',
    usage    TEXT NOT NULL DEFAULT '{}',
    error    TEXT
);
CREATE TABLE IF NOT EXISTS kv (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _row(r):
    return dict(r) if r is not None else None


class Store:
    def __init__(self, path):
        self.path = path
        self.db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(SCHEMA)

    # -- key/value ---------------------------------------------------------

    def get_kv(self, key, default=None):
        r = self.db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(r["value"]) if r else default

    def set_kv(self, key, value):
        self.db.execute(
            "INSERT INTO kv(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )

    # -- players -----------------------------------------------------------

    def create_player(self, name, pw_hash, is_root=False):
        cur = self.db.execute(
            "INSERT INTO players(name, name_key, pw_hash, is_root, created_at) VALUES(?,?,?,?,?)",
            (name, name.casefold(), pw_hash, int(is_root), time.time()),
        )
        return cur.lastrowid

    def player_by_name(self, name):
        return _row(self.db.execute(
            "SELECT * FROM players WHERE name_key=?", (name.casefold(),)).fetchone())

    def player_by_id(self, pid):
        return _row(self.db.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone())

    def all_players(self):
        return [_row(r) for r in self.db.execute("SELECT * FROM players ORDER BY id")]

    def player_count(self):
        return self.db.execute("SELECT COUNT(*) FROM players").fetchone()[0]

    def set_root(self, pid, is_root=True):
        self.db.execute("UPDATE players SET is_root=? WHERE id=?", (int(is_root), pid))

    def set_password(self, pid, pw_hash):
        self.db.execute("UPDATE players SET pw_hash=? WHERE id=?", (pw_hash, pid))
        self.db.execute("DELETE FROM sessions WHERE player_id=?", (pid,))

    # -- sessions ----------------------------------------------------------

    def create_session(self, token_hash, pid):
        self.db.execute(
            "INSERT INTO sessions(token_hash, player_id, created_at) VALUES(?,?,?)",
            (token_hash, pid, time.time()),
        )

    def player_for_token(self, token_hash):
        return _row(self.db.execute(
            "SELECT p.* FROM sessions s JOIN players p ON p.id=s.player_id WHERE s.token_hash=?",
            (token_hash,),
        ).fetchone())

    def delete_session(self, token_hash):
        self.db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))

    # -- log ---------------------------------------------------------------

    def append_log(self, round_no, kind, text, actor=None, action=None):
        ts = time.time()
        cur = self.db.execute(
            "INSERT INTO log(ts, round, kind, actor, action, text) VALUES(?,?,?,?,?,?)",
            (ts, round_no, kind, actor, action, text),
        )
        return {"id": cur.lastrowid, "ts": ts, "round": round_no, "kind": kind,
                "actor": actor, "action": action, "text": text}

    def log_after(self, after_id, limit):
        rows = self.db.execute(
            "SELECT * FROM log WHERE id>? ORDER BY id LIMIT ?", (after_id, limit)).fetchall()
        return [_row(r) for r in rows]

    def log_before(self, before_id, limit):
        rows = self.db.execute(
            "SELECT * FROM log WHERE id<? ORDER BY id DESC LIMIT ?", (before_id, limit)).fetchall()
        return [_row(r) for r in reversed(rows)]

    def log_tail(self, limit):
        return self.log_before(2**62, limit)

    def log_for_round(self, round_no):
        rows = self.db.execute("SELECT * FROM log WHERE round=? ORDER BY id", (round_no,))
        return [_row(r) for r in rows]

    def log_before_round(self, round_no, limit):
        rows = self.db.execute(
            "SELECT * FROM log WHERE round<? ORDER BY id DESC LIMIT ?", (round_no, limit)).fetchall()
        return [_row(r) for r in reversed(rows)]

    def log_count_before_round(self, round_no):
        return self.db.execute("SELECT COUNT(*) FROM log WHERE round<?", (round_no,)).fetchone()[0]

    def max_log_id(self):
        return self.db.execute("SELECT COALESCE(MAX(id), 0) FROM log").fetchone()[0]

    def count_actions(self, round_no, actor=None, action=None):
        q, args = "SELECT COUNT(*) FROM log WHERE round=? AND kind='action'", [round_no]
        if actor is not None:
            q += " AND actor=?"
            args.append(actor)
        if action is not None:
            q += " AND action=?"
            args.append(action)
        return self.db.execute(q, args).fetchone()[0]

    def actions_by_player(self, round_no, actor):
        rows = self.db.execute(
            "SELECT action, COUNT(*) AS n FROM log WHERE round=? AND kind='action' AND actor=? "
            "GROUP BY action", (round_no, actor))
        return {r["action"]: r["n"] for r in rows}

    # -- Claude turns ------------------------------------------------------

    def save_turn(self, turn):
        self.db.execute(
            "INSERT INTO claude_turns(round, started, finished, status, notes, usage, error) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(round) DO UPDATE SET "
            "started=excluded.started, finished=excluded.finished, status=excluded.status, "
            "notes=excluded.notes, usage=excluded.usage, error=excluded.error",
            (turn["round"], turn["started"], turn.get("finished"), turn["status"],
             json.dumps(turn["notes"]), json.dumps(turn["usage"]), turn.get("error")),
        )

    def get_turn(self, round_no):
        r = self.db.execute("SELECT * FROM claude_turns WHERE round=?", (round_no,)).fetchone()
        if r is None:
            return None
        t = dict(r)
        t["notes"] = json.loads(t["notes"])
        t["usage"] = json.loads(t["usage"])
        return t

    def latest_turn(self):
        r = self.db.execute("SELECT round FROM claude_turns ORDER BY round DESC LIMIT 1").fetchone()
        return self.get_turn(r["round"]) if r else None

    def total_usage(self):
        totals = {}
        for r in self.db.execute("SELECT usage FROM claude_turns"):
            for k, v in json.loads(r["usage"]).items():
                if isinstance(v, (int, float)):
                    totals[k] = totals.get(k, 0) + v
        return totals

    # -- reset -------------------------------------------------------------

    def clear_game(self):
        """Wipe the log and Claude turns, keeping accounts and sessions."""
        self.db.execute("DELETE FROM log")
        self.db.execute("DELETE FROM claude_turns")

    def backup_to(self, path):
        dest = sqlite3.connect(path)
        with dest:
            self.db.backup(dest)
        dest.close()
