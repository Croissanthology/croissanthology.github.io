"""
Does a zero-sum world hand everything to a "big baddie"?  Three tests.

Part 1  Yard-sale wealth exchange, with growth added in several different ways.
Part 2  Make-or-grab conflict model with evolving strategies and gangs.
Part 3  Repeated-game arithmetic: growth vs number of players.

Run:  python3 zero_sum.py      (about 2-4 minutes on 4 cores)
Writes results.json and fig*.png into this folder.
"""
import json
import os
import time
from multiprocessing import Pool

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def gini(w):
    w = np.sort(np.asarray(w, float))
    n = len(w)
    s = w.sum()
    if s <= 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1).dot(w) / (n * s))


def top_share(w, frac):
    k = max(1, int(round(frac * len(w))))
    s = np.sort(w)[::-1]
    return float(s[:k].sum() / s.sum())


# ---------------------------------------------------------------------------
# PART 1: yard-sale model
# ---------------------------------------------------------------------------
# Each "sweep" every agent is randomly paired with one other agent.  The pair
# bets a fraction F of the POORER one's wealth on a fair coin.  Then (depending
# on the variant) growth or redistribution is applied once per sweep.
N1 = 1000
F = 0.1
T1 = 100_000
REC = np.unique(np.round(np.logspace(0, np.log10(T1), 60)).astype(int))


def yard_sale(variant, rate=0.0, alpha=1.0, zeta=0.0, seed=0, T=T1, rec=REC, N=N1):
    """Returns dict of time series (shares are scale-free).
    variant: none | proportional | opportunity | entrants | churn | redistribute
      proportional : everyone's wealth *= (1+rate)
      opportunity  : new wealth rate*W split in proportion to w**alpha
                     (alpha=0 equal split, 0.5 diminishing, 1 = proportional, 1.5 increasing)
      entrants     : one entrant per sweep displaces a random incumbent (whose
                     wealth is destroyed) and starts with new wealth rate*W
      churn        : same displacement, but entrant gets only the mean wealth
                     (so on average no growth)  -- ablation for 'entrants'
      redistribute : w += rate*(mean - w), no growth (a flat wealth tax rebated equally)
    zeta: size advantage in each trade: P(i wins) = 1/2 + zeta/2*(wi-wj)/(wi+wj)
    """
    rng = np.random.default_rng(seed)
    w = np.ones(N)
    rec_set = set(int(r) for r in rec)
    out = {"t": [], "gini": [], "top1pct": [], "top_agent": []}
    half = N // 2
    for s in range(1, T + 1):
        p = rng.permutation(N)
        i, j = p[:half], p[half:2 * half]
        wi, wj = w[i], w[j]
        d = F * np.minimum(wi, wj)
        if zeta > 0:
            pwin = 0.5 + 0.5 * zeta * (wi - wj) / (wi + wj)
        else:
            pwin = 0.5
        sgn = np.where(rng.random(half) < pwin, 1.0, -1.0)
        w[i] = wi + sgn * d
        w[j] = wj - sgn * d
        W = w.sum()
        if variant == "proportional":
            w *= 1.0 + rate
        elif variant == "opportunity":
            x = w ** alpha if alpha != 0 else np.ones(N)
            w += rate * W * x / x.sum()
        elif variant == "entrants":
            k = rng.integers(N)
            w[k] = rate * W
        elif variant == "churn":
            k = rng.integers(N)
            w[k] = W / N
        elif variant == "redistribute":
            w += rate * (W / N - w)
        # keep numbers in a sane range (shares are what matter)
        if s % 1000 == 0:
            w /= w.mean()
        if s in rec_set:
            out["t"].append(s)
            out["gini"].append(round(gini(w), 4))
            out["top1pct"].append(round(top_share(w, 0.01), 4))
            out["top_agent"].append(round(float(w.max() / w.sum()), 4))
    return out


def _ys_job(args):
    name, kw = args
    return name, kw.get("seed", 0), yard_sale(**kw)


