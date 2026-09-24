"""VP solver v2: propagate all virtual-pointer equations (F-F-, F+F-, F+F+ contacts)."""
import itertools, sys, pickle, time
from fast import *
from vpcheck import vp_table
from vpsolve import involutions, D_candidates


def canonical_pis(d):
    """involutions up to conjugacy: fix pairs (0,1),(2,3),... then fixed points"""
    out = []
    for npairs in range(d // 2 + 1):
        pi = {}
        for p in range(npairs):
            pi[2 * p] = 2 * p + 1
            pi[2 * p + 1] = 2 * p
        for k in range(2 * npairs, d):
            pi[k] = k
        out.append(pi)
    return out


class VPSolver:
    def __init__(self, E):
        self.E = E
        d = E.d
        self.d = d
        self.one = (1,) * d
        self.m1 = tuple(-1 for _ in range(d))
        self.zero = (0,) * d
        self.mixed = [w for w in itertools.product((1, -1), repeat=d) if w != self.one and w != self.m1]
        self.coset = {w: [gi for gi, g in enumerate(E.frames) if apply(g, self.one) == tuple(-x for x in w)]
                      for w in self.mixed}
        self.cellsign = [None] * len(E.faces)
        self.normal = []
        for f, (v, i, s) in enumerate(E.faces):
            n = [0] * d
            n[i] = s
            self.normal.append(tuple(n))
        self._sf = {}

    def shared(self, B):
        r = self._sf.get(B)
        if r is None:
            r = self.E.shared_faces(B)
            self._sf[B] = r
        return r

    def contacts(self, H, D):
        E = self.E
        d = self.d
        out = []
        for k in range(d):
            ek2 = tuple(-2 * (i == k) for i in range(d))
            out.append((ek2, E.inv[D[k]]))
            uk = tuple(1 - 2 * (i == k) for i in range(d))
            if uk in H:
                out.append((ek2, H[uk]))
        # siblings
        ws = [w for w in itertools.product((1, -1), repeat=d) if w != self.one]
        for u in ws:
            if u not in H:
                continue
            for i in range(d):
                u2 = list(u)
                u2[i] = -u2[i]
                u2 = tuple(u2)
                if u2 == self.one or u2 not in H:
                    continue
                out.append(E.rel((u, H[u]), (u2, H[u2])))
        # add inverses
        res = set()
        for B in out:
            res.add(B)
            res.add(E.rel(B, E.root))
        return res

    def propagate(self, H, D):
        E = self.E
        d = self.d
        changed = True
        while changed:
            changed = False
            for B in self.contacts(H, D):
                t, gb = B
                ginv = E.inv[gb]
                for f, fB, i in self.shared(B):
                    v = E.faces[f][0]
                    vB = E.faces[fB][0]
                    if v not in H:
                        continue
                    hw = H[v]
                    img = apply(E.frames[E.inv[hw]], self.normal[f])
                    j = next(k for k in range(d) if img[k] != 0)
                    if img[j] != -1:
                        return False
                    req = E.mul[E.mul[ginv][hw]][E.inv[D[j]]]
                    if vB in H:
                        if H[vB] != req:
                            return False
                    else:
                        if apply(E.frames[req], self.one) != tuple(-x for x in vB):
                            return False
                        H[vB] = req
                        changed = True
        return True

    def solve_for(self, pi, D, sols, limit=None):
        E = self.E
        H0 = {self.zero: 0, self.m1: 0}

        def rec(H):
            if limit and len(sols) >= limit:
                return
            H = dict(H)
            if not self.propagate(H, D):
                return
            free = [w for w in self.mixed if w not in H]
            if not free:
                sols.append((dict(pi), {k: E.frames[x] for k, x in D.items()},
                             {w: E.frames[h] for w, h in H.items()}))
                return
            # branch on the free w with fewest options? just first
            w = free[0]
            for h in self.coset[w]:
                H2 = dict(H)
                H2[w] = h
                rec(H2)

        rec(H0)

    def all_D(self, pi):
        E = self.E
        d = self.d
        reps = [k for k in range(d) if k <= pi[k]]
        cand = [D_candidates(E, k, pi[k]) for k in reps]
        for choice in itertools.product(*cand):
            D = {}
            ok = True
            for k, gi in zip(reps, choice):
                D[k] = gi
                if pi[k] != k:
                    D[pi[k]] = E.inv[gi]
                elif E.inv[gi] != gi:
                    ok = False
            if not ok:
                continue
            if any(D[k] not in D_candidates(E, k, pi[k]) for k in range(d)):
                continue
            yield D


if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    E = Engine(d)
    V = VPSolver(E)
    allsols = []
    t0 = time.time()
    for pi in canonical_pis(d):
        nD = 0
        for D in V.all_D(pi):
            nD += 1
            sols = []
            V.solve_for(pi, D, sols)
            allsols.extend(sols)
        print("pi", pi, "D choices", nD, "cum sols", len(allsols), round(time.time() - t0, 1), flush=True)
    good = []
    for pi, D, Hs in allsols:
        ch = E.make_children([(w, h) for w, h in Hs.items()])
        ok, tab, C = vp_table(E, ch)
        if ok:
            good.append((pi, D, Hs, len(C)))
    print("candidate solutions", len(allsols), "full VP-consistent", len(good), flush=True)
    pickle.dump(good, open("vp2sol%d.pkl" % d, "wb"))
