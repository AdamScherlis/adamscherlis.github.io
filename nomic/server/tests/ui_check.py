"""Manual UI check: drives a running server with headless Chrome and saves
screenshots. Runs a real Claude Phase if --claude is given.

    uv run python tests/ui_check.py --url http://127.0.0.1:8790 --out /some/dir \
        --root-password devpass [--claude]
"""

import argparse
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--root-name", default="Adam")
    ap.add_argument("--root-password", required=True)
    ap.add_argument("--claude", action="store_true")
    ap.add_argument("--api", help="Game server URL, if the frontend is served from elsewhere.")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")

        def page(viewport, path=""):
            ctx = browser.new_context(viewport=viewport)
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
            if args.api:
                path += ("&" if "?" in path else "?") + "api=" + args.api
            pg.goto(args.url + "/" + path)
            pg.wait_for_selector("#players li", state="attached")
            return pg

        def login(pg, name, pw, mode):
            pg.fill("#auth-name", name)
            pg.fill("#auth-pw", pw)
            pg.click(f"#auth-form button[data-mode={mode}]")
            pg.wait_for_selector("#you:not([hidden])")

        root = page({"width": 1440, "height": 900})
        login(root, args.root_name, args.root_password, "login")
        projector = page({"width": 1920, "height": 1080}, "?view=projector")
        alice = page({"width": 390, "height": 844})
        login(alice, f"Alice{int(time.time()) % 1000}", "alicepw", "signup")
        root.screenshot(path=out / "1-root-lobby.png")
        alice.screenshot(path=out / "1-phone-lobby.png")

        if root.is_visible("button[data-root=start]"):
            root.click("button[data-root=start]")
        root.wait_for_selector("button[data-root=end_phase]:not([hidden])")
        alice.wait_for_selector(".action button:not([disabled])")
        alice.fill(".action textarea", "Every rule proposed in iambic pentameter earns its "
                                       "proposer one Sonnet Token.")
        alice.click(".action button")
        alice.wait_for_function(
            "document.getElementById('actions-used').textContent.startsWith('1/')", timeout=1500)
        root.fill(".action textarea", "The root player may declare one Holiday per day.")
        root.click(".action button")
        root.wait_for_timeout(1000)
        root.screenshot(path=out / "2-root-player-phase.png")
        alice.screenshot(path=out / "2-phone-play.png")
        alice.click("#tabs button[data-tab=log]")
        alice.screenshot(path=out / "2-phone-log.png")
        projector.screenshot(path=out / "2-projector.png")

        if args.claude:
            root.click("button[data-root=end_phase]")
            projector.wait_for_selector("#panel-claude:not([hidden])")
            projector.wait_for_timeout(4000)
            projector.screenshot(path=out / "3-projector-claude.png")
            root.wait_for_selector("button[data-root=end_phase]:not([hidden])", timeout=300000)
            projector.wait_for_timeout(1000)
            projector.screenshot(path=out / "4-projector-after.png")
            root.screenshot(path=out / "4-root-after.png")
            alice.click("#tabs button[data-tab=constitution]")
            alice.screenshot(path=out / "4-phone-constitution.png")
            alice.click("#tabs button[data-tab=players]")
            alice.screenshot(path=out / "4-phone-players.png")

        browser.close()
    print("\n".join(errors) or "no JS errors")


if __name__ == "__main__":
    main()
