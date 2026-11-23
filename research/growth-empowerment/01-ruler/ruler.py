"""
The ruler's calculation.

A ruler picks, every year, a take rate tau (share of human-made output he keeps) and a
control level c (how tightly subjects are watched and coerced). Subjects do two things:

  (a) field effort e: visible and forceable. Voluntary effort is e = (1-tau)(1-mu);
      control forces effort up to c (e = max(voluntary, c)). Effort costs e^2/2.
  (b) innovation s: private, unforceable. A subject only puts in s if she expects to keep
      the future return. Control chills it (productivity factor (1-c)^eta).
      Growth G = g * [ (1-phi) * (1-c)^eta * s + phi ]   (phi = share of growth from machines)

Ruler's yearly payoff per unit of productivity A:
      R = tau*(1-mu)*e + mu - m*c^2 - b
  m*c^2 = cost of watching/coercing; b = payment needed to stop revolt:
      b = max(0, theta*(1-c) - u),  u = subject net utility.  (control makes revolt harder)
  mu = share of field output done by ruler-owned machines (0 except in one variant).

Commitment problem: the ruler cannot promise future tau. Three solution concepts:
  * commitment   : picks a permanent (tau, c) once (benchmark, a "constitution").
  * reputation   : picks a permanent (tau, c) that is self-enforcing: at every date the
                   value of keeping the promise >= value of a one-year grab (static-best
                   take + seizing subjects' accumulated wealth omega*income) followed by
                   the no-trust (Markov) equilibrium forever.
  * markov (MPE) : no promises believed; each year tau is chosen ex post.
Ruler survives each year with prob (1-h) (h = hazard of losing power); discount r.

Run:  python3 ruler.py      (regenerates results.json and all figures, ~1-3 min)
"""
import json, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

np.random.seed(0)
T_HOR = 400          # truncation of infinite sums (years)
TAU = np.linspace(0, 1, 101)
CC = np.linspace(0, 1, 51)
TG, CG = np.meshgrid(TAU, CC, indexing="ij")
TF, CF = TG.ravel(), CG.ravel()

BASE = dict(g=0.02, r=0.04, h=0.02, beta_s=0.95, kappa=5.0, eta=1.0, m=0.15,
            theta=0.15, omega=2.0, phi=0.0, mu=0.0, forceable_growth=False,
            lam=0.0, gR=0.02, SR0=0.25, N=0.0)

COL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, MUTED, GRID = "#1a1a19", "#6b6a63", "#e1e0d9"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "lines.linewidth": 2})


def stage(tau, c, p, vA=None):
    """Per-unit-of-A quantities for policy (tau, c). vA = subjects' value of one more unit
    of A (from their expectation of future policy); default: they expect (tau, c) forever."""
    mu = p["mu"]
    ev = (1 - tau) * (1 - mu)
    e = np.clip(np.maximum(ev, c), 0, 1)
    u0 = (1 - tau) * (1 - mu) * e - e ** 2 / 2          # field net utility
    if vA is None:
        vA = np.maximum(u0, 0) / (1 - p["beta_s"])
    prod = (1 - c) ** p["eta"]
    if p["forceable_growth"]:
        prod = np.ones_like(c * 1.0)
        s_vol = np.clip(p["beta_s"] * vA / p["kappa"], 0, 1)
        s = np.maximum(s_vol, c)                          # can be ordered like field work
    else:
        s = np.clip(p["beta_s"] * prod * vA / p["kappa"], 0, 1)
    gh = p["g"] * (1 - p["phi"])
    G = gh * prod * s + p["g"] * p["phi"]
    u = u0 - p["kappa"] * gh * s ** 2 / 2               # innovation effort cost
    b = np.maximum(0, p["theta"] * (1 - c) - u)
    R = tau * (1 - mu) * e + mu - p["m"] * c ** 2 - b
    C = (1 - tau) * (1 - mu) * e + b                     # subject consumption per A
    Y = (1 - mu) * e + mu                                # output per A
    return dict(e=e, u=u + b, b=b, s=s, G=G, R=R, C=C, Y=Y)


