"""
Political survival with three revenue sources and three non-electoral constraints.

Run:  python3 regimes.py      (regenerates results.json and all PNG figures)

Core: selectorate logic (a leader must keep a winning coalition of size W, drawn from a
selectorate of size S, at least as happy as a challenger could make them). Extended with
  revenue: (1) tax on free skilled output, (2) rents needing no cooperation, (3) forced labour
  constraints: revolt (buy off or repress), exit (emigration + capital flight),
               plurality of power centres (n), plus the option to shrink the electorate.
The leader picks every policy by brute-force search over a grid and keeps the best feasible
choice; nothing is solved by hand except the analytic check in section 0.
"""
import json, os, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
np.random.seed(0)  # model is deterministic; seed fixed for form's sake

# ----------------------------------------------------------------------------- parameters
BASE = dict(
    A1=1.0, A2=1.0, A3=0.5,          # productivity of free work, rents, forced labour
    b=0.10,                          # subsistence everyone has
    a=0.5, g0=0.02,                  # value of public goods v(g)=a*ln(1+g/g0)
    gamma=0.12,                      # public goods raise free output: s(g)=1+gamma*ln(1+g/g0)
    phi_e=1.0, phi_p=0.3,            # how much economic control / political repression hurt free output
    eps0=0.5, capmob=0.5,            # tax-base elasticity = (eps0 + capmob*E)*(1+lam*(1-1/n))
    lam=1.0,                         # P1: competition between provinces for mobile base
    nu=0.5,                          # P2: repression/subversion cost multiplier (1+nu*ln n)
    omega=0.003,                     # P3: each extra power centre adds elites to coalition
    leak0=0.2, tour=1.0,             # P4: local skimming leak0*(1-tour*(1-1/n)) (promotion tournament)
    kap_p=0.4, kap_e=0.1,            # cost of political repression / economic control
    psi0=0.6, rho=2.0,               # revolt credibility psi0*(1-c_p)^rho
    mu=0.3, theta=0.5,               # revolution destroys mu of output; captures theta of rents
    u_out=1.0,                       # what an emigrant gets abroad
    dl=0.5,                          # toil disutility of forced labour per unit output
    c_sub=0.6, sig_s=0.05,           # shrinking electorate needs c_p >= c_sub*(fraction removed) + fixed cost
    allow_sub=True,
    W=0.01, S=1.0, n=3, E=0.5, w=(0.9, 0.1, 0.0),
    rep_auto=0.0,                    # automated security: repression cost * (1 - rep_auto)
    beta0=0.8, rho_c=1.0,            # challenger credibility beta0*(1-c_p)^rho_c (repression hampers rival organising)
)

TG = np.linspace(0.0, 0.95, 18)
CG = np.linspace(0.0, 1.0, 16)
GG = np.concatenate([[0.0], np.geomspace(0.005, 0.8, 13)])
WF = np.array([1.0, 0.5, 0.25, 0.1, 0.04, 0.01])   # electorate kept, as fraction of W_inst


