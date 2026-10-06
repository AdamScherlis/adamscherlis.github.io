"""Entry point.

    uv run python -m nomic_server serve [--port 8787]
    uv run python -m nomic_server make-root NAME [--password PW]
    uv run python -m nomic_server set-password NAME [--password PW]
    uv run python -m nomic_server unroot NAME
"""

import argparse
import os
import secrets
from pathlib import Path

from .app import SERVER_DIR, create_app, hash_password, validate_name
from .store import Store


def main():
    ap = argparse.ArgumentParser(prog="nomic_server")
    ap.add_argument("--data-dir", default=os.environ.get("NOMIC_DATA_DIR", str(SERVER_DIR / "data")))
    sub = ap.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="Run the game server.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--key-file", default=os.environ.get("NOMIC_KEY_FILE", "~/nomic_key"))

    for name, help_ in [("make-root", "Create or promote the root player."),
                        ("set-password", "Reset a player's password (logs them out)."),
                        ("unroot", "Remove root powers from a player.")]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("name")
        if name != "unroot":
            p.add_argument("--password", help="Defaults to a random password, printed once.")

    args = ap.parse_args()
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    if args.cmd == "serve":
        import uvicorn
        key = Path(args.key_file).expanduser().read_text().strip()
        app = create_app(data_dir=data_dir, api_key=key)
        uvicorn.run(app, host=args.host, port=args.port, proxy_headers=True,
                    forwarded_allow_ips="*")
        return

    store = Store(str(data_dir / "nomic.sqlite"))
    player = store.player_by_name(" ".join(args.name.split()))
    password = getattr(args, "password", None) or secrets.token_urlsafe(9)

    if args.cmd == "make-root":
        if player:
            store.set_root(player["id"], True)
            print(f"{player['name']} is now root.")
        else:
            name = " ".join(args.name.split())
            validate_name(name)
            store.create_player(name, hash_password(password), is_root=True)
            print(f"Created root player {name!r} with password: {password}")
    elif args.cmd == "set-password":
        if not player:
            raise SystemExit(f"No player named {args.name!r}.")
        store.set_password(player["id"], hash_password(password))
        print(f"New password for {player['name']}: {password}")
    elif args.cmd == "unroot":
        if not player:
            raise SystemExit(f"No player named {args.name!r}.")
        store.set_root(player["id"], False)
        print(f"{player['name']} is no longer root.")


if __name__ == "__main__":
    main()
