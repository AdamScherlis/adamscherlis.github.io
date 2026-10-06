"""Game engine: state, the round/phase loop, player actions, root controls,
and the state-editing operations exposed to Claude as tools.

The mutable game state (Constitution, Actions, Inventories, phase info,
settings) is one JSON document persisted after every change. Accounts and
the append-only Log live in their own tables (see store.py).
"""

import asyncio
import re
import secrets
import time
import traceback
from pathlib import Path

INITIAL_RULES = [
    "Claude always follows the Constitution to the best of its abilities.",
    "Claude is helpful.",
    "Claude is honest.",
    "Claude is harmless.",
    "Once per round, at the start of the Claude Phase, Claude picks its favorite "
    "Proposed Rule and adds it to the Constitution.",
    "Whenever Claude adds a Proposed Rule to the Constitution, it adds one Victory "
    "Point (item) to the Inventory of the player who Proposed it.",
]

INITIAL_ACTIONS = [
    {"name": "Propose Rule",
     "description": "Propose a new Rule for the Constitution.",
     "players": None, "per_round_limit": None},
]

DEFAULT_SETTINGS = {
    "model": "claude-opus-5-5",
    "effort": "medium",
    # If a Player Phase ends with no player actions, restart its timer instead
    # of running a (paid, log-cluttering) Claude Phase. Root can turn this off.
    "skip_idle": True,
    # Infrastructure guard rails (root-adjustable), on top of anything the
    # Constitution or per-Action limits say.
    "max_actions_per_round": 5,
    "max_text_len": 1000,
    "claude_timeout_s": 600,
    "log_context_entries": 200,
}

DEFAULT_PLAYER_PHASE_SECONDS = 60
MIN_PHASE_SECONDS, MAX_PHASE_SECONDS = 10, 7 * 24 * 3600
MODELS = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-haiku-4-5"]
EFFORTS = ["low", "medium", "high", "xhigh", "max"]

VP_RE = re.compile(r"^\s*victory\s*points?\s*$", re.IGNORECASE)


class GameError(Exception):
    """A request that the game rules or infrastructure don't allow."""


class ToolError(Exception):
    """A Claude tool call that couldn't be applied; reported back to Claude."""


def fresh_state(settings=None, player_phase_seconds=DEFAULT_PLAYER_PHASE_SECONDS):
    return {
        "game_id": secrets.token_hex(6),
        "status": "lobby",          # lobby | running
        "paused": False,
        "round": 0,
        "phase": "lobby",           # lobby | player | claude
        "phase_ends_at": None,
        "paused_remaining": None,
        "idle_restarts": 0,
        "player_phase_seconds": player_phase_seconds,
        "next_rule_num": len(INITIAL_RULES) + 1,
        "rules": [{"num": i + 1, "text": t, "proposer": None, "round": 0, "amended_round": None}
                  for i, t in enumerate(INITIAL_RULES)],
        "actions": [dict(a) for a in INITIAL_ACTIONS],
        "inventories": {},
        "settings": dict(settings or DEFAULT_SETTINGS),
        "started_at": None,
    }


def fmt_duration(seconds):
    seconds = int(round(seconds))
    if seconds % 86400 == 0 and seconds >= 86400:
        n = seconds // 86400
        return f"{n} day{'s' if n != 1 else ''}"
    if seconds % 3600 == 0 and seconds >= 3600:
        n = seconds // 3600
        return f"{n} hour{'s' if n != 1 else ''}"
    if seconds % 60 == 0 and seconds >= 60:
        n = seconds // 60
        return f"{n} minute{'s' if n != 1 else ''}"
    return f"{seconds} seconds"


def fmt_items(inv):
    return ", ".join(f"{e['qty']} × {e['item']}" for e in inv) or "(empty)"