def part1(pool):
    G = 0.01  # growth per sweep for every growth variant
    variants = {
        "no growth (pure exchange)": dict(variant="none"),
        "(a) everyone grows 1%/sweep in proportion": dict(variant="proportional", rate=G),
        "(b1) new opportunity split equally": dict(variant="opportunity", rate=G, alpha=0.0),
        "(b2) new opportunity, diminishing returns to size (w^0.5)": dict(variant="opportunity", rate=G, alpha=0.5),
        "(c) new opportunity, increasing returns to size (w^1.5)": dict(variant="opportunity", rate=G, alpha=1.5),
        "(d) entrants displace a random incumbent": dict(variant="entrants", rate=G),
        "(d-ablation) displacement churn, no growth": dict(variant="churn"),
        "(e) redistribution 1%/sweep, no growth": dict(variant="redistribute", rate=G),
    }
    seeds = [0, 1, 2]
    jobs = [(n, dict(kw, seed=s)) for n, kw in variants.items() for s in seeds]
    res = pool.map(_ys_job, jobs)
    series = {}
    for n in variants:
        runs = [r for (nn, s, r) in res if nn == n]
        series[n] = {
            "t_sweeps": runs[0]["t"],
            "top1pct_share_mean": list(np.round(np.mean([r["top1pct"] for r in runs], 0), 4)),
            "gini_mean": list(np.round(np.mean([r["gini"] for r in runs], 0), 4)),
            "largest_agent_share_mean": list(np.round(np.mean([r["top_agent"] for r in runs], 0), 4)),
        }

    # exactness check: proportional growth vs no growth, same seed -> identical shares?
    a = yard_sale("none", seed=7, T=20000, rec=[20000])
    b = yard_sale("proportional", rate=G, seed=7, T=20000, rec=[20000])
    prop_check = {
        "no_growth_top1_at_20000": a["top1pct"][0],
        "proportional_growth_top1_at_20000": b["top1pct"][0],
        "no_growth_gini": a["gini"][0],
        "proportional_gini": b["gini"][0],
    }
    # equivalence check: equal-split growth g == redistribution at g/(1+g)
    c = yard_sale("opportunity", rate=G, alpha=0.0, seed=7, T=20000, rec=[20000])
    d = yard_sale("redistribute", rate=G / (1 + G), seed=7, T=20000, rec=[20000])
    equiv_check = {"equal_split_growth_gini": c["gini"][0], "redistribution_g_over_1plusg_gini": d["gini"][0],
                   "equal_split_growth_top1": c["top1pct"][0], "redistribution_top1": d["top1pct"][0]}

    # phase diagram: equal-split new-opportunity growth rate vs size advantage zeta
    gs = [0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2]
    zetas = [0.0, 0.02, 0.05, 0.1, 0.2, 0.4]
    Tp = 30000
    jobs = [(f"{g}|{z}", dict(variant="opportunity", rate=g, alpha=0.0, zeta=z, seed=11, T=Tp, rec=[Tp]))
            for g in gs for z in zetas]
    resp = dict((n, r) for (n, s, r) in pool.map(_ys_job, jobs))
    phase_top1 = [[resp[f"{g}|{z}"]["top1pct"][0] for z in zetas] for g in gs]
    phase_agent = [[resp[f"{g}|{z}"]["top_agent"][0] for z in zetas] for g in gs]
    # same diagram but growth proportional (alpha=1): expected to do nothing
    jobs = [(f"{g}|{z}", dict(variant="opportunity", rate=g, alpha=1.0, zeta=z, seed=11, T=Tp, rec=[Tp]))
            for g in [0.0, 1e-2, 3e-2] for z in [0.0, 0.1, 0.4]]
    resq = dict((n, r) for (n, s, r) in pool.map(_ys_job, jobs))
    prop_phase = {k: v["top1pct"][0] for k, v in resq.items()}

    return {
        "settings": {"agents": N1, "bet_fraction_of_poorer_wealth": F, "sweeps": T1, "growth_or_tax_rate_per_sweep": G,
                     "seeds": seeds},
        "series": series,
        "check_proportional_growth_identical_shares": prop_check,
        "check_equal_split_growth_equals_redistribution": equiv_check,
        "phase_diagram": {"note": "top-1% share after 30000 sweeps; rows = equal-split growth per sweep, cols = size advantage zeta",
                          "growth_per_sweep": gs, "size_advantage_zeta": zetas,
                          "top1pct_share": phase_top1, "largest_agent_share": phase_agent},
        "proportional_growth_with_size_advantage_top1": prop_phase,
    }


