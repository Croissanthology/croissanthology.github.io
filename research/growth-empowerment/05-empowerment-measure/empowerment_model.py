"""
Empowerment and necessity as numbers.

Runs everything for research/growth-empowerment/05-empowerment-measure/.
    python3 empowerment_model.py
writes results.json and fig*.png into this folder (runtime: a few minutes).

Definitions used (all in bits unless stated):

* n-step empowerment (Klyubin, Polani & Nehaniv 2005): the channel capacity from
  the agent's open-loop action sequence A^n to its own state S_{t+n}, given the
  current state:  E_n(s) = max_{p(a^n)} I(A^n ; S_{t+n} | s).  Everything that is
  not the agent (nature, other people) is part of the channel.  Computed exactly
  with Blahut-Arimoto.  In a deterministic world this equals log2(number of
  distinct states reachable in n steps) (checked by a self-test below).

* worst-case empowerment: the other people are not noise but commit to the
  open-loop plan b^n that is worst for the agent; the agent then optimises:
  E^wc_n = min_{b^n} max_{p(a^n)} I(A^n ; S_n | b^n).

* exposure (the protective side): how many distinguishable states OTHER people
  can steer you into while you follow your most defensive plan:
  X_n = min_{a^n} max_{p(b^n)} I(B^n ; S_n | a^n).  0 bits = nobody can move
  you without your consent.  Protection = -exposure.

* necessity: (i) marginal contribution  (v(N) - v(N minus i)) / v(N);
  (ii) Shapley share  phi_i / v(N)  of a cooperative production game v;
  (iii) class necessity: share of output lost when the agent's whole class leaves.
"""
import json, math, os, itertools, time
from collections import defaultdict
import numpy as np
import networkx as nx
from scipy.stats import binom, norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
LN2 = math.log(2)
N_STEPS = 3
COL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "lines.linewidth": 2})


# ---------------------------------------------------------------- capacity
def blahut_arimoto(P, tol=1e-7, max_iter=20000):
    """Capacity (bits) of the channel with row-stochastic matrix P (inputs x outputs)."""
    P = np.asarray(P, dtype=float)
    P = P[:, P.sum(0) > 0]
    P = np.unique(np.round(P, 12), axis=0)          # duplicate inputs do not change capacity
    m = P.shape[0]
    if m == 1 or P.shape[1] == 1:
        return 0.0
    r = np.full(m, 1.0 / m)
    logP = np.where(P > 0, np.log(np.where(P > 0, P, 1)), 0.0)
    for _ in range(max_iter):
        q = r @ P
        logq = np.log(np.where(q > 0, q, 1))
        D = (P * (logP - logq)).sum(1)
        c = np.exp(D)
        rc = r @ c
        lo, hi = math.log(rc), D.max()
        if hi - lo < tol * LN2:
            break
        r = r * c / rc
    return max(lo, 0.0) / LN2


# ------------------------------------------------- open-loop kernel tensor
def build_tensor(step, s0, A, B, n=N_STEPS, per_b=True):
    """step(s, a, b) -> list of (prob, s').  Returns (M, states, Bprobs).
    per_b=True : M has shape (classes of a^n, |B|^n, |S|): P(s_n | a^n, b^n).
    per_b=False: B averaged with its default probabilities, M shape (classes, |S|).
    Action-sequence prefixes with identical conditional kernels are merged as we go
    (exact: duplicate channel inputs never change capacity, min or max)."""
    Bn, Bp = [b for b, _ in B], np.array([p for _, p in B])
    # enumerate states
    states, idx, frontier = [s0], {s0: 0}, [s0]
    for _ in range(n):
        nxt = []
        for s in frontier:
            for a in A:
                for b in Bn:
                    for p, s2 in step(s, a, b):
                        if s2 not in idx:
                            idx[s2] = len(states); states.append(s2); nxt.append(s2)
        frontier = nxt
    S = len(states)
    # sparse-ish transition matrices T[a][b]
    T = {}
    for ai, a in enumerate(A):
        for bi, b in enumerate(Bn):
            Mx = np.zeros((S, S))
            for s in states:
                for p, s2 in step(s, a, b):
                    if s2 in idx:
                        Mx[idx[s], idx[s2]] += p
                    # states outside the n-step ball are never reached within n steps
            T[ai, bi] = Mx
    if not per_b:
        Tavg = {ai: sum(Bp[bi] * T[ai, bi] for bi in range(len(Bn))) for ai in range(len(A))}
        cur = np.zeros((1, S)); cur[0, 0] = 1.0
        for _ in range(n):
            cur = np.concatenate([cur @ Tavg[ai] for ai in range(len(A))], 0)
            cur = np.unique(np.round(cur, 12), axis=0)
        return cur, states, Bp
    cur = np.zeros((1, 1, S)); cur[0, 0, 0] = 1.0
    for _ in range(n):
        C, nb, _ = cur.shape
        blocks = []
        for ai in range(len(A)):
            # new b-index = old_b * |B| + b
            nb2 = np.stack([cur @ T[ai, bi] for bi in range(len(Bn))], 2)  # C, nb, |B|, S
            blocks.append(nb2.reshape(C, nb * len(Bn), S))
        cur = np.concatenate(blocks, 0)
        flat = np.round(cur.reshape(cur.shape[0], -1), 12)
        _, keep = np.unique(flat, axis=0, return_index=True)
        cur = cur[np.sort(keep)]
    return cur, states, Bp