def geo(R, q, T=T_HOR):
    q = np.asarray(q, float)
    out = np.where(np.abs(1 - q) < 1e-12, T, (1 - q ** T) / np.where(np.abs(1 - q) < 1e-12, 1, 1 - q))
    return R * out


def beta(p):
    return (1 - p["h"]) / (1 + p["r"])


def solve_mpe(p, iters=300):
    """Markov equilibrium: tau chosen ex post each year; subjects expect the equilibrium."""
    bet = beta(p)
    te, ce, v = 0.5, 0.0, 0.0
    for _ in range(iters):
        se = stage(np.array(te), np.array(ce), p)
        ue = (1 - te) * (1 - p["mu"]) * se["e"] - se["e"] ** 2 / 2
        vA = max(float(ue), 0) / (1 - p["beta_s"])
        st = stage(TF, CF, p, vA=vA)
        obj = st["R"] + bet * (1 + st["G"]) * v
        k = int(np.argmax(obj))
        nt, nc = TF[k], CF[k]
        sk = stage(np.array(nt), np.array(nc), p)
        nv = float(geo(sk["R"], bet * (1 + sk["G"])))
        if abs(nt - te) < 1e-9 and abs(nc - ce) < 1e-9 and abs(nv - v) < 1e-7:
            break
        te, ce, v = nt, nc, 0.5 * v + 0.5 * nv
    return dict(tau=te, c=ce, v=nv, G=float(sk["G"]), R=float(sk["R"]))


def static_best(p):
    st = stage(TF, CF, p, vA=0.0)
    return float(st["R"].max())


def solve(p, mode="reputation"):
    """Best permanent policy. mode in {'commitment','reputation','markov'}."""
    bet = beta(p)
    if mode == "markov":
        m = solve_mpe(p)
        return pack(p, m["tau"], m["c"])
    st = stage(TF, CF, p)
    V = geo(st["R"], bet * (1 + st["G"]))
    if mode == "reputation":
        m = solve_mpe(p)
        D = static_best(p) + p["omega"] * st["C"] + bet * (1 + m["G"]) * m["v"]
        feas = V >= D - 1e-12
        V = np.where(feas, V, -np.inf)
        if not np.isfinite(V).any() or V.max() < m["v"]:
            return pack(p, m["tau"], m["c"], fallback=True)
    k = int(np.argmax(V))
    return pack(p, TF[k], CF[k])


def necessity(p, G, e, N=0.0, horizon=30, A_path=None):
    """Share of 30-year PV output lost if all subjects stop working and inventing."""
    t = np.arange(horizon)
    d = 1.04 ** -t
    A = (1 + G) ** t if A_path is None else A_path[:horizon]
    Y_with = ((1 - p["mu"]) * e + p["mu"]) * A + N
    A0 = (1 + p["g"] * p["phi"]) ** t
    Y_wo = p["mu"] * A0 + N
    return float(1 - (d * Y_wo).sum() / (d * Y_with).sum())


def pack(p, tau, c, fallback=False):
    s = stage(np.array(tau), np.array(c), p)
    share = float(s["C"] / s["Y"]) if s["Y"] > 0 else 0.0
    return dict(tau=float(tau), c=float(c), share_kept=share, freedom=float(1 - c),
                effort=float(s["e"]), innovation=float(s["s"]), growth=float(s["G"]),
                net_surplus=float(s["u"]), ruler_take=float(s["R"]),
                necessity=necessity(p, float(s["G"]), float(s["e"])), markov_fallback=fallback)


def P(**kw):
    q = dict(BASE); q.update(kw); return q