# ---------------------------------------------------------------------------
# PART 2: make-or-grab model with gangs
# ---------------------------------------------------------------------------
# Units are 'detrended': everything is divided by the economy's productivity
# A_t = (1+g)^t, so g appears only where it truly bites: a pile of wealth made
# in the past shrinks relative to today's output by 1/(1+g) each period.
GRID = np.array([(m, a, 10 - m - a) for m in range(11) for a in range(11 - m)], float) / 10.0
P2 = dict(N=300, T=2500, avg_last=800, nu=0.10, kappa=0.10, phi=0.10, waste=0.25, d0=0.05, mut=0.03)


def make_or_grab(g, sigma, delta, seed=0, loot_from="stock", peaceful=False, P=P2):
    rng = np.random.default_rng(seed)
    N = P["N"]
    grid = GRID[GRID[:, 1] == 0] if peaceful else GRID
    strat = rng.integers(len(grid), size=N)
    m, a, d = grid[strat, 0].copy(), grid[strat, 1].copy(), grid[strat, 2].copy()
    H = m / P["nu"]
    W = np.full(N, 10.0)
    gang = -np.ones(N, int)
    next_gang = 0
    acc = {"grab": [], "defend": [], "largest_unit_share": [], "largest_gang_members": [],
           "median_consumption": [], "mean_consumption": [], "largest_single_agent_share": []}
    for t in range(P["T"]):
        y = H.copy()
        H = (1 - P["nu"]) * H + m
        W = W + y
        # ---- raids: Tullock contest over the pool of undefended wealth ----
        grabber = a > 0
        uid = np.where(gang >= 0, gang, np.where(grabber, 10_000_000 + np.arange(N), -1))
        inu = uid >= 0
        loot = np.zeros(N)
        gain = np.zeros(N)
        if inu.any():
            _, inv = np.unique(uid[inu], return_inverse=True)
            S = np.bincount(inv, weights=a[inu])
            Pu = np.where(S > 0, S, 0.0) ** sigma
            Pi = Pu.sum()
            Pown = np.zeros(N)
            Pown[inu] = Pu[inv]
            press = (Pi - Pown) / N
            q = press / (press + d + P["d0"])
            base = W if loot_from == "stock" else y
            loot = P["phi"] * q * base
            denom = Pi - Pown
            f = np.where(denom > 0, (1 - P["waste"]) * loot / np.where(denom > 0, denom, 1), 0.0)
            Ftot = f.sum()
            Fown = np.bincount(inv, weights=f[inu], minlength=len(S))
            R = Pu * (Ftot - Fown)
            gain[inu] = np.where(S[inv] > 0, R[inv] * a[inu] / np.where(S[inv] > 0, S[inv], 1), 0)
        W = W - loot + gain
        c = P["kappa"] * W
        W = (W - c) / (1 + g)
        # ---- measurement ----
        if t >= P["T"] - P["avg_last"]:
            acc["grab"].append(a.mean())
            acc["defend"].append(d.mean())
            uw = np.where(gang >= 0, gang, 10_000_000 + np.arange(N))
            _, inv2 = np.unique(uw, return_inverse=True)
            unitW = np.bincount(inv2, weights=W)
            acc["largest_unit_share"].append(unitW.max() / W.sum())
            acc["largest_single_agent_share"].append(W.max() / W.sum())
            if (gang >= 0).any():
                acc["largest_gang_members"].append(np.bincount(gang[gang >= 0]).max() / N)
            else:
                acc["largest_gang_members"].append(0.0)
            acc["median_consumption"].append(np.median(c))
            acc["mean_consumption"].append(c.mean())
        # ---- births and deaths (delta = survival prob. = patience) ----
        dead = np.flatnonzero(rng.random(N) > delta)
        if len(dead):
            fit = np.maximum(c, 1e-12)
            models = rng.choice(N, size=len(dead), p=fit / fit.sum())
            newm, newa, newd, newg = m[models].copy(), a[models].copy(), d[models].copy(), gang[models].copy()
            mut = rng.random(len(dead)) < P["mut"]
            for k in np.flatnonzero(mut):
                s = grid[rng.integers(len(grid))]
                newm[k], newa[k], newd[k] = s
                newg[k] = -1
                if s[1] > 0:
                    u = rng.random()
                    ingang = np.flatnonzero(gang >= 0)
                    if u < 0.4 and len(ingang):
                        newg[k] = gang[rng.choice(ingang)]
                    elif u < 0.5:
                        newg[k] = next_gang
                        next_gang += 1
            newg[newa == 0] = -1
            m[dead], a[dead], d[dead], gang[dead] = newm, newa, newd, newg
            H[dead] = 0.0  # skills die with the person; wealth W is inherited
    return {k: float(np.mean(v)) for k, v in acc.items()}


