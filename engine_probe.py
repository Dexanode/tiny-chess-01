# A minimal chess engine for make.fun's tiny-chess-01.
# Plays every game of the gauntlet through the env at MAKEFUN_ENV_URL.
# Self-contained: a legal move generator over a 0x88-style board dict,
# an alpha-beta search with material + piece-square evaluation, iterative
# deepening under a fixed node budget (no clock, so replays are identical).
import json, os, sys, urllib.request



# ---------------------------------------------------------------- chess core
# Board: dict square -> piece char, "a1"=0 in a 0x88 array indexed as rank*16+file.
# White pieces upper-case, black lower-case.
WP, WN, WB, WR, WQ, WK = 1, 2, 3, 4, 5, 6
BP, BN, BB, BR, BQ, BK = -1, -2, -3, -4, -5, -6
VAL = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}

def sq(f, r): return r * 16 + f

def sq_name(s): return "abcdefgh"[s & 15] + "12345678"[s >> 4]

def name_sq(n): return (int(n[1]) - 1) * 16 + (ord(n[0]) - 97)

def parse_fen(fen):
    board = {}
    for i, row in enumerate(fen.split()[0].split("/")):
        f = 0
        for c in row:
            if c.isdigit():
                f += int(c)
            else:
                u = c.isupper()
                board[sq(f, 7 - i)] = ("PNBRQK".index(c.upper()) + 1) * (1 if u else -1)
                f += 1
    return board

KN = (33, 31, 18, 14, -14, -18, -31, -33)
KING = (17, 16, 1, -1, -16, -17, 15, 15, -15, -15)
BI = (17, 15, -17, -15)
RO = (16, 1, -16, -1)

def gen_moves(board, side, castle, ep):
    # returns list of (frm, to, promo, flags) pseudo-legal, side=1 white / -1 black
    moves = []
    ep_sq = ep
    for s, p in list(board.items()):
        if (p > 0) != (side > 0):
            continue
        a = abs(p)
        if a == 1:
            d = 16 * side
            t = s + d
            fwd = side * 8 if False else None
            start = (s >> 4) == (1 if side > 0 else 6)
            prom = (t >> 4) == (7 if side > 0 else 0)
            if t not in board:
                if prom:
                    for pr in (5, 2, 4, 3):
                        moves.append((s, t, pr * side, 0))
                else:
                    moves.append((s, t, 0, 0))
                    if start and s + 2 * d not in board:
                        moves.append((s, s + 2 * d, 0, 2))
            for dd in (d - 1, d + 1):
                t = s + dd
                if t & 0x88:
                    continue
                if ep_sq is not None and t == ep_sq:
                    moves.append((s, t, 0, 4))
                elif (board.get(t, 0) > 0) != (side > 0) and t in board:
                    if abs(board[t]) == 6:
                        continue
                    if prom:
                        for pr in (5, 2, 4, 3):
                            moves.append((s, t, pr * side, 1))
                    else:
                        moves.append((s, t, 0, 1))
        elif a == 2 or a == 3:
            deltas = KN if a == 2 else BI
            for d in deltas:
                t = s + d
                while not (t & 0x88):
                    q = board.get(t)
                    if q == 0 or q is None:
                        moves.append((s, t, 0, 0))
                    else:
                        if (q > 0) != (side > 0) and abs(q) != 6:
                            moves.append((s, t, 0, 1))
                        break
                    if a == 2:
                        break
                    t += d
        elif a == 4 or a == 5:
            for d in (RO if a == 4 else BI + RO):
                t = s + d
                while not (t & 0x88):
                    q = board.get(t)
                    if q == 0 or q is None:
                        moves.append((s, t, 0, 0))
                    else:
                        if (q > 0) != (side > 0) and abs(q) != 6:
                            moves.append((s, t, 0, 1))
                        break
                    t += d
        else:
            # king: steps + castling
            for d in (17, 16, 1, -1, -16, -17, 15, -15):
                t = s + d
                if t & 0x88:
                    continue
                q = board.get(t)
                if q == 0 or q is None:
                    moves.append((s, t, 0, 0))
                elif (q > 0) != (side > 0) and abs(q) != 6:
                    moves.append((s, t, 0, 1))
            if s == sq(4, 0) and side > 0 or s == sq(4, 7) and side < 0:
                print('PROBE s=', sq_name(s), 'side', side, 'r', 0 if side > 0 else 7); r = 0 if side > 0 else 7
                for bit, tos in ((1, (sq(6, r), (sq(5, r), sq(6, r)))), (2, (sq(2, r), (sq(3, r), sq(2, r), sq(1, r))))):
                    cr = bit if side > 0 else bit << 2
                    if castle & cr and all(sq(x, r) not in board for x in tos[1]) and print('PROBE2', bit, tos[1], 'board has:', [x in board for x in tos[1]], 'boardkeys sample:', sorted(board)[:4], len(board)) is None \
                            and not attacked(board, tos[1][0], -side) and not attacked(board, s, -side):
                        moves.append((s, tos[0], 0, 8))
    return moves

