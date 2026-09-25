"""Closure + self-similarity identifications of ports."""
from fast import *


def ss_pairs(E, ch):
    """List of (child_port_index, parent_port_index) identifications (same parity)."""
    d = E.d
    m = E.m
    # parent 2L cells (doubled fine coords): {+-1,+-3}^d minus all-positive
    parent_cells = set()
    for x in itertools.product((-3, -1, 1, 3), repeat=d):
        if all(xi > 0 for xi in x):
            continue
        parent_cells.add(x)
    out = []
    for (c, hi) in ch:
        g = E.frames[hi]
        T = (c, hi)
        t2 = tuple(2 * x for x in c)
        for f, (v, i, s) in enumerate(E.faces):
            cell = vadd(t2, apply(g, v))
            nvec = [0] * d
            nvec[i] = s
            wn = apply(g, tuple(nvec))
            ax = next(k for k in range(d) if wn[k] != 0)
            sg = wn[ax]
            nb = list(cell)
            nb[ax] += 2 * sg
            if tuple(nb) in parent_cells:
                continue  # interior face of the parent
            # parent block containing cell: block centre v' with 2v'_k = cell_k -+1
            vp = tuple(1 if x > 0 else -1 for x in cell)
            pf = E.face_index.get((vp, ax, sg))
            if pf is None:
                raise RuntimeError("no parent face")
            for a, q in enumerate(E.torb[i]):
                wq = apply(g, q)
                b = E.tidx[ax][wq]
                out.append((f * m + a, pf * m + b))
    return out


class SSSystem(System2):
    def __init__(self, E, children, use_closure=True):
        self.E = E
        self.ch = E.make_children(children)
        self.children_raw = children
        self.closed = closure_contacts(E, self.ch)
        self.levels = 'closure+ss'
        npt = len(E.faces) * E.m
        uf = UF(npt)
        for B in self.closed:
            for a, b in E.port_pairs(B):
                uf.union(a, b, 1)
        for a, b in ss_pairs(E, self.ch):
            uf.union(a, b, 0)
        self.uf = uf
        self.bad = uf.bad
        self.key = [uf.find(k) for k in range(npt)]
        self.nclasses = len({r for r, p in self.key})
        self._face_ok = {}


if __name__ == "__main__":
    from chair44 import chair44_children
    E = Engine(3)
    S = SSSystem(E, chair44_children())
    print(S.bad, S.nclasses)