def _mg_job(args):
    key, kw = args
    return key, make_or_grab(**kw)


def part2(pool):
    gs = [-0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.05]
    sigmas = [0.7, 1.0, 1.3, 1.6]
    deltas = [0.90, 0.95, 0.98]
    seeds = [0, 1, 2, 3]
    phis = [0.03, 0.3]
    jobs = []
    for g in gs:
        for s in sigmas:
            for dl in deltas:
                if dl != 0.95 and s != 1.3:
                    continue  # patience sweep only at the middle size advantage
                for sd in seeds:
                    jobs.append(((g, s, dl, sd, "stock"), dict(g=g, sigma=s, delta=dl, seed=sd)))
        for sd in seeds:  # ablation: grab only today's output, not accumulated stock
            jobs.append(((g, 1.3, 0.95, sd, "flow"), dict(g=g, sigma=1.3, delta=0.95, seed=sd, loot_from="flow")))
        for ph in phis:  # sensitivity: how big a bite one raid takes out of a stock
            for sd in seeds:
                jobs.append(((g, 1.3, 0.95, sd, f"phi{ph}"), dict(g=g, sigma=1.3, delta=0.95, seed=sd, P=dict(P2, phi=ph))))
        for dl in deltas:  # peaceful benchmark (grabbing impossible)
            for sd in seeds:
                jobs.append(((g, 0, dl, sd, "peace"), dict(g=g, sigma=1.0, delta=dl, seed=sd, peaceful=True)))
    res = dict(pool.map(_mg_job, jobs))

    def avg(g, s, dl, kind):
        rs = [res[(g, s, dl, sd, kind)] for sd in seeds]
        return {k: float(np.mean([r[k] for r in rs])) for k in rs[0]}

    out = {"growth_rates": gs, "size_advantage_sigma": sigmas, "patience_survival_delta": deltas,
           "params": P2, "by_sigma_at_delta_0.95": {}, "by_delta_at_sigma_1.3": {}, "ablation_loot_from_flow": {},
           "peaceful_median_consumption": {}}
    for dl in deltas:
        out["peaceful_median_consumption"][str(dl)] = [avg(g, 0, dl, "peace")["median_consumption"] for g in gs]

    def pack(s, dl, kind):
        rows = [avg(g, s, dl, kind) for g in gs]
        peace = out["peaceful_median_consumption"][str(dl)]
        return {
            "grab_effort_fraction": [round(r["grab"], 4) for r in rows],
            "defence_effort_fraction": [round(r["defend"], 4) for r in rows],
            "largest_agent_or_gang_wealth_share": [round(r["largest_unit_share"], 4) for r in rows],
            "largest_gang_headcount_share": [round(r["largest_gang_members"], 4) for r in rows],
            "ordinary_agent_consumption_vs_peaceful": [round(r["median_consumption"] / p, 4) for r, p in zip(rows, peace)],
        }

    for s in sigmas:
        out["by_sigma_at_delta_0.95"][str(s)] = pack(s, 0.95, "stock")
    for dl in deltas:
        out["by_delta_at_sigma_1.3"][str(dl)] = pack(1.3, dl, "stock")
    out["ablation_loot_from_flow"] = pack(1.3, 0.95, "flow")
    out["sensitivity_raid_bite_phi"] = {str(P2["phi"]): out["by_sigma_at_delta_0.95"]["1.3"],
                                        **{str(ph): pack(1.3, 0.95, f"phi{ph}") for ph in phis}}

    # threshold & sharpness: where grab effort crosses midway between its g=-5% and g=+5% values
    def threshold(series):
        y = np.array(series)
        lo, hi = y[-1], y[0]
        if hi - lo < 0.05:
            return {"threshold_g": None, "width_25_75": None, "drop": float(hi - lo)}

        def cross(level):
            for k in range(len(gs) - 1):
                if (y[k] - level) * (y[k + 1] - level) <= 0 and y[k] != y[k + 1]:
                    return gs[k] + (level - y[k]) * (gs[k + 1] - gs[k]) / (y[k + 1] - y[k])
            return None

        mid = cross(lo + 0.5 * (hi - lo))
        a75, a25 = cross(lo + 0.75 * (hi - lo)), cross(lo + 0.25 * (hi - lo))
        return {"threshold_g": None if mid is None else round(mid, 4),
                "width_25_75": None if (a75 is None or a25 is None) else round(a25 - a75, 4),
                "drop": round(float(hi - lo), 4)}

    out["thresholds"] = {
        **{f"sigma={s},delta=0.95": threshold(out["by_sigma_at_delta_0.95"][str(s)]["grab_effort_fraction"]) for s in sigmas},
        **{f"sigma=1.3,delta={dl}": threshold(out["by_delta_at_sigma_1.3"][str(dl)]["grab_effort_fraction"]) for dl in deltas},
        "flow_ablation": threshold(out["ablation_loot_from_flow"]["grab_effort_fraction"]),
        **{f"phi={ph}": threshold(out["sensitivity_raid_bite_phi"][str(ph)]["grab_effort_fraction"]) for ph in phis},
    }
    return out


