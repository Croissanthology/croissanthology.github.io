import sys,os,io,contextlib,json
# import regimes without running its script body: exec only up to the CASES definition
src=open('../04-regimes/regimes.py').read()
src=src[:src.index('R = {}')]
ns={'__file__':'../04-regimes/regimes.py'}; exec(compile(src,'regimes_head','exec'),ns)
solve,P,CASES=ns['solve'],ns['P'],ns['CASES']
def show(lab,o): print(lab,{k:round(o[k],3) for k in ['welfare_norm','uN','x','t','c_p','c_e','g','m','psi']})
for eps0,cm in [(0.5,0.5),(0.2,0.0),(0.05,0.0)]:
    a=solve(P(W=0.002,w=(1,0,0),allow_sub=False,n=3,E=0.5,eps0=eps0,capmob=cm))
    b=solve(P(W=0.002,w=(0,1,0),allow_sub=False,n=3,E=0.5,eps0=eps0,capmob=cm))
    print('eps0',eps0,'capmob',cm,'free',round(a['welfare_norm'],3),'t',a['t'],'rent',round(b['welfare_norm'],3))
a=solve(P(W=0.002,w=(1,0,0),allow_sub=False,n=3,E=0.5,psi0=0.0)); b=solve(P(W=0.002,w=(0,1,0),allow_sub=False,n=3,E=0.5,psi0=0.0))
print('no revolt threat: free',round(a['welfare_norm'],3),'rent',round(b['welfare_norm'],3))
G=CASES['Gulf-like']; show('Gulf base',solve(P(**G)))
show('Gulf E=0',solve(P(**{**G,'E':0.0})))
show('Gulf citizens=selectorate W=S=0.5',solve(P(**{**G,'W':0.5,'S':0.5})))
show('Gulf W=0.5,S=1',solve(P(**{**G,'W':0.5,'S':1.0})))
show('Gulf n=10',solve(P(**{**G,'n':10})))
show('China base',solve(P(**CASES['China-like'])))
show('China S=1',solve(P(**{**CASES['China-like'],'S':1.0})))
print('---- free vs rent, tiny coalition, decomposition')
for kw in [dict(), dict(E=0.0), dict(E=0.0,psi0=0.0), dict(eps0=0.05,capmob=0.0), dict(eps0=0.05,capmob=0.0,E=0.0), dict(theta=1.0), dict(E=0.0,theta=1.0)]:
    a=solve(P(**{**dict(W=0.002,allow_sub=False,n=3,E=0.5,w=(1,0,0)),**kw})); b=solve(P(**{**dict(W=0.002,allow_sub=False,n=3,E=0.5,w=(0,1,0)),**kw}))
    print(kw,'free',round(a['welfare_norm'],3),'uN',round(a['uN'],3),'m',round(a['m'],3),'t',round(a['t'],2),'| rent',round(b['welfare_norm'],3),'uN',round(b['uN'],3),'m',round(b['m'],3))
print('---- g detail')
for kw in [dict(), dict(E=0.0,psi0=0.0), dict(E=0.0,psi0=0.0,gamma=0.0), dict(E=0.0,psi0=0.0,gamma=0.0,phi_p=0,phi_e=0),dict(E=0.0,psi0=0.0,gamma=0.0,eps0=0.05,capmob=0)]:
    a=solve(P(**{**dict(W=0.002,allow_sub=False,n=3,E=0.5,w=(1,0,0)),**kw}))
    print(kw,{k:round(a[k],3) for k in ['welfare_norm','uN','t','g','c_p','c_e','x','y1','welfare_ref']})
