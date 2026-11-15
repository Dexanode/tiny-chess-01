import json,os,urllib.request,lzma;J=-10**9;F16=[{"id":lzma.FILTER_LZMA1,"pb":0,"lc":0,"lp":0,"dict_size":65536}];VAL = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}
def sq(f, r): return r * 16 + f
def _3(s): return "abcdefgh"[s & 15] + "12345678"[s >> 4]
def _x(n): return (int(n[1]) - 1) * 16 + (ord(n[0]) - 97)
def _ak(fen):
 _a = {}
 for i, row in enumerate(fen.split()[0].split("/")):
  f = 0
  for c in row:
   if c.isdigit():
    f += int(c)
   else:
    u = c.isupper();_a[sq(f, 7 - i)] = ("PNBRQK".index(c.upper()) + 1) * (1 if u else -1);f += 1
 return _a
KN = (33, 31, 18, 14, -14, -18, -31, -33);_a5 = (17, 16, 1, -1, -16, -17, 15, 15, -15, -15);BI = (17, 15, -17, -15);RO = (16, 1, -16, -1)
def _r(_a, _b, _c, ep):
 _d = [];_aa = ep
 for s, p in list(_a.items()):
  if (p > 0) != (_b > 0):
   continue
  a = abs(p)
  if a == 1:
   d = 16 * _b;t = s + d;_ag = (s >> 4) == (1, 6)[_b < 0];_7 = (t >> 4) == (7, 0)[_b < 0]
   if t not in _a:
    if _7:
     for pr in (5, 2, 4, 3):
      _d.append((s, t, pr * _b, 0))
    else:
     _d.append((s, t, 0, 0))
     if _ag and s + 2 * d not in _a:
      _d.append((s, s + 2 * d, 0, 2))
   for dd in (d - 1, d + 1):
    t = s + dd
    if t & 0x88:
     continue
    if _aa is not None and t == _aa:
     _d.append((s, t, 0, 4))
    elif (_a.get(t, 0) > 0) != (_b > 0) and t in _a:
     if abs(_a[t]) == 6:
      continue
     if _7:
      for pr in (5, 2, 4, 3):
       _d.append((s, t, pr * _b, 1))
     else:
      _d.append((s, t, 0, 1))
  elif a == 2 or a == 3:
   _ap = KN if a == 2 else BI
   for d in _ap:
    t = s + d
    while not (t & 0x88):
     q = _a.get(t)
     if q == 0 or q is None:
      _d.append((s, t, 0, 0))
     else:
      if (q > 0) != (_b > 0) and abs(q) != 6:
       _d.append((s, t, 0, 1))
      break
     if a == 2:
      break
     t += d
  elif a == 4 or a == 5:
   for d in (RO if a == 4 else BI + RO):
    t = s + d
    while not (t & 0x88):
     q = _a.get(t)
     if q == 0 or q is None:
      _d.append((s, t, 0, 0))
     else:
      if (q > 0) != (_b > 0) and abs(q) != 6:
       _d.append((s, t, 0, 1))
      break
     t += d
  else:
   for d in (17, 16, 1, -1, -16, -17, 15, -15):
    t = s + d
    if t & 0x88:
     continue
    q = _a.get(t)
    if q == 0 or q is None:
     _d.append((s, t, 0, 0))
    elif (q > 0) != (_b > 0) and abs(q) != 6:
     _d.append((s, t, 0, 1))
   if s == sq(4, 0) and _b > 0 or s == sq(4, 7) and _b < 0:
    r = 0 if _b > 0 else 7
    for bit, tos in ((1, (sq(6, r), (sq(5, r), sq(6, r)))), (2, (sq(2, r), (sq(3, r), sq(2, r), sq(1, r))))):
     cr = bit if _b > 0 else bit << 2
     if _c & cr and all(x not in _a for x in tos[1])  \
       and not _n(_a, tos[1][0], -_b) and not _n(_a, s, -_b):
      _d.append((s, tos[0], 0, 8))
 return _d
def _p(_a, _b, mv):
 frm, to, _g, _j = mv;_o = _a.get(to, 0);_z = None;_l = _a.pop(frm)
 if _j == 8:  # _c: _at the _as too
  if to == sq(6, 0): _a[sq(5, 0)] = _a.pop(sq(7, 0))
  elif to == sq(2, 0): _a[sq(3, 0)] = _a.pop(sq(0, 0))
  elif to == sq(6, 7): _a[sq(5, 7)] = _a.pop(sq(7, 7))
  elif to == sq(2, 7): _a[sq(3, 7)] = _a.pop(sq(0, 7))
 if _j == 2:
  _z = frm + 16 * _b
 if _j == 4:
  cap = _a.pop(to - 16 * _b);_o = cap
 if _g:
  _l = _g
 _a[to] = _l
 return _o, _z
