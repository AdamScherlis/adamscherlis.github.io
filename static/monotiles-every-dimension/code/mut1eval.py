import pickle, sys
from fast import *
from families import coset
d = 4
E = Engine(d)
good = pickle.load(open('vp2sol4.pkl', 'rb'))
which = int(sys.argv[1])
pi, D, Hs, nC = good[which]
base = dict(Hs)
ws = [w for w in sorted(base) if not all(x == 0 for x in w) and not all(x == -1 for x in w)]
seen = 0
for w in ws:
    for h in coset(d, tuple(-x for x in w)):
        if h == base[w]: continue
        H2 = dict(base); H2[w] = h
        S = System2(E, list(H2.items()))
        if S.nclasses < 48: continue
        S.compute_atlas()
        S.parent_atlas()
        s = S.summary()
        print(w, h, {k: s[k] for k in ('closed','classes','atlas','parent_legal','odd','halving_equal','halving_subset')}, flush=True)
