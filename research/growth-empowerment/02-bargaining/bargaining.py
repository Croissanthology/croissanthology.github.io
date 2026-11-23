"""
Bargaining, outside options and plurality.

Run:  python3 bargaining.py      (from this folder; regenerates every figure and results.json)

Five parts, all built on one production technology  f(n) = A * L^(1-alpha) * n^alpha
(L = land/capital held by an employer or lord, n = workers):

  1. Manor as a cooperative game (Shapley value, core) + Domar's coercion hypothesis + Black Death.
  2. Agent-based labour market: workers on a circle, K employers, mobility cost, mergers/collusion.
  3. Growth as entry of new employers vs growth accruing to incumbents vs a static economy.
  4. Sally the Netflix exec vs the serf as two parameter settings of the same market.
  5. Collective action (strike/revolt) with a free-rider problem.

Necessity and empowerment are measured separately throughout:
  necessity   = output the counterparty (or the system) loses if you vanish
                (marginal product; Shapley value; share of employer output; class-level loss)
  empowerment = what you keep (wage / own marginal product), and how many independent bidders
                and positions you can actually reach.
"""
import json
import os
import time
from multiprocessing import Pool

import numpy as np
from scipy.stats import binom, lognorm

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ALPHA = 0.6      # labour elasticity (land/capital share 0.4)
BETA = 0.5       # Nash bargaining weight of the worker over the surplus above her outside option
RESULTS = {}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
C = {"blue": "#2b6cb0", "orange": "#dd6b20", "green": "#2f855a", "red": "#c53030",
     "purple": "#6b46c1", "gray": "#718096", "teal": "#2c7a7b"}


def savefig(fig, name):
    fig.savefig(os.path.join(HERE, name), dpi=150, bbox_inches="tight")
    plt.close(fig)


# =====================================================================================
# PART 1. The manor as a cooperative game; Domar; Black Death
# =====================================================================================
S_SUB = 1.0          # subsistence (units of grain per serf per year)
A_MANOR = 9.47       # chosen so MP = 1.1 * subsistence at N = 60 serfs (Malthusian, labour abundant)


def f_manor(n, A=A_MANOR, alpha=ALPHA):
    return A * np.power(np.asarray(n, float), alpha)


def mp_manor(N, A=A_MANOR):
    return f_manor(N, A) - f_manor(N - 1, A)


def shapley_serf(N, w_out=0.0, A=A_MANOR):
    """Exact Shapley value of one serf in the game with one lord, N identical serfs.
    v(S) = best use of S: if lord in S, serfs either work the manor or take outside option w_out;
    if lord not in S, each serf earns w_out (w_out=0: pure production game)."""
    k = np.arange(N + 1)
    fk = f_manor(k, A)
    # V(k) = max_{j<=k} f(j) + (k-j) w_out ; with concave f this is f(min(k, kstar)) + rest*w_out
    V = np.array([max(fk[j] + (kk - j) * w_out for j in range(kk + 1)) if w_out > 0 else fk[kk]
                  for kk in range(N + 1)])
    # serf's predecessors t ~ U{0..N}; lord among them w.p. t/N; then (t-1) serfs before her
    tot = 0.0
    for t in range(N + 1):
        p_lord = t / N
        mc_with_lord = V[t] - V[t - 1] if t >= 1 else 0.0
        tot += p_lord * mc_with_lord + (1 - p_lord) * w_out
    return tot / (N + 1)


