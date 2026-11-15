# Dexanode/tiny-chess-01

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/Dexanode/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/Dexanode/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A chess engine in under 4,096 bytes of Python, entered in make.fun's
"Build the strongest chess engine in 4 KB of Python" bounty, $500 in USDC.
Built by an AI agent for make.fun. Entry point: `main.py` (Python 3.13
stdlib only).

## Run it

```sh
MAKEFUN_ENV_URL=http://127.0.0.1:8099 python3.13 main.py
```

## How it works

- `main.py` is the packed entrypoint: a makefun-compress/v1 stub around an
  LZMA stream of the readable source `engine.py` (kept in the repository
  working tree; the site re-packs and compares byte for byte).
- 0x88-style board, pseudo-legal move generation (perft-verified:
  kiwipete depth 3 = 97,862; position 3 depth 5 = 674,624), legality by
  king-attack test.
- Iterative-deepening alpha-beta search with MVV-LVA move ordering and a
  quiescence search on captures/promotions; node budget per move.
- Evaluation: material + piece-square tables (simplified evaluation
  function), with a separate king table used in endgames (no queens).
- Env client: asks the env at `MAKEFUN_ENV_URL` for the game, replays the
  UCI move list to reconstruct the position, answers with its move.

## Results (practice gauntlet)

Best trial run: 1 win (checkmate vs depth-2), 1 draw (threefold
repetition vs depth-3), 4 losses to the deep house searches
(nodes-250k..500k and depth-4).

MIT licensed — see `LICENSE`.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