def solve(p, mech=("P1", "P2", "P3", "P4")):
    """Leader's best policy. Returns dict of outcomes."""
    w1, w2, w3 = p["w"]
    n = p["n"]
    t = TG[:, None, None, None, None]
    ce = CG[None, :, None, None, None]
    cp = CG[None, None, :, None, None]
    g = GG[None, None, None, :, None]
    wf = (WF if p["allow_sub"] else WF[:1])[None, None, None, None, :]

    comp = (1 - 1 / n)
    eps = p["eps0"] + p["capmob"] * p["E"]
    # P1: provinces compete for the mobile base. Output does not vanish, it relocates; so a
    # province facing elasticity eps*(1+lam*(1-1/n)) can extract at most its own Laffer rate.
    t_cap = 1 / (1 + eps * (1 + (p["lam"] * comp if "P1" in mech else 0)))
    lnn = np.log(n) if "P2" in mech else 0.0
    leak = p["leak0"] * (1 - (p["tour"] * comp if "P4" in mech else 0))
    s = 1 + p["gamma"] * np.log1p(g / p["g0"])
    v = p["a"] * np.log1p(g / p["g0"])
    y1 = p["A1"] * w1 * (1 - ce) ** p["phi_e"] * (1 - cp) ** p["phi_p"] * (1 - t) ** eps * s * (1 - leak)
    y2 = p["A2"] * w2
    y3 = p["A3"] * w3 * ce
    uN = (1 - t) * y1 + p["b"] + v - p["dl"] * y3                    # ordinary citizen
    m = p["E"] * (1 - ce) * np.clip((p["u_out"] - uN) / p["u_out"], 0, 1)  # emigrants
    K = (p["kap_p"] * (1 - p["rep_auto"]) * cp ** 2 * (1 + p["nu"] * lnn) + p["kap_e"] * ce ** 2)
    R = (1 - m) * (t * y1 + y3) + y2

    # challenger: promises the best package (t', g') to his coalition, same state apparatus,
    # each current coalition member is in the new coalition with prob W/S -> gets (R'-g'-K)/S
    # the challenger promises a free economy (c_e=c_p=0), so his offer cannot be manipulated by
    # wrecking the economy; political repression only lowers how credible he looks (beta).
    Rch = t * y1 + y3 + y2
    spare = (Rch - g - K)[:, :1, :1, :, :]                      # challenger must balance his budget too
    Vch = np.where(spare >= 0, uN[:, :1, :1, :, :] + spare / p["S"], -np.inf).max(axis=(0, 3), keepdims=True)
    beta = p["beta0"] * (1 - cp) ** p["rho_c"]

    W = np.clip(p["W"] * wf + (p["omega"] * (n - 1) if "P3" in mech else 0), 0, 1)
    x = W * np.maximum(0.0, beta * (Vch - uN))                                   # private goods to coalition
    subfrac = 1 - wf
    subcost = p["sig_s"] * (1 + p["nu"] * lnn) * subfrac
    Urev = p["b"] + (1 - p["mu"]) * (p["A1"] * w1 + p["theta"] * y2)
    psi = p["psi0"] * (1 - cp) ** p["rho"]
    ok = (uN >= psi * Urev) & (cp >= p["c_sub"] * subfrac - 1e-9) & (t <= t_cap + 1e-9)
    resid = R - g - x - K - subcost
    viable = bool(np.any(np.broadcast_to(ok & (resid >= 0), np.broadcast_shapes(resid.shape, ok.shape))))
    if viable:                       # ruler must also balance the budget; if impossible, report best try
        ok = ok & (resid >= 0)
    resid = np.where(ok, resid, -np.inf)
    resid = np.broadcast_to(resid, np.broadcast_shapes(resid.shape, (len(TG), len(CG), len(CG), len(GG), wf.shape[-1])))
    i = np.unravel_index(np.argmax(resid), resid.shape)

    def pick(a):
        a = np.broadcast_to(a, resid.shape)
        return float(a[i])

    out = dict(t=float(TG[i[0]]), c_e=float(CG[i[1]]), c_p=float(CG[i[2]]), g=float(GG[i[3]]),
               W_kept_frac=float(WF[i[4]]), W_eff=pick(W), x=pick(x), uN=pick(uN), m=pick(m),
               R=pick(R), y1=pick(y1), resid=pick(resid), psi=pick(psi), viable=viable)
    # average over the original population: stayers, emigrants (who get u_out minus lost home attachment), coalition
    out["welfare"] = (1 - out["m"]) * out["uN"] + out["m"] * 0.5 * (p["u_out"] + out["uN"]) + out["x"]
    out["freedom"] = 1 - 0.5 * (out["c_e"] + out["c_p"])
    out["necessity"] = (1 - out["m"]) * (out["t"] * out["y1"] + p["A3"] * w3 * out["c_e"]) / max(out["R"], 1e-9)
    removal = min(1.0, out["W_eff"] / 0.5)
    escape = p["E"] * (1 - out["c_e"])
    out["revolt_threat"] = float(min(1.0, out["psi"] * Urev / max(out["uN"], 1e-9)) if out["psi"] > 0 else 0.0)
    # chance-like index of being able to remove or escape the ruler: vote, credible revolt, exit
    out["voice_exit"] = 1 - (1 - removal) * (1 - 0.5 * out["psi"]) * (1 - escape)
    # benevolent benchmark with the same technology (no control, all revenue returned)
    ref = (p["A1"] * w1 * (1 - TG[:, None]) ** eps * (1 + p["gamma"] * np.log1p(GG[None, :] / p["g0"]))
           + p["A2"] * w2 + p["b"] + p["a"] * np.log1p(GG[None, :] / p["g0"]) - GG[None, :]).max()
    out["welfare_ref"] = float(ref)
    out["welfare_norm"] = float(np.clip(out["welfare"] / ref, 0, 1))
    out["empowerment"] = (out["welfare_norm"] + out["freedom"] + out["voice_exit"]) / 3
    return out


