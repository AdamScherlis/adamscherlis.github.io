"""Use the exact closed contact set C as the atlas (abstract maximal matching rules)."""
import sys, random, itertools, pickle
from fast import *
from families import coset, random_sub


def abstract_system(E, ch):
    S = System2(E, ch)
    S.atlas = set(S.closed)
    S.ncand = None
    S.parent_atlas()
    return S


if __name__ == "__main__":
    from chair44 import chair44_children
    E3 = Engine(3)
    S = abstract_system(E3, chair44_children())
    print("chair44 abstract:", {k: v for k, v in S.summary().items() if k in ('closed', 'atlas', 'parent_legal', 'halving_equal', 'halving_subset', 'odd')})
    good = pickle.load(open('vp2sol3.pkl', 'rb'))
    S = abstract_system(E3, list(good[0][2].items()))
    print("3D control abstract:", {k: v for k, v in S.summary().items() if k in ('closed', 'atlas', 'parent_legal', 'halving_equal', 'halving_subset', 'odd')})
    d = 4
    E = Engine(d)
    rng = random.Random(5)
    one = (1,) * d; zero = (0,) * d; m1 = tuple(-1 for _ in range(d))
    for trial in range(6):
        ch = random_sub(d, rng)
        ch = [(c, identity(d) if (c == zero or c == m1) else h) for c, h in ch]
        S = abstract_system(E, ch)
        print("4D random", trial, {k: v for k, v in S.summary().items() if k in ('closed', 'atlas', 'parent_legal', 'halving_equal', 'halving_subset', 'odd')}, flush=True)
