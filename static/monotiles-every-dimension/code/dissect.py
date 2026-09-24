"""Enumerate dissections of 2L (d-chair doubled) into 2^d unit chairs (coarse placements)."""
import itertools, sys
from chairlib import *
d = int(sys.argv[1])
cells2L = set()
for x in itertools.product((-3, -1, 1, 3), repeat=d):
    if all(xi > 0 for xi in x):
        continue
    cells2L.add(x)
# coarse placements: origin t (integer), notch direction s. cells = 2t + v for v in {+-1}^d, v != s
places = []
for t in itertools.product(range(-2, 3), repeat=d):
    for s in itertools.product((1, -1), repeat=d):
        cs = frozenset(tuple(2 * ti + vi for ti, vi in zip(t, v)) for v in itertools.product((1, -1), repeat=d) if v != s)
        if cs <= cells2L:
            places.append((t, s, cs))
print("placements inside 2L:", len(places))
cover = {c: [p for p in places if c in p[2]] for c in cells2L}
sols = []
def rec(rem, chosen):
    if not rem:
        sols.append(list(chosen)); return
    c = min(rem, key=lambda c: len([p for p in cover[c] if p[2] <= rem]))
    for p in cover[c]:
        if p[2] <= rem:
            chosen.append(p); rec(rem - p[2], chosen); chosen.pop()
rec(frozenset(cells2L), [])
print("dissections:", len(sols))
for s in sols[:10]:
    print(sorted((p[0], p[1]) for p in s))