def P(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


CASES = {
    "USA-like":   dict(W=0.5,   S=1.0,  w=(0.93, 0.07, 0.00), n=12, E=0.9),
    "China-like": dict(W=0.01,  S=0.07, w=(0.85, 0.12, 0.03), n=10, E=0.4),
    "NK-like":    dict(W=0.002, S=1.0,  w=(0.35, 0.15, 0.50), n=1,  E=0.03),
    "Gulf-like":  dict(W=0.01,  S=0.05, w=(0.15, 0.85, 0.00), n=2,  E=0.8),
}
COL = {"USA-like": "#1f77b4", "China-like": "#d62728", "NK-like": "#444444", "Gulf-like": "#e69f00"}

R = {}
t0 = time.time()

# ----------------------------------------------------------------------------- 0. check selectorate logic
# With linear private goods and v(g)=a ln(1+g/g0), the cheapest way to give each coalition member one more
# util is private goods (cost W) or public goods (cost 1/v'(g)); so g* = a*W - g0 when nothing else matters.
chk = []
for Wv in [0.005, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5]:
    o = solve(P(W=Wv, w=(0.0, 1.0, 0.0), gamma=0.0, psi0=0.0, allow_sub=False, n=1, E=0.0, rho_c=0.0))
    chk.append(dict(W=Wv, g_model=o["g"], g_formula=max(0, BASE["a"] * BASE["beta0"] * Wv - BASE["g0"]),
                    leader_keeps_share=o["resid"] / o["R"]))
R["check_selectorate"] = chk

# ----------------------------------------------------------------------------- 1. grid
Ws = np.geomspace(0.002, 0.5, 10)
mixes = np.linspace(0, 1, 11)
grid = {}
for kind in ["rent", "forced"]:
    wel = np.zeros((len(mixes), len(Ws))); fr = np.zeros_like(wel); uN = np.zeros_like(wel); tx = np.zeros_like(wel)
    for a_, sh in enumerate(mixes):
        w = (1 - sh, sh, 0.0) if kind == "rent" else (1 - sh, 0.0, sh)
        for b_, Wv in enumerate(Ws):
            o = solve(P(W=Wv, w=w, allow_sub=False, n=3, E=0.5, S=1.0))
            wel[a_, b_] = o["welfare_norm"]; fr[a_, b_] = o["freedom"]; uN[a_, b_] = o["uN"]; tx[a_, b_] = o["t"]
    grid[kind] = dict(share=mixes.tolist(), W=Ws.tolist(), welfare_norm=wel.round(4).tolist(),
                      freedom=fr.round(4).tolist(), ordinary_citizen_utility=uN.round(4).tolist(), tax=tx.round(3).tolist(),
                      election_premium=(wel[:, -1] - wel[:, 0]).round(4).tolist())
R["grid"] = grid
# ablation: no productivity effect of public goods (Olson channel) and no freedom->output link
abl = {}
for name, kw in [("baseline", {}), ("no_public_goods_productivity", dict(gamma=0.0)),
                 ("repression_free_for_output", dict(phi_p=0.0, phi_e=0.0))]:
    prem = []
    for sh in mixes:
        lo = solve(P(W=Ws[0], w=(1 - sh, sh, 0), allow_sub=False, **kw))["welfare_norm"]
        hi = solve(P(W=Ws[-1], w=(1 - sh, sh, 0), allow_sub=False, **kw))["welfare_norm"]
        prem.append(dict(rent_share=float(sh), welfare_small_W=lo, welfare_electoral=hi))
    abl[name] = prem
R["grid_ablation"] = abl
print("grid done", round(time.time() - t0, 1))

# ----------------------------------------------------------------------------- 2. cases
cases = {k: solve(P(**v)) for k, v in CASES.items()}
R["cases"] = cases
# which single parameter moves China toward NK?
ch, nk = CASES["China-like"], CASES["NK-like"]
swap = {}
for key in ["W", "S", "w", "n", "E"]:
    o = solve(P(**{**ch, key: nk[key]}))
    swap[key] = dict(welfare_norm=o["welfare_norm"], freedom=o["freedom"], empowerment=o["empowerment"])
# split revenue mix into rent part and forced-labour part
o = solve(P(**{**ch, "w": (0.85 - 0.47, 0.12, 0.50)})); swap["w_forced_only"] = dict(welfare_norm=o["welfare_norm"], freedom=o["freedom"], empowerment=o["empowerment"])
o = solve(P(**{**ch, "w": (0.35, 0.62, 0.03)})); swap["w_rent_only"] = dict(welfare_norm=o["welfare_norm"], freedom=o["freedom"], empowerment=o["empowerment"])
R["china_to_nk_one_param"] = swap
print("cases done", round(time.time() - t0, 1))

# ----------------------------------------------------------------------------- 3. automation
alphas = np.linspace(0, 1, 21)
variants = {"baseline": {}, "no_electorate_shrinking": dict(allow_sub=False),
            "automated_security": "auto", "rebels_cannot_seize_AI": dict(theta=0.0)}
auto = {}
for vname, vkw in variants.items():
    auto[vname] = {}
    for cname, cp_ in CASES.items():
        rows = []
        w1, w2, w3 = cp_["w"]
        for al in alphas:
            kw = dict(cp_); kw["w"] = (w1 * (1 - al), w2 + w1 * al, w3)
            if vkw == "auto":
                kw["rep_auto"] = 0.8 * al
            else:
                kw.update(vkw)
            o = solve(P(**kw))
            rows.append({k: round(o[k], 4) for k in ["welfare", "welfare_norm", "uN", "x", "freedom", "W_eff", "W_kept_frac",
                                                     "necessity", "empowerment", "c_p", "c_e", "t", "g", "m"]})
        auto[vname][cname] = rows
R["automation"] = dict(alpha=alphas.tolist(), runs=auto)
# sensitivity of the electorate-shrinking threshold for USA-like
sens = []
for c_sub in [0.3, 0.6, 0.9]:
    for sig in [0.02, 0.05, 0.15]:
        thr = None
        for al in alphas:
            w1, w2, w3 = CASES["USA-like"]["w"]
            o = solve(P(**{**CASES["USA-like"], "w": (w1 * (1 - al), w2 + w1 * al, w3), "c_sub": c_sub, "sig_s": sig}))
            if o["W_kept_frac"] < 1:
                thr = float(al); break
        sens.append(dict(c_sub=c_sub, sig_s=sig, alpha_threshold=thr))
R["usa_shrink_threshold_sensitivity"] = sens
print("automation done", round(time.time() - t0, 1))

# ----------------------------------------------------------------------------- 4. plurality
ns = [1, 2, 3, 5, 8, 12, 20, 30]
plur = {}
for cname in ["China-like", "USA-like", "Gulf-like"]:
    plur[cname] = {}
    for mname, mech in [("all", ("P1", "P2", "P3", "P4")), ("P1_tax_competition", ("P1",)),
                        ("P2_costly_repression", ("P2",)), ("P3_more_elites", ("P3",)),
                        ("P4_promotion_tournament", ("P4",))]:
        rows = []
        for nv in ns:
            o = solve(P(**{**CASES[cname], "n": nv}), mech=mech)
            rows.append({k: round(o[k], 4) for k in ["welfare_norm", "freedom", "empowerment", "uN", "t", "c_p"]})
        plur[cname][mname] = rows
R["plurality"] = dict(n=ns, runs=plur)
print("plurality done", round(time.time() - t0, 1))

with open(os.path.join(HERE, "results.json"), "w") as f:
    json.dump(R, f, indent=1)

# ----------------------------------------------------------------------------- figures
plt.rcParams.update({"font.size": 10})
fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
for ax, kind, lab in [(axs[0], "rent", "share of economy from rents (oil / aid / AI)"),
                      (axs[1], "forced", "share of economy from forced labour")]:
    im = ax.imshow(np.array(grid[kind]["welfare_norm"]), origin="lower", aspect="auto", vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(Ws))); ax.set_xticklabels([f"{x:.3f}" for x in Ws], rotation=60)
    ax.set_yticks(range(len(mixes))); ax.set_yticklabels([f"{x:.1f}" for x in mixes])
    ax.set_xlabel("size of group the ruler must satisfy (share of population)"); ax.set_ylabel(lab)
    ax.set_title("Citizen welfare (1 = best achievable)")
    plt.colorbar(im, ax=ax)