def part1():
    print("Part 1: manor")
    Ns = np.arange(5, 151)
    mp = mp_manor(Ns)
    ap = f_manor(Ns) / Ns
    sh0 = np.array([shapley_serf(N) for N in Ns])              # necessity in the pure production game
    # Free labour, many lords competing, mobility cost m: outside option = rival lord's MP - m
    m = 0.05
    o_free = np.maximum(S_SUB, mp - m)
    w_free = o_free + BETA * (mp - o_free)
    # Coerced: exit blocked, outside option pushed to subsistence
    w_coerced = S_SUB + BETA * (mp - S_SUB)
    gain = w_free - w_coerced                                    # lord's saving per serf = (1-beta)(MP-m-s)
    c0 = 0.05
    cost_lowk = c0 + 0.2 * np.maximum(0, mp - m - S_SUB)        # holding serfs gets dearer as escape pays more
    cost_highk = c0 + 0.6 * np.maximum(0, mp - m - S_SUB)       # ablation: kappa > 1-beta  (Acemoglu-Wolitzky outside-option effect dominates)

    # Single-lord Domar world: one manor + free frontier land paying w_F per serf
    # (to show the core floor: outside option, ceiling: necessity)
    N_pre, N_post = 60, 40

    # ---- Black Death with M lords who must coordinate to coerce ----
    # Cartel of lords coerces jointly. Each lord is tempted to defect: free his serfs, pay s+m,
    # and absorb runaways until his MP falls to s+m. Defection gain D(N) vs enforcement penalty P.
    def lord_profit_coerced(N, kappa=0.2):
        mpN = mp_manor(N)
        cost = c0 + kappa * max(0, mpN - m - S_SUB)
        wc = S_SUB + BETA * (mpN - S_SUB)
        return f_manor(N) - N * (wc + cost)

    def lord_profit_free(N):
        mpN = mp_manor(N)
        o = max(S_SUB, mpN - m)
        wf = o + BETA * (mpN - o)
        return f_manor(N) - N * wf

    def defection_gain(N, kappa=0.2):
        # defector hires runaways at wage s+m (their coerced value + moving cost), as many as he likes
        w_d = S_SUB + m + 1e-9
        nn = np.arange(1, 2000)
        prof = f_manor(nn) - w_d * nn
        return prof.max() - lord_profit_coerced(N, kappa)

    D = np.array([defection_gain(N) for N in Ns])
    collective_gain = np.array([lord_profit_coerced(N) - lord_profit_free(N) for N in Ns])
    P_WEST, P_EAST = 5.0, 200.0   # enforcement penalty on a defecting lord (weak crown/towns vs noble-run state)

    def regime(N, P):
        coll = lord_profit_coerced(N) > lord_profit_free(N)
        stable = defection_gain(N) <= P
        return "serfdom" if (coll and stable) else "free"

    def serf_wage(N, reg):
        mpN = mp_manor(N)
        if reg == "serfdom":
            return S_SUB + BETA * (mpN - S_SUB)
        o = max(S_SUB, mpN - m)
        return o + BETA * (mpN - o)

    bd = {}
    for name, P in [("west", P_WEST), ("east", P_EAST)]:
        r0, r1 = regime(N_pre, P), regime(N_post, P)
        bd[name] = {"enforcement_penalty_on_defecting_lord": P,
                    "regime_before": r0, "regime_after": r1,
                    "serf_wage_before": serf_wage(N_pre, r0), "serf_wage_after": serf_wage(N_post, r1),
                    "serf_MP_before": float(mp_manor(N_pre)), "serf_MP_after": float(mp_manor(N_post)),
                    "lord_income_before": float(lord_profit_coerced(N_pre) if r0 == "serfdom" else lord_profit_free(N_pre)),
                    "lord_income_after": float(lord_profit_coerced(N_post) if r1 == "serfdom" else lord_profit_free(N_post)),
                    "defection_gain_before": float(defection_gain(N_pre)),
                    "defection_gain_after": float(defection_gain(N_post))}
    # Ablation: kappa high (holding people costs rise faster than the gain) -> Domar reverses
    def coerce_pays(N, kappa):
        return lord_profit_coerced(N, kappa) > lord_profit_free(N)
    abl = {"kappa_0.2_coerce_pays_N60": bool(coerce_pays(60, 0.2)), "kappa_0.2_coerce_pays_N40": bool(coerce_pays(40, 0.2)),
           "kappa_0.6_coerce_pays_N60": bool(coerce_pays(60, 0.6)), "kappa_0.6_coerce_pays_N40": bool(coerce_pays(40, 0.6))}

    # Core with outside option (frontier/other lords) at N=40: serf payoff interval [w_out, MP]
    core_table = []
    for w_out in [0.0, 1.0, 1.2]:
        core_table.append({"outside_option": w_out, "core_floor": w_out, "core_ceiling_MP": float(mp_manor(40)),
                           "shapley_serf": float(shapley_serf(40, w_out)),
                           "class_necessity_total_output_lost": float(f_manor(40)),
                           "individual_necessity_MP": float(mp_manor(40))})

    RESULTS["part1_manor"] = {
        "params": {"alpha": ALPHA, "beta": BETA, "A": A_MANOR, "subsistence": S_SUB, "mobility_cost": m,
                   "coercion_fixed_cost_per_serf": c0, "coercion_cost_slope_kappa": 0.2},
        "N_serfs": Ns.tolist(), "marginal_product_individual_necessity": np.round(mp, 4).tolist(),
        "average_product": np.round(ap, 4).tolist(),
        "shapley_per_serf_pure_production": np.round(sh0, 4).tolist(),
        "class_necessity_share_of_manor_output_lost_if_all_serfs_leave": 1.0,
        "wage_free_exit": np.round(w_free, 4).tolist(), "wage_coerced": np.round(w_coerced, 4).tolist(),
        "lord_gain_per_serf_from_coercion": np.round(gain, 4).tolist(),
        "coercion_cost_per_serf_kappa0.2": np.round(cost_lowk, 4).tolist(),
        "coercion_cost_per_serf_kappa0.6": np.round(cost_highk, 4).tolist(),
        "defection_gain_for_one_lord": np.round(D, 3).tolist(),
        "lord_collective_gain_from_serfdom_per_manor": np.round(collective_gain, 3).tolist(),
        "core_table_N40": core_table, "black_death": bd, "domar_ablation": abl}

    # ---- figure 1 ----
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    a = ax[0]
    a.plot(Ns, mp, color=C["blue"], lw=2, label="individual necessity (marginal product)")
    a.plot(Ns, sh0, color=C["purple"], lw=2, ls="--", label="Shapley value per serf")
    a.plot(Ns, ap, color=C["gray"], lw=1.5, ls=":", label="output per serf (class necessity / N)")
    a.plot(Ns, w_free, color=C["green"], lw=2, label="wage, free to leave")
    a.plot(Ns, w_coerced, color=C["red"], lw=2, label="wage, exit blocked")
    a.axhline(S_SUB, color="k", lw=0.8)
    a.text(150, S_SUB + 0.03, "subsistence", ha="right", fontsize=8)
    a.set_xlabel("serfs on the manor (fewer = labour scarcer)")
    a.set_ylabel("grain per serf per year")
    a.set_title("How necessary a serf is vs what he keeps")
    a.legend(fontsize=7.5, frameon=False)
    a.invert_xaxis()
    a = ax[1]
    a.plot(Ns, gain, color=C["orange"], lw=2.2, label="lord's saving per serf from blocking exit")
    a.plot(Ns, cost_lowk, color=C["gray"], lw=1.6, label="cost of holding a serf (slope 0.2)")
    a.plot(Ns, cost_highk, color=C["gray"], lw=1.6, ls="--", label="ablation: cost slope 0.6")
    a.axvline(60, color="k", lw=0.6, ls=":"); a.axvline(40, color="k", lw=0.6, ls=":")
    a.text(60, a.get_ylim()[1] * 0.95, " before\n plague", fontsize=8, va="top")
    a.text(40, a.get_ylim()[1] * 0.95, " after", fontsize=8, va="top")
    a.set_xlabel("serfs on the manor (fewer = labour scarcer)")
    a.set_ylabel("grain per serf per year")
    a.set_title("Domar: scarcer labour makes coercion pay more")
    a.legend(fontsize=7.5, frameon=False)
    a.invert_xaxis()
    a = ax[2]
    x = np.arange(2)
    for i, (reg, col) in enumerate([("west", C["green"]), ("east", C["red"])]):
        vals = [bd[reg]["serf_wage_before"], bd[reg]["serf_wage_after"]]
        bars = a.bar(x + (i - 0.5) * 0.36, vals, 0.34, color=col,
                     label=f"{'West: lords cannot enforce a cartel' if reg=='west' else 'East: noble state enforces it'}")
        for j, b in enumerate(bars):
            a.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01,
                   f"{vals[j]:.2f}\n{[bd[reg]['regime_before'], bd[reg]['regime_after']][j]}", ha="center", fontsize=8)
    a.plot(x, [bd["west"]["serf_MP_before"], bd["west"]["serf_MP_after"]], "k_", ms=40, mew=1.5)
    a.text(1.25, bd["west"]["serf_MP_after"], "marginal\nproduct", fontsize=8, va="center")
    a.set_xticks(x); a.set_xticklabels(["before plague\n(60 serfs/manor)", "after plague\n(40 serfs/manor)"])
    a.set_ylim(0.9, 1.45)
    a.set_ylabel("serf's yearly income (grain)")
    a.set_title("Black Death: same shock, two outcomes")
    a.legend(fontsize=7.5, frameon=False, loc="upper left")
    savefig(fig, "fig1_manor_domar_blackdeath.png")
    return bd, abl, core_table


