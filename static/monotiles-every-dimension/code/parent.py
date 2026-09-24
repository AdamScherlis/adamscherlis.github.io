"""Parent atlas: coarsen legal contacts and compare with the fine atlas."""
from chairlib import *
from atlas import *


def parent_of(child, children, i):
    """If `child`=(t,G) is child i of a parent, return parent as (T, GP) with T the
    parent's reentrant vertex in fine coordinates (parent body = T + GP(2L))."""
    t, g = child
    c, h = children[i]
    gp = compose(g, inverse(h))
    T = vsub(t, apply(gp, c))
    return (T, gp)


def children_of(parent, children):
    T, gp = parent
    return [(vadd(T, apply(gp, c)), compose(gp, h)) for (c, h) in children]


def parent_atlas(proto, atlas, children, atlas_set=None):
    d = proto.d
    if atlas_set is None:
        atlas_set = set(atlas)
    A = ((0,) * d, identity(d))
    cand = set()
    for B in atlas:
        for i in range(len(children)):
            PA = parent_of(A, children, i)
            for j in range(len(children)):
                PB = parent_of(B, children, j)
                cand.add(normalize(PA, PB))
    # now filter
    res = set()
    n_disjoint = 0
    for R in cand:
        PA = ((0,) * d, identity(d))
        chA = children_of(PA, children)
        chB = children_of(R, children)
        cellsA = set()
        for T in chA:
            cellsA |= set(tile_cells2(T))
        cellsB = {}
        for k, T in enumerate(chB):
            for c in tile_cells2(T):
                cellsB[c] = k
        if cellsA & set(cellsB):
            continue
        n_disjoint += 1
        ok = True
        for Ta in chA:
            nb = set()
            ta, ga = Ta
            for (v, i, s) in proto.faces:
                n = list(v)
                n[i] += 2 * s
                nw = vadd(vscale(2, ta), apply(ga, tuple(n)))
                if nw in cellsB:
                    nb.add(cellsB[nw])
            for k in nb:
                if normalize(Ta, chB[k]) not in atlas_set:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            res.add(R)
    return cand, n_disjoint, res


def halve(res):
    out = set()
    odd = 0
    for (T, g) in res:
        if any(x % 2 for x in T):
            odd += 1
            continue
        out.add((tuple(x // 2 for x in T), g))
    return out, odd


def analyse(d, children, levels=4, verbose=True, frames=None):
    proto, closed, tiles = closed_contacts(d, children, levels)
    uf = keys_from_contacts(proto, closed)
    if uf.bad:
        return dict(bad=True)
    ncls = len({uf.find(k) for k in range(len(proto.ports))})
    if frames is None:
        frames = all_frames(d, True)
    atlas, ncand = legal_atlas(proto, uf, frames)
    cand, ndis, res = parent_atlas(proto, atlas, children)
    half, odd = halve(res)
    out = dict(bad=False, closed=len(closed), classes=ncls, candidates=ncand,
               atlas=len(atlas), parent_cand=len(cand), parent_disjoint=ndis,
               parent_legal=len(res), odd=odd, halving_equal=(half == atlas and odd == 0),
               halving_subset=(half <= atlas and odd == 0))
    if verbose:
        print(out)
    return out, proto, closed, uf, atlas


if __name__ == "__main__":
    from chair44 import chair44_children
    analyse(3, chair44_children())