for kind, ls in [("rent", "-"), ("forced", "--")]:
    axs[2].plot(mixes, grid[kind]["election_premium"], ls, marker="o", label=f"varying {kind} share")
axs[2].set_xlabel("share of economy not from free citizens' work"); axs[2].set_ylabel("welfare gain: electoral vs tiny coalition")
axs[2].set_title("Where elections matter most"); axs[2].legend(); axs[2].grid(alpha=.3)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "fig1_grid.png"), dpi=150); plt.close()

fig, axs = plt.subplots(2, 3, figsize=(15, 8))
keys = [("welfare_norm", "Citizen welfare (share of best achievable)"), ("freedom", "Freedom"),
        ("W_eff", "Effective electorate size"), ("necessity", "Ruler's revenue that needs citizens"),
        ("empowerment", "Empowerment index"), ("c_p", "Political repression")]
for ax, (k, tt) in zip(axs.flat, keys):
    for cname in CASES:
        ax.plot(alphas, [r[k] for r in auto["baseline"][cname]], color=COL[cname], label=cname, lw=2)
        ax.plot(alphas, [r[k] for r in auto["no_electorate_shrinking"][cname]], color=COL[cname], ls=":", lw=1.2)
    ax.set_title(tt); ax.set_xlabel("share of citizens' work taken over by machines"); ax.grid(alpha=.3)
