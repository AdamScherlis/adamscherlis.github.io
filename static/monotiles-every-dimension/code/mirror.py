import itertools, sys, pickle
from multiprocessing import Pool
from fast import *
from chairlib import all_frames
d = int(sys.argv[1])
E = Engine(d, proper_only=False)
one = (1,)*d; zero=(0,)*d; m1 = tuple(-1 for _ in range(d))
mixed = [w for w in itertools.product((1,-1), repeat=d) if w != one and w != m1]
odd0 = [g for g in all_frames(d, False) if apply(g, one) == one and det(g) == -1]
cos = {w: [g for g in all_frames(d, True) if apply(g, one) == tuple(-x for x in w)] for w in mixed}
def run(args):
    h0i, idx = args
    h0 = odd0[h0i]
    ch = [(zero, h0), (m1, compose(h0, h0))] + [(w, cos[w][i]) for w, i in zip(mixed, idx)]
    S = System3(E, ch)
    return (S.nzero, S.nclasses, len(S.closed), h0i, idx)
if __name__ == "__main__":
    jobs = [(a, idx) for a in range(len(odd0)) for idx in itertools.product(*[range(len(cos[w])) for w in mixed])]
    print(len(jobs), flush=True)
    with Pool(4) as p:
        res = p.map(run, jobs, chunksize=20)
    from collections import Counter
    print(Counter((r[0], r[1]) for r in res))
    good = sorted(res, key=lambda r: -r[1])[:20]
    for r in good: print(r)
    pickle.dump(good, open('mirror%d.pkl' % d, 'wb'))