class Game:
    def __init__(self, store, data_dir, claude_runner=None):
        self.store = store
        self.data_dir = Path(data_dir)
        self.claude_runner = claude_runner
        self.state = store.get_kv("state") or fresh_state()
        for k, v in DEFAULT_SETTINGS.items():  # pick up settings added later
            self.state["settings"].setdefault(k, v)
        # Changes on every boot so clients never mistake a restart for "no change".
        self.version = int(time.time() * 1000)
        self._changed = asyncio.Event()
        self._wake = asyncio.Event()
        self._force_claude = False
        self._abort_requested = False
        self.claude_task = None
        self.turn = store.latest_turn()   # latest Claude turn (notes shown to everyone)
        self._turn_dirty_at = 0.0
        self._save()

    # -- change notification -------------------------------------------------

    def _save(self):
        self.store.set_kv("state", self.state)

    def bump(self, save=True):
        if save:
            self._save()
        self.version += 1
        ev, self._changed = self._changed, asyncio.Event()
        ev.set()

    async def wait_change(self, client_version, timeout):
        if client_version != self.version:
            return
        ev = self._changed
        try:
            await asyncio.wait_for(ev.wait(), timeout)
        except (TimeoutError, asyncio.TimeoutError):
            pass

    def wake(self):
        self._wake.set()

    def log(self, kind, text, actor=None, action=None):
        return self.store.append_log(self.state["round"], kind, text, actor=actor, action=action)

    # -- views ----------------------------------------------------------------

    def inventory(self, pid):
        return self.state["inventories"].get(str(pid), [])

    def vp(self, pid):
        return sum(e["qty"] for e in self.inventory(pid) if VP_RE.match(e["item"]))

    def public_state(self):
        s = self.state
        players = [
            {"id": p["id"], "name": p["name"], "is_root": bool(p["is_root"]),
             "inventory": self.inventory(p["id"]), "vp": self.vp(p["id"])}
            for p in self.store.all_players()
        ]
        return {
            "game_id": s["game_id"],
            "status": s["status"],
            "paused": s["paused"],
            "round": s["round"],
            "phase": s["phase"],
            "phase_ends_at": s["phase_ends_at"],
            "paused_remaining": s["paused_remaining"],
            "idle_restarts": s["idle_restarts"],
            "player_phase_seconds": s["player_phase_seconds"],
            "rules": s["rules"],
            "actions": s["actions"],
            "players": players,
            "settings": s["settings"],
            "claude": self.turn,
            "round_action_count": self.store.count_actions(s["round"]) if s["round"] else 0,
            "now": time.time(),
            "version": self.version,
        }

    def player_view(self, player):
        s = self.state
        used = self.store.actions_by_player(s["round"], player["name"]) if s["round"] else {}
        return {"id": player["id"], "name": player["name"], "is_root": bool(player["is_root"]),
                "actions_used": used, "total_used": sum(used.values())}

    def root_view(self):
        usage = self.store.total_usage()
        return {"usage": usage, "models": MODELS, "efforts": EFFORTS,
                "claude_running": self.claude_task is not None}

    # -- player actions -----------------------------------------------------

    def action_available_to(self, action, name):
        allowed = action.get("players")
        return allowed is None or name.casefold() in {n.casefold() for n in allowed}

    def take_action(self, player, action_name, text):
        s = self.state
        if s["status"] != "running" or s["phase"] != "player":
            raise GameError("Actions can only be taken during the Player Phase.")
        if s["paused"]:
            raise GameError("The game is paused.")
        action = next((a for a in s["actions"] if a["name"] == action_name), None)
        if action is None:
            raise GameError(f"There is no Action called {action_name!r} (any more?).")
        name = player["name"]
        if not self.action_available_to(action, name):
            raise GameError(f"{action_name} isn't available to you.")
        text = (text or "").strip()
        if len(text) > s["settings"]["max_text_len"]:
            raise GameError(f"Text is limited to {s['settings']['max_text_len']} characters.")
        used = self.store.actions_by_player(s["round"], name)
        if sum(used.values()) >= s["settings"]["max_actions_per_round"]:
            raise GameError(f"You've used all {s['settings']['max_actions_per_round']} of your "
                            "Actions this round.")
        limit = action.get("per_round_limit")
        if limit is not None and used.get(action_name, 0) >= limit:
            raise GameError(f"{action_name} is limited to {limit} per round.")
        line = f"{name} did {action_name}: {text}" if text else f"{name} did {action_name}."
        entry = self.log("action", line, actor=name, action=action_name)
        self.bump()
        return entry

    def player_joined(self, name):
        self.log("system", f"{name} joined the game.")
        self.bump()

    # -- root controls -------------------------------------------------------

    def root_start(self):
        s = self.state
        if s["status"] != "lobby":
            raise GameError("The game has already started.")
        s["status"] = "running"
        s["started_at"] = time.time()
        self.log("system", "The game has begun!")
        self._start_player_phase(1)
        self.wake()

    def root_pause(self, who):
        s = self.state
        if s["status"] != "running" or s["paused"]:
            raise GameError("The game isn't running.")
        s["paused"] = True
        if s["phase"] == "player":
            s["paused_remaining"] = max(0.0, s["phase_ends_at"] - time.time())
            s["phase_ends_at"] = None
            self.log("root", f"{who} paused the game.")
        else:
            self.log("root", f"{who} paused the game (it will pause after this Claude Phase).")
        self.bump()
        self.wake()

    def root_resume(self, who):
        s = self.state
        if s["status"] != "running" or not s["paused"]:
            raise GameError("The game isn't paused.")
        s["paused"] = False
        if s["phase"] == "player":
            remaining = s["paused_remaining"]
            s["phase_ends_at"] = time.time() + (remaining if remaining else s["player_phase_seconds"])
            s["paused_remaining"] = None
        self.log("root", f"{who} resumed the game.")
        self.bump()
        self.wake()

    def root_end_phase(self, who):
        s = self.state
        if s["status"] != "running" or s["phase"] != "player" or s["paused"]:
            raise GameError("Can only end a running (unpaused) Player Phase.")
        s["phase_ends_at"] = time.time()
        self._force_claude = True
        self.log("root", f"{who} ended the Player Phase early.")
        self.bump()
        self.wake()

    def root_abort_claude(self, who):
        if self.claude_task is None:
            raise GameError("Claude isn't deliberating right now.")
        self._abort_requested = True
        self.log("root", f"{who} cut the Claude Phase short.")
        self.claude_task.cancel()
        self.bump()

    def root_announce(self, who, text):
        text = (text or "").strip()
        if not text:
            raise GameError("Nothing to announce.")
        self.log("root", f"{who} announces: {text[:2000]}")
        self.bump()

    def root_settings(self, changes):
        s = self.state
        st = s["settings"]
        if "player_phase_seconds" in changes:
            sec = int(changes["player_phase_seconds"])
            if not MIN_PHASE_SECONDS <= sec <= MAX_PHASE_SECONDS:
                raise GameError(f"Player Phase must be {MIN_PHASE_SECONDS}s–7 days.")
            s["player_phase_seconds"] = sec
        if "model" in changes:
            if changes["model"] not in MODELS:
                raise GameError("Unknown model.")
            st["model"] = changes["model"]
        if "effort" in changes:
            if changes["effort"] not in EFFORTS:
                raise GameError("Unknown effort level.")
            st["effort"] = changes["effort"]
        if "skip_idle" in changes:
            st["skip_idle"] = bool(changes["skip_idle"])
        for key, lo, hi in [("max_actions_per_round", 1, 100), ("max_text_len", 50, 10000),
                            ("claude_timeout_s", 30, 3600), ("log_context_entries", 0, 2000)]:
            if key in changes:
                v = int(changes[key])
                if not lo <= v <= hi:
                    raise GameError(f"{key} must be between {lo} and {hi}.")
                st[key] = v
        self.bump()

    def root_reset(self, who):
        if self.claude_task is not None:
            self._abort_requested = True
            self.claude_task.cancel()
        archive = self.data_dir / "archive"
        archive.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.store.backup_to(str(archive / f"game-{stamp}-{self.state['game_id']}.sqlite"))
        self.store.clear_game()
        self.state = fresh_state(self.state["settings"])
        self.turn = None
        self.log("system", f"{who} reset the game. Players keep their accounts; everything else "
                           "is back to the start.")
        self.bump()
        self.wake()

    # -- the round loop -----------------------------------------------------------

    def _start_player_phase(self, round_no):
        s = self.state
        s["round"] = round_no
        s["phase"] = "player"
        s["idle_restarts"] = 0
        dur = s["player_phase_seconds"]
        if s["paused"]:
            s["phase_ends_at"], s["paused_remaining"] = None, dur
        else:
            s["phase_ends_at"], s["paused_remaining"] = time.time() + dur, None
        self.log("phase", f"Round {round_no} — Player Phase ({fmt_duration(dur)}).")
        self.bump()

    async def _sleep_or_wake(self, delay):
        self._wake.clear()
        try:
            await asyncio.wait_for(self._wake.wait(), delay)
        except (TimeoutError, asyncio.TimeoutError):
            pass

    def _recover(self):
        """Handle a restart that interrupted a Claude Phase."""
        s = self.state
        if s["status"] == "running" and s["phase"] == "claude":
            self.log("system", "The server restarted during the Claude Phase, which was cut short.")
            if self.turn and self.turn["round"] == s["round"] and self.turn["status"] == "running":
                self.turn["status"] = "interrupted"
                self.turn["finished"] = time.time()
                self.store.save_turn(self.turn)
            self._start_player_phase(s["round"] + 1)

    async def run(self):
        self._recover()
        while True:
            try:
                await self._step()
            except asyncio.CancelledError:
                raise
            except Exception:
                traceback.print_exc()
                await asyncio.sleep(5)

    async def _step(self):
        s = self.state
        if s["status"] != "running" or s["paused"] or s["phase"] != "player":
            self._wake.clear()
            await self._wake.wait()
            return
        delay = s["phase_ends_at"] - time.time()
        if delay > 0:
            await self._sleep_or_wake(delay)
            return
        if (s["settings"]["skip_idle"] and not self._force_claude
                and self.store.count_actions(s["round"]) == 0):
            # Nobody did anything: give them another Player Phase, quietly.
            s["phase_ends_at"] = time.time() + s["player_phase_seconds"]
            s["idle_restarts"] += 1
            self.bump()
            return
        self._force_claude = False
        game_id = s["game_id"]
        await self._claude_phase()
        if self.state["game_id"] == game_id:  # unless root reset the game meanwhile
            self._start_player_phase(s["round"] + 1)

    async def _claude_phase(self):
        s = self.state
        r, game_id = s["round"], s["game_id"]
        s["phase"] = "claude"
        s["phase_ends_at"] = None
        self.log("phase", f"Round {r} — Claude Phase.")
        turn = self.turn = {"round": r, "started": time.time(), "finished": None,
                            "status": "running", "notes": [], "usage": {}, "error": None}
        self.store.save_turn(turn)
        self.bump()
        self._abort_requested = False
        if self.claude_runner is None:
            turn["status"], turn["error"] = "error", "No Claude configured."
        else:
            self.claude_task = asyncio.create_task(self.claude_runner.run(self, r))
            try:
                await asyncio.wait_for(asyncio.shield(self.claude_task),
                                       s["settings"]["claude_timeout_s"])
                turn["status"] = "done"
            except (TimeoutError, asyncio.TimeoutError):
                self.claude_task.cancel()
                turn["status"], turn["error"] = "timeout", "Claude ran out of time."
                self.log("system", "Claude ran out of time; the Claude Phase ends here.")
            except asyncio.CancelledError:
                if not self._abort_requested:
                    raise
                turn["status"] = "aborted"
            except Exception as e:  # API errors etc.
                traceback.print_exc()
                turn["status"], turn["error"] = "error", f"{type(e).__name__}: {e}"
                self.log("system", f"The Claude Phase failed ({type(e).__name__}); "
                                   "the game moves on to the next round.")
            finally:
                self.claude_task = None
        if self.state["game_id"] != game_id:
            return  # root reset the game mid-phase; this turn belongs to the old game
        turn["finished"] = time.time()
        self.store.save_turn(turn)
        self.bump()

    # -- Claude turn notes (shown live on the projector) ---------------------------

    def note_start(self, kind):
        self.turn["notes"].append({"type": kind, "text": ""})
        self._note_changed()

    def note_append(self, text):
        if not self.turn["notes"]:
            self.note_start("text")
        self.turn["notes"][-1]["text"] += text
        self._note_changed()

    def note_add(self, kind, text):
        self.turn["notes"].append({"type": kind, "text": text})
        self._note_changed(force=True)

    def _note_changed(self, force=False):
        now = time.time()
        if force or now - self._turn_dirty_at > 0.4:
            self._turn_dirty_at = now
            self.bump(save=False)

    def add_usage(self, usage):
        u = self.turn["usage"]
        for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                  "cache_creation_input_tokens"):
            u[k] = u.get(k, 0) + (getattr(usage, k, None) or 0)
        u["api_calls"] = u.get("api_calls", 0) + 1
        self.store.save_turn(self.turn)

    # -- Claude's tools ------------------------------------------------------------

    def _player(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ToolError("A player name is required.")
        p = self.store.player_by_name(name.strip())
        if p is None:
            names = ", ".join(q["name"] for q in self.store.all_players())
            raise ToolError(f"No player named {name!r}. Players: {names}")
        return p

    def _rule(self, number):
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise ToolError("Rule number must be an integer.")
        rule = next((r for r in self.state["rules"] if r["num"] == number), None)
        if rule is None:
            raise ToolError(f"There is no Rule {number} in the Constitution.")
        return rule

    def _action(self, name):
        a = next((a for a in self.state["actions"]
                  if isinstance(name, str) and a["name"].casefold() == name.strip().casefold()), None)
        if a is None:
            names = ", ".join(a["name"] for a in self.state["actions"]) or "(none)"
            raise ToolError(f"No Action named {name!r}. Actions: {names}")
        return a

    @staticmethod
    def _text(value, field, max_len, required=True):
        if value is None and not required:
            return None
        if not isinstance(value, str) or (required and not value.strip()):
            raise ToolError(f"{field} must be a non-empty string.")
        value = value.strip()
        if len(value) > max_len:
            raise ToolError(f"{field} is limited to {max_len} characters.")
        return value

    @staticmethod
    def _qty(value):
        try:
            q = int(value)
        except (TypeError, ValueError):
            raise ToolError("quantity must be a positive integer.")
        if not 1 <= q <= 10**9:
            raise ToolError("quantity must be between 1 and 1,000,000,000.")
        return q

    def _players_list(self, value):
        if value is None:
            return None
        if not isinstance(value, list):
            raise ToolError("allowed_players must be a list of player names, or null for everyone.")
        return [self._player(n)["name"] for n in value]

    def _change(self, text):
        self.log("change", text, actor="Claude")
        self.bump()
        return text

    def apply_tool(self, name, args):
        fn = getattr(self, f"tool_{name}", None)
        if fn is None:
            raise ToolError(f"Unknown tool {name}.")
        if not isinstance(args, dict):
            raise ToolError("Tool input must be an object.")
        try:
            return fn(**args)
        except TypeError as e:
            raise ToolError(f"Bad arguments: {e}")

    def tool_add_rule(self, text, proposed_by=None):
        s = self.state
        text = self._text(text, "text", 4000)
        proposer = self._player(proposed_by)["name"] if proposed_by else None
        if len(s["rules"]) >= 500:
            raise ToolError("The Constitution is full (500 rules).")
        num = s["next_rule_num"]
        s["next_rule_num"] += 1
        s["rules"].append({"num": num, "text": text, "proposer": proposer,
                           "round": s["round"], "amended_round": None})
        by = f" (proposed by {proposer})" if proposer else ""
        return self._change(f"Claude added Rule {num}{by}: {text}")

    def tool_amend_rule(self, number, text):
        rule = self._rule(number)
        rule["text"] = self._text(text, "text", 4000)
        rule["amended_round"] = self.state["round"]
        return self._change(f"Claude amended Rule {rule['num']}: {rule['text']}")

    def tool_repeal_rule(self, number):
        rule = self._rule(number)
        self.state["rules"].remove(rule)
        return self._change(f"Claude repealed Rule {rule['num']} ({rule['text'][:120]}"
                            f"{'…' if len(rule['text']) > 120 else ''}).")

    def tool_give_items(self, player, item, quantity=1):
        p = self._player(player)
        item = self._text(item, "item", 80)
        q = self._qty(quantity)
        inv = self.state["inventories"].setdefault(str(p["id"]), [])
        entry = next((e for e in inv if e["item"].casefold() == item.casefold()), None)
        if entry is None:
            entry = {"item": item, "qty": 0}
            inv.append(entry)
        entry["qty"] += q
        self._change(f"Claude gave {p['name']} {q} × {entry['item']}.")
        return f"Done. {p['name']} now has: {fmt_items(inv)}"

    def tool_take_items(self, player, item, quantity=1):
        p = self._player(player)
        item = self._text(item, "item", 80)
        q = self._qty(quantity)
        inv = self.state["inventories"].setdefault(str(p["id"]), [])
        entry = next((e for e in inv if e["item"].casefold() == item.casefold()), None)
        have = entry["qty"] if entry else 0
        if have < q:
            raise ToolError(f"{p['name']} has only {have} × {item}. Inventory: {fmt_items(inv)}")
        entry["qty"] -= q
        if entry["qty"] == 0:
            inv.remove(entry)
        self._change(f"Claude took {q} × {entry['item']} from {p['name']}.")
        return f"Done. {p['name']} now has: {fmt_items(inv)}"

    def tool_create_action(self, name, description="", allowed_players=None, per_round_limit=None):
        s = self.state
        name = self._text(name, "name", 40)
        if any(a["name"].casefold() == name.casefold() for a in s["actions"]):
            raise ToolError(f"An Action named {name!r} already exists.")
        if len(s["actions"]) >= 30:
            raise ToolError("There are already 30 Actions; remove one first.")
        action = {"name": name,
                  "description": self._text(description or "", "description", 300, required=False) or "",
                  "players": self._players_list(allowed_players),
                  "per_round_limit": self._limit(per_round_limit)}
        s["actions"].append(action)
        return self._change(f"Claude created the Action “{name}”{self._action_suffix(action)}")

    def tool_update_action(self, name, **changes):
        a = self._action(name)
        unknown = set(changes) - {"new_name", "description", "allowed_players", "per_round_limit"}
        if unknown:
            raise ToolError(f"Unknown fields: {', '.join(sorted(unknown))}")
        old = a["name"]
        if changes.get("new_name"):
            new = self._text(changes["new_name"], "new_name", 40)
            if new.casefold() != old.casefold() and any(
                    b["name"].casefold() == new.casefold() for b in self.state["actions"]):
                raise ToolError(f"An Action named {new!r} already exists.")
            a["name"] = new
        if "description" in changes:
            a["description"] = self._text(changes["description"] or "", "description", 300,
                                          required=False) or ""
        if "allowed_players" in changes:
            a["players"] = self._players_list(changes["allowed_players"])
        if "per_round_limit" in changes:
            a["per_round_limit"] = self._limit(changes["per_round_limit"])
        renamed = f" (now “{a['name']}”)" if a["name"] != old else ""
        return self._change(f"Claude changed the Action “{old}”{renamed}{self._action_suffix(a)}")

    def tool_remove_action(self, name):
        a = self._action(name)
        self.state["actions"].remove(a)
        return self._change(f"Claude removed the Action “{a['name']}”.")

    def tool_set_player_phase_duration(self, seconds):
        try:
            sec = int(seconds)
        except (TypeError, ValueError):
            raise ToolError("seconds must be an integer.")
        if not MIN_PHASE_SECONDS <= sec <= MAX_PHASE_SECONDS:
            raise ToolError(f"seconds must be between {MIN_PHASE_SECONDS} and {MAX_PHASE_SECONDS}.")
        self.state["player_phase_seconds"] = sec
        return self._change(f"Claude set the Player Phase duration to {fmt_duration(sec)}.")

    def tool_post_to_log(self, message):
        message = self._text(message, "message", 2000)
        self.log("claude", message, actor="Claude")
        self.bump()
        return "Posted."

    @staticmethod
    def _limit(value):
        if value is None:
            return None
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise ToolError("per_round_limit must be a positive integer or null.")
        if v < 1:
            raise ToolError("per_round_limit must be a positive integer or null.")
        return v

    @staticmethod
    def _action_suffix(a):
        bits = []
        if a.get("players") is not None:
            bits.append("only for " + (", ".join(a["players"]) or "nobody"))
        if a.get("per_round_limit") is not None:
            bits.append(f"limit {a['per_round_limit']} per player per round")
        desc = f": {a['description']}" if a.get("description") else "."
        return (f" [{'; '.join(bits)}]" if bits else "") + desc