axs[0, 0].legend(fontsize=8); axs[0, 2].text(0.02, 0.03, "dotted: ruler cannot shrink the electorate", transform=axs[0, 2].transAxes, fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "fig3_automation.png"), dpi=150); plt.close()

fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
for ax, cname in zip(axs, ["China-like", "USA-like", "Gulf-like"]):
    for mname, rows in plur[cname].items():
        ax.plot(ns, [r["empowerment"] for r in rows], marker="o", label=mname, lw=2.5 if mname == "all" else 1.2)
    ax.set_xscale("log"); ax.set_xlabel("number of independent power centres"); ax.set_ylabel("empowerment index")
    ax.set_title(cname); ax.grid(alpha=.3)
axs[0].legend(fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "fig4_plurality.png"), dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(7, 5.5))
for cname in CASES:
    rows = auto["baseline"][cname]
    xs = [r["necessity"] for r in rows]; ys = [r["empowerment"] for r in rows]
    ax.plot(xs, ys, color=COL[cname], alpha=.5)
    ax.scatter(xs[0], ys[0], color=COL[cname], s=90, label=f"{cname} today", zorder=3)
    ax.scatter(xs[-1], ys[-1], color=COL[cname], s=90, marker="x", zorder=3)
ax.set_xlabel("necessity: share of ruler's revenue lost if citizens stop cooperating")
ax.set_ylabel("empowerment: welfare + freedom + ability to remove or escape")
ax.set_title("Necessity vs empowerment (line = path as machines take over work, x = full automation)")
ax.title.set_fontsize(9); ax.legend(); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "fig5_necessity_vs_empowerment.png"), dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(8, 4.5))
names = list(CASES)
mets = ["welfare_norm", "freedom", "voice_exit", "empowerment"]
for j, mname in enumerate(mets):
    ax.bar(np.arange(4) + j * 0.2, [cases[c][mname] for c in names], 0.2, label=mname)
ax.set_xticks(np.arange(4) + 0.3); ax.set_xticklabels(names); ax.legend(); ax.set_title("Four stylized regimes, same model")
plt.tight_layout(); plt.savefig(os.path.join(HERE, "fig2_cases.png"), dpi=150); plt.close()
print("total", round(time.time() - t0, 1))
