# Code for "Monotiles in every dimension"

Pure Python 3.11 (plus `python-sat` only for experiments not reported here). Run from this directory.

| Script | What it checks | Runtime |
|---|---|---|
| `repro_chair44.py` | Rebuilds Chair44's finite certificates from its substitution alone: 30 closed contacts, 12 port classes, 44 legal contacts out of 1,194, parent contacts 697 → 116 → 44 halving to the same atlas, 33 first shells → 15 alive, each with a unique parent. Also checks that weak self-similarity holds and that there are exactly three virtual-pointer relations | ~5 s |
| `search3f.py 3` | Exhaustive search over all 6,561 child-frame choices in d = 3 | ~9 min on 4 cores |
| `searchss.py 3` | The same search with strong self-similarity imposed (everything collapses) | ~25 s |
| `vpsolve2.py d` | Solves the virtual-pointer equations for d = 3, 4, 5 (proper frames, central and anticentral children unrotated) | 1 s / 1 s / 2 min |
| `vpsolve3.py d` | The same, with reflections allowed | seconds |
| `evalsol.py`-style checks (`d5eval.py`, `lift4.py`, `twist4*.py`, `mut*.py`, `annealC.py`) | The d = 4 and d = 5 experiments summarised on the page | minutes each |
| `prismsys.py 4` | Dissections of the doubled 4D prism chair (129) | ~10 s |

Conventions: a signed permutation is a tuple `g` with `g[j] = s*(p+1)` meaning `g e_j = s e_p`.
A tile is `(t, g)` with cells at doubled centres `2t + g v`, where `v` ranges over the
prototile's cells (`{±1}^d` minus the all-ones vector for the d-chair). Children of a
supertile are listed as `(c, H)`: the child sits at `2t + G c` with frame `G H`.
