import itertools, pickle, sys
from multiprocessing import Pool
from fast import *
from chairlib import all_frames
from chair44 import chair44_children
d = 4
E = Engine(d)
c44 = {c: g for c, g in chair44_children()}
F3all = all_frames(3, False)
def emb(g3, s4):
    return tuple(list(g3) + [s4 * 4])
prop111 = [g for g in F3all if det(g) == 1 and apply(g, (1,1,1)) == (-1,-1,-1)]
impr = {}
for v in itertools.product((1,-1), repeat=3):
    if v == (1,1,1): continue
    impr[v] = [g for g in F3all if det(g) == -1 and apply(g, (1,1,1)) == tuple(-x for x in v)]
keys = sorted(impr)
def build(p, choice):
    ch = [((0,0,0,0), identity(4))]
    for v in itertools.product((1,-1), repeat=3):
        w = v + (-1,)
        if v == (1,1,1): g3 = prop111[p]
        elif v == (-1,-1,-1): g3 = (1,2,3)
        else: g3 = c44[v]
        ch.append((w, emb(g3, 1)))
    for k, v in enumerate(keys):
        ch.append((v + (1,), emb(impr[v][choice[k]], -1)))
    return ch
def run(args):
    p, choice = args
    ch = build(p, choice)
    S = System2(E, ch)
    return (S.nclasses, len(S.closed), p, choice, S.bad)
if __name__ == "__main__":
    jobs = [(p, c) for p in range(len(prop111)) for c in itertools.product(*[range(len(impr[v])) for v in keys])]
    print(len(jobs))
    with Pool(4) as pool:
        res = pool.map(run, jobs, chunksize=20)
    res.sort(key=lambda r: (-r[0], r[1]))
    for r in res[:15]: print(r)
    pickle.dump(res, open('lift4.pkl','wb'))
