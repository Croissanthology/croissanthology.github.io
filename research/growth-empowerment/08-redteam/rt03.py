import sys,time,numpy as np
sys.path.insert(0,'../03-zero-sum'); import zero_sum as Z
from multiprocessing import Pool
def job(a):
    g,kap,sd=a
    r=Z.make_or_grab(g=g,sigma=1.3,delta=0.95,seed=sd,P=dict(Z.P2,kappa=kap))
    return a,(r['grab'],r['largest_gang_members'])
if __name__=='__main__':
    t=time.time()
    jobs=[(g,k,s) for k in [0.10,0.02] for g in [0.0,0.05,0.15,0.30] for s in [0,1]]
    with Pool(4) as p: res=p.map(job,jobs)
    agg={}
    for (g,k,s),v in res: agg.setdefault((k,g),[]).append(v)
    for k,v in sorted(agg.items()): print(k, np.round(np.mean(v,0),3))
    print(time.time()-t)
