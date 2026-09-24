"""Uniform-in-d candidate substitutions for the d-chair."""
import itertools, random
from chairlib import *


def offsets(d):
    one = (1,) * d
    return [(0,) * d] + [w for w in itertools.product((1, -1), repeat=d) if w != one]


def coset(d, target):
    return [g for g in all_frames(d, True) if apply(g, (1,) * d) == target]


def diag(v):
    return tuple(s * (i + 1) for i, s in enumerate(v))


def transposition(d, a, b):
    g = list(range(1, d + 1))
    g[a], g[b] = g[b], g[a]
    return tuple(g)


def fam_diag(d, pick="neg"):
    """M_w = diag(-w) o tau, tau = transposition of two coords (chosen by `pick`) if
    needed for properness.  Central and anticentral children: identity."""
    ch = []
    for w in offsets(d):
        if all(x == 0 for x in w) or all(x == -1 for x in w):
            ch.append((w, identity(d)))
            continue
        g = diag(tuple(-x for x in w))
        if det(g) == -1:
            neg = [i for i in range(d) if w[i] < 0]
            pos = [i for i in range(d) if w[i] > 0]
            if pick == "neg":
                pool = neg if len(neg) >= 2 else pos
            else:
                pool = pos if len(pos) >= 2 else neg
            a, b = pool[0], pool[1]
            g = compose(g, transposition(d, a, b))
        assert apply(g, (1,) * d) == tuple(-x for x in w) or all(x == -1 for x in w)
        ch.append((w, g))
    return ch


def random_sub(d, rng):
    ch = []
    for w in offsets(d):
        target = (1,) * d if all(x == 0 for x in w) else tuple(-x for x in w)
        ch.append((w, rng.choice(coset(d, target))))
    return ch
