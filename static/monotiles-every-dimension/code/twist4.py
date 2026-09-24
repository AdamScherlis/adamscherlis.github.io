import itertools, sys, time
from prodtwist import *
from fast import *
from chairlib import all_frames

d = 4
E = Engine(d)
blocks = [[0, 1], [2, 3]]
one = (1,) * d


def sinv(w, b):
    a, c = w[b[0]], w[b[1]]
    if (a, c) == (-1, 1):
        return 1
    if (a, c) == (1, -1):
        return -1
    return 0


def power(g, n):
    r = identity(d)
    if n < 0:
        g = inverse(g)
        n = -n
    for _ in range(n):
        r = compose(r, g)
    return r


stab1 = [g for g in all_frames(d, True) if apply(g, one) == one]
print("stab1", len(stab1))
res = []
t0 = time.time()
for K1 in stab1:
    for K2 in stab1:
        ch = []
        for w, g in product_children(d, blocks):
            if all(x == 0 for x in w) or all(x == -1 for x in w):
                ch.append((w, g)); continue
            s1, s2 = sinv(w, blocks[0]), sinv(w, blocks[1])
            g2 = compose(g, compose(power(K1, s1), power(K2, s2)))
            ch.append((w, g2))
        S = System2(E, ch)
        if S.bad:
            continue
        res.append((S.nclasses, K1, K2))
res.sort(reverse=True)
print(time.time() - t0)
from collections import Counter
print(Counter(r[0] for r in res))
for r in res[:15]:
    print(r)
