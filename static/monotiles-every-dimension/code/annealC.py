import pickle, sys, time, random, math, itertools
from fast import *
from families import coset
d = int(sys.argv[1]); seed = int(sys.argv[2]); iters = int(sys.argv[3])
rng = random.Random(seed)
E = Engine(d)
one = (1,) * d; m1 = tuple(-1 for _ in range(d)); zero = (0,) * d
mixed = [w for w in itertools.product((1, -1), repeat=d) if w != one and w != m1]
cos = {w: coset(d, tuple(-x for x in w)) for w in mixed}
def gen_group(frames):
    G = {0}; gens = [E.fidx[f] for f in frames]; fr = [0]
    while fr:
        x = fr.pop()
        for g in gens:
            y = E.mul[x][g]
            if y not in G: G.add(y); fr.append(y)
    return len(G)
full = len(E.frames)
def chl(H):
    return E.make_children([(zero, identity(d)), (m1, identity(d))] + [(w, H[w]) for w in mixed])
def score(H):
    return len(closure_contacts(E, chl(H)))
while True:
    H = {w: rng.choice(cos[w]) for w in mixed}
    if gen_group(H.values()) == full: break
cur = score(H); T = 5.0
best = (cur, dict(H)); pool = []
for it in range(iters):
    w = rng.choice(mixed); h = rng.choice(cos[w])
    if h == H[w]: continue
    H2 = dict(H); H2[w] = h
    if gen_group(H2.values()) != full: continue
    sc = score(H2)
    if sc <= cur or rng.random() < math.exp((cur - sc) / T):
        H, cur = H2, sc
        if cur < best[0]: best = (cur, dict(H))
        pool.append((cur, dict(H)))
    T = max(0.3, T * 0.998)
    if it % 500 == 0: print(it, cur, best[0], round(T, 2), flush=True)
pool.sort(key=lambda x: x[0])
seen=set(); top=[]
for sc, Hh in pool:
    k = tuple(sorted(Hh.items()))
    if k in seen: continue
    seen.add(k); top.append((sc, Hh))
    if len(top) >= 30: break
print("best", best[0], [s for s, _ in top[:10]])
pickle.dump(top, open('annealC_%d_%d.pkl' % (d, seed), 'wb'))