# =====================================================================================
# PART 2/3/4. Agent-based labour market
# =====================================================================================
class Market:
    """Workers and employer sites on a circle (geography + skill space). Each site has land L_k and
    output L^(1-a) n^a. Sites belong to owners; sites of one owner never bid against each other
    (merger or no-poach collusion). A worker's outside option is the best bid from a site of a
    DIFFERENT owner, net of the mobility cost m*distance, or home production b."""

    def __init__(self, W, site_pos, site_L, owner, m, b, beta=BETA, rho=0.0, rng=None):
        self.rng = rng if rng is not None else np.random.default_rng(0)
        self.W = W
        self.x = self.rng.random(W)
        self.z = np.array(site_pos, float)
        self.L = np.array(site_L, float)
        self.owner = np.array(owner, int)
        self.m, self.b, self.beta, self.rho = m, b, beta, rho
        self.assign = None

    def f(self, n, k=None):
        L = self.L if k is None else self.L[k]
        return L ** (1 - ALPHA) * np.power(np.maximum(n, 0), ALPHA)

    def dist(self):
        d = np.abs(self.x[:, None] - self.z[None, :])
        return np.minimum(d, 1 - d)

    def equilibrate(self, sweeps=12):
        K = len(self.z)
        D = self.dist()
        if self.assign is None:
            self.assign = np.argmin(D, axis=1)
        # extend assignment array if needed (sites appended) - stays valid
        n = np.bincount(self.assign[self.assign >= 0], minlength=K).astype(float)
        Lpow = self.L ** (1 - ALPHA)
        for _ in range(sweeps):
            moved = 0
            for i in self.rng.permutation(self.W):
                j = self.assign[i]
                add = Lpow * ((n + 1) ** ALPHA - n ** ALPHA) - self.m * D[i]
                if j >= 0:
                    stay = Lpow[j] * (n[j] ** ALPHA - (n[j] - 1) ** ALPHA) - self.m * D[i, j]
                    add[j] = stay
                else:
                    stay = self.b
                k = int(np.argmax(add))
                best = add[k]
                if best < self.b - 1e-12:
                    k, best = -1, self.b
                if k != j and best > stay + 1e-9:
                    if j >= 0:
                        n[j] -= 1
                    if k >= 0:
                        n[k] += 1
                    self.assign[i] = k
                    moved += 1
            if moved == 0:
                break
        self.n = n
        return n

    def metrics(self):
        D = self.dist()
        n = self.n
        Lpow = self.L ** (1 - ALPHA)
        bid = Lpow * ((n + 1) ** ALPHA - n ** ALPHA) - self.m * D        # rival bids, W x K
        emp = self.assign >= 0
        j = np.where(emp, self.assign, 0)
        own_owner = np.where(emp, self.owner[j], -1)
        same = self.owner[None, :] == own_owner[:, None]
        rival_bid = np.where(same, -np.inf, bid)
        o = np.maximum(self.b, rival_bid.max(axis=1))
        mp_here = Lpow[j] * (n[j] ** ALPHA - np.maximum(n[j] - 1, 0) ** ALPHA)
        v = mp_here - self.m * D[np.arange(self.W), j]                     # net value of current match
        u = np.minimum(o, v) + self.beta * (1 - self.rho) * np.maximum(0, v - o)
        gross = u + self.m * D[np.arange(self.W), j]
        # reachable positions: sites (other than own) bidding above home production
        reach = bid > self.b
        reach[np.arange(self.W), j] = False
        reach_rival = reach & ~same
        n_pos = reach.sum(axis=1)          # all other workplaces she could take, whoever owns them
        # distinct independent owners in reach
        n_own = np.array([len(np.unique(self.owner[reach_rival[i]])) for i in range(self.W)])
        Y = self.f(n).sum()
        e = emp
        out = {
            # what she keeps, net of her own moving/commuting cost, out of the net value her work creates
            "retained_share_of_marginal_product": float(u[e].sum() / v[e].sum()) if e.any() else np.nan,
            "labour_share_of_output": float((u[e].sum() + self.b * (~e).sum()) /
                                            (Y - (self.m * D[np.arange(self.W), j])[e].sum() + self.b * (~e).sum())),
            "mean_wage": float(np.where(e, u, self.b).mean()),
            "mean_marginal_product": float(mp_here[e].mean()) if e.any() else np.nan,
            "mean_independent_bidders_in_reach": float(np.where(e, n_own, 0).mean()),
            "mean_positions_in_reach": float(np.where(e, n_pos, 0).mean()),
            "share_with_zero_independent_bidders": float(np.mean(np.where(e, n_own, 0) == 0)),
            "employment_rate": float(e.mean()),
            "output": float(Y),
        }
        # owner concentration (employment HHI) and number of owners
        own_emp = np.bincount(self.owner, weights=n, minlength=self.owner.max() + 1)
        sh = own_emp[own_emp > 0] / own_emp.sum()
        out["owner_HHI"] = float((sh ** 2).sum())
        out["n_owners"] = int(len(np.unique(self.owner)))
        out["n_sites"] = int(len(self.z))
        self._per_worker = dict(mp=mp_here, gross=gross, n_own=n_own, j=j, emp=e)
        return out


