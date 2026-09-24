"""Closed contact set of a substitution, generic port keys, legal atlas."""
import sys
from chairlib import *


class ParityUF:
    def __init__(self, n):
        self.p = list(range(n))
        self.par = [0] * n  # parity relative to parent
        self.bad = False

    def find(self, x):
        path = []
        while self.p[x] != x:
            path.append(x)
            x = self.p[x]
        root = x
        # compress
        acc = 0
        for y in reversed(path):
            acc ^= self.par[y]
            self.par[y] = acc
            self.p[y] = root
        return root

    def parity(self, x):
        self.find(x)
        return self.par[x] if self.p[x] != x else 0

    def union(self, a, b, rel):
        """key(a) = (-1)^rel key(b)"""
        ra, rb = self.find(a), self.find(b)
        pa, pb = self.parity(a), self.parity(b)
        if ra == rb:
            if (pa ^ pb) != rel:
                self.bad = True
            return
        self.p[ra] = rb
        self.par[ra] = pa ^ pb ^ rel


class Proto:
    def __init__(self, d):
        self.d = d
        self.faces = proto_faces(d)
        self.ports = proto_ports(d)
        self.port_index = {X: k for k, (fi, X) in enumerate(self.ports)}
        self.cells = set(chair_cells(d))
        self.face_of_port = [fi for fi, X in self.ports]
        self.ports_of_face = {}
        for k, (fi, X) in enumerate(self.ports):
            self.ports_of_face.setdefault(fi, []).append(k)

    def world_to_local_X(self, tile, W):
        t, g = tile
        return apply(inverse(g), vsub(W, vscale(2 * self.d, t)))

    def shared_port_pairs(self, A, B):
        """For tiles A, B (disjoint), list of (portA, portB) for coincident ports on
        shared faces."""
        d = self.d
        cellsB = set(tile_cells2(B))
        out = []
        tA, gA = A
        for fi, (v, i, s) in enumerate(self.faces):
            n = list(v)
            n[i] += 2 * s
            nw = vadd(vscale(2, tA), apply(gA, tuple(n)))
            if nw not in cellsB:
                continue
            for k in self.ports_of_face[fi]:
                W = tile_to_world_X(A, self.ports[k][1])
                XB = self.world_to_local_X(B, W)
                kb = self.port_index.get(XB)
                if kb is None:
                    raise RuntimeError("port mismatch")
                out.append((k, kb))
        return out


def patch_contacts(proto, tiles):
    d = proto.d
    owner = {}
    for idx, T in enumerate(tiles):
        for c in tile_cells2(T):
            assert c not in owner
            owner[c] = idx
    rel = set()
    pairs = []
    for idx, T in enumerate(tiles):
        t, g = T
        nbrs = set()
        for (v, i, s) in proto.faces:
            n = list(v)
            n[i] += 2 * s
            nw = vadd(vscale(2, t), apply(g, tuple(n)))
            o = owner.get(nw)
            if o is not None and o != idx:
                nbrs.add(o)
        for o in nbrs:
            r = normalize(T, tiles[o])
            if r not in rel:
                rel.add(r)
                pairs.append(r)
    return rel


def keys_from_contacts(proto, contacts):
    d = proto.d
    uf = ParityUF(len(proto.ports))
    A = ((0,) * d, identity(d))
    for B in contacts:
        for ka, kb in proto.shared_port_pairs(A, B):
            uf.union(ka, kb, 1)
    return uf


def candidate_contacts(proto, frames):
    d = proto.d
    A_cells = proto.cells
    out = set()
    for g in frames:
        for v in A_cells:
            for i in range(d):
                for s in (1, -1):
                    n = list(v)
                    n[i] += 2 * s
                    n = tuple(n)
                    if n in A_cells:
                        continue
                    for w in chair_cells(d):
                        gw = apply(g, w)
                        diff = vsub(n, gw)
                        if any(x % 2 for x in diff):
                            continue
                        t = tuple(x // 2 for x in diff)
                        B = (t, g)
                        if set(tile_cells2(B)) & A_cells:
                            continue
                        out.add(B)
    return out


def legal(proto, uf, B):
    d = proto.d
    A = ((0,) * d, identity(d))
    for ka, kb in proto.shared_port_pairs(A, B):
        if uf.find(ka) != uf.find(kb):
            return False
        if uf.parity(ka) == uf.parity(kb):
            return False
    return True


def legal_atlas(proto, uf, frames):
    cands = candidate_contacts(proto, frames)
    return {B for B in cands if legal(proto, uf, B)}, len(cands)


def closed_contacts(d, children, levels):
    proto = Proto(d)
    tiles = [((0,) * d, identity(d))]
    allrel = set()
    for L in range(levels):
        tiles = substitute(tiles, children)
        rel = patch_contacts(proto, tiles)
        allrel |= rel
    return proto, allrel, tiles


if __name__ == "__main__":
    from chair44 import chair44_children
    d = 3
    ch = chair44_children()
    proto, closed, tiles = closed_contacts(d, ch, 4)
    print("closed contacts", len(closed))
    uf = keys_from_contacts(proto, closed)
    ncls = len({uf.find(k) for k in range(len(proto.ports))})
    print("port classes", ncls, "contradiction", uf.bad)
    atlas, ncand = legal_atlas(proto, uf, all_frames(d, True))
    print("candidates", ncand, "legal", len(atlas), "closed subset", closed <= atlas)
    atlas_all, ncand2 = legal_atlas(proto, uf, all_frames(d, False))
    print("with reflections: candidates", ncand2, "legal", len(atlas_all))
