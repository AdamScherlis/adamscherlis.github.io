"""Virtual-pointer consistency: across every axial face of C, D = V'^{-1} V depends only on j."""
from fast import *
from vp import is_notch_face


def vp_table(E, ch, C=None):
    if C is None:
        C = closure_contacts(E, ch)
    d = E.d
    H = {c: hi for c, hi in ch}
    table = {}
    ok = True
    for B in C:
        t, gi = B
        for f, fB, i in E.shared_faces(B):
            fa = E.faces[f]
            fb = E.faces[fB]
            if is_notch_face(fa) or is_notch_face(fb):
                continue
            v, ax, s = fa
            n = [0] * d
            n[ax] = s
            Vi = H[v]
            img = apply(E.frames[E.inv[Vi]], tuple(n))  # = -e_j
            j = next(k for k in range(d) if img[k] != 0)
            assert img[j] == -1, (img, fa)
            Vp = E.mul[gi][H[fb[0]]]
            D = E.mul[E.inv[Vp]][Vi]
            if j in table and table[j] != D:
                ok = False
            table.setdefault(j, D)
    return ok, {j: E.frames[D] for j, D in table.items()}, C


if __name__ == "__main__":
    import json, sys
    from families import offsets, coset
    d = 3
    E = Engine(d)
    offs = offsets(d)
    one = (1,) * d
    choices = [coset(d, one if w == (0,) * d else tuple(-x for x in w)) for w in offs]
    n = 0
    for idx in itertools.product(*[range(len(c)) for c in choices]):
        ch = E.make_children([(offs[k], choices[k][idx[k]]) for k in range(len(offs))])
        ok, tab, C = vp_table(E, ch)
        if ok:
            n += 1
            print(idx, tab, len(C))
    print("VP-consistent:", n)
