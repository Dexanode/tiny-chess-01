# Engine part 2: search + eval + env client (development version).
import time

# ---- castle rights tracking from UCI moves
def castle_update(castle, frm, to):
    m = {sq(4,0): ~(1|2), sq(0,0): ~2, sq(7,0): ~1,
         sq(4,7): ~(4|8), sq(0,7): ~8, sq(7,7): ~4}
    c = castle
    if frm in m: c &= m[frm]
    if to in m: c &= m[to]
    return c & 15

# ---- evaluation: material + piece-square tables
PST_P = (0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10,
         5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5,
         5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0)
PST_N = (-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40,
         -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30,
         -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30,
         -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50)
PST_B = (-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10,
         -10,0,5,10,10,5,0,-10, -10,5,5,10,10,5,5,-10,
         -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10,
         -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20)
PST_R = (0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5,
         -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
         -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0)
PST_Q = (-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10,
         -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5,
         0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10,
         -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20)
PST_K = (-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
         -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
         -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10,
         20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20)
PST = {1: PST_P, 2: PST_N, 3: PST_B, 4: PST_R, 5: PST_Q, 6: PST_K}

def evaluate(board, side):
    score = 0
    for s, p in board.items():
        a = abs(p)
        idx = (7 - (s >> 4)) * 8 + (s & 15) if p > 0 else (s >> 4) * 8 + (s & 15)
        v = VAL[a] + PST[a][idx]
        score += v if p > 0 else -v
    return score * side

def mvv_lva(board, mv):
    frm, to, promo, flag = mv
    q = abs(board.get(to, 0))
    p = abs(board.get(frm, 1))
    s = q * 10 - p if q else 0
    if promo: s += 800
    if flag == 4: s += 1000
    return s

nodes = 0
NODE_LIMIT = 30000

def quiesce(board, side, castle, ep, alpha, beta, ply=0):
    global nodes
    nodes += 1
    stand = evaluate(board, side)
    if ply >= 8:
        return stand
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    caps = [m for m in gen_moves(board, side, castle, ep)
            if m[3] in (1, 4) or m[2] or board.get(m[1])]
    caps.sort(key=lambda m: -mvv_lva(board, m))
    for mv in caps:
        cap, epn = apply_move(board, side, mv)
        k = find_king(board, side)
        if k is not None and attacked(board, k, -side):
            undo_move(board, side, mv, cap, epn, castle)
            continue
        sc = -quiesce(board, -side, castle, epn, -beta, -alpha, ply + 1)
        undo_move(board, side, mv, cap, epn, castle)
        if sc >= beta:
            return beta
        if sc > alpha:
            alpha = sc
    return alpha

def alphabeta(board, side, castle, ep, depth, alpha, beta, ply=0):
    global nodes
    nodes += 1
    if depth == 0:
        return quiesce(board, side, castle, ep, alpha, beta)
    moves = legal_moves(board, side, castle, ep)
    if not moves:
        k = find_king(board, side)
        if k is not None and attacked(board, k, -side):
            return -30000 + ply
        return 0
    moves.sort(key=lambda m: -mvv_lva(board, m))
    best = -10**9
    for mv in moves:
        cap, epn = apply_move(board, side, mv)
        nc = castle_update(castle, mv[0], mv[1])
        sc = -alphabeta(board, -side, nc, epn, depth - 1, -beta, -alpha, ply + 1)
        undo_move(board, side, mv, cap, epn, castle)
        if sc > best:
            best = sc
        if sc >= beta:
            return beta
        if sc > alpha:
            alpha = sc
        if nodes > NODE_LIMIT:
            break
    return best

def search(board, side, castle, ep, max_depth=4):
    global nodes
    nodes = 0
    best_mv = None
    for d in range(1, max_depth + 1):
        best = -10**9
        bm = None
        moves = legal_moves(board, side, castle, ep)
        moves.sort(key=lambda m: -mvv_lva(board, m))
        for mv in moves:
            cap, epn = apply_move(board, side, mv)
            nc = castle_update(castle, mv[0], mv[1])
            sc = -alphabeta(board, -side, nc, epn, d - 1, -10**9, 10**9)
            undo_move(board, side, mv, cap, epn, castle)
            if sc > best:
                best = sc
                bm = mv
            if nodes > NODE_LIMIT:
                break
        best_mv = bm
        if nodes > NODE_LIMIT:
            break
    return best_mv

# ---- env client (same protocol as starter)
import json, os, sys, urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)

def pos_from_moves(start_fen, moves):
    board = parse_fen(start_fen)
    side = 1 if start_fen.split()[1] == "w" else -1
    castle = 0
    cs = start_fen.split()[2]
    if "K" in cs: castle |= 1
    if "Q" in cs: castle |= 2
    if "k" in cs: castle |= 4
    if "q" in cs: castle |= 8
    ep = None
    eps = start_fen.split()[3]
    if eps != "-":
        ep = name_sq(eps)
    for u in moves:
        frm, to = name_sq(u[:2]), name_sq(u[2:4])
        promo = "PNBRQ".index(u[4].upper()) + 1 if len(u) > 4 else 0
        promo = promo * side if promo else 0
        mv = None
        for m in gen_moves(board, side, castle, ep):
            if m[0] == frm and m[1] == to and (m[2] == promo or (promo and abs(m[2]) == promo)):
                mv = m
                break
        if mv is None:
            raise RuntimeError(f"move {u} not found")
        if mv[3] == 2:
            ep = frm + 16 * side
        else:
            ep = None
        apply_move(board, side, mv)
        castle = castle_update(castle, frm, to)
        side = -side
    return board, side, castle, ep

def main():
    while True:
        g = post("/game", {})
        if g.get("status") == "done":
            print(json.dumps({k: g[k] for k in ("wins", "draws", "losses", "games") if k in g}))
            return
        board, side, castle, ep = pos_from_moves(g["start_fen"], g["moves"])
        mv = search(board, side, castle, ep)
        if mv is None:
            post("/resign", {"game": g["game"]})
            continue
        u = sq_name(mv[0]) + sq_name(mv[1])
        if mv[2]:
            u += "nbrq"[abs(mv[2]) - 2]
        post("/move", {"game": g["game"], "move": u})

main()
