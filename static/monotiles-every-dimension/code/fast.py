"""Faster engine: frames indexed, cached tables.  Tiles are (t, gi)."""
import itertools
from functools import lru_cache
from chairlib import (apply, compose, inverse, det, identity, chair_cells, proto_faces,
                      tangent_orbit, vadd, vsub, vscale)


def _faces_of(cells, d):
    cs = set(cells)
    out = []
    for v in cells:
        for i in range(d):
            for s in (1, -1):
                nb = list(v); nb[i] += 2 * s
                if tuple(nb) in cs:
                    continue
                out.append((v, i, s))
    return tuple(out)


class Engine:
    def __init__(self, d, proper_only=True, cells=None):
        self.d = d
        frames = []
        for perm in itertools.permutations(range(d)):
            for signs in itertools.product((1, -1), repeat=d):
                g = tuple(s * (p + 1) for p, s in zip(perm, signs))
                if not proper_only or det(g) == 1:
                    frames.append(g)
        # identity first
        frames.sort(key=lambda g: g != identity(d))
        self.frames = frames
        self.fidx = {g: k for k, g in enumerate(frames)}
        n = len(frames)
        self.nf = n
        self.inv = [self.fidx[inverse(g)] for g in frames]
        self.mul = [[self.fidx.get(compose(a, b), -1) for b in frames] for a in frames]
        self.one = (1,) * d
        self.cells = tuple(cells) if cells is not None else chair_cells(d)
        self.cellvec = [tuple(apply(g, v) for v in self.cells) for g in frames]
        self.cellset = [frozenset(c) for c in self.cellvec]
        self.faces = proto_faces(d) if cells is None else _faces_of(self.cells, d)  # (v, i, s)
        self.face_index = {(v, i, s): k for k, (v, i, s) in enumerate(self.faces)}
        # neighbour cell of root face f (doubled)
        self.face_nb = []
        for (v, i, s) in self.faces:
            n_ = list(v)
            n_[i] += 2 * s
            self.face_nb.append(tuple(n_))
        # tangent orbits per axis
        self.m = len(tangent_orbit(d))
        self.torb = []
        self.tidx = []
        for i in range(d):
            lst = []
            for q in tangent_orbit(d):
                X = [0] * d
                k = 0
                for j in range(d):
                    if j == i:
                        continue
                    X[j] = q[k]
                    k += 1
                lst.append(tuple(X))
            self.torb.append(lst)
            self.tidx.append({X: k for k, X in enumerate(lst)})
        # tmap[gi][i] : tangent index map for B frame g, root face axis i:
        # root port q (world) -> B local G^{-1} q
        self.tmap = []
        for gi, g in enumerate(frames):
            ginv = frames[self.inv[gi]]
            row = []
            for i in range(d):
                ax = abs(ginv[i]) - 1  # G^{-1} e_i = +-e_ax
                row.append([self.tidx[ax][apply(ginv, q)] for q in self.torb[i]])
            self.tmap.append(row)
        self.origin = (0,) * d
        self.root = (self.origin, 0)
        self._cache_cells = {}

    # ------------------------------------------------------------ tiles
    def tile_cells(self, T):
        c = self._cache_cells.get(T)
        if c is None:
            t, gi = T
            t2 = tuple(2 * x for x in t)
            c = frozenset(tuple(a + b for a, b in zip(t2, v)) for v in self.cellvec[gi])
            self._cache_cells[T] = c
        return c

    def act(self, R, T):
        """R o T for placements"""
        t, gi = R
        tT, gT = T
        return (vadd(t, apply(self.frames[gi], tT)), self.mul[gi][gT])

    def rel(self, A, B):
        """A^{-1} B"""
        ta, ga = A
        tb, gb = B
        gi = self.inv[ga]
        return (apply(self.frames[gi], vsub(tb, ta)), self.mul[gi][gb])

    def notch_dir(self, gi):
        return apply(self.frames[gi], self.one)

    # ------------------------------------------------------------ contacts
    def shared_faces(self, B):
        """for root vs B (disjoint): list of (f_root, f_B, axis_i, gB)"""
        t, gi = B
        cs = self.cellset[gi]
        g = self.frames[gi]
        ginv = self.frames[self.inv[gi]]
        t2 = tuple(2 * x for x in t)
        out = []
        for f, nb in enumerate(self.face_nb):
            loc = vsub(nb, t2)
            if loc not in cs:
                continue
            v, i, s = self.faces[f]
            vB = apply(ginv, loc)
            nvec = [0] * self.d
            nvec[i] = -s
            nB = apply(ginv, tuple(nvec))
            ax = next(k for k in range(self.d) if nB[k] != 0)
            fB = self.face_index[(vB, ax, nB[ax])]
            out.append((f, fB, i))
        return out

    def port_pairs(self, B):
        gi = B[1]
        m = self.m
        out = []
        for f, fB, i in self.shared_faces(B):
            tm = self.tmap[gi][i]
            for a in range(m):
                out.append((f * m + a, fB * m + tm[a]))
        return out

    def candidates(self):
        out = set()
        d = self.d
        root_cells = self.cellset[0]
        for gi in range(self.nf):
            for nb in set(self.face_nb):
                for w in self.cellvec[gi]:
                    diff = vsub(nb, w)
                    if any(x % 2 for x in diff):
                        continue
                    t = tuple(x // 2 for x in diff)
                    B = (t, gi)
                    if self.tile_cells(B) & root_cells:
                        continue
                    out.add(B)
        return out

    # ------------------------------------------------------------ substitution
    def make_children(self, children):
        """children given as list of (c, g tuple) -> list of (c, gi)"""
        return [(c, self.fidx[g]) for c, g in children]

    def substitute(self, tiles, ch):
        out = []
        for (t, gi) in tiles:
            g = self.frames[gi]
            t2 = tuple(2 * x for x in t)
            for (c, hi) in ch:
                out.append((vadd(t2, apply(g, c)), self.mul[gi][hi]))
        return out

    def patch_contacts(self, tiles):
        owner = {}
        for k, T in enumerate(tiles):
            for c in self.tile_cells(T):
                owner[c] = k
        rels = set()
        for k, T in enumerate(tiles):
            t, gi = T
            t2 = tuple(2 * x for x in t)
            g = self.frames[gi]
            nbrs = set()
            for nb in self.face_nb:
                w = vadd(t2, apply(g, nb))
                o = owner.get(w)
                if o is not None and o != k:
                    nbrs.add(o)
            for o in nbrs:
                rels.add(self.rel(T, tiles[o]))
        return rels


class UF:
    def __init__(self, n):
        self.p = list(range(n))
        self.par = [0] * n
        self.bad = False

    def find(self, x):
        par = 0
        y = x
        while self.p[y] != y:
            par ^= self.par[y]
            y = self.p[y]
        root = y
        # path compression
        y = x
        acc = par
        while self.p[y] != y:
            nxt = self.p[y]
            pp = self.par[y]
            self.p[y] = root
            self.par[y] = acc
            acc ^= pp
            y = nxt
        return root, par

    def union(self, a, b, rel=1):
        ra, pa = self.find(a)
        rb, pb = self.find(b)
        if ra == rb:
            if pa ^ pb != rel:
                self.bad = True
            return
        self.p[ra] = rb
        self.par[ra] = pa ^ pb ^ rel


class System:
    """A substitution with its closed contacts, generic port keys and legal atlas."""

    def __init__(self, E, children, levels=None, max_tiles=200000):
        self.E = E
        d = E.d
        self.ch = E.make_children(children)
        self.children_raw = children
        tiles = [E.root]
        closed = set()
        lv = 0
        while True:
            tiles = E.substitute(tiles, self.ch)
            lv += 1
            new = E.patch_contacts(tiles)
            grew = not (new <= closed)
            closed |= new
            if levels is not None and lv >= levels:
                break
            if levels is None and (not grew and lv >= 3):
                break
            if len(tiles) * len(self.ch) > max_tiles:
                break
        self.closed = closed
        self.levels = lv
        npt = len(E.faces) * E.m
        uf = UF(npt)
        for B in closed:
            for a, b in E.port_pairs(B):
                uf.union(a, b, 1)
        self.uf = uf
        self.bad = uf.bad
        self.key = [uf.find(k) for k in range(npt)]
        self.nclasses = len({r for r, p in self.key})
        self._face_ok = {}

    def face_ok(self, f, fB, i, gi):
        k = (f, fB, gi)
        r = self._face_ok.get(k)
        if r is None:
            m = self.E.m
            tm = self.E.tmap[gi][i]
            r = True
            for a in range(m):
                ra, pa = self.key[f * m + a]
                rb, pb = self.key[fB * m + tm[a]]
                if ra != rb or pa == pb:
                    r = False
                    break
            self._face_ok[k] = r
        return r

    def legal(self, B):
        for f, fB, i in self.E.shared_faces(B):
            if not self.face_ok(f, fB, i, B[1]):
                return False
        return True

    def compute_atlas(self, cands=None):
        if cands is None:
            cands = self.E.candidates()
        self.ncand = len(cands)
        self.atlas = {B for B in cands if self.legal(B)}
        return self.atlas

    # ---------------------------------------------------------- parents
    def parent_of(self, T, i):
        E = self.E
        t, gi = T
        c, hi = self.ch[i]
        gp = E.mul[gi][E.inv[hi]]
        return (vsub(t, apply(E.frames[gp], c)), gp)

    def children_of(self, P):
        E = self.E
        T, gp = P
        g = E.frames[gp]
        return [(vadd(T, apply(g, c)), E.mul[gp][hi]) for (c, hi) in self.ch]

    def parent_atlas(self):
        E = self.E
        atlas = self.atlas
        n = len(self.ch)
        cand = set()
        for B in atlas:
            for i in range(n):
                PA = self.parent_of(E.root, i)
                inv = E.inv[PA[1]]
                for j in range(n):
                    PB = self.parent_of(B, j)
                    cand.add(E.rel(PA, PB))
        cand.discard(E.root)
        chA = self.children_of(E.root)
        cellsA = {}
        for k, T in enumerate(chA):
            for c in E.tile_cells(T):
                cellsA[c] = k
        res = set()
        ndis = 0
        for R in cand:
            chB = self.children_of(R)
            cellsB = {}
            clash = False
            for k, T in enumerate(chB):
                for c in E.tile_cells(T):
                    if c in cellsA:
                        clash = True
                        break
                    cellsB[c] = k
                if clash:
                    break
            if clash:
                continue
            ndis += 1
            ok = True
            for Ta in chA:
                t, gi = Ta
                t2 = tuple(2 * x for x in t)
                g = E.frames[gi]
                nb = set()
                for w in E.face_nb:
                    x = vadd(t2, apply(g, w))
                    k = cellsB.get(x)
                    if k is not None:
                        nb.add(k)
                for k in nb:
                    if E.rel(Ta, chB[k]) not in atlas:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                res.add(R)
        self.parent_cand = len(cand)
        self.parent_disjoint = ndis
        self.parent_legal = res
        half = set()
        odd = 0
        for (T, g) in res:
            if any(x % 2 for x in T):
                odd += 1
            else:
                half.add((tuple(x // 2 for x in T), g))
        self.half = half
        self.odd = odd
        return res

    def summary(self):
        return dict(levels=self.levels, closed=len(self.closed), classes=self.nclasses,
                    bad=self.bad, cand=getattr(self, 'ncand', None),
                    atlas=len(getattr(self, 'atlas', ())),
                    closed_in_atlas=(self.closed <= getattr(self, 'atlas', set())),
                    parent_cand=getattr(self, 'parent_cand', None),
                    parent_disjoint=getattr(self, 'parent_disjoint', None),
                    parent_legal=len(getattr(self, 'parent_legal', ())),
                    odd=getattr(self, 'odd', None),
                    halving_equal=(getattr(self, 'half', None) == getattr(self, 'atlas', None)
                                   and getattr(self, 'odd', 1) == 0),
                    halving_subset=(getattr(self, 'half', {1}) <= getattr(self, 'atlas', set())
                                    and getattr(self, 'odd', 1) == 0))


def full(d, children, E=None, parent=True):
    if E is None:
        E = Engine(d)
    S = System(E, children)
    if S.bad:
        return S
    S.compute_atlas()
    if parent:
        S.parent_atlas()
    return S


if __name__ == "__main__":
    import time
    from chair44 import chair44_children
    t = time.time()
    S = full(3, chair44_children())
    print(S.summary(), time.time() - t)


def closure_contacts(E, ch):
    """Exact closed contact set: sibling contacts, closed under induced child contacts."""
    root = E.root

    def kids(T):
        t, gi = T
        g = E.frames[gi]
        t2 = tuple(2 * x for x in t)
        return [(vadd(t2, apply(g, c)), E.mul[gi][hi]) for (c, hi) in ch]

    def contacts_between(As, Bs):
        cellsB = {}
        for k, T in enumerate(Bs):
            for c in E.tile_cells(T):
                cellsB[c] = k
        out = set()
        for A in As:
            t, gi = A
            t2 = tuple(2 * x for x in t)
            g = E.frames[gi]
            nb = set()
            for w in E.face_nb:
                k = cellsB.get(vadd(t2, apply(g, w)))
                if k is not None:
                    nb.add(k)
            for k in nb:
                if Bs[k] != A:
                    out.add(E.rel(A, Bs[k]))
        return out

    K0 = kids(root)
    K = contacts_between(K0, K0)
    work = list(K)
    while work:
        R = work.pop()
        new = contacts_between(K0, kids(R))
        for x in new:
            if x not in K:
                K.add(x)
                work.append(x)
    return K


_cand_cache = {}


def cached_candidates(E):
    key = (E.d, E.cells, E.nf)
    if key not in _cand_cache:
        cs = sorted(E.candidates())
        _cand_cache[key] = [(B, E.shared_faces(B)) for B in cs]
    return _cand_cache[key]


class System2(System):
    def __init__(self, E, children):
        self.E = E
        self.ch = E.make_children(children)
        self.children_raw = children
        self.closed = closure_contacts(E, self.ch)
        self.levels = 'closure'
        npt = len(E.faces) * E.m
        uf = UF(npt)
        for B in self.closed:
            for a, b in E.port_pairs(B):
                uf.union(a, b, 1)
        self.uf = uf
        self.bad = uf.bad
        self.key = [uf.find(k) for k in range(npt)]
        self.nclasses = len({r for r, p in self.key})
        self._face_ok = {}

    def compute_atlas(self, cands=None):
        cc = cached_candidates(self.E)
        self.ncand = len(cc)
        at = set()
        for B, sf in cc:
            ok = True
            for f, fB, i in sf:
                if not self.face_ok(f, fB, i, B[1]):
                    ok = False
                    break
            if ok:
                at.add(B)
        self.atlas = at
        return at


def full2(d, children, E=None, parent=True, max_atlas=None):
    if E is None:
        E = Engine(d)
    S = System2(E, children)
    if S.bad:
        return S
    S.compute_atlas()
    if parent and (max_atlas is None or len(S.atlas) <= max_atlas):
        S.parent_atlas()
    return S


class UFZ(UF):
    """Union-find with parity; classes forced to equal their own negation become 'zero'."""
    def __init__(self, n):
        super().__init__(n)
        self.zero = set()

    def union(self, a, b, rel=1):
        ra, pa = self.find(a)
        rb, pb = self.find(b)
        if ra == rb:
            if pa ^ pb != rel:
                self.zero.add(ra)
            return
        self.p[ra] = rb
        self.par[ra] = pa ^ pb ^ rel
        if ra in self.zero:
            self.zero.discard(ra)
            self.zero.add(rb)


class System3(System2):
    """Like System2 but contradictory classes become flat (key 0)."""
    def __init__(self, E, children, extra_pairs=()):
        self.E = E
        self.ch = E.make_children(children)
        self.children_raw = children
        self.closed = closure_contacts(E, self.ch)
        self.levels = 'closure'
        npt = len(E.faces) * E.m
        uf = UFZ(npt)
        for B in self.closed:
            for a, b in E.port_pairs(B):
                uf.union(a, b, 1)
        for a, b, r in extra_pairs:
            uf.union(a, b, r)
        self.uf = uf
        self.bad = False
        zr = {uf.find(z)[0] for z in uf.zero}
        key = []
        for k in range(npt):
            r, p = uf.find(k)
            key.append(('Z', 0) if r in zr else (r, p))
        self.key = key
        self.nclasses = len({r for r, p in key if r != 'Z'})
        self.nzero = sum(1 for r, p in key if r == 'Z')
        self._face_ok = {}

    def face_ok(self, f, fB, i, gi):
        k = (f, fB, gi)
        r = self._face_ok.get(k)
        if r is None:
            m = self.E.m
            tm = self.E.tmap[gi][i]
            r = True
            for a in range(m):
                ra, pa = self.key[f * m + a]
                rb, pb = self.key[fB * m + tm[a]]
                if ra == 'Z' or rb == 'Z':
                    if not (ra == 'Z' and rb == 'Z'):
                        r = False
                        break
                    continue
                if ra != rb or pa == pb:
                    r = False
                    break
            self._face_ok[k] = r
        return r
