"""Prism-chair P_d = chair3 x [0,1]^(d-3): engine, dissections of 2P, children options."""
import itertools, pickle, os
from fast import *
from chairlib import all_frames


def prism_cells(d):
    out = []
    for v in itertools.product((1, -1), repeat=3):
        if v == (1, 1, 1):
            continue
        out.append(tuple(v) + tuple([-1] * (d - 3)))
    return tuple(out)


def parent_cells(Pc, d):
    return frozenset(tuple(2 * a + b for a, b in zip(v, e)) for v in Pc for e in itertools.product((1, -1), repeat=d))


def dissections(E):
    d = E.d
    Pc = E.cells
    target = parent_cells(Pc, d)
    # all placements (c, gi) with 2c + g Pc subset of target
    shapes = {}
    for gi in range(E.nf):
        shapes.setdefault(frozenset(E.cellvec[gi]), []).append(gi)
    pl = {}
    for cs0, gis in shapes.items():
        # choose translation c so that 2c + cs0 subset target
        v0 = next(iter(cs0))
        for tc in target:
            diff = tuple(a - b for a, b in zip(tc, v0))
            if any(x % 2 for x in diff):
                continue
            c = tuple(x // 2 for x in diff)
            cs = frozenset(tuple(2 * a + b for a, b in zip(c, v)) for v in cs0)
            if cs <= target:
                pl[cs] = (c, gis)
    places = list(pl.keys())
    cover = {c: [p for p in places if c in p] for c in target}
    sols = []

    def rec(rem, chosen):
        if not rem:
            sols.append([(pl[p][0], pl[p][1]) for p in chosen])
            return
        c = min(rem, key=lambda c: sum(1 for p in cover[c] if p <= rem))
        for p in cover[c]:
            if p <= rem:
                chosen.append(p)
                rec(rem - p, chosen)
                chosen.pop()
    rec(target, [])
    return sols


def get(d, proper=True):
    E = Engine(d, proper_only=proper, cells=prism_cells(d))
    fn = 'prismdiss%d_%d.pkl' % (d, int(proper))
    if os.path.exists(fn):
        sols = pickle.load(open(fn, 'rb'))
    else:
        sols = dissections(E)
        pickle.dump(sols, open(fn, 'wb'))
    return E, sols


if __name__ == "__main__":
    import sys
    d = int(sys.argv[1])
    E, sols = get(d)
    print("frames", E.nf, "faces", len(E.faces), "dissections", len(sols))
    # which dissections have the pieces' extra axes mixed?
    def mixing(sol):
        ax = set()
        for c, gis in sol:
            g = E.frames[gis[0]]
            # image of the interval axes
            for j in range(3, d):
                ax.add(abs(g[j]) - 1)
        return sorted(ax)
    from collections import Counter
    print(Counter(tuple(mixing(s)) for s in sols))