def _k(_a, _b, mv, _o, _z, _a1):
 frm, to, _g, _j = mv;_l = _a.pop(to)
 if _j == 4:
  _a[frm] = _l;_a[to - 16 * _b] = -_b;return
 if _g:
  _l = _b
 _a[frm] = _l
 if _o:
  _a[to] = _o
 if _j == 8:
  if to == sq(6, 0): _a[sq(7, 0)] = _a.pop(sq(5, 0))
  elif to == sq(2, 0): _a[sq(0, 0)] = _a.pop(sq(3, 0))
  elif to == sq(6, 7): _a[sq(7, 7)] = _a.pop(sq(5, 7))
  elif to == sq(2, 7): _a[sq(0, 7)] = _a.pop(sq(3, 7))
def _s(_a, _b):
 for s, p in _a.items():
  if p == 6 * _b:
   return s
 return None
def _n(_a, t, by):
 g = by > 0
 for d in (-1, 1, -16, 16, -17, 17, -15, 15):
  s = t + d;dg = d not in (1, -1, 16, -16)
  while not (s & 0x88):
   q = _a.get(s)
   if q:
    if (q > 0) == g and (abs(q) == 5 or abs(q) == (3 if dg else 4)):
     return True
    break
   s += d
 if any(_a.get(t + d) == 2 * by for d in KN if not ((t + d) & 0x88)):
  return True
 if any(_a.get(t + d) == 6 * by for d in (17, 16, 1, -1, -16, -17, 15, -15) if not ((t + d) & 0x88)):
  return True
 return _a.get(t - 15 * by) == by or _a.get(t - 17 * by) == by
def _am(_a, _b, _c, ep):
 out = []
 for mv in _r(_a, _b, _c, ep):
  cap, epn = _p(_a, _b, mv);k = _s(_a, _b);bad = k is None or _n(_a, k, -_b);_k(_a, _b, mv, cap, epn, _c)
  if not bad:
   out.append(mv)
 return out
def _t(_c, frm, to):
 m = {sq(4,0): ~(1|2), sq(0,0): ~2, sq(7,0): ~1,
  sq(4,7): ~(4|8), sq(0,7): ~8, sq(7,7): ~4}
 c = _c
 if frm in m: c &= m[frm]
 if to in m: c &= m[to]
 return c & 15
TQ='003)3y*KixwBw$ou1oS_7Y|pVfj0YSPVn-`UqA;1bR8rXhc)(0lt28|OC`Ci;W6^&;ID0<t?GE`55t+2pK+oL|FAY{Yqde(FvfAM_2|kgOUT|_$Btyvzb?wem%dEE7RkBn<Ik7d+50?xy!g3IC^YhvGC4^wLXn)+b%aq_f55mfESE<&J*h{NT=6ARWx0gb9)As(W1H#P=Eb0#72A5VCDV}y*m{%PbRdmk4RAOEFe8x;=4*ZtWhjmQ(O7)>#dD_r&ETkw';_z=lzma.decompress(base64.b85decode(TQ),format=lzma.FORMAT_RAW,filters=F16);PST={i+1:tuple((b>>1)^-(b&1) for b in _z[i*64:i*64+64]) for i in range(7)};KE=PST[7]
def _ao(_a, _b):
 _5 = 0
 q = 5 in map(abs, _a.values())
 for s, p in _a.items():
  a = abs(p);idx = (7 - (s >> 4)) * 8 + (s & 15) if p > 0 else (s >> 4) * 8 + (s & 15);v = VAL[a] + (KE if a == 6 and not q else PST[a])[idx];_5 += v if p > 0 else -v
 return _5 * _b
def _y(_a, mv):
 frm, to, _g, _j = mv;q = abs(_a.get(to, 0));p = abs(_a.get(frm, 1));s = q * 10 - p if q else 0
 if _g: s += 800
 if _j == 4: s += 1000
 return s