# ---------------------------------------------------------------- threat world
def threat_solve(p, T=T_HOR, Tcheck=120, mode="reputation"):
    """Rival state strength SR0*(1+gR)^t; own strength = ruler revenue (R*A + N).
    Yearly hazard of losing power h = h0 + lam*max(0, 1 - own/rival)."""
    bet = 1 / (1 + p["r"])
    h0, lam, N = p["h"], p["lam"], p["N"]
    st = stage(TF, CF, p)
    t = np.arange(T)
    SR = p["SR0"] * (1 + p["gR"]) ** t
    logA = np.outer(np.log1p(st["G"]), t)                       # (pol, T)
    A = np.exp(logA)
    pay = st["R"][:, None] * A + N
    h = np.clip(h0 + lam * np.maximum(0, 1 - pay / SR[None, :]), 0, 1)
    V = np.zeros_like(A)
    nxt = np.zeros(len(TF))
    for k in range(T - 1, -1, -1):
        V[:, k] = pay[:, k] + bet * (1 - h[:, k]) * nxt
        nxt = V[:, k]
    if mode == "commitment":
        k = int(np.argmax(V[:, 0]))
        return tpack(p, k, st, A, h, SR)
    # punishment = Markov policy of the no-threat game (approximation), value on (t, logA) grid
    m = solve_mpe(p)
    sm = stage(np.array(m["tau"]), np.array(m["c"]), p)
    RM, GM = float(sm["R"]), float(sm["G"])
    grid = np.linspace(-2, 25, 600)
    W = np.zeros((T + 1, grid.size))
    for k in range(T - 1, -1, -1):
        Ag = np.exp(grid)
        payk = RM * Ag + N
        hk = np.clip(h0 + lam * np.maximum(0, 1 - payk / SR[k]), 0, 1)
        Wn = np.interp(grid + np.log1p(GM), grid, W[k + 1])
        W[k] = payk + bet * (1 - hk) * Wn
    Rdev = static_best(p)
    D = np.zeros((len(TF), Tcheck))
    for k in range(Tcheck):
        Wn = np.interp(logA[:, k] + np.log1p(GM), grid, W[k + 1])
        D[:, k] = Rdev * A[:, k] + N + p["omega"] * st["C"] * A[:, k] + bet * (1 - h[:, k]) * Wn
    feas = (V[:, :Tcheck] >= D - 1e-9).all(axis=1)
    kM = int(np.argmin(np.abs(TF - m["tau"]) + np.abs(CF - m["c"])))
    feas[kM] = True
    V0 = np.where(feas, V[:, 0], -np.inf)
    k = int(np.argmax(V0))
    return tpack(p, k, st, A, h, SR)


def tpack(p, k, st, A, h, SR, years=50):
    Ak = A[k, :years]
    Y = st["Y"][k] * Ak + p["N"]
    share = float(np.mean(st["C"][k] * Ak / Y))
    surv = float(np.prod(1 - h[k, :years]))
    return dict(tau=float(TF[k]), c=float(CF[k]), share_kept=share, freedom=float(1 - CF[k]),
                growth=float(st["G"][k]), innovation=float(st["s"][k]),
                survive_50y=surv, hazard_y0=float(h[k, 0]), hazard_y50=float(h[k, years - 1]),
                necessity=necessity(p, float(st["G"][k]), float(st["e"][k]), N=p["N"]),
                gdp_50y_vs_rival=float(Ak[-1] / ((1 + p["gR"]) ** (years - 1))))