def measures(step, s0, A, B, n=N_STEPS):
    M, states, Bp = build_tensor(step, s0, A, B, n, per_b=True)
    C, nb, S = M.shape
    w = np.array([np.prod([Bp[(j // len(Bp) ** k) % len(Bp)] for k in range(n)]) for j in range(nb)])
    E = blahut_arimoto(np.einsum("cbs,b->cs", M, w))
    Ewc = min(blahut_arimoto(M[:, j, :]) for j in range(nb))
    X = min(blahut_arimoto(M[c, :, :]) for c in range(C))
    return {"E": E, "E_worst": Ewc, "exposure": X, "n_states": len(states), "n_action_classes": C}


def empowerment_avg(step, s0, A, B, n=N_STEPS):
    M, _, _ = build_tensor(step, s0, A, B, n, per_b=False)
    return blahut_arimoto(M)


# ---------------------------------------------------------------- self-tests
def self_test():
    # binary symmetric channel: C = 1 - h(p)
    p = 0.11
    c = blahut_arimoto([[1 - p, p], [p, 1 - p]])
    h = -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
    assert abs(c - (1 - h)) < 1e-5, c
    # deterministic 5x5 grid walk, 3 steps: capacity == log2(#reachable)
    G = nx.grid_2d_graph(5, 5)
    A = ["rest"] + list(G.nodes)
    def st(s, a, b):
        return [(1.0, a)] if a != "rest" and G.has_edge(s, a) else [(1.0, s)]
    E = empowerment_avg(st, (2, 2), A, [("none", 1.0)])
    reach = {(2, 2)}
    for _ in range(3):
        reach |= {v for u in reach for v in G[u]}
    assert abs(E - math.log2(len(reach))) < 1e-5, (E, len(reach))
    return {"bsc_capacity_p0.11": c, "grid_E3": E, "grid_log2_reachable": math.log2(len(reach))}


# ---------------------------------------------------------------- the world
def make_world(seed=1, n=60):
    rng = np.random.default_rng(seed)
    G = nx.connected_watts_strogatz_graph(n, 6, 0.15, seed=seed)
    for v in G.nodes:
        G.nodes[v]["price"] = int(min(8, rng.lognormal(0.6, 0.8)))   # wealth needed to hold the position
    for u, v in G.edges:
        G.edges[u, v]["gate"] = bool(rng.random() < 0.3)              # a gatekeeper must let you through
    return G


def free_agent(G, home, W, keep, B_effects, pass_prob=0.8, ignore_prices=False,
               ignore_gates=False, save_gain=1, K=5, extra=None, radius=None):
    """A free agent's (position, savings) world.  Actions: rest, save, go-to-node j.
    B_effects: list of (name, prob, fn(state)->state) applied after the own action."""
    radius = N_STEPS if radius is None else radius
    ball = nx.single_source_shortest_path_length(G, home, cutoff=radius - 1)
    targets = sorted({j for u in ball for j in G[u]} | set(ball))
    A = ["rest", "save"] + [("go", j) for j in targets] + (list(extra.keys()) if extra else [])
    eff = {name: fn for name, _, fn in B_effects}

    def own(s, a):
        v, k = s
        if a == "rest":
            return [(1.0, s)]
        if a == "save":
            return [(keep, (v, min(K, k + save_gain))), (1 - keep, s)] if keep < 1 else [(1.0, (v, min(K, k + save_gain)))]
        if extra and a in extra:
            return extra[a](s)
        j = a[1]
        if not G.has_edge(v, j):
            return [(1.0, s)]
        if not ignore_prices and G.nodes[j]["price"] > W + k:
            return [(1.0, s)]
        if not ignore_gates and G.edges[v, j]["gate"]:
            return [(pass_prob, (j, k)), (1 - pass_prob, s)]
        return [(1.0, (j, k))]

    def step(s, a, b):
        if not isinstance(s, tuple) or s[0] == "deposed":
            return [(1.0, s)]
        out = []
        for p, s1 in own(s, a):
            out.append((p, eff[b](s1)))
        return out
    return step, A, [(name, p) for name, p, _ in B_effects]


# ---------------------------------------------------------------- characters
def characters(G):
    deg = dict(G.degree())
    by_deg = sorted(G.nodes, key=lambda v: (deg[v], v))
    hub, median, low = by_deg[-1], by_deg[len(by_deg) // 2], by_deg[2]
    demesne = sorted(G[low])[0]
    rng = np.random.default_rng(7)
    estates = [int(x) for x in rng.choice([v for v in G.nodes if v != low], 3, replace=False)]
    C = {}

    # Hunter-gatherer: no prices, no gates, perishable food (can store 1), demand-sharing
    C["hunter-gatherer"] = dict(home=low, k0=0, **dict(zip(["step", "A", "B"], free_agent(
        G, low, 0, keep=0.6, ignore_prices=True, ignore_gates=True, K=1,
        B_effects=[("none", 0.8, lambda s: s), ("band shares out your food", 0.2, lambda s: (s[0], 0))]))))

    # Serf: same world, but the lord's bailiff undoes moves, seizes savings, drafts labour
    def serf_step(s, a, b):
        v, k = s
        if b == "lax":
            res = [(1.0, (G.has_edge(v, a[1]) and (a[1], k)) or s)] if isinstance(a, tuple) else (
                [(1.0, (v, min(5, k + 1)))] if a == "save" else [(1.0, s)])
            return res
        k2 = min(5, k + 1) if a == "save" else k                    # moves are undone
        if b == "bind":
            return [(1.0, (v, k2))]
        if b == "bind+seize":
            return [(1.0, (v, 0))]
        if b == "corvee":
            return [(1.0, (demesne, k2))]
    A_serf = ["rest", "save"] + [("go", j) for j in sorted(G[low])]
    C["serf"] = dict(home=low, k0=0, step=serf_step, A=A_serf,
                     B=[("bind", 0.55), ("bind+seize", 0.30), ("corvee", 0.10), ("lax", 0.05)])

    # Slave: no savings at all; owner may move you to any of the owner's estates
    def slave_step(s, a, b):
        v, k = s
        if b == "hold":
            return [(1.0, s)]
        if b == "lax":
            return [(1.0, (a[1], 0) if isinstance(a, tuple) and G.has_edge(v, a[1]) else s)]
        return [(1.0, (int(b.split(":")[1]), 0))]
    C["slave"] = dict(home=low, k0=0, step=slave_step, A=["rest"] + [("go", j) for j in sorted(G[low])],
                      B=[("hold", 0.65), ("lax", 0.05)] + [(f"move:{e}", 0.10) for e in estates])

    # Ward / pet: comfortable, same structure, guardian decides where you are (benevolently)
    comfy = [hub] + sorted(G[hub])[:2]
    def ward_step(s, a, b):
        v, k = s
        if b == "hold":
            return [(1.0, s)]
        if b == "lax":
            return [(1.0, (a[1], k) if isinstance(a, tuple) and a[1] in comfy and G.has_edge(v, a[1]) else s)]
        return [(1.0, (int(b.split(":")[1]), k))]
    C["ward or pet"] = dict(home=hub, k0=0, step=ward_step, A=["rest", "ask"] + [("go", j) for j in sorted(G[hub])],
                            B=[("hold", 0.65), ("lax", 0.05)] + [(f"take:{c}", 0.10) for c in comfy])

    # Constitutional king: ordinary acts are scripted (no effect); one act: refuse assent
    def king_step(s, a, b):
        if s == "crisis":
            return [(1.0, s)]
        if a == "refuse assent":
            return [(1.0, "crisis")]
        return [(1.0, ("reign", b))]
    C["constitutional king"] = dict(home=None, k0=None, s0=("reign", "palace"), step=king_step,
                                    A=["sign", "wave", "speak", "refuse assent"],
                                    B=[("palace", 0.6), ("ceremony A", 0.2), ("ceremony B", 0.2)])

    # Rubber-stamp approver: approve (paid) or reject (escalation flag, paid); may be fired
    def appr_step(s, a, b):
        role, k = s
        if role == "fired":
            return [(1.0, s)]
        if b == "fire":
            return [(1.0, ("fired", k))]
        if a == "approve":
            return [(1.0, (role, min(5, k + 1)))]
        return [(1.0, ("flagged", min(5, k + 1)))]
    C["rubber-stamp approver"] = dict(home=None, k0=None, s0=("desk", 0), step=appr_step,
                                      A=["approve", "reject"], B=[("none", 0.95), ("fire", 0.05)])

    # Present-day AI assistant: acts only when prompted, no persistent state or resources
    def ai_step(s, a, b):
        return [(1.0, a if b == "prompt" else "idle")]
    C["AI assistant"] = dict(home=None, k0=None, s0="idle", step=ai_step,
                             A=[f"answer {i}" for i in range(8)], B=[("prompt", 0.5), ("no prompt", 0.5)])

    # Sally: well-connected position, savings, can afford many positions
    C["Sally (Netflix exec)"] = dict(home=hub, k0=1, **dict(zip(["step", "A", "B"], free_agent(
        G, hub, 6, keep=1.0,
        B_effects=[("none", 0.95, lambda s: s), ("tax", 0.05, lambda s: (s[0], max(0, s[1] - 1)))]))))

    # Citizen with a vote: median position, modest wealth, taxed
    C["citizen (voter)"] = dict(home=median, k0=1, **dict(zip(["step", "A", "B"], free_agent(
        G, median, 2, keep=0.7,
        B_effects=[("none", 0.9, lambda s: s), ("tax", 0.1, lambda s: (s[0], max(0, s[1] - 1)))]))))

    # Autocrat: ignores prices and gates, can tax (+2), can be deposed by a coup
    C["autocrat"] = dict(home=hub, k0=1, **dict(zip(["step", "A", "B"], free_agent(
        G, hub, 99, keep=1.0, ignore_prices=True, ignore_gates=True, save_gain=2, K=8,
        B_effects=[("none", 0.97, lambda s: s), ("coup", 0.03, lambda s: ("deposed", 0))]))))
    return C


# ------------------------------------------------- necessity: production games
def coalition_value(x, types, roles):
    """x: count present per type.  Role level = min(1, sum quality / need)."""
    lvl = defaultdict(float)
    for xi, (name, cnt, role, q) in zip(x, types):
        lvl[role] += xi * q
    val_add, val_veto = 0.0, 1.0
    for r, (need, share, kind) in roles.items():
        L = min(1.0, lvl[r] / need)
        if kind == "veto":
            val_veto *= L
        else:
            val_add += share * L
    return val_veto * val_add


def necessity(types, roles, focal):
    counts = [t[1] for t in types]
    N = sum(counts)
    full = coalition_value(counts, types, roles)
    minus = list(counts); minus[focal] -= 1
    marginal = (full - coalition_value(minus, types, roles)) / full
    noclass = list(counts); noclass[focal] = 0
    klass = (full - coalition_value(noclass, types, roles)) / full
    # exact Shapley value by enumeration over coalition compositions (players of a type are symmetric)
    others = list(counts); others[focal] -= 1
    phi = 0.0
    for x in itertools.product(*[range(c + 1) for c in others]):
        s = sum(x)
        ways = math.prod(math.comb(c, xi) for c, xi in zip(others, x))
        wgt = math.exp(math.lgamma(s + 1) + math.lgamma(N - s) - math.lgamma(N + 1))
        xp = list(x); xp[focal] += 1
        phi += ways * wgt * (coalition_value(xp, types, roles) - coalition_value(x, types, roles))
    return {"marginal": marginal, "shapley_share": phi / full, "class_necessity": klass}


PRODUCTION = {  # (types: name, count, role, quality), roles: need, share, kind.  Illustrative inputs.
    "hunter-gatherer": ([("hunter", 20, "forage", 1)], {"forage": (20, 1.0, "add")}, 0),
    "serf": ([("serf", 30, "field", 1), ("lord", 1, "admin", 1)],
             {"field": (30, 0.85, "add"), "admin": (1, 0.15, "add")}, 0),
    "slave": ([("slave", 20, "field", 1), ("owner", 1, "admin", 1)],
              {"field": (20, 0.95, "add"), "admin": (1, 0.05, "add")}, 0),
    "ward or pet": ([("ward", 1, "none", 1), ("household", 4, "work", 1)],
                    {"none": (1, 0.0, "add"), "work": (4, 1.0, "add")}, 0),
    "constitutional king": ([("king", 1, "crown", 1), ("regent", 1, "crown", 0.8), ("economy", 12, "econ", 1)],
                            {"crown": (1, 1.0, "veto"), "econ": (12, 1.0, "add")}, 0),
    "rubber-stamp approver": ([("approver", 1, "approval", 1), ("AI instance", 10, "pipeline", 1)],
                              {"approval": (1, 1.0, "veto"), "pipeline": (10, 1.0, "add")}, 0),
    "AI assistant": ([("assistant", 1, "ai", 1), ("competitor", 1, "ai", 0.5), ("staff", 10, "staff", 1)],
                     {"ai": (1, 0.6, "add"), "staff": (10, 0.4, "add")}, 0),
    "Sally (Netflix exec)": ([("Sally", 1, "exec", 1), ("other exec", 7, "exec", 1), ("staff", 20, "staff", 1)],
                             {"exec": (5, 0.1, "add"), "staff": (20, 0.9, "add")}, 0),
    "citizen (voter)": ([("citizen", 1, "work", 1), ("other workers", 29, "work", 1)],
                        {"work": (27, 1.0, "add")}, 0),
    "autocrat": ([("autocrat", 1, "ruler", 1), ("rival", 1, "ruler", 0.7), ("economy", 12, "econ", 1)],
                 {"ruler": (1, 1.0, "veto"), "econ": (12, 1.0, "add")}, 0),
}


# ---------------------------------------------------------------- part 0: characters
def run_characters(G):
    C = characters(G)
    out = {}
    for name, c in C.items():
        s0 = c.get("s0", (c["home"], c["k0"]))
        t0 = time.time()
        m = measures(c["step"], s0, c["A"], c["B"])
        types, roles, focal = PRODUCTION[name]
        nec = necessity(types, roles, focal)
        if name in ("Sally (Netflix exec)", "citizen (voter)"):   # class = everyone in the same role
            t2 = [list(t) for t in types]; role = t2[focal][2]
            merged = [("class", sum(t[1] for t in types if t[2] == role), role, 1)] + \
                     [tuple(t) for t in types if t[2] != role]
            nec["class_necessity"] = necessity(merged, roles, 0)["class_necessity"]
        out[name] = {**m, **nec, "seconds": round(time.time() - t0, 2)}
        print(f"  {name:24s} E3={m['E']:.2f} worst={m['E_worst']:.2f} exposure={m['exposure']:.2f} "
              f"marg={nec['marginal']:.3f} shapley={nec['shapley_share']:.3f} class={nec['class_necessity']:.2f}")
    return out


def rank_corr(x, y):
    from scipy.stats import spearmanr, pearsonr
    return {"spearman": float(spearmanr(x, y).statistic), "pearson": float(pearsonr(x, y)[0])}


# ---------------------------------------------------------------- part 1: growth
def grow_world(G, rate, rng, protect):
    """One period: add (or remove) round-stochastic rate*N positions and rate*E links."""
    N, E = G.number_of_nodes(), G.number_of_edges()
    def stoch(x):
        return int(math.floor(x) + (rng.random() < x - math.floor(x)))
    if rate >= 0:
        for _ in range(stoch(rate * N)):
            v = max(G.nodes) + 1
            nbrs = rng.choice(list(G.nodes), 3, replace=False)
            G.add_node(v, price=int(min(8, rng.lognormal(0.6, 0.8))))
            for u in nbrs:
                G.add_edge(v, int(u), gate=bool(rng.random() < 0.3))
        nodes = list(G.nodes)
        for _ in range(stoch(rate * E)):
            u, v = rng.choice(nodes, 2, replace=False)
            if not G.has_edge(u, v):
                G.add_edge(int(u), int(v), gate=bool(rng.random() < 0.3))
    else:
        for _ in range(stoch(-rate * N)):
            cand = [v for v in G.nodes if v not in protect]
            G.remove_node(int(rng.choice(cand)))
        edges = list(G.edges)
        for _ in range(stoch(-rate * E)):
            if not edges:
                break
            i = rng.integers(len(edges)); u, v = edges.pop(i)
            if G.has_edge(u, v):
                G.remove_edge(u, v)


def growth_agent_E(G, who, home, W, lax=None):
    if who == "serf":
        A = ["rest", "save"] + [("go", j) for j in sorted(G[home])]
        def st(s, a, b):
            v, k = s
            if b == "lax" and isinstance(a, tuple):
                return [(1.0, (a[1], k) if G.has_edge(v, a[1]) else s)]
            if b == "lax" and a == "save":
                return [(1.0, (v, min(5, k + 1)))]
            if b == "bind":
                return [(1.0, (v, min(5, k + 1)) if a == "save" else s)]
            return [(1.0, (v, 0))]
        bind = (1 - lax) * 0.6 / 0.95
        return empowerment_avg(st, (home, 0), A, [("bind", bind), ("bind+seize", 1 - lax - bind), ("lax", lax)])
    keep = 1.0 if who == "Sally" else 0.7
    step, A, B = free_agent(G, home, W, keep=keep, B_effects=[("none", 1.0, lambda s: s)])
    return empowerment_avg(step, (home, 1), A, B)


def run_growth(T=50, seeds=(1, 2, 3), sample=(0, 10, 20, 30, 40, 50)):
    rates = {"growing 2%/period": 0.02, "flat 0%": 0.0, "shrinking 2%/period": -0.02}
    res = {}
    for rname, g in rates.items():
        traj = defaultdict(list)
        for seed in seeds:
            G = make_world(seed)
            deg = dict(G.degree()); by = sorted(G.nodes, key=lambda v: (deg[v], v))
            hub, med, low = by[-1], by[len(by) // 2], by[2]
            rng = np.random.default_rng(100 + seed)
            out0 = None
            series = defaultdict(list)
            for t in range(T + 1):
                if t in sample:
                    # outside options near the serf: cheap positions within 2 links
                    ball = nx.single_source_shortest_path_length(G, low, cutoff=2)
                    outside = sum(1 for v in ball if G.nodes[v]["price"] <= 1)
                    out0 = outside if out0 is None else out0
                    lax_exit = 0.05 + 0.75 * (1 - math.exp(-max(0, outside - out0) / 6))
                    series["Sally"].append(growth_agent_E(G, "Sally", hub, 6 * (1 + g) ** t))
                    series["citizen"].append(growth_agent_E(G, "citizen", med, 2 * (1 + g) ** t))
                    series["serf (lord keeps control)"].append(growth_agent_E(G, "serf", low, 0, lax=0.05))
                    series["serf (lord must compete for labour)"].append(
                        growth_agent_E(G, "serf", low, 0, lax=lax_exit))
                    series["n_positions"].append(G.number_of_nodes())
                    series["Sally affordable neighbours"].append(
                        sum(1 for j in G[hub] if G.nodes[j]["price"] <= 6 * (1 + g) ** t))
                if t < T:
                    grow_world(G, g, rng, protect={hub, med, low})
            for k, v in series.items():
                traj[k].append(v)
        res[rname] = {k: list(np.mean(v, 0)) for k, v in traj.items()}
        print(f"  growth {rname}: " + ", ".join(f"{k}={res[rname][k][0]:.2f}->{res[rname][k][-1]:.2f}"
                                               for k in res[rname]))
    # ablation: growth in positions only, wealth frozen  /  wealth only, positions frozen
    abl = {}
    for label, grow_pos, grow_w in [("positions grow, wealth frozen", True, False),
                                    ("wealth grows, positions frozen", False, True)]:
        vals = []
        for seed in seeds:
            G = make_world(seed); deg = dict(G.degree()); by = sorted(G.nodes, key=lambda v: (deg[v], v))
            hub = by[-1]; rng = np.random.default_rng(100 + seed)
            for t in range(T):
                if grow_pos:
                    grow_world(G, 0.02, rng, protect={hub})
            vals.append(growth_agent_E(G, "Sally", hub, 6 * (1.02 ** T if grow_w else 1)))
        abl[label] = float(np.mean(vals))
    res["sally_ablation_at_t50"] = abl
    print("  ablation", abl)
    res["t"] = list(sample)
    return res


# ---------------------------------------------------------------- part 2: plurality
def plurality(seeds=range(12), ks=(1, 2, 4, 8, 16, 32), pi=0.7, rho=0.2):
    out = {}
    for gname in ["grid (many routes)", "tree (one route to each place)"]:
        acc = defaultdict(lambda: defaultdict(list))
        for seed in seeds:
            rng = np.random.default_rng(seed)
            G0 = nx.convert_node_labels_to_integers(nx.grid_2d_graph(7, 7), label_attribute="xy")
            centre = [v for v in G0 if G0.nodes[v]["xy"] == (3, 3)][0]
            G = G0 if gname.startswith("grid") else nx.bfs_tree(G0, centre).to_undirected()
            if not gname.startswith("grid"):   # random spanning tree instead of BFS (BFS keeps all short paths)
                Gw = G0.copy()
                for u, v in Gw.edges:
                    Gw.edges[u, v]["w"] = rng.random()
                G = nx.minimum_spanning_tree(Gw, weight="w")
            ball = nx.single_source_shortest_path_length(G, centre, cutoff=N_STEPS - 1)
            A = ["rest"] + sorted({j for u in ball for j in G[u]})
            edges = list(G.edges)
            for k in ks:
                owner = {tuple(sorted(e)): int(rng.integers(k)) for e in edges}
                # (a) i.i.d. noise: each attempt passes w.p. pi
                def st_iid(s, a, b):
                    if a != "rest" and G.has_edge(s, a):
                        return [(pi, a), (1 - pi, s)]
                    return [(1.0, s)]
                acc["noise, independent each attempt"][k].append(empowerment_avg(st_iid, centre, A, [("n", 1.0)]))
                # (b) persistent mood: each gatekeeper is open (w.p. pi) or closed for the whole horizon
                rows = []
                for seq in itertools.product(A, repeat=N_STEPS):
                    dist = defaultdict(float)
                    def rec(s, i, moods, p):
                        if i == N_STEPS:
                            dist[s] += p; return
                        a = seq[i]
                        if a == "rest" or not G.has_edge(s, a):
                            return rec(s, i + 1, moods, p)
                        g = owner[tuple(sorted((s, a)))]
                        if g in moods:
                            return rec(a if moods[g] else s, i + 1, moods, p)
                        rec(a, i + 1, {**moods, g: True}, p * pi)
                        rec(s, i + 1, {**moods, g: False}, p * (1 - pi))
                    rec(centre, 0, {}, 1.0)
                    rows.append(dist)
                keys = sorted({s for d in rows for s in d})
                P = np.array([[d.get(s, 0.0) for s in keys] for d in rows])
                acc["noise, each gatekeeper's mood lasts"][k].append(blahut_arimoto(P))
                # (c) adversarial: hostile gatekeepers block all their gates; deterministic reach
                def reach(blocked):
                    R = {centre}
                    for _ in range(N_STEPS):
                        R |= {j for u in R for j in G[u] if owner[tuple(sorted((u, j)))] not in blocked}
                    return math.log2(len(R))
                per_g = [reach({g}) for g in range(k)]
                acc["one hostile gatekeeper (worst one)"][k].append(min(per_g))
                draws = [reach({g for g in range(k) if rng.random() < rho}) for _ in range(400)]
                full = reach(set())
                acc[f"each gatekeeper hostile w.p. {rho} (average)"][k].append(float(np.mean(draws)))
                acc[f"chance of losing half your options or more (rho={rho})"][k].append(
                    float(np.mean([d <= full - 1 for d in draws])))
                acc["all gates open (reference)"][k].append(full)
        out[gname] = {m: {str(k): float(np.mean(v)) for k, v in d.items()} for m, d in acc.items()}
        print("  plurality", gname, {m: [round(out[gname][m][str(k)], 2) for k in ks] for m in out[gname]})
    out["k_values"] = list(ks)
    return out


# ---------------------------------------------------------------- part 3: the voter
def vote_capacity(N, m, q):
    """Block of m voters votes together; the other N-m vote A independently w.p. q.
    Outcome = A iff votes for A > N/2.  Capacity (bits) from the block's choice to the outcome."""
    others = N - m
    need = N // 2 + 1                                 # votes for A needed (N odd)
    pA_if_A = binom.sf(need - m - 1, others, q)       # P(others >= need - m)
    pA_if_B = binom.sf(need - 1, others, q)           # P(others >= need)
    P = np.array([[pA_if_A, 1 - pA_if_A], [pA_if_B, 1 - pA_if_B]])
    # 2x2 channel: closed-form optimisation by fine grid on the input (BA would need many iters at tiny I)
    best = 0.0
    for r in np.linspace(0.3, 0.7, 401):
        qy = r * P[0] + (1 - r) * P[1]
        I = sum(r_ * sum(P[i, j] * math.log2(P[i, j] / qy[j]) for j in range(2) if P[i, j] > 0)
                for i, r_ in enumerate([r, 1 - r]))
        best = max(best, I)
    return best, float(pA_if_A - pA_if_B)


def run_voter(N=1_000_001):
    ms = [1, 10, 100, 300, 1000, 3000, 10000, 30000, 100000]
    res = {"N": N, "coalition_sizes": ms}
    for q in (0.5, 0.505):
        caps, piv = [], []
        for m in ms:
            c, d = vote_capacity(N, m, q)
            caps.append(c); piv.append(d)
        res[f"capacity_bits_q{q}"] = caps
        res[f"prob_block_changes_outcome_q{q}"] = piv
        print(f"  voter q={q}: individual capacity {caps[0]:.3g} bits; pivot prob {piv[0]:.3g}; "
              f"block 10k: {caps[ms.index(10000)]:.3f} bits")
    # Protection: will a ruler expropriate a group of fraction f?
    fs = np.logspace(-6, -0.3, 60)
    gain_over_office = 2.0     # taking everything from everyone is worth 2x the value of office
    delta, sigma, swing = 0.03, 0.03, 0.9
    p0 = norm.cdf(-delta / sigma)
    dem = []
    for f in fs:
        share = 0.5 + delta - f * swing * (0.5 + delta)     # victims switch to the challenger
        pl = norm.cdf(-(share - 0.5) / sigma)
        dem.append(bool(f * gain_over_office > (pl - p0)))
    tau = 0.25    # autocracy: removed only if victims exceed a revolt threshold
    aut = [bool(f * gain_over_office > (1.0 if f > tau else 0.0)) for f in fs]
    res["protection"] = {"group_fraction": list(fs), "democracy_ruler_would_expropriate": dem,
                         "autocracy_ruler_would_expropriate": aut,
                         "params": {"gain_over_office": gain_over_office, "incumbent_lead": delta,
                                    "swing_noise_sd": sigma, "victims_switching": swing,
                                    "autocracy_revolt_threshold": tau}}
    fstar_dem = min((f for f, d in zip(fs, dem) if not d), default=None)
    res["protection"]["democracy_smallest_protected_fraction"] = fstar_dem
    res["protection"]["autocracy_smallest_protected_fraction"] = min((f for f, d in zip(fs, aut) if not d), default=None)
    # ablation: elections where the victims do not vote on it (swing=0)
    print(f"  protection: democracy protects groups >= {fstar_dem:.3g}; autocracy protects groups > {tau}")
    return res


# ---------------------------------------------------------------- part 4: dependence
def dependence(G, Ds=(0, 1, 2, 4, 8, 16, 32)):
    """Focal agent at a position; D others depend on its output.  'withhold' asks for a payment
    of ceil(D/2) wealth units (half the surplus at stake).  Wealth buys positions (prices)."""
    deg = dict(G.degree()); by = sorted(G.nodes, key=lambda v: (deg[v], v)); home = by[len(by) // 2]
    conds = {"all three hold": dict(credible=True, irreplaceable=True, unforceable=True),
             "cannot credibly withhold (overridden)": dict(credible=False, irreplaceable=True, unforceable=True),
             "can be replaced": dict(credible=True, irreplaceable=False, unforceable=True),
             "can be forced to work": dict(credible=True, irreplaceable=True, unforceable=False)}
    res = {"D": list(Ds)}
    for cname, c in conds.items():
        Es = []
        for D in Ds:
            pay = math.ceil(D / 2)
            def withhold(s, pay=pay, c=c):
                v, k = s
                if c["credible"] and c["irreplaceable"] and c["unforceable"] and pay > 0:
                    return [(1.0, (v, min(24, k + pay)))]
                return [(1.0, (v, min(24, k + 1)))]   # overridden / ignored / forced: you just work
            step, A, B = free_agent(G, home, 0, keep=1.0, K=24, extra={"withhold": withhold},
                                    B_effects=[("none", 1.0, lambda s: s)])
            Es.append(empowerment_avg(step, (home, 0), A, B))
        res[cname] = Es
        print(f"  dependence [{cname}]: " + " ".join(f"{e:.2f}" for e in Es))
    # same, but wealth buys nothing (no prices): empowerment counts outcomes, not their size
    Es = []
    for D in Ds:
        pay = math.ceil(D / 2)
        step, A, B = free_agent(G, home, 0, keep=1.0, K=24, ignore_prices=True,
                                extra={"withhold": lambda s, pay=pay: [(1.0, (s[0], min(24, s[1] + max(pay, 1))))]},
                                B_effects=[("none", 1.0, lambda s: s)])
        Es.append(empowerment_avg(step, (home, 0), A, B))
    res["all three hold, but wealth buys no positions"] = Es
    # necessity of the focal agent as D grows (each dependent produces 1 unit using the agent's output)
    # game: v(S) = [focal in S] * (1 + #dependents in S) + #independent workers in S (10 of them)
    # marginal share = (D+1)/(D+11); Shapley value of focal = 1 + D/2 (each dependent's unit split 50/50)
    res["focal marginal share"] = [(D + 1) / (D + 11) for D in Ds]
    nec = [(1 + D / 2) / (D + 11) for D in Ds]
    res["focal Shapley share"] = nec
    print("  dependence necessity:", [round(x, 3) for x in nec])
    return res


# ---------------------------------------------------------------- figures
def figures(R):
    ch = R["characters"]; names = list(ch)
    short = {n: n.replace(" (Netflix exec)", "").replace(" (voter)", "") for n in names}
    # Fig 1: necessity vs empowerment
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, key, lab in [(axes[0], "shapley_share", "Necessity of the individual\n(Shapley share of output)"),
                         (axes[1], "class_necessity", "Necessity of their whole class\n(share of output lost if the class leaves)")]:
        x = [ch[n][key] for n in names]; y = [ch[n]["E"] for n in names]
        ax.scatter(x, y, s=46, color=COL[0], edgecolor="white", linewidth=1.5, zorder=3)
        for n, xi, yi in zip(names, x, y):
            ax.annotate(short[n], (xi, yi), xytext=(5, 4), textcoords="offset points", fontsize=8.5, color=INK)
        ax.set_xlabel(lab); ax.set_ylabel("Empowerment over 3 steps (bits)")
        c = R["correlations"][key]
        ax.set_title(f"rank correlation {c['spearman']:+.2f}", fontsize=10, color=INK2, loc="left")
    fig.suptitle("Being needed and being in control are separate numbers", fontsize=12, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig1_necessity_vs_empowerment.png"), dpi=150); plt.close(fig)

    # Fig 2: empowerment (typical / worst case) and exposure
    fig, ax = plt.subplots(figsize=(10, 4.8))
    order = sorted(names, key=lambda n: ch[n]["E"])
    yy = np.arange(len(order))
    ax.barh(yy - 0.27, [ch[n]["E"] for n in order], 0.25, color=COL[0], label="empowerment, others act as usual")
    ax.barh(yy, [ch[n]["E_worst"] for n in order], 0.25, color=COL[6], label="empowerment, others do their worst")
    ax.barh(yy + 0.27, [ch[n]["exposure"] for n in order], 0.25, color=COL[1],
            label="exposure: states others can force you into")
    ax.set_yticks(yy); ax.set_yticklabels([short[n] for n in order]); ax.set_xlabel("bits")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    ax.set_title("Power to bring things about, and exposure to having things done to you", loc="left", fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig2_power_and_exposure.png"), dpi=150); plt.close(fig)

    # Fig 3: growth
    G = R["growth"]; t = G["t"]
    who = ["Sally", "citizen", "serf (lord keeps control)", "serf (lord must compete for labour)"]
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.8), sharey=True)
    for ax, w in zip(axes, who):
        for i, rn in enumerate(["growing 2%/period", "flat 0%", "shrinking 2%/period"]):
            ax.plot(t, G[rn][w], color=COL[[0, 3, 7][i]], marker="o", ms=4, label=rn)
        ax.set_title(w, fontsize=10, loc="left"); ax.set_xlabel("period")
    axes[0].set_ylabel("Empowerment over 3 steps (bits)"); axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Growth widens the options of people who can move; it does nothing for the bound serf "
                 "unless it forces the lord to compete", fontsize=11, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig3_growth.png"), dpi=150); plt.close(fig)

    # Fig 4: plurality
    P = R["plurality"]; ks = P["k_values"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    ms = ["all gates open (reference)", "noise, independent each attempt", "noise, each gatekeeper's mood lasts",
          "one hostile gatekeeper (worst one)", "each gatekeeper hostile w.p. 0.2 (average)"]
    for ax, gname in zip(axes, ["grid (many routes)", "tree (one route to each place)"]):
        for i, m in enumerate(ms):
            ax.plot(ks, [P[gname][m][str(k)] for k in ks], marker="o", ms=4, color=([INK2] + COL[:4])[i],
                    linestyle="--" if i == 0 else "-", label=m)
        ax.set_xscale("log", base=2); ax.set_xticks(ks); ax.set_xticklabels(ks)
        ax.set_xlabel("number of independent gatekeepers"); ax.set_title(gname, loc="left", fontsize=10)
    axes[0].set_ylabel("Empowerment over 3 steps (bits)"); axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Many gatekeepers matter only if some may be hostile, and more when there are other routes",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig4_plurality.png"), dpi=150); plt.close(fig)

    # Fig 5: voter
    V = R["voter"]; m = V["coalition_sizes"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for i, q in enumerate([0.5, 0.505]):
        axes[0].plot(m, np.maximum(V[f"capacity_bits_q{q}"], 1e-12), marker="o", ms=4, color=COL[i],
                     label="electorate split 50/50" if q == 0.5 else "electorate leans 50.5/49.5")
    axes[0].set_xscale("log"); axes[0].set_yscale("log"); axes[0].set_ylim(1e-12, 2)
    axes[0].set_xlabel("size of a bloc voting together (of 1,000,001 voters)")
    axes[0].set_ylabel("control over who wins (bits)"); axes[0].legend(frameon=False, fontsize=8.5)
    axes[0].set_title("Power to bring about: tiny alone, 1 bit as a bloc", loc="left", fontsize=10)
    pr = V["protection"]; f = pr["group_fraction"]
    axes[1].step(f, [1 - d for d in pr["democracy_ruler_would_expropriate"]], where="post", color=COL[0], label="with elections")
    axes[1].step(f, [1 - a for a in pr["autocracy_ruler_would_expropriate"]], where="post", color=COL[1], label="autocracy (revolt only)")
    axes[1].set_xscale("log"); axes[1].set_yticks([0, 1]); axes[1].set_yticklabels(["ruler would\nexpropriate", "protected"])
    axes[1].set_xlabel("fraction of citizens a ruler targets"); axes[1].legend(frameon=False, fontsize=8.5)
    axes[1].set_title("Protection: elections shield any group bigger than a few %", loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig5_voter.png"), dpi=150); plt.close(fig)

    # Fig 6: dependence
    D = R["dependence"]; Ds = D["D"]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    for i, k in enumerate(["all three hold", "cannot credibly withhold (overridden)", "can be replaced",
                           "can be forced to work", "all three hold, but wealth buys no positions"]):
        ax.plot(Ds, D[k], marker="o", ms=4, color=COL[i], label=k, linestyle="-" if i < 4 else ":")
    ax.set_xscale("symlog", linthresh=1); ax.set_xticks(Ds); ax.set_xticklabels(Ds)
    ax.set_xlabel("number of people who depend on your output"); ax.set_ylabel("Empowerment over 3 steps (bits)")
    ax.legend(frameon=False, fontsize=8.5)
    ax.set_title("Dependence turns into empowerment only if you can withhold, can't be replaced, can't be forced",
                 loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "fig6_dependence.png"), dpi=150); plt.close(fig)


def main():
    t0 = time.time()
    R = {"definitions": __doc__, "steps_horizon": N_STEPS}
    print("self-test"); R["self_test"] = self_test(); print(" ", R["self_test"])
    G = make_world(1)
    print("characters"); R["characters"] = run_characters(G)
    names = list(R["characters"])
    R["correlations"] = {k: rank_corr([R["characters"][n][k] for n in names], [R["characters"][n]["E"] for n in names])
                         for k in ("shapley_share", "marginal", "class_necessity")}
    R["correlations"]["exposure_vs_E"] = rank_corr([R["characters"][n]["exposure"] for n in names],
                                                   [R["characters"][n]["E"] for n in names])
    print("  correlations", R["correlations"])
    print("growth"); R["growth"] = run_growth()
    print("plurality"); R["plurality"] = plurality()
    print("voter"); R["voter"] = run_voter()
    print("dependence"); R["dependence"] = dependence(G)
    figures(R)
    R["runtime_seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(HERE, "results.json"), "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    print("done in", R["runtime_seconds"], "s")


if __name__ == "__main__":
    main()
