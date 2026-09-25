"""Chair44 child table (Tsiokos, Table 1) in chairlib conventions."""
from chairlib import *

TABLE = [
    ((0, 1, 2), (1, 1, 1), (0, 0, 0)),
    ((1, 0, 2), (1, 1, -1), (0, 0, 4)),
    ((0, 2, 1), (1, -1, 1), (0, 4, 0)),
    ((2, 0, 1), (1, -1, -1), (0, 4, 4)),
    ((2, 1, 0), (-1, 1, 1), (4, 0, 0)),
    ((1, 2, 0), (-1, 1, -1), (4, 0, 4)),
    ((0, 1, 2), (-1, -1, 1), (4, 4, 0)),
    ((0, 1, 2), (1, 1, 1), (1, 1, 1)),
]


def frame_from_ps(p, s):
    d = len(p)
    g = [0] * d
    for i in range(d):
        g[p[i]] = s[i] * (i + 1)
    return tuple(g)


def chair44_children():
    out = []
    for p, s, u in TABLE:
        g = frame_from_ps(p, s)
        t = vadd(apply(g, (1, 1, 1)), u)
        c = vsub(t, (2, 2, 2))
        out.append((c, g))
    return out


if __name__ == "__main__":
    ch = chair44_children()
    for c, g in ch:
        print(c, g, det(g), "notch dir", apply(g, (1, 1, 1)))
    print("partition ok:", check_children(3, ch))
