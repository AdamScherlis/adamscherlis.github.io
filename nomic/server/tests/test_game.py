"""End-to-end API tests with a scripted stand-in for Claude (no API calls)."""

import time

import pytest
from fastapi.testclient import TestClient

from nomic_server.app import create_app


class FakeClaude:
    """Adopts the first proposal of the round, like the initial Constitution says."""

    def __init__(self):
        self.calls = 0

    async def run(self, game, round_no):
        self.calls += 1
        game.note_start("thinking")
        game.note_append("Reading the proposals…")
        proposals = [e for e in game.store.log_for_round(round_no)
                     if e["kind"] == "action" and e["action"] == "Propose Rule"]
        if proposals:
            p = proposals[0]
            text = p["text"].split(": ", 1)[1]
            game.apply_tool("add_rule", {"text": text, "proposed_by": p["actor"]})
            game.apply_tool("give_items", {"player": p["actor"], "item": "Victory Point",
                                           "quantity": 1})
        game.apply_tool("post_to_log", {"message": f"Round {round_no} judged."})


@pytest.fixture
def env(tmp_path):
    fake = FakeClaude()
    app = create_app(data_dir=tmp_path, claude_runner=fake)
    with TestClient(app) as client:
        yield client, app, fake


def signup(client, name, pw="pass1234"):
    r = client.post("/api/signup", json={"name": name, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def state(client, headers=None):
    return client.get("/api/state", headers=headers or {}).json()


def wait_for(client, pred, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = state(client)
        if pred(s):
            return s
        time.sleep(0.05)
    raise AssertionError("condition never became true")


def test_signup_validation(env):
    client, app, _ = env
    signup(client, "Alice")
    assert client.post("/api/signup", json={"name": "alice", "password": "xxxx"}).status_code == 400
    assert client.post("/api/signup", json={"name": "Claude", "password": "xxxx"}).status_code == 400
    assert client.post("/api/signup", json={"name": "<b>x</b>", "password": "xxxx"}).status_code == 400
    assert client.post("/api/signup", json={"name": "Bob", "password": "x"}).status_code == 400
    r = client.post("/api/login", json={"name": "ALICE", "password": "pass1234"})
    assert r.status_code == 200
    assert client.post("/api/login", json={"name": "Alice", "password": "nope"}).status_code == 400


def test_full_round(env):
    client, app, fake = env
    root = signup(client, "Adam")
    app.state.store.set_root(app.state.store.player_by_name("Adam")["id"])
    alice = signup(client, "Alice")
    bob = signup(client, "Bob")

    # Not started yet
    r = client.post("/api/act", headers=alice, json={"action": "Propose Rule", "text": "x"})
    assert r.status_code == 400
    # Non-root can't start
    assert client.post("/api/root/start", headers=alice, json={}).status_code == 400
    assert client.post("/api/root/start", headers=root, json={}).status_code == 200

    s = state(client, alice)
    assert s["state"]["phase"] == "player" and s["state"]["round"] == 1
    assert s["me"]["name"] == "Alice" and "root" not in s

    r = client.post("/api/act", headers=alice,
                    json={"action": "Propose Rule", "text": "Alice is cool."})
    assert r.status_code == 200, r.text
    client.post("/api/act", headers=bob, json={"action": "Propose Rule", "text": "Bob rules."})
    assert client.post("/api/act", headers=bob,
                       json={"action": "Nonexistent", "text": "x"}).status_code == 400
    # Per-round cap
    for _ in range(4):
        assert client.post("/api/act", headers=bob, json={"action": "Propose Rule"}).status_code == 200
    r = client.post("/api/act", headers=bob, json={"action": "Propose Rule"})
    assert r.status_code == 400 and "all 5" in r.json()["error"]

    assert client.post("/api/root/end_phase", headers=root, json={}).status_code == 200
    s = wait_for(client, lambda s: s["state"]["round"] == 2)
    assert fake.calls == 1
    rules = s["state"]["rules"]
    assert rules[-1]["text"] == "Alice is cool." and rules[-1]["num"] == 7
    alice_p = next(p for p in s["state"]["players"] if p["name"] == "Alice")
    assert alice_p["vp"] == 1
    texts = [e["text"] for e in s["log"]]
    assert "Alice did Propose Rule: Alice is cool." in texts
    assert any("Claude added Rule 7 (proposed by Alice)" in t for t in texts)
    assert s["state"]["claude"]["status"] == "done"
    assert s["state"]["claude"]["notes"][0]["text"] == "Reading the proposals…"

    # Incremental log fetch
    last = s["log"][-1]["id"]
    s2 = client.get(f"/api/state?log_after={last}").json()
    assert s2["log"] == [] and not s2["log_reset"]


def test_long_poll_wakes_on_change(env):
    client, app, _ = env
    alice = signup(client, "Alice")
    v = state(client)["state"]["version"]
    t0 = time.time()
    # No change: returns after the timeout... too slow to test fully, so make a change first.
    signup(client, "Bob")
    s = client.get(f"/api/state?v={v}&wait=1").json()
    assert s["state"]["version"] != v and time.time() - t0 < 5


def test_pause_resume_reset(env):
    client, app, fake = env
    root = signup(client, "Adam")
    app.state.store.set_root(app.state.store.player_by_name("Adam")["id"])
    client.post("/api/root/start", headers=root, json={})
    assert client.post("/api/root/pause", headers=root, json={}).status_code == 200
    s = state(client)["state"]
    assert s["paused"] and s["phase_ends_at"] is None and s["paused_remaining"] > 50
    r = client.post("/api/act", headers=root, json={"action": "Propose Rule", "text": "x"})
    assert r.status_code == 400
    assert client.post("/api/root/resume", headers=root, json={}).status_code == 200
    assert state(client)["state"]["phase_ends_at"] > time.time() + 50

    r = client.post("/api/root/settings", headers=root,
                    json={"player_phase_seconds": 120, "effort": "low", "skip_idle": False})
    assert r.status_code == 200
    s = state(client, root)
    assert s["state"]["player_phase_seconds"] == 120 and s["state"]["settings"]["effort"] == "low"
    assert "usage" in s["root"]

    assert client.post("/api/root/reset", headers=root, json={}).status_code == 400
    old_game = s["state"]["game_id"]
    assert client.post("/api/root/reset", headers=root, json={"confirm": "RESET"}).status_code == 200
    s = state(client)
    assert s["state"]["status"] == "lobby" and s["state"]["game_id"] != old_game
    assert len(s["state"]["rules"]) == 6
    assert s["state"]["settings"]["effort"] == "low"  # settings survive a reset
    assert list((app.state.game.data_dir / "archive").glob("*.sqlite"))


def test_tools_validation(env):
    client, app, _ = env
    signup(client, "Alice")
    g = app.state.game
    from nomic_server.game import ToolError
    with pytest.raises(ToolError):
        g.apply_tool("give_items", {"player": "Nobody", "item": "Gold", "quantity": 1})
    g.apply_tool("give_items", {"player": "alice", "item": "Gold", "quantity": 3})
    g.apply_tool("give_items", {"player": "Alice", "item": "gold", "quantity": 2})
    assert g.inventory(g.store.player_by_name("Alice")["id"]) == [{"item": "Gold", "qty": 5}]
    with pytest.raises(ToolError):
        g.apply_tool("take_items", {"player": "Alice", "item": "Gold", "quantity": 6})
    g.apply_tool("take_items", {"player": "Alice", "item": "Gold", "quantity": 5})
    assert g.inventory(g.store.player_by_name("Alice")["id"]) == []
    g.apply_tool("create_action", {"name": "Trade", "description": "Offer a trade.",
                                   "allowed_players": ["alice"], "per_round_limit": 1})
    assert g.state["actions"][-1]["players"] == ["Alice"]
    g.apply_tool("update_action", {"name": "trade", "allowed_players": None})
    assert g.state["actions"][-1]["players"] is None
    with pytest.raises(ToolError):
        g.apply_tool("update_action", {"name": "trade", "bogus": 1})
    g.apply_tool("remove_action", {"name": "Trade"})
    with pytest.raises(ToolError):
        g.apply_tool("repeal_rule", {"number": 99})
    g.apply_tool("repeal_rule", {"number": 2})
    assert [r["num"] for r in g.state["rules"]] == [1, 3, 4, 5, 6]
    with pytest.raises(ToolError):
        g.apply_tool("set_player_phase_duration", {"seconds": 1})
    g.apply_tool("set_player_phase_duration", {"seconds": 300})
    assert g.state["player_phase_seconds"] == 300


def test_vp_counting(env):
    client, app, _ = env
    signup(client, "Alice")
    g = app.state.game
    g.apply_tool("give_items", {"player": "Alice", "item": "Victory Points", "quantity": 2})
    g.apply_tool("give_items", {"player": "Alice", "item": "victory point", "quantity": 1})
    assert g.vp(g.store.player_by_name("Alice")["id"]) == 3