# ---------------------------------------------------------------- experiments
def main():
    t0 = time.time()
    res = {"parameters_baseline": BASE,
           "notes": "Policies are per-year take rate tau and control c in [0,1]; share_kept = subjects' "
                    "consumption / total output; freedom = 1 - control; necessity = share of 30y "
                    "present-value output lost if subjects stop all work and invention."}

    # ---- Q1: sweep growth potential g, several horizons, three solution concepts
    gs = np.round(np.arange(0, 0.0501, 0.0025), 4)
    hs = {"tenure ~100y (h=1%)": 0.01, "tenure ~33y (h=3%)": 0.03,
          "tenure ~14y (h=7%)": 0.07, "tenure ~7y (h=15%)": 0.15}
    q1 = {}
    for mode in ["commitment", "reputation", "markov"]:
        q1[mode] = {}
        for lab, h in hs.items():
            rows = [solve(P(g=float(g), h=h), mode) for g in gs]
            q1[mode][lab] = {k: [r_[k] for r_ in rows] for k in
                             ["tau", "c", "share_kept", "freedom", "growth", "innovation", "ruler_take"]}
    res["q1_growth_sweep"] = {"g": gs.tolist(), "by_mode": q1}

    # thresholds: smallest g at which optimal control falls below 0.5
    def thresh(p_over, mode):
        for g in np.arange(0, 0.2001, 0.0025):
            if solve(P(g=float(g), **p_over), mode)["c"] < 0.5:
                return float(round(g, 4))
        return None
    hgrid = [0.0, 0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20]
    thr = {}
    for mode in ["commitment", "reputation", "markov"]:
        thr[mode] = {f"r={r}": [thresh(dict(h=h, r=r), mode) for h in hgrid] for r in [0.02, 0.04, 0.08]}
    res["q1_threshold_g_vs_hazard"] = {"hazard_h": hgrid, "threshold_g_by_mode_and_r": thr,
                                       "definition": "smallest achievable growth g (searched 0-20%) at which "
                                                     "the ruler's best control level drops below 0.5; null = none"}
    # sensitivity of threshold to unknown parameters (reputation, r=4%, h=3%)
    sens = {}
    for name, vals in [("kappa", [2.5, 5, 10]), ("eta", [0.5, 1, 2]), ("m", [0.05, 0.15, 0.3]),
                       ("theta", [0.05, 0.15, 0.3]), ("omega", [0, 2, 5]), ("beta_s", [0.9, 0.95, 0.98])]:
        sens[name] = {str(v): thresh({"h": 0.03, name: v}, "reputation") for v in vals}
    res["q1_threshold_sensitivity_reputation_r4_h3"] = sens

    # ablation: growth made forceable (can be ordered, not chilled by control)
    abl = {}
    for lab, h in [("h=3%", 0.03)]:
        rows = [solve(P(g=float(g), h=h, forceable_growth=True), "reputation") for g in gs]
        abl[lab] = {k: [r_[k] for r_ in rows] for k in ["tau", "c", "share_kept", "freedom", "growth"]}
    res["ablation_forceable_growth"] = {"g": gs.tolist(), **abl}
    print("Q1 done", round(time.time() - t0, 1))

    # ---- Q2: the serf. g = 0
    serf = solve(P(g=0.0, h=0.03), "reputation")
    serf_ms = {str(m): solve(P(g=0.0, h=0.03, m=m), "reputation") for m in [0.05, 0.15, 0.25, 0.35, 0.5]}
    # ruler payoff as a function of control at g=0 (best tau for each c)
    st = stage(TF, CF, P(g=0.0))
    Rmat = st["R"].reshape(TG.shape)
    res["q2_serf"] = {"policy_g0": serf, "by_coercion_cost_m": serf_ms,
                      "ruler_best_take_by_control": {"c": CC.tolist(), "R": Rmat.max(axis=0).tolist()}}
    print("Q2 done", round(time.time() - t0, 1))

    # ---- Q3: outside threat + revolt (China vs North Korea)
    scen3 = {
        "Dynasty, rival threat, catch-up potential 5% (China-like)": P(g=0.05, h=0.02, lam=0.15, gR=0.02),
        "Same but nukes (threat off)": P(g=0.05, h=0.02, lam=0.0),
        "Short horizon (h=15%), rival threat": P(g=0.05, h=0.15, lam=0.15),
        "Nukes + short horizon + outside rents (North Korea-like)": P(g=0.05, h=0.15, lam=0.0, N=0.15),
        "Nukes + long horizon + outside rents": P(g=0.05, h=0.02, lam=0.0, N=0.15),
        "Threat + short horizon + outside rents": P(g=0.05, h=0.15, lam=0.15, N=0.15),
    }
    q3 = {k: threat_solve(v) for k, v in scen3.items()}
    lams = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3]
    h0s = [0.01, 0.03, 0.05, 0.08, 0.12, 0.2]
    grid_free = [[threat_solve(P(g=0.05, h=h0, lam=l))["freedom"] for l in lams] for h0 in h0s]
    grid_share = [[threat_solve(P(g=0.05, h=h0, lam=l))["share_kept"] for l in lams] for h0 in h0s]
    res["q3_threat"] = {"scenarios": q3, "sweep": {"threat_lam": lams, "base_hazard_h0": h0s,
                        "freedom[h0][lam]": grid_free, "share_kept[h0][lam]": grid_share,
                        "g": 0.05, "rival_growth": 0.02}}
    print("Q3 done", round(time.time() - t0, 1))

    # ---- Q4: AI dial
    phis = np.round(np.linspace(0, 1, 51), 3)
    q4 = {}
    for lab, kw in [("g=2%, h=2%", dict(g=0.02, h=0.02)), ("g=4%, h=2%", dict(g=0.04, h=0.02)),
                    ("g=4%, h=2%, commitment", dict(g=0.04, h=0.02))]:
        mode = "commitment" if "commitment" in lab else "reputation"
        rows = [solve(P(phi=float(f), **kw), mode) for f in phis]
        q4[lab] = {k: [r_[k] for r_ in rows] for k in ["tau", "c", "share_kept", "freedom", "growth",
                                                       "necessity", "ruler_take"]}
    # variant: machines also take over field work (mu)
    mus = np.round(np.linspace(0, 1, 26), 3)
    rows = [solve(P(g=0.04, h=0.02, phi=1.0, mu=float(mu)), "reputation") for mu in mus]
    q4_mu = {"mu": mus.tolist(), **{k: [r_[k] for r_ in rows] for k in
                                    ["tau", "c", "share_kept", "freedom", "necessity"]}}
    res["q4_ai_dial"] = {"phi_machine_share_of_growth": phis.tolist(), "runs": q4,
                         "field_automation_variant_phi1": q4_mu}
    print("Q4 done", round(time.time() - t0, 1))

    # ---- Q5: scatter
    sc = {}
    sc["Serf (no growth to be had)"] = solve(P(g=0.0, h=0.03), "reputation")
    sc["Dynasty, 2% growth"] = solve(P(g=0.02, h=0.01), "reputation")
    sc["Dynasty, 4% growth"] = solve(P(g=0.04, h=0.01), "reputation")
    sc["Short-tenure ruler, 4% growth"] = solve(P(g=0.04, h=0.15), "reputation")
    sc["No credible promises, 4% growth"] = solve(P(g=0.04, h=0.01), "markov")
    sc["Forceable growth, 4%"] = solve(P(g=0.04, h=0.01, forceable_growth=True), "reputation")
    sc["China-like"] = q3["Dynasty, rival threat, catch-up potential 5% (China-like)"]
    sc["North Korea-like"] = q3["Nukes + short horizon + outside rents (North Korea-like)"]
    sc["AI makes 50% of growth"] = solve(P(g=0.04, h=0.02, phi=0.5), "reputation")
    sc["AI makes 100% of growth"] = solve(P(g=0.04, h=0.02, phi=1.0), "reputation")
    sc["AI: all growth + 60% of field work"] = solve(P(g=0.04, h=0.02, phi=1.0, mu=0.6), "reputation")
    sc["AI: all growth + 95% of field work"] = solve(P(g=0.04, h=0.02, phi=1.0, mu=0.95), "reputation")
    for v in sc.values():
        v["empowerment_index"] = 0.5 * v["share_kept"] + 0.5 * v["freedom"]
    res["q5_scatter"] = sc
    print("Q5 done", round(time.time() - t0, 1))

    with open("results.json", "w") as f:
        json.dump(res, f, indent=1, default=float)
    figures(res)
    print("all done", round(time.time() - t0, 1))