# ---------------------------------------------------------------------------
# PART 3: repeated-game arithmetic
# ---------------------------------------------------------------------------
def deviation_gain(delta, g, T_, R_, P_, horizon=20000):
    """Numerically: discounted value of cooperating forever minus defecting once
    then being punished forever (grim trigger), with all stakes growing at g."""
    k = np.arange(horizon)
    disc = (delta * (1 + g)) ** k
    coop = (R_ * disc).sum()
    dev = T_ + (P_ * disc[1:]).sum()
    return coop - dev


def numeric_threshold(g, T_, R_, P_):
    lo, hi = 0.0, 1.0 / (1 + g) - 1e-9
    if deviation_gain(hi, g, T_, R_, P_) < 0:
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if deviation_gain(mid, g, T_, R_, P_) >= 0:
            hi = mid
        else:
            lo = mid
    return hi


def part3():
    out = {}
    # (i) generic PD: cooperation holds iff delta*(1+g) >= (T-R)/(T-P)
    # 'grab the pie' game with n players: peace gives 1/n each; a grabber takes the
    # whole pie once, then everyone fights forever (payoff 0).  Needed: delta_eff >= 1 - 1/n.
    rows = []
    for n in [2, 3, 5, 10, 20, 50, 100]:
        T_, R_, P_ = 1.0, 1.0 / n, 0.0
        r = {"n": n, "formula_needed_effective_patience": round(1 - 1 / n, 4)}
        for g in [0.0, 0.02]:
            th = numeric_threshold(g, T_, R_, P_)
            r[f"numeric_needed_delta_at_g={g}"] = None if th is None else round(th, 5)
        rows.append(r)
    out["grab_the_pie_game"] = rows
    # public-goods game: each puts in 1, pot multiplied by M=2 and shared by n
    M = 2.0
    pg = []
    for n in [2, 3, 5, 10, 20, 50, 100]:
        T_, R_, P_ = M * (n - 1) / n, M - 1, 0.0
        need = (T_ - R_) / (T_ - P_)
        pg.append({"n": n, "needed_effective_patience": round(need, 4)})
    out["public_goods_game_multiplier_2"] = pg

    # realistic discount rates: annual r = 2..6% -> delta = 1/(1+r)
    table = []
    for r_ in [0.02, 0.03, 0.04, 0.05, 0.06]:
        dl = 1 / (1 + r_)
        row = {"discount_rate": r_, "delta": round(dl, 4)}
        for g in [0.0, 0.02]:
            de = dl * (1 + g)
            row[f"effective_patience_g={g}"] = round(de, 4)
            row[f"future_weight_d_over_1minus_d_g={g}"] = round(de / (1 - de), 1) if de < 1 else float("inf")
            row[f"max_players_grab_the_pie_g={g}"] = round(1 / (1 - de), 1) if de < 1 else float("inf")
        table.append(row)
    out["realistic_discounting"] = table

    # Ramsey caveat: if interest rates rise with growth, r = rho + theta*g
    ram = []
    for theta in [0.0, 1.0, 1.5, 2.0]:
        rho = 0.02
        row = {"theta": theta}
        for g in [0.0, 0.02]:
            de = (1 + g) / (1 + rho + theta * g)
            row[f"effective_patience_g={g}"] = round(de, 4)
            row[f"max_players_g={g}"] = round(1 / (1 - de), 1) if de < 1 else float("inf")
        ram.append(row)
    out["if_interest_rate_rises_with_growth_rho_2pct"] = ram
    return out


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------
COLORS = ["#222222", "#1f77b4", "#2ca02c", "#17becf", "#d62728", "#9467bd", "#c5b0d5", "#ff7f0e"]