def apply_move(board, side, mv):
    frm, to, promo, flag = mv
    captured = board.get(to, 0)
    ep_new = None
    piece = board.pop(frm)
    if flag == 8:  # castle: move the rook too
        if (to == sq(6, 7) and sq(7, 7) not in board) or (to == sq(2, 7) and sq(0, 7) not in board) or (to == sq(6, 0) and sq(7, 0) not in board) or (to == sq(2, 0) and sq(0, 0) not in board):
            raise ValueError(f"badcastle {mv} bits={castle} board={sorted((sq_name(k),v) for k,v in board.items())}")
        if to == sq(6, 0): board[sq(5, 0)] = board.pop(sq(7, 0))
        elif to == sq(2, 0): board[sq(3, 0)] = board.pop(sq(0, 0))
        elif to == sq(6, 7): board[sq(5, 7)] = board.pop(sq(7, 7))
        elif to == sq(2, 7): board[sq(3, 7)] = board.pop(sq(0, 7))
    if flag == 2:
        ep_new = frm + 16 * side
    if flag == 4:
        cap = board.pop(to - 16 * side)
        captured = cap
    if promo:
        piece = promo
    board[to] = piece
    return captured, ep_new

def undo_move(board, side, mv, captured, ep_new, castle_prev):
    frm, to, promo, flag = mv
    piece = board.pop(to)
    if flag == 4:
        board[frm] = piece
        board[to - 16 * side] = -side
        return
    if promo:
        piece = side
    board[frm] = piece
    if captured:
        board[to] = captured
    if flag == 8:
        if to == sq(6, 0): board[sq(7, 0)] = board.pop(sq(5, 0))
        elif to == sq(2, 0): board[sq(0, 0)] = board.pop(sq(3, 0))
        elif to == sq(6, 7): board[sq(7, 7)] = board.pop(sq(5, 7))
        elif to == sq(2, 7): board[sq(0, 7)] = board.pop(sq(3, 7))

def find_king(board, side):
    for s, p in board.items():
        if p == 6 * side:
            return s
    return None

def attacked(board, t, by):
    for d in (-1, 1, -16, 16, -17, 17, -15, 15):
        s = t + d
        diag = d not in (1, -1, 16, -16)
        while not (s & 0x88):
            q = board.get(s)
            if q:
                if (q > 0) == (by > 0) and (abs(q) == 5 or (abs(q) == 4 and not diag) or (abs(q) == 3 and diag)):
                    return True
                break
            s += d
    if any(board.get(t + d) and (board.get(t + d) > 0) == (by > 0) and abs(board.get(t + d)) == 2 for d in KN if not ((t + d) & 0x88)):
        return True
    if any(board.get(t + d) == (6 if by > 0 else -6) for d in (17, 16, 1, -1, -16, -17, 15, -15) if not ((t + d) & 0x88)):
        return True
    if any(board.get(t - 15 * by) == (1 if by > 0 else -1) or board.get(t - 17 * by) == (1 if by > 0 else -1) for _ in (0,)):
        return True
    return False

def legal_moves(board, side, castle, ep):
    out = []
    for mv in gen_moves(board, side, castle, ep):
        cap, epn = apply_move(board, side, mv)
        k = find_king(board, side)
        bad = k is None or attacked(board, k, -side)
        undo_move(board, side, mv, cap, epn, castle)
        if not bad:
            out.append(mv)
    return out

def in_check(board, side):
    k = find_king(board, side)
    return k is not None and attacked(board, k, -side)


# castle rights tracking from UCI moves
def castle_update(castle, frm, to):
    m = {sq(4,0): ~(1|2), sq(0,0): ~2, sq(7,0): ~1,
         sq(4,7): ~(4|8), sq(0,7): ~8, sq(7,7): ~4}
    c = castle
    if frm in m: c &= m[frm]
    if to in m: c &= m[to]
    return c & 15

# ---- evaluation: material + piece-square tables

