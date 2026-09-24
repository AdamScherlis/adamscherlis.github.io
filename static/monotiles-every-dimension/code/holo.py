"""Face-meeting graph with twists; holonomy diagnostics."""
from fast import *
from collections import defaultdict


def face_meetings(E, contacts):
    """dict (f, g) -> set of twists (tuple mapping tangent index a -> b) and example contacts"""
    meet = defaultdict(set)
    ex = defaultdict(list)
    for B in contacts:
        gi = B[1]
        for f, fB, i in E.shared_faces(B):
            tw = tuple(E.tmap[gi][i])
            meet[(f, fB)].add(tw)
            ex[(f, fB, tw)].append(B)
    return meet, ex


if __name__ == "__main__":
    import sys
    from chair44 import chair44_children
    E = Engine(3)
    ch = E.make_children(chair44_children())
    C = closure_contacts(E, ch)
    meet, ex = face_meetings(E, C)
    multi = {k: v for k, v in meet.items() if len(v) > 1}
    print("chair44: face pairs", len(meet), "with multiple twists", len(multi))