def figures(res):
    g = np.array(res["q1_growth_sweep"]["g"]) * 100
    # Fig 1: Q1
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    for j, mode in enumerate(["reputation", "commitment", "markov"]):
        d = res["q1_growth_sweep"]["by_mode"][mode]
        for i, (lab, v) in enumerate(d.items()):
            ax[j].plot(g, v["share_kept"], color=COL[i], label=lab)
            ax[j].plot(g, v["freedom"], color=COL[i], ls=":", lw=1.6)
        ax[j].set_title({"reputation": "Ruler can't sign contracts, but cares about reputation",
                         "commitment": "Ruler can bind himself (a constitution)",
                         "markov": "Nobody believes the ruler's promises"}[mode], fontsize=10)
        ax[j].set_xlabel("growth achievable through subjects' free initiative (%/yr)")
        ax[j].set_ylim(-0.02, 1.02)
    ax[0].set_ylabel("solid: share subjects keep   dotted: freedom (1 - control)")
    ax[0].legend(fontsize=8, loc="center right")
    fig.suptitle("How much the ruler leaves his subjects, as possible growth rises (ruler discount 4%/yr)")
    fig.tight_layout(); fig.savefig("fig1_growth_sweep.png", dpi=150); plt.close(fig)

    # Fig 1b: thresholds
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    th = res["q1_threshold_g_vs_hazard"]
    hz = np.array(th["hazard_h"]) * 100
    for i, (rl, ys) in enumerate(th["threshold_g_by_mode_and_r"]["reputation"].items()):
        y = np.array([np.nan if v is None else v * 100 for v in ys])
        ax.plot(hz, y, "o-", color=COL[i], label=f"reputation, {rl}")
    for i, (rl, ys) in enumerate(th["threshold_g_by_mode_and_r"]["commitment"].items()):
        y = np.array([np.nan if v is None else v * 100 for v in ys])
        ax.plot(hz, y, "s--", color=COL[i], lw=1.2, label=f"commitment, {rl}")
    ax.axhline(2, color=MUTED, lw=1); ax.text(hz.max(), 2.2, "2%", color=MUTED, ha="right")
    ax.set_xlabel("ruler's yearly chance of losing power (%)")
    ax.set_ylabel("growth needed before ruler loosens control (%/yr)")
    ax.set_title("The growth threshold depends on the ruler's horizon")
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig("fig1b_threshold.png", dpi=150); plt.close(fig)

    # Fig 2: serf + ablation
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    s2 = res["q2_serf"]["ruler_best_take_by_control"]
    ax[0].plot(s2["c"], s2["R"], color=COL[0])
    ax[0].set_xlabel("control / coercion level"); ax[0].set_ylabel("ruler's best yearly take (per unit output potential)")
    ax[0].set_title("No growth to be had: coercion pays")
    ab = res["ablation_forceable_growth"]["h=3%"]
    rp = res["q1_growth_sweep"]["by_mode"]["reputation"]["tenure ~33y (h=3%)"]
    ax[1].plot(g, rp["share_kept"], color=COL[0], label="share kept: growth needs free initiative")
    ax[1].plot(g, rp["freedom"], color=COL[0], ls=":", label="freedom: growth needs free initiative")
    ax[1].plot(g, ab["share_kept"], color=COL[1], label="share kept: growth can be ordered")
    ax[1].plot(g, ab["freedom"], color=COL[1], ls=":", label="freedom: growth can be ordered")
    ax[1].set_xlabel("achievable growth (%/yr)"); ax[1].set_ylim(-0.02, 1.02)
    ax[1].set_title("Ablation: same growth, but forceable"); ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig("fig2_serf_and_ablation.png", dpi=150); plt.close(fig)

    # Fig 3: threat heatmap
    sw = res["q3_threat"]["sweep"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for j, key in enumerate(["share_kept[h0][lam]", "freedom[h0][lam]"]):
        im = ax[j].imshow(np.array(sw[key]), origin="lower", cmap="Blues", vmin=0, vmax=1, aspect="auto")
        ax[j].set_xticks(range(len(sw["threat_lam"]))); ax[j].set_xticklabels([f"{l:.2f}" for l in sw["threat_lam"]])
        ax[j].set_yticks(range(len(sw["base_hazard_h0"]))); ax[j].set_yticklabels([f"{h*100:.0f}%" for h in sw["base_hazard_h0"]])
        ax[j].set_xlabel("extra yearly risk of falling if out-produced by rival")
        ax[j].set_ylabel("ruler's baseline yearly risk of losing power"); ax[j].grid(False)
        ax[j].set_title({0: "Share subjects keep", 1: "Freedom (1 - control)"}[j])
        for a in range(len(sw["base_hazard_h0"])):
            for b_ in range(len(sw["threat_lam"])):
                v = sw[key][a][b_]
                ax[j].text(b_, a, f"{v:.2f}", ha="center", va="center", fontsize=7,
                           color="white" if v > 0.55 else INK)
    fig.suptitle("Rival states and the ruler's horizon (5% growth possible, rival grows 2%)")
    fig.tight_layout(); fig.savefig("fig3_threat.png", dpi=150); plt.close(fig)

    # Fig 4: AI dial
    q4 = res["q4_ai_dial"]; phi = np.array(q4["phi_machine_share_of_growth"]) * 100
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for i, (lab, v) in enumerate(q4["runs"].items()):
        ax[0].plot(phi, v["share_kept"], color=COL[i], label=f"share kept ({lab})")
        ax[0].plot(phi, v["freedom"], color=COL[i], ls=":", label=f"freedom ({lab})")
    ax[0].plot(phi, q4["runs"]["g=4%, h=2%"]["necessity"], color=INK, lw=1, ls="--", label="necessity (g=4%)")
    ax[0].set_xlabel("share of growth produced by machines (%)"); ax[0].set_ylim(-0.02, 1.05)
    ax[0].set_title("Machines take over invention only"); ax[0].legend(fontsize=7)
    mu = q4["field_automation_variant_phi1"]
    ax[1].plot(np.array(mu["mu"]) * 100, mu["share_kept"], color=COL[0], label="share kept")
    ax[1].plot(np.array(mu["mu"]) * 100, mu["freedom"], color=COL[0], ls=":", label="freedom")
    ax[1].plot(np.array(mu["mu"]) * 100, mu["necessity"], color=INK, ls="--", lw=1, label="necessity")
    ax[1].set_xlabel("share of field work done by machines (%), with all growth from machines")
    ax[1].set_ylim(-0.02, 1.05); ax[1].set_title("Machines then take over field work too"); ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig("fig4_ai_dial.png", dpi=150); plt.close(fig)

    # Fig 5: scatter
    sc = res["q5_scatter"]
    fig, ax = plt.subplots(figsize=(8.5, 6))
    for i, (lab, v) in enumerate(sc.items()):
        ax.scatter(v["necessity"], v["empowerment_index"], s=70, color=COL[i % 8],
                   edgecolor="white", linewidth=1.5, zorder=3, marker="os^D"[i // 8 % 4])
        ax.annotate(lab, (v["necessity"], v["empowerment_index"]), fontsize=7.5, xytext=(6, 3),
                    textcoords="offset points", color=INK)
    ax.set_xlabel("necessity: share of output lost if subjects stop (30-year horizon)")
    ax.set_ylabel("empowerment: average of share kept and freedom")
    ax.set_xlim(-0.03, 1.15); ax.set_ylim(-0.03, 1.03)
    ax.set_title("Being needed and being empowered are different things")
    fig.tight_layout(); fig.savefig("fig5_necessity_vs_empowerment.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
