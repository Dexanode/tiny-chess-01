# Minimal engine entrypoint for tiny-chess-01 (work in progress).
# Plays the gauntlet through the env at MAKEFUN_ENV_URL.
import json, os, sys, urllib.request

ENV = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("no MAKEFUN_ENV_URL")

def post(path, body):
    req = urllib.request.Request(ENV + path, data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def main():
    while True:
        g = post("/game", {})
        if g.get("status") == "done":
            print(json.dumps({k: g[k] for k in ("wins", "draws", "losses", "games") if k in g}))
            return
        # TODO: real search; pick a legal move for now
        mv = sorted(g["legal_moves"])[0]
        post("/move", {"game": g["game"], "move": mv})

main()
