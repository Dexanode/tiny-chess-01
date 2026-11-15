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
    rows = fen.split()[0].split("/")
    for i, row in enumerate(rows):
        f = 0
        r = 7 - i
        for c in row:
            if c.isdigit():
                f += int(c)
            else:
                board[sq(f, r)] = (1 if c.isupper() else -1) * "PNBRQK".index(c.upper()) + (1 if c.isupper() else 0)
                f += 1
    # rewrite cleanly
    board = {}
    for i, row in enumerate(rows):
        f = 0
        r = 7 - i
        for c in row:
            if c.isdigit():
                f += int(c)
            else:
                u = c.isupper()
                board[sq(f, r)] = ("PNBRQK".index(c.upper()) + 1) * (1 if u else -1)
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
            if side > 0 and s == sq(4, 0):
                if (castle & 1) and sq(5, 0) not in board and sq(6, 0) not in board \
                        and not attacked(board, sq(5, 0), -1) and not attacked(board, s, -1):
                    moves.append((s, sq(6, 0), 0, 8))
                if (castle & 2) and sq(3, 0) not in board and sq(2, 0) not in board and sq(1, 0) not in board \
                        and not attacked(board, sq(3, 0), -1) and not attacked(board, s, -1):
                    moves.append((s, sq(2, 0), 0, 8))
            if side < 0 and s == sq(4, 7):
                if (castle & 4) and sq(5, 7) not in board and sq(6, 7) not in board \
                        and not attacked(board, sq(5, 7), 1) and not attacked(board, s, 1):
                    moves.append((s, sq(6, 7), 0, 8))
                if (castle & 8) and sq(3, 7) not in board and sq(2, 7) not in board and sq(1, 7) not in board \
                        and not attacked(board, sq(3, 7), 1) and not attacked(board, s, 1):
                    moves.append((s, sq(2, 7), 0, 8))
    return moves

def apply_move(board, side, mv):
    frm, to, promo, flag = mv
    captured = board.get(to, 0)
    ep_new = None
    piece = board.pop(frm)
    if flag == 8:  # castle: move the rook too
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
    # is square t attacked by colour `by` (1/-1)?
    for d in (-1, 1, -16, 16, -17, 17, -15, 15):
        s = t + d
        while not (s & 0x88):
            q = board.get(s)
            if q:
                a = abs(q)
                if (q > 0) == (by > 0):
                    if a == 5:
                        return True
                    if a == 4 and d in (1, -1, 16, -16):
                        return True
                    if a == 3 and d not in (1, -1, 16, -16):
                        return True
                break
            s += d
    for d in KN:
        s = t + d
        if not (s & 0x88):
            q = board.get(s)
            if q and (q > 0) == (by > 0) and abs(q) == 2:
                return True
    for d in (17, 16, 1, -1, -16, -17, 15, -15):
        s = t + d
        if not (s & 0x88):
            q = board.get(s)
            if q and (q > 0) == (by > 0) and abs(q) == 6:
                return True
    dd = (-15 * by, -17 * by)
    for d in dd:
        s = t + d
        if not (s & 0x88):
            q = board.get(s)
            if q and (q > 0) == (by > 0) and abs(q) == 1:
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
