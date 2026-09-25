import time, pickle
from d5 import *
from vpcheck import vp_table
ch = build(0)
S = System2(E, ch)
ok, tab, C = vp_table(E, S.ch)
print("VP ok", ok, tab, flush=True)
t = time.time()
cc = cached_candidates(E)
print("candidates", len(cc), time.time() - t, flush=True)
S.compute_atlas()
print("atlas", len(S.atlas), "closed in atlas", S.closed <= S.atlas, time.time() - t, flush=True)
S.parent_atlas()
s = S.summary()
print({k: s[k] for k in ('closed','classes','atlas','parent_cand','parent_disjoint','parent_legal','odd','halving_equal','halving_subset')}, time.time()-t, flush=True)
pickle.dump((ch, S.atlas, S.closed), open('d5sys.pkl','wb'))
