"""VP solver allowing improper frames."""
import sys, pickle, time
from fast import *
from vpcheck import vp_table
from vpsolve2 import VPSolver, canonical_pis


def D_cands_any(E, k, pk):
    d = E.d
    one = (1,) * d
    tgt1 = tuple(1 - 2 * (i == pk) for i in range(d))
    ek = tuple(int(i == k) for i in range(d))
    tgtk = tuple(-int(i == pk) for i in range(d))
    return [gi for gi, g in enumerate(E.frames) if apply(g, one) == tgt1 and apply(g, ek) == tgtk]


class VPSolverAny(VPSolver):
    def all_D(self, pi):
        E = self.E
        d = self.d
        reps = [k for k in range(d) if k <= pi[k]]
        cand = [D_cands_any(E, k, pi[k]) for k in reps]
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
            if any(D[k] not in D_cands_any(E, k, pi[k]) for k in range(d)):
                continue
            yield D


if __name__ == "__main__":
    d = int(sys.argv[1])
    E = Engine(d, proper_only=False)
    V = VPSolverAny(E)
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
    pickle.dump(good, open("vp3sol%d.pkl" % d, "wb"))
