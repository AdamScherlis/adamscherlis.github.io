import pickle, sys, time
from fast import *
d = int(sys.argv[1]); fn = sys.argv[2]; proper = sys.argv[3] == '1'
E = Engine(d, proper_only=proper)
good = pickle.load(open(fn, 'rb'))
def gen_group(frames):
    G = {0}; gens = [E.fidx[f] for f in frames]; fr = [0]
    while fr:
        x = fr.pop()
        for g in gens:
            y = E.mul[x][g]
            if y not in G: G.add(y); fr.append(y)
    return len(G)
for idx, sol in enumerate(good):
    pi, D, Hs, nC = sol
    t = time.time()
    ch = [(w, h) for w, h in Hs.items()]
    S = System2(E, ch)
    S.compute_atlas()
    r = dict(bad=S.bad, closed=len(S.closed), classes=S.nclasses, atlas=len(S.atlas), grp=gen_group(Hs.values()))
    if len(S.atlas) < 3000:
        S.parent_atlas()
        s = S.summary()
        r.update(parent_legal=s['parent_legal'], odd=s['odd'], halving=s['halving_equal'], subset=s['halving_subset'])
    print(idx, pi, r, round(time.time() - t, 1), flush=True)
