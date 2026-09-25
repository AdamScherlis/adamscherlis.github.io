import itertools, json, sys
from multiprocessing import Pool
from selfsim import *
from families import offsets, coset

d = int(sys.argv[1]) if len(sys.argv) > 1 else 3
proper = True
E = Engine(d)
offs = offsets(d)
one = (1,) * d
choices = []
for w in offs:
    target = one if w == (0,) * d else tuple(-x for x in w)
    choices.append(coset(d, target))


def run(idx):
    ch = [(offs[k], choices[k][idx[k]]) for k in range(len(offs))]
    S = SSSystem(E, ch)
    if S.bad:
        return idx, dict(bad=True)
    return idx, dict(bad=False, classes=S.nclasses)


if __name__ == "__main__":
    allidx = list(itertools.product(*[range(len(c)) for c in choices]))
    with Pool(4) as p:
        res = p.map(run, allidx, chunksize=50)
    json.dump([[list(i), r] for i, r in res], open("searchss%d.json" % d, "w"))
    from collections import Counter
    print(Counter((r.get('bad'), r.get('classes')) for i, r in res))
