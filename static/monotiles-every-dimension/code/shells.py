"""First-shell enumeration, arc-consistency pruning and unique-parent checks."""
import sys
from chairlib import *
from parent import parent_of, children_of


def transform(r, T):
    """apply placement r=(t,G) to tile T (both in fine coords): r o T"""
    t, g = r
    tT, gT = T
    return (vadd(t, apply(g, tT)), compose(g, gT))


class ShellSystem:
    def __init__(self, proto, atlas, children):
        self.proto = proto
        self.d = proto.d
        self.atlas = set(atlas)
        self.children = children
        d = self.d
        self.root = ((0,) * d, identity(d))
        self.root_cells = set(tile_cells2(self.root))
        shell = set()
        for v in self.root_cells:
            for i in range(d):
                for s in (1, -1):
                    n = list(v)
                    n[i] += 2 * s
                    n = tuple(n)
                    if n not in self.root_cells:
                        shell.add(n)
        self.shell_cells = sorted(shell)
        self.cells_of = {B: frozenset(tile_cells2(B)) for B in self.atlas}
        self.cover = {c: [] for c in self.shell_cells}
        for B, cs in self.cells_of.items():
            for c in cs:
                if c in self.cover:
                    self.cover[c].append(B)

    def adjacent(self, B, C):
        cb = self.cells_of.get(B) or frozenset(tile_cells2(B))
        cc = self.cells_of.get(C) or frozenset(tile_cells2(C))
        for v in cb:
            for i in range(self.d):
                for s in (2, -2):
                    n = list(v)
                    n[i] += s
                    if tuple(n) in cc:
                        return True
        return False

    def compatible(self, B, C):
        cb = self.cells_of.get(B) or frozenset(tile_cells2(B))
        cc = self.cells_of.get(C) or frozenset(tile_cells2(C))
        if cb & cc:
            return B == C
        if self.adjacent(B, C):
            return normalize(B, C) in self.atlas
        return True

    def enumerate_shells(self, limit=None):
        shells = []
        chosen = []
        covered = set()

        def rec():
            if limit and len(shells) >= limit:
                return
            # first uncovered cell with fewest options
            best = None
            bestopts = None
            for c in self.shell_cells:
                if c in covered:
                    continue
                opts = []
                for B in self.cover[c]:
                    cb = self.cells_of[B]
                    if cb & covered:
                        continue
                    ok = True
                    for C in chosen:
                        if not self.compatible(B, C):
                            ok = False
                            break
                    if ok:
                        opts.append(B)
                if best is None or len(opts) < len(bestopts):
                    best, bestopts = c, opts
                    if not opts:
                        break
            if best is None:
                shells.append(frozenset(chosen))
                return
            for B in bestopts:
                chosen.append(B)
                added = self.cells_of[B]
                covered.update(added)
                rec()
                covered.difference_update(added)
                chosen.pop()

        rec()
        return shells

    # --- hypotheses
    def hypotheses(self):
        out = []
        for i in range(len(self.children)):
            P = parent_of(self.root, self.children, i)
            sibs = [T for k, T in enumerate(children_of(P, self.children)) if k != i]
            out.append((i, P, sibs))
        return out

    def consistent(self, shell, hyp):
        """siblings covering shell cells must be present exactly; siblings must not
        conflict with shell tiles."""
        i, P, sibs = hyp
        for S in sibs:
            if S in shell:
                continue
            cs = frozenset(tile_cells2(S))
            if cs & self.root_cells:
                return False
            for c in cs:
                if c in self.cover:  # a shell cell, but S not in shell
                    return False
            for C in shell:
                if not self.compatible(S, C):
                    return False
        return True


def patch_ok(ss, tiles):
    tiles = list(tiles)
    for a in range(len(tiles)):
        for b in range(a + 1, len(tiles)):
            if tiles[a] == tiles[b]:
                continue
            if not ss.compatible(tiles[a], tiles[b]):
                return False
    return True


def run_checks(proto, atlas, children, verbose=True, prune_rounds=10):
    ss = ShellSystem(proto, atlas, children)
    shells = ss.enumerate_shells()
    if verbose:
        print("shell cells", len(ss.shell_cells), "shells", len(shells))
    root = ss.root
    # arc consistency: shell S of root survives if for every neighbour X in S there is
    # a surviving shell S' with (X o S') compatible with root+S.
    alive = set(range(len(shells)))
    shell_list = [sorted(s) for s in shells]
    changed = True
    rnd = 0
    while changed and rnd < prune_rounds:
        changed = False
        rnd += 1
        for k in sorted(alive):
            S = shell_list[k]
            base = [root] + S
            ok = True
            for X in S:
                found = False
                for k2 in alive:
                    S2 = [transform(X, T) for T in shell_list[k2]]
                    # X's shell must contain root (root is adjacent to X)
                    if root not in S2:
                        continue
                    if patch_ok(ss, base + S2):
                        found = True
                        break
                if not found:
                    ok = False
                    break
            if not ok:
                alive.discard(k)
                changed = True
        if verbose:
            print("prune round", rnd, "alive", len(alive))
    hyps = ss.hypotheses()
    report = []
    for k in sorted(alive):
        S = set(shell_list[k])
        cons = [h[0] for h in hyps if ss.consistent(S, h)]
        report.append((k, cons))
    nuniq = sum(1 for k, c in report if len(c) == 1)
    nzero = sum(1 for k, c in report if len(c) == 0)
    nmulti = sum(1 for k, c in report if len(c) > 1)
    if verbose:
        print("alive shells: unique hyp", nuniq, "none", nzero, "multi", nmulti)
    return ss, shells, alive, report


if __name__ == "__main__":
    from chair44 import chair44_children
    from parent import analyse
    out, proto, closed, uf, atlas = analyse(3, chair44_children())
    run_checks(proto, atlas, chair44_children())


def completion_check(ss, shells, alive, report, verbose=True):
    """For each alive shell with unique hypothesis h, verify all siblings present in
    every compatible extension by an alive shell of the central sibling."""
    root = ss.root
    shell_list = [sorted(s) for s in shells]
    hyps = {h[0]: h for h in ss.hypotheses()}
    central_index = [k for k, (c, h) in enumerate(ss.children) if all(x == 0 for x in c)][0]
    bad = 0
    for k, cons in report:
        if len(cons) != 1:
            bad += 1
            continue
        i, P, sibs = hyps[cons[0]]
        S = set(shell_list[k])
        if i == central_index:
            if not all(T in S for T in sibs):
                bad += 1
            continue
        C = children_of(P, ss.children)[central_index]
        assert C in S, "central sibling not adjacent?"
        base = [root] + shell_list[k]
        nfound = 0
        for k2 in alive:
            S2 = [transform(C, T) for T in shell_list[k2]]
            if root not in S2:
                continue
            if not patch_ok(ss, base + S2):
                continue
            nfound += 1
            have = set(S2) | S | {root}
            if not all(T in have for T in sibs):
                bad += 1
                break
        if nfound == 0:
            bad += 1
    if verbose:
        print("completion failures", bad)
    return bad == 0
