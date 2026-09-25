"""Virtual-pointer relative frames D = V'^{-1} V across axial faces of closed contacts."""
from fast import *
from collections import defaultdict, Counter


def is_notch_face(face):
    v, i, s = face
    return v[i] == -1 and s == 1 and sum(1 for x in v if x == -1) == 1


def vp_relations(E, ch, contacts=None):
    if contacts is None:
        contacts = closure_contacts(E, ch)
    H = {c: hi for c, hi in ch}
    rels = Counter()
    for B in contacts:
        t, gi = B
        for f, fB, i in E.shared_faces(B):
            fa = E.faces[f]
            fb = E.faces[fB]
            if is_notch_face(fa) or is_notch_face(fb):
                continue
            # V = H_{w}, V' = G_B H_{w'}
            V = H[fa[0]]
            Vp = E.mul[gi][H[fb[0]]]
            D = E.mul[E.inv[Vp]][V]
            rels[E.frames[D]] += 1
    return rels


if __name__ == "__main__":
    from chair44 import chair44_children
    E = Engine(3)
    ch = E.make_children(chair44_children())
    r = vp_relations(E, ch)
    for D, n in sorted(r.items()):
        print(D, n, "det", det(D))