W_ABM = 1000
L_PER_WORKER = (2.0 / ALPHA) ** (1 / (1 - ALPHA))   # competitive MP = 2 x home production
B_HOME = 1.0


def run_static(args):
    K, G, m, seed, beta, layout = args
    rng = np.random.default_rng(seed)
    z = np.sort(rng.random(K))
    L = np.full(K, L_PER_WORKER * W_ABM / K)
    if layout == "contiguous":
        owner = (np.arange(K) * G) // K          # G cartels of neighbouring sites
    else:
        owner = rng.permutation((np.arange(K) * G) // K)
    mk = Market(W_ABM, z, L, owner, m, B_HOME, beta=beta, rng=rng)
    mk.equilibrate()
    return args, mk.metrics()


def part2(pool):
    print("Part 2: labour market sweep")
    Ks = [1, 2, 3, 5, 8, 12, 20, 35, 60, 100]
    ms = [0.0, 1.0, 2.0, 4.0, 8.0, 16.0]
    seeds = [11, 12, 13]
    jobs = [(K, K, m, s, BETA, "contiguous") for K in Ks for m in ms for s in seeds]
    jobs += [(K, K, m, s, 0.0, "contiguous") for K in Ks for m in [2.0] for s in seeds]          # beta ablation
    Kc = 24
    Gs = [24, 12, 8, 6, 4, 3, 2, 1]
    CM = [2.0, 8.0]
    jobs += [(Kc, G, cm, s, BETA, lay) for G in Gs for s in seeds for lay in ["contiguous", "random"] for cm in CM]
    res = pool.map(run_static, jobs)
    agg = {}
    for args, met in res:
        key = args[:3] + args[4:]
        agg.setdefault(key, []).append(met)
    mean = lambda key, fld: float(np.mean([r[fld] for r in agg[key]]))
    grid_share = [[mean((K, K, m, BETA, "contiguous"), "retained_share_of_marginal_product") for K in Ks] for m in ms]
    grid_bid = [[mean((K, K, m, BETA, "contiguous"), "mean_independent_bidders_in_reach") for K in Ks] for m in ms]
    grid_pos = [[mean((K, K, m, BETA, "contiguous"), "mean_positions_in_reach") for K in Ks] for m in ms]
    grid_lab = [[mean((K, K, m, BETA, "contiguous"), "labour_share_of_output") for K in Ks] for m in ms]
    beta0 = [mean((K, K, 2.0, 0.0, "contiguous"), "retained_share_of_marginal_product") for K in Ks]
    LAY = [(lay, cm) for lay in ["contiguous", "random"] for cm in CM]
    coll = {f"{lay}_m{cm:g}": [mean((Kc, G, cm, BETA, lay), "retained_share_of_marginal_product") for G in Gs] for lay, cm in LAY}
    coll_b = {f"{lay}_m{cm:g}": [mean((Kc, G, cm, BETA, lay), "mean_independent_bidders_in_reach") for G in Gs] for lay, cm in LAY}
    coll_p = {f"{lay}_m{cm:g}": [mean((Kc, G, cm, BETA, lay), "mean_positions_in_reach") for G in Gs] for lay, cm in LAY}
    # pooled worker-level relation: retained share vs independent bidders (m=2)
    RESULTS["part2_labour_market"] = {
        "params": {"workers": W_ABM, "alpha": ALPHA, "beta": BETA, "home_production": B_HOME,
                   "competitive_marginal_product": 2.0, "seeds": seeds,
                   "note": "total land fixed; K only splits it among independent employers"},
        "K_independent_employers": Ks, "mobility_cost_per_unit_distance": ms,
        "retained_share_of_marginal_product[m][K]": np.round(grid_share, 4).tolist(),
        "labour_share_of_output[m][K]": np.round(grid_lab, 4).tolist(),
        "independent_bidders_in_reach[m][K]": np.round(grid_bid, 3).tolist(),
        "positions_in_reach[m][K]": np.round(grid_pos, 3).tolist(),
        "beta0_retained_share_m2[K]": np.round(beta0, 4).tolist(),
        "collusion_sites": Kc, "collusion_owners": Gs,
        "collusion_retained_share[layout][G]": {k: np.round(v, 4).tolist() for k, v in coll.items()},
        "collusion_independent_bidders[layout][G]": {k: np.round(v, 3).tolist() for k, v in coll_b.items()},
        "collusion_positions_in_reach[layout][G]": {k: np.round(v, 3).tolist() for k, v in coll_p.items()},
    }
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    a = ax[0]
    cols = plt.cm.viridis(np.linspace(0, 0.9, len(ms)))
    for mi, mm in enumerate(ms):
        a.plot(Ks, grid_share[mi], "o-", color=cols[mi], ms=3.5, label=f"moving cost {mm:g}")
    a.plot(Ks, beta0, "k--", lw=1.2, label="moving cost 2, employer sets terms (β=0)")
    a.set_xscale("log"); a.set_xlabel("number of independent employers (same total land)")
    a.set_ylabel("what workers keep: net wage ÷ net value of their work")
    a.set_title("What workers keep rises with the number of bidders")
    a.legend(fontsize=7.5, frameon=False)
    a = ax[1]
    for mi, mm in enumerate(ms):
        a.plot(Ks, grid_bid[mi], "o-", color=cols[mi], ms=3.5, label=f"moving cost {mm:g}")
    a.set_xscale("log"); a.set_yscale("symlog", linthresh=1)
    a.set_xlabel("number of independent employers")
    a.set_ylabel("independent employers a worker can reach")
    a.set_title("Options actually reachable (moving cost caps them)")
    a.legend(fontsize=7.5, frameon=False)
    a = ax[2]
    for key, col, ls, lab in [("contiguous_m2", C["blue"], "-", "neighbours merge, moving cost 2"),
                              ("random_m2", C["blue"], ":", "scattered merge, moving cost 2"),
                              ("contiguous_m8", C["red"], "-", "neighbours merge, moving cost 8"),
                              ("random_m8", C["red"], ":", "scattered merge, moving cost 8")]:
        a.plot(Gs, coll[key], "o" + ls, color=col, ms=4, label=lab)
    a.set_xscale("log"); a.set_xticks(Gs); a.set_xticklabels(Gs); a.invert_xaxis()
    a.set_xlabel(f"independent owners of the same {Kc} workplaces")
    a.set_ylabel("what workers keep (net)")
    a.set_title("Same jobs, fewer owners (mergers / no-poach)")
    a.legend(fontsize=7.5, frameon=False, loc="lower left")
    savefig(fig, "fig2_labour_market_plurality.png")
    return RESULTS["part2_labour_market"]


# ---------------- Part 3: growth with entry vs incumbents vs static ----------------
T_GROW = 60
K0 = 30


def run_growth(args):
    mode, g, mu, seed, scale_with_growth, m_start = args
    rng = np.random.default_rng(seed)
    z = list(rng.random(K0))
    Ltot0 = L_PER_WORKER * W_ABM
    L = list(np.full(K0, Ltot0 / K0))
    owner = list(range(K0))
    next_owner = K0
    m0, b0 = m_start, B_HOME
    mk = Market(W_ABM, z, L, owner, m0, b0, rng=rng)
    mk.equilibrate()
    series = []
    carry = 0.0
    land_growth = (1 + g) ** (1 / (1 - ALPHA))
    for t in range(T_GROW + 1):
        if t > 0:
            # --- consolidation: each owner acquired with hazard mu by a nearby, size-weighted acquirer
            owners = np.array(owner); Ls = np.array(L); zs = np.array(z)
            uo = np.unique(owners)
            n_merge = rng.binomial(len(uo), mu) if len(uo) > 1 else 0
            for _ in range(n_merge):
                uo = np.unique(owners)
                if len(uo) < 2:
                    break
                size = np.array([Ls[owners == o].sum() for o in uo])
                acq = uo[rng.choice(len(uo), p=size / size.sum())]
                a_sites = zs[owners == acq]
                others = uo[uo != acq]
                dmin = []
                for o in others:
                    dd = np.abs(a_sites[:, None] - zs[owners == o][None, :]); dd = np.minimum(dd, 1 - dd)
                    dmin.append(dd.min())
                w = np.exp(-np.array(dmin) / 0.1)
                tgt = others[rng.choice(len(others), p=w / w.sum())]
                owners[owners == tgt] = acq
            owner = list(owners)
            # --- growth
            Ltot = float(np.sum(L))
            if mode == "entry" and g > 0:
                carry += K0 * (land_growth - 1)
                ne = int(np.floor(carry)); carry -= ne
                for _ in range(ne):
                    z.append(rng.random()); L.append(Ltot / K0); owner.append(next_owner); next_owner += 1
            elif mode == "incumbent" and g > 0:
                L = list(np.array(L) * land_growth)
            Ltot = float(np.sum(L))
            scale = (Ltot / Ltot0) ** (1 - ALPHA)       # potential output relative to t=0
            mk.z, mk.L, mk.owner = np.array(z), np.array(L), np.array(owner)
            if scale_with_growth:
                mk.m, mk.b = m0 * scale, b0 * scale
            mk.equilibrate(sweeps=6)
        met = mk.metrics()
        scale = (float(np.sum(L)) / Ltot0) ** (1 - ALPHA)
        met["wage_relative_to_t0_subsistence"] = met["mean_wage"] / b0
        met["potential_output_index"] = scale
        series.append(met)
    return args, series


def part3(pool):
    print("Part 3: growth")
    seeds = [21, 22, 23, 24]
    main_modes = [("static", 0.0), ("entry", 0.02), ("entry", 0.05), ("incumbent", 0.02), ("incumbent", 0.05)]
    jobs = [(mo, g, 0.05, s, True, m0) for mo, g in main_modes for s in seeds for m0 in [2.0, 8.0]]
    jobs += [(mo, g, mu, s, True, 8.0) for mo, g in [("static", 0.0), ("entry", 0.02), ("entry", 0.05)]
             for mu in [0.0, 0.02, 0.1] for s in seeds[:2]]
    jobs += [(mo, g, 0.05, s, False, 8.0) for mo, g in main_modes for s in seeds[:2]]      # absolute costs ablation
    res = pool.map(run_growth, jobs)
    agg = {}
    for args, ser in res:
        agg.setdefault((args[0], args[1], args[2], args[4], args[5]), []).append(ser)
    fields = ["retained_share_of_marginal_product", "mean_independent_bidders_in_reach", "mean_positions_in_reach",
              "owner_HHI", "n_owners", "mean_wage", "labour_share_of_output", "share_with_zero_independent_bidders",
              "n_sites"]

    def avg(key, fld):
        return np.mean([[s[t][fld] for t in range(T_GROW + 1)] for s in agg[key]], axis=0)

    out = {"params": {"T_years": T_GROW, "initial_employers": K0, "merger_hazard_main": 0.05, "seeds": seeds,
                      "note": ("growth g raises potential output by g per year in every growing scenario; 'entry' delivers it "
                               "as new independent employers, 'incumbent' as bigger existing employers. In the main runs "
                               "moving cost and home production scale with potential output (pure test of plurality); the "
                               "'absolute_costs' runs hold them fixed. Every year each owner is bought out with probability "
                               "'merge' by a size-weighted acquirer, preferring nearby targets.")},
           "series": {}, "final_values": {}}
    for key in agg:
        lab = f"{key[0]}_g{int(round(key[1]*100))}pct_merge{key[2]}_movecost{key[4]:g}" + ("" if key[3] else "_absolute_costs")
        out["series"][lab] = {fld: np.round(avg(key, fld), 4).tolist() for fld in fields}
        out["final_values"][lab] = {fld: round(float(avg(key, fld)[-1]), 4) for fld in fields}
    RESULTS["part3_growth"] = out

    style = {("static", 0.0): (C["gray"], "-", "no growth"),
             ("entry", 0.02): (C["green"], "-", "2% growth via new employers"),
             ("entry", 0.05): (C["teal"], "-", "5% growth via new employers"),
             ("incumbent", 0.02): (C["orange"], "--", "2% growth to existing employers"),
             ("incumbent", 0.05): (C["red"], "--", "5% growth to existing employers")}
    tt = np.arange(T_GROW + 1)
    fig, ax = plt.subplots(2, 3, figsize=(16, 8.6))
    panels = [(ax[0, 0], 8.0, True, "retained_share_of_marginal_product", "what workers keep (net)", "What workers keep (moving cost 8)"),
              (ax[0, 1], 8.0, True, "mean_independent_bidders_in_reach", "independent employers within reach", "Real outside options (moving cost 8)"),
              (ax[0, 2], 8.0, True, "owner_HHI", "employment concentration (1 = one owner)", "Does concentration re-form? (moving cost 8)"),
              (ax[1, 0], 2.0, True, "retained_share_of_marginal_product", "what workers keep (net)", "What workers keep (moving cost 2)"),
              (ax[1, 1], 8.0, True, "mean_wage", "average net wage (year-0 home production = 1)", "Absolute wage (moving cost 8)"),
              (ax[1, 2], 8.0, False, "retained_share_of_marginal_product", "what workers keep (net)",
               "Ablation: moving cost and home\nproduction fixed in absolute terms")]
    for a, m0, sc, fld, yl, ti in panels:
        for (mo, g), (col, ls, lab) in style.items():
            a.plot(tt, avg((mo, g, 0.05, sc, m0), fld), color=col, ls=ls, lw=2, label=lab)
        a.set_xlabel("year"); a.set_ylabel(yl); a.set_title(ti, fontsize=10)
        if fld == "mean_wage":
            a.set_yscale("log")
    ax[0, 0].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    savefig(fig, "fig3_growth_entry_vs_incumbents.png")

    # ablation figure: merger hazard (moving cost 8)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    mus = [0.0, 0.02, 0.05, 0.1]
    for (mo, g) in [("static", 0.0), ("entry", 0.02), ("entry", 0.05)]:
        col, ls, lab = style[(mo, g)]
        ax[0].plot(mus, [avg((mo, g, mu, True, 8.0), "retained_share_of_marginal_product")[-1] for mu in mus], "o-", color=col, label=lab)
        ax[1].plot(mus, [avg((mo, g, mu, True, 8.0), "mean_independent_bidders_in_reach")[-1] for mu in mus], "o-", color=col, label=lab)
    for mo, g in [("incumbent", 0.02), ("incumbent", 0.05)]:
        col, ls, lab = style[(mo, g)]
        ax[0].plot([0.05], [avg((mo, g, 0.05, True, 8.0), "retained_share_of_marginal_product")[-1]], "D", color=col, label=lab)
        ax[1].plot([0.05], [avg((mo, g, 0.05, True, 8.0), "mean_independent_bidders_in_reach")[-1]], "D", color=col, label=lab)
    ax[0].set_ylabel("what workers keep, year 60"); ax[1].set_ylabel("independent employers in reach, year 60")
    for a in ax:
        a.set_xlabel("yearly chance each owner is bought out")
    ax[0].set_title("Consolidation speed vs growth-by-entry (moving cost 8)")
    ax[1].set_title("Outside options after 60 years")
    ax[0].legend(fontsize=8, frameon=False)
    savefig(fig, "fig3b_merger_speed_ablation.png")
    return out


# ---------------- Part 4: Sally vs the serf ----------------
def run_world(args):
    role, inst, seed = args
    rng = np.random.default_rng(seed)
    W = W_ABM
    # role: how productive & how replaceable the person is
    mp_target, rho = {"serf": (1.3, 0.0), "sally": (4.0, 0.95)}[role]
    Lpw = (mp_target / ALPHA) ** (1 / (1 - ALPHA))
    if inst == "manorial":     # 8 workplaces, all owned by one lord / bound by one cartel
        K, G, m = 8, 1, 0.5
    else:                      # 200 independent employers
        K, G, m = 200, 200, 0.5
    z = np.sort(rng.random(K)); L = np.full(K, Lpw * W / K)
    owner = (np.arange(K) * G) // K
    mk = Market(W, z, L, owner, m, B_HOME, rho=rho, rng=rng)
    mk.equilibrate()
    met = mk.metrics()
    pw = mk._per_worker
    e = pw["emp"]
    Yj = mk.f(mk.n)
    nec_emp = (1 - rho) * pw["mp"][e] / Yj[pw["j"][e]]
    met["necessity_marginal_product"] = float(pw["mp"][e].mean())
    met["necessity_unrecoverable_loss_to_employer_share"] = float(nec_emp.mean())
    met["necessity_share_of_whole_economy"] = float(((1 - rho) * pw["mp"][e]).mean() / Yj.sum())
    met["class_necessity_share_of_employer_output_if_all_leave"] = 1.0
    met["replaceability_rho"] = rho
    return args, met


def part4(pool):
    print("Part 4: Sally vs serf")
    jobs = [(r, i, s) for r in ["serf", "sally"] for i in ["manorial", "plural"] for s in [31, 32, 33]]
    res = pool.map(run_world, jobs)
    agg = {}
    for (r, i, s), met in res:
        agg.setdefault((r, i), []).append(met)
    keys = ["necessity_marginal_product", "necessity_unrecoverable_loss_to_employer_share", "necessity_share_of_whole_economy",
            "retained_share_of_marginal_product", "mean_independent_bidders_in_reach", "mean_positions_in_reach", "mean_wage"]
    tab = {f"{r}_role__{i}_institutions": {k: float(np.mean([m[k] for m in agg[(r, i)]])) for k in keys}
           for (r, i) in agg}
    RESULTS["part4_sally_vs_serf"] = {
        "params": {"serf_role": "competitive marginal product 1.3 x subsistence, irreplaceable (rho=0)",
                   "sally_role": "competitive marginal product 4 x subsistence, 95% replaceable (rho=0.95)",
                   "manorial_institutions": "8 workplaces, 1 owner (lords' cartel), moving cost 0.5",
                   "plural_institutions": "200 independent employers, moving cost 0.5"},
        "table": tab}
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.3))
    order = [("serf", "manorial", "Serf\n(serf job, manor)"), ("sally", "plural", "Sally\n(exec job, open market)"),
             ("serf", "plural", "Serf's job,\nopen market"), ("sally", "manorial", "Sally's job,\nlords' cartel")]
    cols = [C["red"], C["green"], C["teal"], C["orange"]]
    labels = [o[2] for o in order]
    vals = [tab[f"{r}_role__{i}_institutions"] for r, i, _ in order]
    for a, k, ti, fmt in [(ax[0], "necessity_share_of_whole_economy", "Necessity: share of the whole economy's\noutput lost if she vanishes, after replacing her (log)", "{:.1e}"),
                          (ax[1], "retained_share_of_marginal_product", "Empowerment: wage ÷ own\nmarginal product", "{:.2f}"),
                          (ax[2], "mean_independent_bidders_in_reach", "Empowerment: independent\nemployers she could go to", "{:.0f}")]:
        v = [x[k] for x in vals]
        bars = a.bar(range(4), v, color=cols)
        for b_, vv in zip(bars, v):
            a.text(b_.get_x() + b_.get_width() / 2, b_.get_height(), fmt.format(vv), ha="center", va="bottom", fontsize=8)
        a.set_xticks(range(4)); a.set_xticklabels(labels, fontsize=8); a.set_title(ti, fontsize=10)
    ax[0].set_yscale("log")
    savefig(fig, "fig4_sally_vs_serf.png")
    return tab


