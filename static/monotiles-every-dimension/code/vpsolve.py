"""Solve the virtual-pointer (VP) relations for substitutions of the d-chair.

Unknowns: H_w (w mixed), with H_0 = H_{-1} = I;  D_k (k axes), involution pi.
V1: for every axis k and every cell w with w_k = -1:
      H_{D_k w^(k)} = D_k H_w D_j^{-1},  where H_w e_j = e_k  (j = axis of H_w^{-1} e_k).
Constraints on D_k: D_k e_k = -e_{pi k}, D_k 1 = 1 - 2 e_{pi k}, D_{pi k} = D_k^{-1}, proper.
Solutions of V1 are then filtered by the full closure VP check.
"""
import itertools, sys
from fast import *
from vpcheck import vp_table


def involutions(d):
    out = []

    def rec(rem, cur):
        if not rem:
            out.append(dict(cur))
            return
        a = rem[0]
        # fixed
        cur[a] = a
        rec(rem[1:], cur)
        del cur[a]
        for b in rem[1:]:
            cur[a] = b
            cur[b] = a
            rec([x for x in rem[1:] if x != b], cur)
            del cur[a]
            del cur[b]
    rec(list(range(d)), {})
    return out


def D_candidates(E, k, pk):
    d = E.d
    one = (1,) * d
    tgt1 = tuple(1 - 2 * (i == pk) for i in range(d))
    ek = tuple(int(i == k) for i in range(d))
    tgtk = tuple(-int(i == pk) for i in range(d))
    return [gi for gi, g in enumerate(E.frames) if apply(g, one) == tgt1 and apply(g, ek) == tgtk]


def flip(w, k):
    w = list(w)
    w[k] = -w[k]
    return tuple(w)


def solve(E, verbose=False, max_solutions=None, pi_filter=None):
    d = E.d
    one = (1,) * d
    mixed = [w for w in itertools.product((1, -1), repeat=d) if w != one and w != tuple(-x for x in one)]
    minus1 = tuple(-1 for _ in range(d))
    cosets = {w: [gi for gi, g in enumerate(E.frames) if apply(g, one) == tuple(-x for x in w)] for w in mixed}
    I = 0
    sols = []
    for pi in involutions(d):
        if pi_filter and not pi_filter(pi):
            continue
        # choose D_k for representatives k <= pi(k)
        reps = [k for k in range(d) if k <= pi[k]]
        cand = [D_candidates(E, k, pi[k]) for k in reps]
        for choice in itertools.product(*cand):
            D = {}
            okD = True
            for k, gi in zip(reps, choice):
                D[k] = gi
                if pi[k] != k:
                    D[pi[k]] = E.inv[gi]
                elif E.mul[gi][gi] != I and E.inv[gi] != gi:
                    # D_k for self-dual k must equal its own inverse
                    okD = False
            if not okD:
                continue
            # check D_{pi k} satisfies constraints too
            if any(D[k] not in D_candidates(E, k, pi[k]) for k in range(d)):
                continue
            # V1 propagation via backtracking
            Hs = {tuple(0 for _ in range(d)): I, minus1: I}

            def constraints_from(w):
                """yield (w', required H index) from known H_w"""
                hw = Hs[w]
                g = E.frames[hw]
                ginv = E.frames[E.inv[hw]]
                for k in range(d):
                    if w[k] != -1:
                        continue
                    ek = tuple(int(i == k) for i in range(d))
                    img = apply(ginv, ek)
                    j = next(i for i in range(d) if img[i] != 0)
                    if img[j] != 1:
                        return None  # H_w e_j = -e_k: not allowed? (w_k=-1 means H_w 1 has +1 at k)
                    wp = apply(E.frames[D[k]], flip(w, k))
                    req = E.mul[E.mul[D[k]][hw]][E.inv[D[j]]]
                    yield wp, req

            def consistent_all():
                for w in list(Hs):
                    if all(x == 0 for x in w):
                        continue
                    res = constraints_from(w)
                    if res is None:
                        return False
                    for wp, req in res:
                        if wp in Hs:
                            if Hs[wp] != req:
                                return False
                return True

            def propagate():
                changed = True
                while changed:
                    changed = False
                    for w in list(Hs):
                        if all(x == 0 for x in w):
                            continue
                        res = constraints_from(w)
                        if res is None:
                            return False
                        for wp, req in res:
                            if wp in Hs:
                                if Hs[wp] != req:
                                    return False
                            else:
                                if apply(E.frames[req], one) != tuple(-x for x in wp):
                                    return False
                                Hs[wp] = req
                                changed = True
                return True

            def rec():
                if max_solutions and len(sols) >= max_solutions:
                    return
                saved = dict(Hs)
                if not propagate():
                    Hs.clear(); Hs.update(saved)
                    return
                free = [w for w in mixed if w not in Hs]
                if not free:
                    sols.append((dict(pi), {k: E.frames[v] for k, v in D.items()},
                                 {w: E.frames[h] for w, h in Hs.items()}))
                    Hs.clear(); Hs.update(saved)
                    return
                w = free[0]
                for h in cosets[w]:
                    Hs[w] = h
                    rec()
                    del Hs[w]
                Hs.clear(); Hs.update(saved)

            rec()
    return sols


if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    E = Engine(d)
    sols = solve(E)
    print("V1 solutions:", len(sols))
    good = []
    for pi, D, Hs in sols:
        ch = [(w, h) for w, h in Hs.items()]
        chi = E.make_children(ch)
        ok, tab, C = vp_table(E, chi)
        if ok:
            good.append((pi, D, Hs, len(C)))
    print("full VP-consistent:", len(good))
    import pickle
    pickle.dump(good, open("vpsol%d.pkl" % d, "wb"))
    for pi, D, Hs, nC in good[:20]:
        print(pi, D, nC)
