import sys, pickle, time
from multiprocessing import Pool
from vpalt import *
d = int(sys.argv[1])
E = Engine(d); S = AltSolver(E)
Dlists = {tuple(sorted(pi.items())): list(all_D(E, pi)) for pi in involutions(d)}
alld = [D for L in Dlists.values() for D in L]
canon = [tuple(sorted(p.items())) for p in canonical_pis(d)]
Da_list = [D for key in canon for D in Dlists[key]]
def job(i):
    sols = []
    for Db in alld:
        S.solve_for({'a': Da_list[i], 'b': Db}, sols)
    out = []
    for Dd, H in sols:
        out.append((gen_group(E, list(H['a'].values()) + list(H['b'].values())), Dd, H))
    return out
if __name__ == "__main__":
    print(len(Da_list), len(alld), flush=True)
    res = []
    t0 = time.time()
    with Pool(4) as p:
        for k, r in enumerate(p.imap_unordered(job, range(len(Da_list)))):
            res.extend(r)
            print(k, len(res), sorted(set(x[0] for x in res)), round(time.time()-t0), flush=True)
    pickle.dump(res, open('vpalt%d.pkl' % d, 'wb'))
