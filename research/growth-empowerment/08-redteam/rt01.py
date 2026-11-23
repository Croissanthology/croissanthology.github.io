import sys, time, numpy as np
sys.path.insert(0,'../01-ruler'); import ruler as R
t=time.time()
def cliff(g,h=0.02,mode="reputation"):
    for f in np.round(np.linspace(0,1,51),3):
        if R.solve(R.P(g=g,h=h,phi=float(f)),mode)["c"]>0.5: return f
    return None
for g in [0.03,0.04,0.06,0.08]: print("phi cliff g",g,cliff(g), time.time()-t)
# distinct control levels across a fine g sweep with different curvature
for kw in [dict(), dict(eta=0.3), dict(eta=3), dict(m=0.02), dict(theta=0.0)]:
    cs=sorted(set(round(R.solve(R.P(g=float(g),h=0.01,**kw))["c"],2) for g in np.arange(0,0.08,0.005)))
    print(kw,"control levels used:",cs)
print(time.time()-t)