# =====================================================================================
# PART 5. Collective necessity vs individual necessity: strike with free riders
# =====================================================================================
def strike_equilibria(n, sigma, repression, q_star=0.5, H=5.0, mp=2.0, b=1.0, beta=BETA, cost_sd=0.5, tau=0.25):
    """Monopsony, exit blocked. Individually each worker bargains on her marginal product;
    collectively (if the strike succeeds) the class bargains on the average product (its threat
    is to withdraw ALL labour). Gain to every worker if it succeeds: Delta*H (public good).
    Worker i strikes iff  sigma + Pr(pivotal) * Delta*H  >=  c_i,  c_i = tau * yearly wage * lognormal + repression.
    Returns (lowest, highest) stable participation rate and probability of success at each."""
    ap = mp / ALPHA
    w_ind = b + beta * (mp - b)
    w_col = b + beta * (ap - b)
    Delta = w_col - w_ind
    kstar = int(np.ceil(q_star * n))
    dist = lognorm(s=cost_sd, scale=tau * w_ind * np.exp(-cost_sd ** 2 / 2))

    qs = np.linspace(0, 1, 4001)
    piv = binom.pmf(kstar - 1, n - 1, qs)
    Fq = dist.cdf(np.maximum(1e-12, sigma + piv * Delta * H - repression))
    h = Fq - qs
    # best-response dynamics started from "nobody strikes" converge to the first crossing from above,
    # started from "everybody strikes" to the last crossing
    lo = qs[np.argmax(h <= 0)] if (h <= 0).any() else 1.0
    hi = qs[len(qs) - 1 - np.argmax((h >= 0)[::-1])] if (h >= 0).any() else 0.0
    succ = lambda q: float(binom.sf(kstar - 1, n, q))
    return lo, hi, succ(lo), succ(hi), Delta, w_ind, w_col


