"""Block-product frozen substitutions and twists."""
import itertools
from fast import *


def h1(v):  # 1D block: v in {+-1}
    return [-1] if v[0] == 1 else [1]


def h2(v):
    a, b = v
    # maps (1,1) -> -(a,b) ; rotations
    if (a, b) == (-1, -1):
        return [1, 2]
    if (a, b) == (-1, 1):
        return [-2, 1]   # e1->-e2, e2->e1 : (1,1)->(1,-1)= -(-1,1) ok
    if (a, b) == (1, -1):
        return [2, -1]   # e1->e2, e2->-e1 : (1,1)->(-1,1) ok
    return [-1, -2]


def h2r(v):
    a, b = v
    if (a, b) == (-1, -1):
        return [2, 1]
    if (a, b) == (-1, 1):
        return [1, -2]
    if (a, b) == (1, -1):
        return [-1, 2]
    return [-2, -1]


def block_frame(blocks, w, refl_block=None):
    """blocks: list of lists of axes. returns signed perm tuple for H_w; if the product
    of rotations is improper, the first 2D block uses a reflection."""
    d = sum(len(b) for b in blocks)
    sgn = 1
    for b in blocks:
        if len(b) == 1 and w[b[0]] == 1:
            sgn = -sgn
    first2 = next((k for k, b in enumerate(blocks) if len(b) == 2), None)
    g = [0] * d
    for bi, b in enumerate(blocks):
        v = tuple(w[i] for i in b)
        if len(b) == 1:
            loc = h1(v)
        elif sgn == -1 and bi == first2:
            loc = h2r(v)
        else:
            loc = h2(v)
        for jloc, img in enumerate(loc):
            src = b[jloc]
            dst = b[abs(img) - 1]
            g[src] = (1 if img > 0 else -1) * (dst + 1)
    return tuple(g)


def product_children(d, blocks, twist=None, K=None):
    one = (1,) * d
    out = []
    for w in [(0,) * d] + [w for w in itertools.product((1, -1), repeat=d) if w != one]:
        if all(x == 0 for x in w) or all(x == -1 for x in w):
            out.append((w, identity(d)))
            continue
        g = block_frame(blocks, w)
        if twist is not None and twist(w):
            g = compose(g, K)
        out.append((w, g))
    return out


if __name__ == "__main__":
    E = Engine(3)
    ch = product_children(3, [[0, 1], [2]])
    for c, g in ch:
        print(c, g, det(g), apply(g, (1, 1, 1)))
    K = (2, 3, 1)
    ch2 = product_children(3, [[0, 1], [2]], twist=lambda w: w[0] != w[1], K=K)
    S = full2(3, ch2, E=E)
    print(S.summary())
