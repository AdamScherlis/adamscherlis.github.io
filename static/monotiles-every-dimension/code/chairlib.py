"""d-dimensional chair tiles with frames, substitution, ports, contact atlases.

Conventions
-----------
* Signed permutation G is a tuple g of length d with g[j] = s*(p+1): G e_j = s e_p.
* Chair L (prototile, origin at the reentrant vertex, notch direction +1):
  cells = sign vectors v in {+-1}^d minus the all-ones vector; cell centre = v/2.
* A tile is (t, G) with t in Z^d: cells t + G v/2.  Notch direction G(1).
* "Doubled" coordinates: 2x.  Cell centre doubled = 2t + G v (all coords odd).
"""
import itertools
from functools import lru_cache


def apply(g, x):
    y = [0] * len(g)
    for j, gj in enumerate(g):
        p = abs(gj) - 1
        y[p] += (1 if gj > 0 else -1) * x[j]
    return tuple(y)


def compose(g, h):
    """(g o h)"""
    out = []
    for hj in h:
        p = abs(hj) - 1
        s = 1 if hj > 0 else -1
        gp = g[p]
        out.append(s * gp)
    return tuple(out)


def inverse(g):
    d = len(g)
    out = [0] * d
    for j, gj in enumerate(g):
        p = abs(gj) - 1
        s = 1 if gj > 0 else -1
        out[p] = s * (j + 1)
    return tuple(out)


def det(g):
    perm = [abs(x) - 1 for x in g]
    sgn = 1
    for x in g:
        if x < 0:
            sgn = -sgn
    # permutation parity
    seen = [False] * len(perm)
    for i in range(len(perm)):
        if not seen[i]:
            j = i
            L = 0
            while not seen[j]:
                seen[j] = True
                j = perm[j]
                L += 1
            if L % 2 == 0:
                sgn = -sgn
    return sgn


def identity(d):
    return tuple(range(1, d + 1))


@lru_cache(None)
def all_frames(d, proper_only=True):
    out = []
    for perm in itertools.permutations(range(d)):
        for signs in itertools.product((1, -1), repeat=d):
            g = tuple(s * (p + 1) for p, s in zip(perm, signs))
            if not proper_only or det(g) == 1:
                out.append(g)
    return tuple(out)


def vadd(a, b):
    return tuple(x + y for x, y in zip(a, b))


def vsub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def vscale(k, a):
    return tuple(k * x for x in a)


@lru_cache(None)
def chair_cells(d):
    """sign vectors of the prototile's cells"""
    one = (1,) * d
    return tuple(v for v in itertools.product((1, -1), repeat=d) if v != one)


def tile_cells2(tile):
    """doubled cell centres of tile (t,G)"""
    t, g = tile
    d = len(t)
    t2 = vscale(2, t)
    return [vadd(t2, apply(g, v)) for v in chair_cells(d)]


@lru_cache(None)
def proto_faces(d):
    """exposed faces of the prototile: list of (cell v, normal n) with n = +-e_i
    as a signed axis (s, i).  Returns list of (v, i, s)."""
    cells = set(chair_cells(d))
    out = []
    for v in chair_cells(d):
        for i in range(d):
            for s in (1, -1):
                nb = list(v)
                # neighbour cell centre v/2 + s e_i  -> doubled v + 2 s e_i
                nb[i] += 2 * s
                nbt = tuple(nb)
                if nbt in cells:
                    continue
                out.append((v, i, s))
    return tuple(out)


def unit(d, i, s=1):
    e = [0] * d
    e[i] = s
    return tuple(e)


# ---------------------------------------------------------------- ports
@lru_cache(None)
def tangent_orbit(d):
    """Signed permutations of (1..d-1) as tangent offsets: list of tuples length d-1."""
    base = list(range(1, d))
    out = []
    for perm in itertools.permutations(base):
        for signs in itertools.product((1, -1), repeat=d - 1):
            out.append(tuple(s * p for s, p in zip(signs, perm)))
    return tuple(out)


@lru_cache(None)
def proto_ports(d):
    """Ports of the prototile in scaled coordinates X = d * (2x).
    Face (v,i,s): centre doubled = v + s e_i ; scaled = d*(v + s e_i).
    Port = centre + tangent offsets (values in +-1..+-(d-1), |.|<d = half width).
    Returns list of (face_index, X) ."""
    faces = proto_faces(d)
    out = []
    for fi, (v, i, s) in enumerate(faces):
        c = list(vscale(d, v))
        c[i] += d * s
        for q in tangent_orbit(d):
            X = list(c)
            k = 0
            for j in range(d):
                if j == i:
                    continue
                X[j] += q[k]
                k += 1
            out.append((fi, tuple(X)))
    return tuple(out)


def tile_to_world_X(tile, X):
    t, g = tile
    d = len(t)
    return vadd(vscale(2 * d, t), apply(g, X))


# ---------------------------------------------------------------- substitution
def substitute(tiles, children):
    """children: list of (c, H) with c integer offset (parent coords, relative to the
    parent's reentrant vertex scaled by 2 -> child origin = 2t + G c), H child frame."""
    out = []
    for (t, g) in tiles:
        t2 = vscale(2, t)
        for (c, h) in children:
            out.append((vadd(t2, apply(g, c)), compose(g, h)))
    return out


def check_children(d, children):
    """Check the children partition 2L exactly."""
    cells = []
    for (c, h) in children:
        cells.extend(tile_cells2((c, h)))
    # 2L cells in doubled coords: unit cells inside [-2,2]^d minus [0,2]^d
    target = set()
    for x in itertools.product((-3, -1, 1, 3), repeat=d):
        if all(xi > 0 for xi in x):
            continue
        target.add(x)
    return len(cells) == len(set(cells)) and set(cells) == target


def normalize(a, b):
    """relative placement of b in the frame of a: a^{-1} b"""
    ta, ga = a
    tb, gb = b
    gi = inverse(ga)
    return (apply(gi, vsub(tb, ta)), compose(gi, gb))