_i = 0;_1 = 600000
def _6(_a, _b, _c, ep, _e, _h, ply=0):
 global _i;_i += 1;_q = _ao(_a, _b)
 if ply >= 6:
  return _q
 if _q >= _h:
  return _h
 if _q > _e:
  _e = _q
 _ac = [m for m in _r(_a, _b, _c, ep)
   if m[3] in (1, 4) or m[2] or _a.get(m[1])]
 _ac.sort(key=lambda m: -_y(_a, m))
 for mv in _ac:
  cap, epn = _p(_a, _b, mv)
  if abs(cap) == 6:
   _k(_a, _b, mv, cap, epn, _c)
   return 30000 - ply
  sc = -_6(_a, -_b, _t(_c, mv[0], mv[1]), epn, -_h, -_e, ply + 1);_k(_a, _b, mv, cap, epn, _c)
  if sc >= _h:
   return _h
  if sc > _e:
   _e = sc
 return _e
def _ae(_a, _b, _c, ep, _ab, _e, _h, ply=0):
 global _i;_i += 1
 if _ab == 0:
  return _6(_a, _b, _c, ep, _e, _h)
 _d = _r(_a, _b, _c, ep);_d.sort(key=lambda m: -_y(_a, m));_m = J;_ad = False
 for mv in _d:
  cap, epn = _p(_a, _b, mv)
  if abs(cap) == 6:
   _k(_a, _b, mv, cap, epn, _c)
   return 30000 - ply
  nc = _t(_c, mv[0], mv[1]);k = _s(_a, _b)
  if k is not None and _n(_a, k, -_b):
   _k(_a, _b, mv, cap, epn, _c);continue
  _ad = True;sc = -_ae(_a, -_b, nc, epn, _ab - 1, -_h, -_e, ply + 1);_k(_a, _b, mv, cap, epn, _c)
  if sc > _m:
   _m = sc
  if sc >= _h:
   return _h
  if sc > _e:
   _e = sc
 if not _ad:
  k = _s(_a, _b)
  if k is not None and _n(_a, k, -_b):
   return -30000 + ply
  return 0
 return _m
def _ah(_a, _b, _c, ep, _al=5):
 global _i;_i = 0;_0 = None;_d = _am(_a, _b, _c, ep)
 if not _d:
  return None
 _d.sort(key=lambda m: -_y(_a, m));_0 = _d[0]
 for d in range(1, _al + 1):
  _m = J;bm = None;_e = J
  for mv in _d:
   cap, epn = _p(_a, _b, mv);nc = _t(_c, mv[0], mv[1]);sc = -_ae(_a, -_b, nc, epn, d - 1, J, -_e);_k(_a, _b, mv, cap, epn, _c)
   if sc > _m:
    _m = sc;bm = mv
   if sc > _e:
    _e = sc
   if _i > _1:
    break
  if bm is not None and _i <= _1:
   _0 = bm;_d.sort(key=lambda m: 0 if m != bm else 1)
  if _i > _1:
   break
 return _0
import json,os,urllib.request,lzma;_ar = os.environ.get("MAKEFUN_ENV_URL")
def _w(_aj, _aq):
 req = urllib.request.Request(_ar + _aj, json.dumps(_aq).encode(), {"content-type": "application/json"})
 return json.load(urllib.request.urlopen(req))
def _ai(_2, _d):
 _a = _ak(_2);f = _2.split();_b = 1 if f[1] == "w" else -1;_c = sum(1 << i for i, c in enumerate("KQkq") if c in f[2]);ep = _x(f[3]) if f[3] != "-" else None
 for u in _d:
  frm, to = _x(u[:2]), _x(u[2:4]);_g = ("PNBRQ".index(u[4].upper()) + 1) * _b if len(u) > 4 else 0;mv = next(m for m in _r(_a, _b, _c, ep)
    if m[0] == frm and m[1] == to and (m[2] == _g or (_g and abs(m[2]) == _g)))
  ep = frm + 16 * _b if mv[3] == 2 else None;_p(_a, _b, mv);_c = _t(_c, frm, to);_b = -_b
 return _a, _b, _c, ep
def _8():
 while True:
  g = _w("/game", {})
  if g.get("status") == "done":
   return
  b, s, c, e = _ai(g["start_fen"], g["moves"]);mv = _ah(b, s, c, e)
  if mv is None:
   _w("/resign", {"game": g["game"]});continue
  u = _3(mv[0]) + _3(mv[1]) + ("nbrq"[abs(mv[2]) - 2] if mv[2] else "");_w("/move", {"game": g["game"], "move": u})
if __name__ == "__main__":
 _8()
if __name__ == "__main__":
 _8()