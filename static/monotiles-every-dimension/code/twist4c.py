import itertools, pickle
from multiprocessing import Pool
from fast import *
from chairlib import all_frames
from prodtwist import product_children
d = 4
E = Engine(d)
one = (1,)*d
base = dict(product_children(d, [[0, 1], [2], [3]]))
def sinv(w):
    a, c = w[0], w[1]
    return 1 if (a, c) == (-1, 1) else (-1 if (a, c) == (1, -1) else 0)
def power(g, n):
    r = identity(d)
    if n < 0: g = inverse(g); n = -n
    for _ in range(n): r = compose(r, g)
    return r
cyc3 = [g for g in all_frames(d, True) if apply(g, one) == one and compose(g, compose(g, g)) == identity(d) and g != identity(d)]
ctx = list(itertools.product((1, -1), repeat=2))
def run(args):
    K, avals = args
    a = dict(zip(ctx, avals))
    ch = []
    for w, g in base.items():
        if all(x == 0 for x in w) or all(x == -1 for x in w):
            ch.append((w, g)); continue
        n = a[(w[2], w[3])] * sinv(w)
        ch.append((w, compose(g, power(K, n))))
    S = System2(E, ch)
    return (S.nclasses, len(S.closed), K, avals)
if __name__ == "__main__":
    jobs = [(K, av) for K in cyc3 for av in itertools.product((-1, 0, 1), repeat=4)]
    print(len(jobs), flush=True)
    with Pool(4) as p:
        res = p.map(run, jobs, chunksize=10)
    res.sort(key=lambda r: (-r[0], r[1]))
    from collections import Counter
    print(Counter(r[0] for r in res))
    for r in res[:15]: print(r)
    pickle.dump(res, open('twist4c.pkl', 'wb'))
