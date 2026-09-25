import pickle, sys, time, itertools
from fast import *
from families import coset
d = 4
E = Engine(d)
good = pickle.load(open('vp2sol4.pkl', 'rb'))
which = int(sys.argv[1])
pi, D, Hs, nC = good[which]
base = dict(Hs)
def gen_group(frames):
    G = {0}; gens = [E.fidx[f] for f in frames]; fr = [0]
    while fr:
        x = fr.pop()
        for g in gens:
            y = E.mul[x][g]
            if y not in G: G.add(y); fr.append(y)
    return len(G)
ws = [w for w in sorted(base) if not all(x == 0 for x in w) and not all(x == -1 for x in w)]
cos = {w: [h for h in coset(d, tuple(-x for x in w)) if h != base[w]] for w in ws}
singles = []
for w in ws:
    for h in cos[w]:
        H2 = dict(base); H2[w] = h
        S = System2(E, list(H2.items()))
        singles.append((S.nclasses, w, h))
singles = [s for s in singles if s[0] >= 48]
print("singles >=48:", len(singles), flush=True)
out = []
for a in range(len(singles)):
    for b in range(a + 1, len(singles)):
        _, w1, h1 = singles[a]; _, w2, h2 = singles[b]
        if w1 == w2: continue
        H2 = dict(base); H2[w1] = h1; H2[w2] = h2
        g = gen_group(H2.values())
        if g < 192: continue
        S = System2(E, list(H2.items()))
        if S.nclasses >= 24:
            out.append((S.nclasses, w1, h1, w2, h2))
            print(out[-1], flush=True)
print("done", len(out))
pickle.dump(out, open('mut2_%d.pkl' % which, 'wb'))
