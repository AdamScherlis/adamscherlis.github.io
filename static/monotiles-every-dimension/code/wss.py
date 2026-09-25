"""Closure + weak self-similarity (carrier) identifications."""
from fast import *


def wss_pairs(E, ch):
    """child anticell (-1) outer faces of each noncentral child v  <->  parent's outer face (v, a)."""
    d = E.d
    m = E.m
    out = []
    m1 = tuple(-1 for _ in range(d))
    for (c, hi) in ch:
        if all(x == 0 for x in c):
            continue
        g = E.frames[hi]
        for a in range(d):
            # parent face: cell v=c, axis a, sign c[a]  (outer face of block c)
            pf = E.face_index.get((c, a, c[a]))
            if pf is None:
                continue
            # child's anticell outer face whose world normal is c[a] e_a
            n = [0] * d
            n[a] = c[a]
            nl = apply(E.frames[E.inv[hi]], tuple(n))
            ax = next(k for k in range(d) if nl[k] != 0)
            cf = E.face_index.get((m1, ax, nl[ax]))
            assert cf is not None
            for al, q in enumerate(E.torb[ax]):
                wq = apply(g, q)
                b = E.tidx[a][wq]
                out.append((cf * m + al, pf * m + b))
    return out


class WSSSystem(System2):
    def __init__(self, E, children):
        self.E = E
        self.ch = E.make_children(children)
        self.children_raw = children
        self.closed = closure_contacts(E, self.ch)
        self.levels = 'closure+wss'
        npt = len(E.faces) * E.m
        uf = UF(npt)
        for B in self.closed:
            for a, b in E.port_pairs(B):
                uf.union(a, b, 1)
        for a, b in wss_pairs(E, self.ch):
            uf.union(a, b, 0)
        self.uf = uf
        self.bad = uf.bad
        self.key = [uf.find(k) for k in range(npt)]
        self.nclasses = len({r for r, p in self.key})
        self._face_ok = {}


if __name__ == "__main__":
    import sys, itertools, json
    from families import offsets, coset
    from chair44 import chair44_children
    E = Engine(3)
    S = WSSSystem(E, chair44_children())
    print("chair44 wss", S.bad, S.nclasses)
    d = 3
    offs = offsets(d); one = (1,) * d
    choices = [coset(d, one if w == (0,) * d else tuple(-x for x in w)) for w in offs]
    from collections import Counter
    cnt = Counter(); goods = []
    for idx in itertools.product(*[range(len(c)) for c in choices]):
        ch = [(offs[k], choices[k][idx[k]]) for k in range(len(offs))]
        S = WSSSystem(E, ch)
        cnt[(S.bad, S.nclasses)] += 1
        if not S.bad and S.nclasses > 4:
            goods.append((idx, S.nclasses))
    print(cnt)
    print(goods[:20])