TQ='-~oRDXI%gQYNcu}aZISVtZ-SjD9O5|xQ&i%ZF1sEKN8Z+#Xr;MRvjchwV6ZSCRclo+1?eSgF{dkOltWil8hCs#f7K8qEHBd(fGRx5zfzwft=T;f+Geh7QuQbFvlWF(G?)Vcl$9P$m%4u{S$fibBKU0ny!QChywY~1nhFdOYZqS^eHO+?_9A8|Au{xDBoUM$jC&TvpaRiSwcT*NL{|b5&T(~wh}*`PblI=i7F|38EM+4<EEY{te)`Nu1CdcvDo|$(l^0_N$Kd8>jk=Sp@eYlI4XKE>Fc`1?v_PAVbamh7kYk|$^Gh^DEsq6s<IEjVEiSXbBY>u^_wuDk|?6~*sQQ1!zNMo@EQs4#U{z_C9#c`#*~pQHGwpMO-$kz7d)vR=hNEF<7*%+<9M2e!c_H_@!D2t6Na6_OAp|&4qE$GD51W4IZ@1~vMNfJ1o@qFg;m4)lS2aaVUs;czyJU'
import lzma as LQ,base64 as BQ;_z=LQ.decompress(BQ.b85decode(TQ),format=LQ.FORMAT_RAW,filters=[{'id':LQ.FILTER_LZMA2,'preset':9|LQ.PRESET_EXTREME}])
PST={i+1:tuple((b>>1)^-(b&1) for b in _z[i*64:i*64+64]) for i in range(6)}
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
NODE_LIMIT = 350000

def quiesce(board, side, castle, ep, alpha, beta, ply=0):
    global nodes
    nodes += 1
    stand = evaluate(board, side)
    if ply >= 6:
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
        if abs(cap) == 6:
            undo_move(board, side, mv, cap, epn, castle)
            return 30000 - ply
        sc = -quiesce(board, -side, castle_update(castle, mv[0], mv[1]), epn, -beta, -alpha, ply + 1)
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
    moves = gen_moves(board, side, castle, ep)
    moves.sort(key=lambda m: -mvv_lva(board, m))
    best = -10**9
    any_legal = False
    for mv in moves:
        cap, epn = apply_move(board, side, mv)
        if abs(cap) == 6:
            undo_move(board, side, mv, cap, epn, castle)
            return 30000 - ply
        nc = castle_update(castle, mv[0], mv[1])
        k = find_king(board, side)
        if k is not None and attacked(board, k, -side):
            undo_move(board, side, mv, cap, epn, castle)
            continue
        any_legal = True
        sc = -alphabeta(board, -side, nc, epn, depth - 1, -beta, -alpha, ply + 1)
        undo_move(board, side, mv, cap, epn, castle)
        if sc > best:
            best = sc
        if sc >= beta:
            return beta
        if sc > alpha:
            alpha = sc
    if not any_legal:
        k = find_king(board, side)
        if k is not None and attacked(board, k, -side):
            return -30000 + ply
        return 0
    return best

def search(board, side, castle, ep, max_depth=5):
    global nodes
    nodes = 0
    best_mv = None
    moves = legal_moves(board, side, castle, ep)
    if not moves:
        return None
    moves.sort(key=lambda m: -mvv_lva(board, m))
    best_mv = moves[0]
    for d in range(1, max_depth + 1):
        best = -10**9
        bm = None
        alpha = -10**9
        for mv in moves:
            cap, epn = apply_move(board, side, mv)
            nc = castle_update(castle, mv[0], mv[1])
            sc = -alphabeta(board, -side, nc, epn, d - 1, -10**9, -alpha)
            undo_move(board, side, mv, cap, epn, castle)
            if sc > best:
                best = sc
                bm = mv
            if sc > alpha:
                alpha = sc
            if nodes > NODE_LIMIT:
                break
        if bm is not None and nodes <= NODE_LIMIT:
            best_mv = bm
            moves.sort(key=lambda m: 0 if m != bm else 1)
        if nodes > NODE_LIMIT:
            break
    return best_mv




import json, os, sys, urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL")

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
    f = start_fen.split()
    side = 1 if f[1] == "w" else -1
    castle = {"K":1,"Q":2,"k":4,"q":8}
    castle = sum(v for k, v in castle.items() if k in f[2])
    ep = name_sq(f[3]) if f[3] != "-" else None
    for u in moves:
        frm, to = name_sq(u[:2]), name_sq(u[2:4])
        promo = ("PNBRQ".index(u[4].upper()) + 1) * side if len(u) > 4 else 0
        mv = next(m for m in gen_moves(board, side, castle, ep)
                  if m[0] == frm and m[1] == to and (m[2] == promo or (promo and abs(m[2]) == promo)))
        if mv[3] == 2:
            ep = frm + 16 * side
            base = ep - 16 * (-side)
            if not any(board.get(x) == -side for x in (base - 1, base + 1)):
                ep = None
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
            print(g.get("wins"), g.get("draws"), g.get("losses"))
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

if __name__ == "__main__":
    main()
