"""Manual UI check: the root Settings form follows server-side changes (e.g.
Claude editing the spam limits) and a save only sends fields root edited.

    uv run python tests/ui_settings_check.py --url http://127.0.0.1:8790 --root-password devpass
"""

import argparse
import json
import urllib.request

from playwright.sync_api import sync_playwright


def post(url, path, body, token=None):
    req = urllib.request.Request(url + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--root-name", default="Adam")
    ap.add_argument("--root-password", required=True)
    args = ap.parse_args()
    token = post(args.url, "/api/login", {"name": args.root_name,
                                          "password": args.root_password})["token"]
    settings = lambda body: post(args.url, "/api/root/settings", body, token)  # noqa: E731
    settings({"max_actions_per_round": 5, "player_phase_seconds": 60})

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        pg = browser.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(args.url + "/")
        pg.fill("#auth-name", args.root_name)
        pg.fill("#auth-pw", args.root_password)
        pg.click("#auth-form button[data-mode=login]")
        pg.wait_for_selector("#root:not([hidden])")
        pg.click("#root-settings summary")
        field = "#settings-form [name=max_actions_per_round]"
        assert pg.input_value(field) == "5"

        settings({"max_actions_per_round": 3})       # stands in for Claude's tool
        pg.wait_for_function(f"document.querySelector('{field}').value === '3'", timeout=3000)
        print("form picked up a server-side change")

        pg.fill("#settings-form [name=player_phase_seconds]", "90")   # root starts editing
        settings({"max_actions_per_round": 7})       # changed underneath the open form
        pg.wait_for_timeout(1000)
        assert pg.input_value(field) == "3", "dirty form must not be overwritten"
        pg.click("#settings-form button[type=submit]")
        pg.wait_for_function(f"document.querySelector('{field}').value === '7'", timeout=3000)
        state = json.load(urllib.request.urlopen(args.url + "/api/state"))["state"]
        assert state["settings"]["max_actions_per_round"] == 7, state["settings"]
        assert state["player_phase_seconds"] == 90
        print("save sent only the edited field; the server-side change survived")
        browser.close()
    settings({"max_actions_per_round": 5, "player_phase_seconds": 60})


if __name__ == "__main__":
    main()