def figures(r1, r2, r3):
    s = r1["series"]
    for key, fname, ylab in [("top1pct_share_mean", "fig1_exchange_top1pct.png", "share of all wealth held by richest 1%"),
                             ("gini_mean", "fig2_exchange_gini.png", "Gini coefficient (0 = equal, 1 = one owner)")]:
        fig, ax = plt.subplots(figsize=(8.5, 5))
        for (n, v), col in zip(s.items(), COLORS):
            ls = "--" if n.startswith("(a)") else "-"
            ax.plot(v["t_sweeps"], v[key], ls, color=col, lw=2 if ls == "-" else 2.5, label=n)
        ax.set_xscale("log")
        ax.set_xlabel("rounds of trading (each agent trades once per round)")
        ax.set_ylabel(ylab)
        ax.set_ylim(0, 1)
        ax.set_title("Fair coin-flip trading, with different kinds of growth added (1% per round)")
        ax.legend(fontsize=7.5, loc="upper left", frameon=False)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, fname), dpi=150)
        plt.close(fig)

    ph = r1["phase_diagram"]
    fig, ax = plt.subplots(figsize=(7, 4.8))
    im = ax.imshow(np.array(ph["top1pct_share"]), origin="lower", cmap="magma_r", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(ph["size_advantage_zeta"])), [str(z) for z in ph["size_advantage_zeta"]])
    ax.set_yticks(range(len(ph["growth_per_sweep"])), [f"{g:g}" for g in ph["growth_per_sweep"]])
    ax.set_xlabel("advantage of the richer side in each trade (zeta)")
    ax.set_ylabel("new opportunity per round, shared equally")
    for i_ in range(len(ph["growth_per_sweep"])):
        for j_ in range(len(ph["size_advantage_zeta"])):
            v = ph["top1pct_share"][i_][j_]
            ax.text(j_, i_, f"{v:.2f}", ha="center", va="center", fontsize=8, color="white" if v > 0.5 else "black")
    fig.colorbar(im, ax=ax, label="richest 1% share after 30,000 rounds")
    ax.set_title("Equal-access growth vs. a built-in edge for the big")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig3_growth_vs_size_edge.png"), dpi=150)
    plt.close(fig)

    gs = np.array(r2["growth_rates"]) * 100
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
    for (sg, v), col in zip(r2["by_sigma_at_delta_0.95"].items(), ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728"]):
        lab = f"size edge in fights = {sg}"
        axs[0].plot(gs, v["grab_effort_fraction"], "o-", color=col, label=lab)
        axs[1].plot(gs, v["largest_agent_or_gang_wealth_share"], "o-", color=col, label=lab)
        axs[2].plot(gs, v["ordinary_agent_consumption_vs_peaceful"], "o-", color=col, label=lab)
    axs[0].set_ylabel("share of all effort spent grabbing")
    axs[1].set_ylabel("wealth share of largest agent or gang")
    axs[2].set_ylabel("typical agent's consumption\n(1 = same as a world with no grabbing)")
    for ax in axs:
        ax.set_xlabel("growth of the pie per year (%)")
        ax.axvline(0, color="grey", lw=0.6)
    axs[0].legend(fontsize=8, frameon=False)
    fig.suptitle("Make-or-grab world: what changes as the pie shrinks or grows (patience: 5% chance of exit per year)")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig4_make_or_grab_by_size_edge.png"), dpi=150)
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    for (dl, v), col in zip(r2["by_delta_at_sigma_1.3"].items(), ["#d62728", "#1f77b4", "#2ca02c"]):
        axs[0].plot(gs, v["grab_effort_fraction"], "o-", color=col, label=f"yearly survival {dl}")
        axs[1].plot(gs, v["largest_agent_or_gang_wealth_share"], "o-", color=col, label=f"yearly survival {dl}")
    ab = r2["ablation_loot_from_flow"]
    axs[0].plot(gs, ab["grab_effort_fraction"], "s--", color="grey", label="ablation: only today's output can be grabbed")
    axs[1].plot(gs, ab["largest_agent_or_gang_wealth_share"], "s--", color="grey", label="ablation")
    axs[0].set_ylabel("share of all effort spent grabbing")
    axs[1].set_ylabel("wealth share of largest agent or gang")
    for ax in axs:
        ax.set_xlabel("growth of the pie per year (%)")
        ax.axvline(0, color="grey", lw=0.6)
    axs[0].legend(fontsize=8, frameon=False)
    fig.suptitle("Patience, and what happens if old wealth cannot be grabbed (size edge 1.3)")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig5_make_or_grab_patience_and_ablation.png"), dpi=150)
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    ns = [row["n"] for row in r3["grab_the_pie_game"]]
    axs[0].plot(ns, [row["numeric_needed_delta_at_g=0.0"] for row in r3["grab_the_pie_game"]], "o-", label="no growth")
    axs[0].plot(ns, [row["numeric_needed_delta_at_g=0.02"] for row in r3["grab_the_pie_game"]], "o-", label="2% growth")
    axs[0].set_xscale("log")
    axs[0].set_xlabel("number of independent players")
    axs[0].set_ylabel("patience needed to keep the peace\n(yearly discount factor)")
    axs[0].set_title("'Grab the pie' game")
    axs[0].legend(frameon=False)
    rr = [row["discount_rate"] * 100 for row in r3["realistic_discounting"]]
    axs[1].plot(rr, [row["max_players_grab_the_pie_g=0.0"] for row in r3["realistic_discounting"]], "o-", label="no growth")
    axs[1].plot(rr, [row["max_players_grab_the_pie_g=0.02"] for row in r3["realistic_discounting"]], "o-", label="2% growth")
    axs[1].set_yscale("log")
    axs[1].set_xlabel("discount rate (% per year)")
    axs[1].set_ylabel("largest number of players that can keep the peace")
    axs[1].set_title("How much 2% buys")
    axs[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig6_repeated_game.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    t0 = time.time()
    with Pool(4) as pool:
        r1 = part1(pool)
        print(f"part 1 done {time.time() - t0:.0f}s", flush=True)
        r2 = part2(pool)
        print(f"part 2 done {time.time() - t0:.0f}s", flush=True)
    r3 = part3()
    with open(os.path.join(HERE, "results.json"), "w") as fh:
        json.dump({"part1_exchange": r1, "part2_make_or_grab": r2, "part3_repeated_game": r3}, fh, indent=1)
    figures(r1, r2, r3)
    print(f"all done {time.time() - t0:.0f}s")