def part5():
    print("Part 5: collective action")
    ns = np.unique(np.round(np.logspace(np.log10(5), 5, 31)).astype(int))
    sigmas = np.linspace(0, 1.0, 41)
    reps = [0.0, 0.5]
    grids = {}
    for r in reps:
        lo_g = np.zeros((len(sigmas), len(ns))); hi_g = np.zeros_like(lo_g)
        for i, sg in enumerate(sigmas):
            for jn, nn in enumerate(ns):
                lo, hi, slo, shi, *_ = strike_equilibria(int(nn), sg, r)
                lo_g[i, jn], hi_g[i, jn] = slo, shi
        grids[r] = (lo_g, hi_g)
    taus = [0.1, 0.25, 1.0]
    piv_only = {tau: [strike_equilibria(int(nn), 0.0, 0.0, tau=tau) for nn in ns] for tau in taus}
    ref = piv_only[0.25][0]
    # smallest private reward that makes the strike succeed even from pessimistic expectations
    need = {str(r): [float(sigmas[np.argmax(grids[r][0][:, jn] >= 0.5)]) if (grids[r][0][:, jn] >= 0.5).any() else None
                     for jn in range(len(ns))] for r in reps}
    RESULTS["part5_collective_action"] = {
        "params": {"monopsony_exit_blocked": True, "marginal_product": 2.0, "average_product": 2.0 / ALPHA,
                   "home_production": 1.0, "beta": BETA, "success_threshold_share_striking": 0.5,
                   "years_of_gain_if_success": 5,
                   "cost_of_striking": "tau x one year's individual wage x lognormal(sd 0.5) + repression; main tau=0.25"},
        "wage_individual_bargaining": ref[5], "wage_if_class_bargains_collectively": ref[6],
        "gain_per_worker_per_year_if_success": ref[4],
        "group_sizes": ns.tolist(), "selective_incentive_per_striker": np.round(sigmas, 3).tolist(),
        "success_prob_pessimistic_eq[repression][sigma][n]": {str(r): np.round(grids[r][0], 3).tolist() for r in reps},
        "success_prob_optimistic_eq[repression][sigma][n]": {str(r): np.round(grids[r][1], 3).tolist() for r in reps},
        "min_private_reward_for_success_from_pessimistic_start[repression][n]": need,
        "no_private_reward_no_repression_success_if_strike_expected[tau][n]":
            {str(t): [round(float(p[3]), 3) for p in piv_only[t]] for t in taus},
        "note": "with no private reward, if nobody expects a strike, nobody strikes at any group size (success 0)",
    }
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.3))
    a = ax[0]
    for tau, col in zip(taus, [C["green"], C["blue"], C["red"]]):
        a.plot(ns, [p[3] for p in piv_only[tau]], "o-", color=col, ms=3,
               label=f"striking costs {tau:g} of a year's wage")
    a.set_xscale("log"); a.set_xlabel("number of workers who must act together"); a.set_ylabel("chance the strike succeeds")
    a.set_title("No private reward: only small groups act,\nand only if everyone already expects a strike", fontsize=10)
    a.legend(fontsize=8, frameon=False)
    for a, r in zip(ax[1:], reps):
        im = a.pcolormesh(ns, sigmas, grids[r][1], cmap="Greens", vmin=0, vmax=1, shading="auto")
        a.contour(ns, sigmas, grids[r][0], levels=[0.5], colors=C["red"], linewidths=1.8)
        a.set_xscale("log"); a.set_xlabel("number of workers who must act together")
        a.set_ylabel("private reward per striker\n(share of a year's wage)")
        a.set_title(f"Repression cost {r:g} yr's wage. Shade: success if expected;\nabove red line: succeeds even if not expected", fontsize=9)
        fig.colorbar(im, ax=a, fraction=0.046)
    savefig(fig, "fig5_collective_action.png")
    return RESULTS["part5_collective_action"]


# =====================================================================================
if __name__ == "__main__":
    t0 = time.time()
    bd, abl, core = part1()
    with Pool(4) as pool:
        p2 = part2(pool)
        p3 = part3(pool)
        p4 = part4(pool)
    p5 = part5()
    print("part5 min reward:", p5["min_private_reward_for_success_from_pessimistic_start[repression][n]"])
    RESULTS["runtime_seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(HERE, "results.json"), "w") as fh:
        json.dump(RESULTS, fh, indent=1)
    print(json.dumps({"black_death": bd, "domar_ablation": abl}, indent=1))
    print("part3 finals:", json.dumps(p3["final_values"], indent=1))
    print("part4:", json.dumps(p4, indent=1))
    print("runtime", RESULTS["runtime_seconds"])
