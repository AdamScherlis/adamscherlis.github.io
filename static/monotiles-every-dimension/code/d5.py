import itertools, time, sys
from fast import *
from chairlib import all_frames
from chair44 import chair44_children
from prodtwist import h2
d = 5
t0 = time.time()
E = Engine(d)
print("engine", time.time() - t0, flush=True)
c44 = {c: g for c, g in chair44_children()}
ext = [g for g in all_frames(3, True) if apply(g, (1,1,1)) == (-1,-1,-1)]
def build(e3, block=None):
    ch = [((0,)*5, identity(5))]
    for w in itertools.product((1,-1), repeat=5):
        if w == (1,)*5: continue
        w3, w2 = w[:3], w[3:]
        g3 = ext[e3] if w3 == (1,1,1) else c44.get(w3, (1,2,3))
        if w3 == (-1,-1,-1): g3 = (1,2,3)
        r = h2(w2)
        g = list(g3) + [ (1 if x > 0 else -1) * (abs(x) + 3) for x in r]
        ch.append((w, tuple(g)))
    return ch
for e3 in range(len(ext)):
    ch = build(e3)
    t = time.time()
    S = System2(E, ch)
    print(e3, ext[e3], "closed", len(S.closed), "classes", S.nclasses, "bad", S.bad, round(time.time()-t,1), flush=True)
