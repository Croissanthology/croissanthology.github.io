"""Empirical tests of claims A-D (see FINDINGS.md) on public country-year data.

Run:  python3 download_data.py   (once; fetches into ./raw/)
      python3 analysis.py        (regenerates results.json and all PNGs)

Requires numpy, pandas, matplotlib, statsmodels, pyreadr (to read V-Dem's .RData).
All regressions are OLS with standard errors clustered by country.
"""
import json, os, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)
np.random.seed(0)

GULF = ["SAU", "KWT", "ARE", "QAT", "BHR", "OMN"]
NAMEFIX = {"Kosovo": "XKX", "Timor": "TLS", "Korea": "KOR", "Czech Republic": "CZE",
           "Macedonia": "MKD"}

# ----------------------------------------------------------------------------- load
def load_vdem():
    cache = os.path.join(CACHE, "vdem_slim.csv")
    if os.path.exists(cache):
        return pd.read_csv(cache)
    import pyreadr
    d = pyreadr.read_r(os.path.join(RAW, "vdem.RData"))["vdem"]
    keep = {
        "country_name": "name", "country_text_id": "iso", "year": "year",
        "e_gdppc": "vdem_gdppc", "e_total_resources_income_pc": "res_pc",
        "e_total_oil_income_pc": "oil_pc", "v2stfisccap": "taxcap",
        "e_pelifeex": "lifeex", "e_peaveduc": "educ", "e_pechmor": "chmor",
        "v2x_civlib": "civlib", "v2x_clphy": "clphy", "v2x_clpol": "clpol",
        "v2x_clpriv": "clpriv", "v2x_regime": "regime", "v2x_polyarchy": "polyarchy",
        "v2clfmove": "foreign_move", "v2x_feduni": "feduni", "e_fh_cl": "fh_cl",
        "v2x_jucon": "jucon",
    }
    d = d[list(keep)].rename(columns=keep)
    d = d[d.year >= 1900]
    d.to_csv(cache, index=False)
    return d


def owid_csv(fn, cols, iso_map):
    x = pd.read_csv(os.path.join(RAW, fn))
    x = x[["Entity", "Year"] + list(cols)].rename(columns={"Year": "year", **cols})
    x["iso"] = x.Entity.map(lambda n: iso_map.get(n, NAMEFIX.get(n)))
    return x.dropna(subset=["iso"]).drop(columns="Entity")


def load_all():
    en = pd.read_csv(os.path.join(RAW, "owid_energy.csv"),
                     usecols=["country", "iso_code", "year", "oil_prod_per_capita",
                              "gas_prod_per_capita"])
    iso_map = dict(en.dropna(subset=["iso_code"])[["country", "iso_code"]].drop_duplicates().values)
    en = en.dropna(subset=["iso_code"]).rename(columns={"iso_code": "iso"})
    en["hydro_kwh_pc"] = en[["oil_prod_per_capita", "gas_prod_per_capita"]].sum(axis=1, min_count=1)
    en = en[["iso", "year", "hydro_kwh_pc"]]

    pwt = owid_csv("pwt10.csv", {
        "GDP per capita (output, multiple price benchmarks)": "gdppc",
        "GDP per capita (using national accounts growth rates)": "gdppc_na",
        "Share of labour compensation in GDP": "labsh",
        "Trade openness (share of exports and imports in GDP)": "openness",
        "Share of government consumption in GDP": "gov_cons",
        "Population": "pop_pwt"}, iso_map)
    wid = owid_csv("wid_pretax.csv", {"P99-P100 - share of the top 1%": "top1",
                                      "P0-P50 - share of the bottom 50%": "bottom50"}, iso_map)
    tax = owid_csv("oecd_revenue.csv", {"Total tax (% of GDP) (OECD (2018))": "tax_gdp"}, iso_map)
    eci = owid_csv("eci.csv", {"Economic Complexity Index (ECI) (Observatory of Economic Complexity (2016))": "eci"}, iso_map)

    v = load_vdem()
    df = v
    for other in (pwt, wid, tax, eci, en):
        df = df.merge(other, on=["iso", "year"], how="left")
    df = df.sort_values(["iso", "year"]).reset_index(drop=True)
    df["lgdp"] = np.log(df.gdppc)
    # resource income (Haber-Menaldo, production x world price, per capita) relative to PPP GDP per capita.
    # A rough share: numerator at market prices, denominator PPP, so read it as an index, in % points.
    df["res_share"] = (100 * df.res_pc / df.gdppc).clip(upper=80)
    df["lres_share"] = np.log1p(df.res_share)
    df["lhydro"] = np.log1p(df.hydro_kwh_pc)
    df["lchmor"] = np.log(df.chmor)
    df["lopen"] = np.log(df.openness)
    df["autoc"] = df.regime <= 1
    df["closed"] = df.regime == 0
    df["nonres_lgdp"] = np.log((df.gdppc - df.res_pc).where(lambda s: s > 100))
    return df

# ----------------------------------------------------------------------------- regressions
def reg(df, y, x, controls=("lgdp",), fe="year", extra=None):
    cols = [y, x] + list(controls) + ["iso", "year"]
    d = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if d.iso.nunique() < 8 or len(d) < 40:
        return None
    rhs = [x] + list(controls)
    if fe == "year":
        rhs.append("C(year)")
    elif fe == "country+year":
        rhs += ["C(iso)", "C(year)"]
    f = f"{y} ~ " + " + ".join(rhs)
    m = smf.ols(f, data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.iso)[0]})
    return {"coef": float(m.params[x]), "se": float(m.bse[x]), "p": float(m.pvalues[x]),
            "n_obs": int(len(d)), "n_countries": int(d.iso.nunique()),
            "years": [int(d.year.min()), int(d.year.max())], "x_sd": float(d[x].std()),
            "y_sd": float(d[y].std())}


def fmt(r):
    if r is None:
        return "n/a"
    return f"{r['coef']:+.3f} (se {r['se']:.3f}, p={r['p']:.3f}; {r['n_countries']} countries, {r['n_obs']} obs, {r['years'][0]}-{r['years'][1]})"


def spec_grid(df, y, x, controls=("lgdp",)):
    out = {}
    out["pooled_yearFE_all"] = reg(df, y, x, controls, "year")
    out["pooled_yearFE_autocracies"] = reg(df[df.autoc], y, x, controls, "year")
    out["pooled_yearFE_democracies"] = reg(df[df.regime >= 2], y, x, controls, "year")
    out["countryFE_all"] = reg(df, y, x, controls, "country+year")
    out["countryFE_autocracies"] = reg(df[df.autoc], y, x, controls, "country+year")
    return out

OUTCOME_LABEL = {
    "civlib": "Civil liberties (V-Dem, 0-1)",
    "clphy": "Freedom from torture/killing (V-Dem, 0-1)",
    "clpol": "Political civil liberties (V-Dem, 0-1)",
    "lifeex": "Life expectancy (years)",
    "educ": "Avg years of schooling",
    "lchmor": "log child mortality",
    "labsh": "Labour share of GDP (PWT)",
    "bottom50": "Bottom-50% income share (WID, %)",
}

# ----------------------------------------------------------------------------- claim A
def claim_A(df, R):
    print("\n=== CLAIM A: resource-funded states ===")
    d = df[(df.year >= 1960) & (df.year <= 2019)]
    A = {"predictors": {
        "lres_share": "log(1 + resource income as % of GDP), Haber-Menaldo resource income / PWT GDP pc, 1960-2006",
        "taxcap": "V-Dem v2stfisccap: how the state funds itself (low = from state-owned assets/resources, high = income/property taxes), expert-coded",
        "lhydro": "log(1 + oil+gas production kWh per person), OWID energy data, 1965-2019 (robustness)",
        "tax_gdp": "OECD Global Revenue Statistics total tax % GDP, 1990-2016, ~80 countries (robustness)"},
        "results": {}}
    outcomes = ["civlib", "clphy", "lifeex", "educ", "lchmor", "labsh", "bottom50"]
    for x in ["lres_share", "taxcap"]:
        A["results"][x] = {}
        for y in outcomes:
            g = spec_grid(d, y, x)
            A["results"][x][y] = g
            print(f"{x:>10} -> {y:<9} pooled all {fmt(g['pooled_yearFE_all'])}")
            print(f"{'':>10}    {'':<9} pooled autoc {fmt(g['pooled_yearFE_autocracies'])}")
            print(f"{'':>10}    {'':<9} countryFE autoc {fmt(g['countryFE_autocracies'])}")
    rob = {}
    rob["hydro_civlib"] = spec_grid(d, "civlib", "lhydro")
    rob["hydro_lifeex"] = spec_grid(d, "lifeex", "lhydro")
    rob["tax_gdp_civlib"] = spec_grid(d, "civlib", "tax_gdp")
    rob["lres_civlib_nonres_income_control"] = spec_grid(d, "civlib", "lres_share", ("nonres_lgdp",))
    rob["lres_civlib_exclude_gulf"] = spec_grid(d[~d.iso.isin(GULF)], "civlib", "lres_share")
    rob["lres_lifeex_nonres_income_control"] = spec_grid(d, "lifeex", "lres_share", ("nonres_lgdp",))
    rob["lres_civlib_vdem_income"] = spec_grid(d.assign(lv=np.log(d.vdem_gdppc)), "civlib", "lres_share", ("lv",))
    rob["lres_civlib_closed_autocracies_pooled"] = reg(d[d.closed], "civlib", "lres_share", ("lgdp",), "year")
    rob["taxcap_civlib_closed_autocracies_pooled"] = reg(d[d.closed], "civlib", "taxcap", ("lgdp",), "year")
    for k, g in rob.items():
        if isinstance(g, dict) and "pooled_yearFE_all" in g:
            print(f"ROB {k}: pooled all {fmt(g['pooled_yearFE_all'])} | autoc {fmt(g['pooled_yearFE_autocracies'])} | cFE autoc {fmt(g['countryFE_autocracies'])}")
        else:
            print(f"ROB {k}: {fmt(g)}")
    A["robustness"] = rob

    # cross-section of country means 1970-2006 for the scatter + outliers
    cs = d[(d.year >= 1970) & (d.year <= 2006)].groupby("iso").agg(
        name=("name", "first"), lres=("lres_share", "mean"), res=("res_share", "mean"),
        lgdp=("lgdp", "mean"), civlib=("civlib", "mean"), lifeex=("lifeex", "mean"),
        taxcap=("taxcap", "mean"), autoc=("autoc", "mean")).dropna()
    cs = cs[cs.index.notna()]
    for y in ["civlib", "lifeex"]:
        m = smf.ols(f"{y} ~ lgdp", data=cs).fit()
        cs[f"{y}_resid"] = m.resid
    m2 = smf.ols("civlib_resid ~ lres", data=cs).fit(cov_type="HC1")
    m2a = smf.ols("civlib_resid ~ lres", data=cs[cs.autoc > 0.5]).fit(cov_type="HC1")
    A["cross_section_1970_2006"] = {
        "slope_all": [float(m2.params.lres), float(m2.bse.lres), int(m2.nobs)],
        "slope_mostly_autocratic": [float(m2a.params.lres), float(m2a.bse.lres), int(m2a.nobs)],
        "points": [{"iso": i, "name": r["name"], "resource_share_pct": round(r.res, 2),
                    "log1p_resource_share": round(r.lres, 3), "civlib_resid_given_income": round(r.civlib_resid, 3),
                    "lifeex_resid_given_income": round(r.lifeex_resid, 2), "share_years_autocracy": round(r.autoc, 2)}
                   for i, r in cs.iterrows()]}
    # contradicting cases: resource-heavy (>=8% index) but better civil liberties than income predicts
    contra = cs[cs.res >= 8].sort_values("civlib_resid", ascending=False)
    A["contradicting_cases"] = [{"name": r["name"], "resource_share_pct": round(r.res, 1),
                                 "civlib_resid": round(r.civlib_resid, 3)} for _, r in contra.head(8).iterrows()]
    # tax-reliant but unfree: high taxcap residual-free yet low civlib
    contra2 = cs[cs.taxcap > cs.taxcap.quantile(0.66)].sort_values("civlib_resid").head(8)
    A["tax_reliant_but_unfree"] = [{"name": r["name"], "taxcap": round(r.taxcap, 2),
                                    "civlib_resid": round(r.civlib_resid, 3)} for _, r in contra2.iterrows()]
    named = ["NOR", "BWA", "SGP", "RWA", "SAU", "KWT", "ARE", "QAT", "CHN", "VEN", "NGA", "IRN", "RUS"]
    A["named_countries"] = {cs.loc[i, "name"]: {"resource_share_pct": round(cs.loc[i, "res"], 1),
                                                "civlib_resid": round(cs.loc[i, "civlib_resid"], 3),
                                                "taxcap": round(cs.loc[i, "taxcap"], 2)}
                            for i in named if i in cs.index}
    R["A"] = A
    print("cross-section slope", A["cross_section_1970_2006"]["slope_all"], A["cross_section_1970_2006"]["slope_mostly_autocratic"])
    print("contradicting", A["contradicting_cases"])
    print("named", A["named_countries"])

    # figure A1: scatter
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    for ax, y, lab in [(axes[0], "civlib_resid", "Civil liberties vs. what income predicts"),
                       (axes[1], "lifeex_resid", "Life expectancy vs. what income predicts (years)")]:
        au = cs.autoc > 0.5
        ax.scatter(cs.res[~au], cs[y][~au], s=18, c="#3a78b5", alpha=.7, label="mostly democratic")
        ax.scatter(cs.res[au], cs[y][au], s=18, c="#d1495b", alpha=.7, label="mostly autocratic")
        xs = np.linspace(0, cs.lres.max(), 100)
        mm = smf.ols(f"{y} ~ lres", data=cs).fit()
        ax.plot(np.expm1(xs), mm.params.Intercept + mm.params.lres * xs, c="k", lw=1.5, label="fitted (all)")
        mma = smf.ols(f"{y} ~ lres", data=cs[au]).fit()
        ax.plot(np.expm1(xs), mma.params.Intercept + mma.params.lres * xs, c="#d1495b", lw=1.5, ls="--", label="fitted (autocratic)")
        ax.set_xscale("symlog", linthresh=1)
        ax.axhline(0, c="grey", lw=.5)
        for iso in ["NOR", "BWA", "SAU", "KWT", "QAT", "ARE", "SGP", "CHN", "RWA", "VEN", "NGA", "USA", "OMN", "TTO", "CHL"]:
            if iso in cs.index:
                ax.annotate(cs.loc[iso, "name"].replace(" of America", ""), (cs.loc[iso, "res"], cs.loc[iso, y]), fontsize=7)
        ax.set_xlabel("Natural-resource income, % of GDP (rough index, 1970-2006 average)")
        ax.set_title(lab, fontsize=11)
    axes[0].legend(fontsize=8)
    fig.suptitle("Countries living on resource income: freer or less free than their income predicts?", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_A_resources_vs_freedom.png"), dpi=150)
    plt.close(fig)

    # figure A2: coefficient plot (standardised: effect of +1 SD predictor, in SDs of outcome)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
    specs = [("pooled_yearFE_all", "all, income held fixed"), ("pooled_yearFE_autocracies", "autocracies only"),
             ("countryFE_all", "within-country, all"), ("countryFE_autocracies", "within-country, autocracies")]
    cols = ["#222222", "#d1495b", "#7a7a7a", "#f08a4b"]
    for ax, x, title in [(axes[0], "lres_share", "More resource income"), (axes[1], "taxcap", "State funded more by taxes")]:
        for j, (sk, sl) in enumerate(specs):
            for i, y in enumerate(outcomes):
                r = A["results"][x][y][sk]
                if r is None:
                    continue
                b = r["coef"] * r["x_sd"] / r["y_sd"]
                s = r["se"] * r["x_sd"] / r["y_sd"]
                yy = i + (j - 1.5) * 0.18
                ax.errorbar(b, yy, xerr=1.96 * s, fmt="o", c=cols[j], ms=4, label=sl if i == 0 else None)
        ax.axvline(0, c="grey", lw=.6)
        ax.set_yticks(range(len(outcomes)))
        ax.set_yticklabels([OUTCOME_LABEL[o] for o in outcomes], fontsize=8)
        ax.set_title(title + " (+1 SD), effect in SDs of outcome", fontsize=10)
        ax.invert_yaxis()
    axes[0].legend(fontsize=8, loc="lower left")
    fig.suptitle("How ordinary people fare where the state lives on resources vs taxes (95% intervals)\n"
                 "Note: child mortality is 'bad', so a positive bar there means worse off", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_A_coefficients.png"), dpi=150)
    plt.close(fig)

# ----------------------------------------------------------------------------- claim B
def build_windows(df, step=5, span=10):
    """For each country and anchor year t: growth over [t-span, t], outcome change over [t, t+span]."""
    ys = ["civlib", "clphy", "clpol", "lifeex", "educ", "lchmor", "polyarchy"]
    base = df[["iso", "year", "name", "regime", "lgdp", "lres_share", "taxcap", "gdppc_na"] + ys]
    def at(offset, cols):
        s = base[["iso", "year"] + cols].copy()
        s["year"] = s["year"] - offset   # value observed at (year+offset), keyed by anchor year
        return s.rename(columns={c: f"{c}@{offset}" for c in cols})
    w = base[base.year.isin(range(1970, 2016, step))]
    w = w.merge(at(-span, ["gdppc_na"] + ys), on=["iso", "year"], how="left")
    w = w.merge(at(span, ys), on=["iso", "year"], how="left")
    # future growth: up to t+10, but GDP ends in 2019
    fut = base[["iso", "year", "gdppc_na"]].rename(columns={"year": "yf", "gdppc_na": "gdp_f"})
    w["yf"] = np.minimum(w.year + span, 2019)
    w = w.merge(fut, on=["iso", "yf"], how="left")
    w["growth_past"] = 100 * (np.log(w.gdppc_na) - np.log(w[f"gdppc_na@{-span}"])) / span
    w["growth_future"] = 100 * (np.log(w.gdp_f) - np.log(w.gdppc_na)) / (w.yf - w.year)
    for y in ys:
        w[y + "_0"] = w[y]
        w["d_" + y] = w[f"{y}@{span}"] - w[y]
        w["dpast_" + y] = w[y] - w[f"{y}@{-span}"]
    w = w.replace([np.inf, -np.inf], np.nan).dropna(subset=["growth_past", "regime"])
    w["autoc"] = w.regime <= 1
    w["closed"] = w.regime == 0
    w["stagnant"] = (w.growth_past <= 0).astype(float)
    return w


def claim_B(df, R):
    print("\n=== CLAIM B: growth in autocracies ===")
    w = build_windows(df)
    B = {"design": "Anchor years t = 1970,1975,...,2015. Predictor: average annual growth of real GDP per capita (PWT, national-accounts) over the 10 years BEFORE t. Outcome: change over the 10 years AFTER t. Controls: log income at t and outcome level at t; period fixed effects; SEs clustered by country.",
         "results": {}}
    for y in ["civlib", "clphy", "clpol", "lifeex", "educ", "lchmor"]:
        ctrl = ("lgdp", y + "_0")
        B["results"][y] = {
            "all": reg(w, "d_" + y, "growth_past", ctrl, "year"),
            "autocracies": reg(w[w.autoc], "d_" + y, "growth_past", ctrl, "year"),
            "closed_autocracies": reg(w[w.closed], "d_" + y, "growth_past", ctrl, "year"),
            "autocracies_countryFE": reg(w[w.autoc], "d_" + y, "growth_past", ctrl, "country+year"),
            "democracies": reg(w[~w.autoc], "d_" + y, "growth_past", ctrl, "year"),
        }
        for k, r in B["results"][y].items():
            print(f"growth -> d_{y:<7} {k:<22} {fmt(r)}")
    # stagnation -> loss of freedom
    B["stagnation"] = {}
    for grp, sub in [("all", w), ("autocracies", w[w.autoc]), ("democracies", w[~w.autoc])]:
        B["stagnation"][grp] = {y: reg(sub, "d_" + y, "stagnant", ("lgdp", y + "_0"), "year") for y in ["civlib", "polyarchy"]}
        print("stagnation", grp, fmt(B["stagnation"][grp]["civlib"]), "| polyarchy", fmt(B["stagnation"][grp]["polyarchy"]))
    # does growth matter more when it is not resource-driven? interaction with taxcap / resource share
    wa = w[w.autoc].copy()
    out = {}
    for mod in ["taxcap", "lres_share"]:
        d = wa[["d_civlib", "growth_past", mod, "lgdp", "civlib_0", "iso", "year"]].dropna()
        d["inter"] = d.growth_past * (d[mod] - d[mod].mean())
        m = smf.ols(f"d_civlib ~ growth_past + {mod} + inter + lgdp + civlib_0 + C(year)", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d.iso)[0]})
        out[mod] = {"growth_coef": float(m.params.growth_past), "growth_se": float(m.bse.growth_past),
                    "interaction_coef": float(m.params.inter), "interaction_se": float(m.bse.inter),
                    "interaction_p": float(m.pvalues.inter), "n_obs": int(m.nobs), "n_countries": int(d.iso.nunique())}
        print("interaction growth x", mod, out[mod])
    B["growth_x_revenue_source_autocracies"] = out
    # reverse direction: does a freedom gain predict faster growth afterwards?
    B["reverse_freedom_then_growth"] = {
        "all": reg(w, "growth_future", "dpast_civlib", ("lgdp", "civlib_0"), "year"),
        "autocracies": reg(w[w.autoc], "growth_future", "dpast_civlib", ("lgdp", "civlib_0"), "year")}
    print("reverse: past d_civlib -> future growth", fmt(B["reverse_freedom_then_growth"]["autocracies"]))
    # Level comparison among autocracies: tax-funded growers vs others
    # contradicting cases: autocratic windows with fast growth (>4%/yr) but falling civil liberties
    fast = w[w.autoc & (w.growth_past > 4)].dropna(subset=["d_civlib"]).sort_values("d_civlib")
    B["fast_growth_but_freedom_fell"] = [{"name": r["name"], "t": int(r.year), "growth_past_pct": round(r.growth_past, 1),
                                          "d_civlib_next10": round(r.d_civlib, 3)} for _, r in fast.head(10).iterrows()]
    B["share_fast_growth_autocratic_windows_with_civlib_gain"] = float((fast.d_civlib > 0).mean())
    slow = w[w.autoc & (w.growth_past <= 0)].dropna(subset=["d_civlib"])
    B["share_stagnant_autocratic_windows_with_civlib_gain"] = float((slow.d_civlib > 0).mean())
    B["n_fast_windows"] = int(len(fast)); B["n_stagnant_windows"] = int(len(slow))
    chn = w[w.iso == "CHN"][["year", "growth_past", "d_civlib", "civlib_0", "d_lifeex"]].round(3)
    B["china_windows"] = chn.to_dict(orient="records")
    print("fast growth & civlib fell:", B["fast_growth_but_freedom_fell"][:6])
    print("share fast autoc windows w/ gain", B["share_fast_growth_autocratic_windows_with_civlib_gain"], len(fast),
          "| stagnant", B["share_stagnant_autocratic_windows_with_civlib_gain"], len(slow))
    # long-difference: one observation per country that was an autocracy at the start
    LD = {}
    ld_tables = {}
    for (t0, t1) in [(1990, 2019), (1970, 2000)]:
        a = df[df.year == t0].set_index("iso"); b = df[df.year == t1].set_index("iso")
        ld = pd.DataFrame({"name": a.name, "autoc0": a.autoc, "lgdp0": a.lgdp,
                           "growth": 100 * (np.log(b.gdppc_na) - np.log(a.gdppc_na)) / (t1 - t0)})
        for y in ["civlib", "lifeex", "lchmor", "polyarchy"]:
            ld[y + "0"] = a[y]; ld["d_" + y] = b[y] - a[y]
        ld = ld[ld.autoc0 == True].dropna(subset=["growth", "d_civlib", "lgdp0"])
        LD[f"{t0}-{t1}"] = {}
        for y in ["civlib", "lifeex", "lchmor", "polyarchy"]:
            dd = ld.dropna(subset=["d_" + y, y + "0"])
            m = smf.ols(f"d_{y} ~ growth + lgdp0 + {y}0", data=dd).fit(cov_type="HC1")
            LD[f"{t0}-{t1}"][y] = {"coef": float(m.params.growth), "se": float(m.bse.growth),
                                    "p": float(m.pvalues.growth), "n_countries": int(m.nobs)}
            print(f"long diff {t0}-{t1} growth -> d_{y}: {m.params.growth:+.4f} (se {m.bse.growth:.4f}, p={m.pvalues.growth:.3f}, n={int(m.nobs)})")
        ld_tables[f"{t0}-{t1}"] = ld
    B["long_difference_autocracies"] = LD
    ld = ld_tables["1990-2019"]
    B["long_difference_points_1990_2019"] = [{"iso": i, "name": r["name"], "growth_pct": round(r.growth, 2),
                                              "d_civlib": round(r.d_civlib, 3), "d_lifeex": round(r.d_lifeex, 2)}
                                             for i, r in ld.iterrows()]
    R["B"] = B
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, y, lab in [(axes[0], "d_civlib", "Change in civil liberties 1990-2019"),
                       (axes[1], "d_lifeex", "Change in life expectancy 1990-2019 (years)")]:
        dd = ld.dropna(subset=[y])
        ax.scatter(dd.growth, dd[y], s=18, c="#d1495b", alpha=.7)
        mm = smf.ols(f"{y} ~ growth", data=dd).fit()
        xs = np.linspace(dd.growth.min(), dd.growth.max(), 50)
        ax.plot(xs, mm.params.Intercept + mm.params.growth * xs, c="k")
        for iso in ["CHN", "VNM", "RWA", "SGP", "SAU", "PRK", "ETH", "LAO", "KHM", "MYS", "BLR", "IDN", "KOR", "TWN", "ZWE", "MMR", "IRN", "EGY", "CUB", "VEN"]:
            if iso in dd.index:
                ax.annotate(dd.loc[iso, "name"], (dd.loc[iso, "growth"], dd.loc[iso, y]), fontsize=7)
        ax.axhline(0, c="grey", lw=.5)
        ax.set_xlabel("Avg annual GDP-per-person growth 1990-2019 (%)")
        ax.set_title(lab, fontsize=10)
    fig.suptitle(f"Countries that were autocracies in 1990 ({len(ld)}): growth vs. what happened to their people", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_B_long_run_autocracies.png"), dpi=150)
    plt.close(fig)

    # figure: binned scatter in autocracies
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    wa = w[w.autoc].dropna(subset=["d_civlib", "lifeex_0"]).copy()
    wa["bin"] = pd.qcut(wa.growth_past, 10, duplicates="drop")
    for ax, y, lab in [(axes[0], "d_civlib", "Change in civil liberties, next 10 yrs"),
                       (axes[1], "d_lifeex", "Change in life expectancy, next 10 yrs"),
                       (axes[2], "d_polyarchy", "Change in electoral democracy index, next 10 yrs")]:
        b = wa.groupby("bin").agg(x=("growth_past", "mean"), y=(y, "mean"), se=(y, lambda s: s.std() / np.sqrt(len(s))))
        ax.scatter(wa.growth_past.clip(-10, 12), wa[y], s=4, alpha=.15, c="grey")
        ax.errorbar(b.x, b.y, yerr=1.96 * b.se, fmt="o", c="#d1495b", label="decile means (95% CI)")
        ax.axvline(0, c="k", lw=.5); ax.axhline(0, c="k", lw=.5)
        ax.set_xlabel("Avg annual GDP-per-person growth, previous 10 yrs (%)")
        ax.set_title(lab, fontsize=10)
        lo, hi = np.nanpercentile(wa[y], [1, 99]); ax.set_ylim(lo, hi)
    axes[0].legend(fontsize=8)
    fig.suptitle(f"Autocracies: does a decade of growth come before more freedom? ({wa.iso.nunique()} countries, {len(wa)} country-decades, overlapping, 1970-2015)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_B_growth_then_freedom.png"), dpi=150)
    plt.close(fig)
    R["B_binned"] = {y: wa.groupby("bin").agg(x=("growth_past", "mean"), y=(y, "mean")).round(4).values.tolist()
                     for y in ["d_civlib", "d_lifeex", "d_polyarchy"]}

# ----------------------------------------------------------------------------- claim C
def claim_C(df, R):
    print("\n=== CLAIM C: plurality / exit ===")
    d = df[(df.year >= 1960) & (df.year <= 2019)]
    C = {"predictors": {
        "eci": "Economic Complexity Index (OEC 2016 release), 1964-2016",
        "lopen": "log trade openness, exports+imports % GDP (PWT 10)",
        "feduni": "V-Dem division-of-power (federalism/subnational elected govts) index, 0-1",
        "foreign_move": "V-Dem freedom of foreign movement / emigration (v2clfmove); part of the civil-liberties index, so tested only against physical integrity",
        "gov_cons": "government consumption % GDP (PWT) - a crude 'state crowds out private' measure"},
        "note": "Outcome 'clphy' (freedom from political killing and torture) is used for the exit variable to avoid mechanical overlap.",
        "results": {}}
    for x in ["eci", "lopen", "feduni", "gov_cons"]:
        C["results"][x] = {y: spec_grid(d, y, x) for y in ["civlib", "clphy", "lifeex"]}
        for y in ["civlib", "clphy"]:
            g = C["results"][x][y]
            print(f"{x:>8} -> {y}: all {fmt(g['pooled_yearFE_all'])} | autoc {fmt(g['pooled_yearFE_autocracies'])} | cFE autoc {fmt(g['countryFE_autocracies'])}")
    C["results"]["foreign_move"] = {"clphy": spec_grid(d, "clphy", "foreign_move")}
    g = C["results"]["foreign_move"]["clphy"]
    print(f"foreign_move -> clphy: all {fmt(g['pooled_yearFE_all'])} | autoc {fmt(g['pooled_yearFE_autocracies'])} | cFE autoc {fmt(g['countryFE_autocracies'])}")
    # robustness: ECI controlling for resource dependence (diversification vs resources)
    C["robustness_eci_with_resource_control"] = spec_grid(d, "civlib", "eci", ("lgdp", "lres_share"))
    g = C["robustness_eci_with_resource_control"]
    print("ROB eci+res: all", fmt(g["pooled_yearFE_all"]), "| autoc", fmt(g["pooled_yearFE_autocracies"]))
    # small states trade more for mechanical reasons; drop countries under 5 million people
    C["robustness_open_exclude_small"] = spec_grid(d[d.pop_pwt >= 5e6], "civlib", "lopen")
    g = C["robustness_open_exclude_small"]
    print("ROB open, pop>=5m: all", fmt(g["pooled_yearFE_all"]), "| autoc", fmt(g["pooled_yearFE_autocracies"]))
    # outliers in autocracies: high complexity but low liberty, cross-section 1990-2016
    cs = d[(d.year >= 1990) & (d.year <= 2016)].groupby("iso").agg(
        name=("name", "first"), eci=("eci", "mean"), lgdp=("lgdp", "mean"), civlib=("civlib", "mean"),
        open=("lopen", "mean"), autoc=("autoc", "mean")).dropna()
    m = smf.ols("civlib ~ lgdp", data=cs).fit(); cs["resid"] = m.resid
    hi = cs[cs.eci > cs.eci.quantile(.66)].sort_values("resid").head(8)
    lo = cs[cs.eci < cs.eci.quantile(.33)].sort_values("resid", ascending=False).head(8)
    C["complex_but_unfree"] = [{"name": r["name"], "eci": round(r.eci, 2), "civlib_resid": round(r.resid, 3)} for _, r in hi.iterrows()]
    C["simple_but_free"] = [{"name": r["name"], "eci": round(r.eci, 2), "civlib_resid": round(r.resid, 3)} for _, r in lo.iterrows()]
    print("complex but unfree", C["complex_but_unfree"])
    R["C"] = C

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, x, lab in [(axes[0], "eci", "Economic complexity (1990-2016 avg)"), (axes[1], "open", "log trade openness (1990-2016 avg)")]:
        au = cs.autoc > .5
        ax.scatter(cs[x][~au], cs.resid[~au], s=16, c="#3a78b5", alpha=.7, label="mostly democratic")
        ax.scatter(cs[x][au], cs.resid[au], s=16, c="#d1495b", alpha=.7, label="mostly autocratic")
        for sub, c, ls in [(cs, "k", "-"), (cs[au], "#d1495b", "--")]:
            mm = smf.ols(f"resid ~ {x}", data=sub).fit()
            xs = np.linspace(cs[x].min(), cs[x].max(), 50)
            ax.plot(xs, mm.params.Intercept + mm.params[x] * xs, c=c, ls=ls)
        for iso in ["SGP", "CHN", "SAU", "VNM", "BWA", "RWA", "USA", "MYS", "KOR", "NOR", "QAT", "BLR"]:
            if iso in cs.index:
                ax.annotate(cs.loc[iso, "name"].replace(" of America", ""), (cs.loc[iso, x], cs.loc[iso, "resid"]), fontsize=7)
        ax.axhline(0, c="grey", lw=.5)
        ax.set_xlabel(lab); ax.set_ylabel("Civil liberties vs. what income predicts")
    axes[0].legend(fontsize=8)
    fig.suptitle("More diversified, more open economies: freer than their income predicts?", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_C_plurality.png"), dpi=150)
    plt.close(fig)
    R["C"]["scatter_points"] = [{"iso": i, "name": r["name"], "eci": round(r.eci, 3), "log_openness": round(r.open, 3),
                                 "civlib_resid": round(r.resid, 3)} for i, r in cs.iterrows()]

# ----------------------------------------------------------------------------- claim D
def claim_D(df, R):
    print("\n=== CLAIM D: long-run curves ===")
    countries = ["USA", "CHN", "GBR", "FRA", "JPN", "RUS", "IND", "BRA", "SAU"]
    D = {"series": {}, "missing": "Union density: no reachable source (OECD/AIAS ICTWSS, ILOSTAT and OWID grapher hosts were blocked by the container's network policy; no GitHub mirror found)."}
    fig, axes = plt.subplots(3, 3, figsize=(14, 11), sharex=True, sharey=True)
    for ax, iso in zip(axes.flat, countries):
        s = df[(df.iso == iso) & (df.year >= 1900)].sort_values("year")
        name = s.name.iloc[0].replace(" of America", "")
        ser = {}
        for col, lab, c, scale in [("civlib", "civil liberties (V-Dem, 0-1)", "#222222", 1),
                                   ("labsh", "labour share of GDP (PWT)", "#3a78b5", .01),
                                   ("bottom50", "bottom-50% income share (WID)", "#2a9d8f", .01),
                                   ("top1", "top-1% income share (WID)", "#d1495b", .01)]:
            t = s[["year", col]].dropna()
            if len(t):
                ax.plot(t.year, t[col] * scale, c=c, lw=1.6, label=lab)
                ser[col] = [[int(a), round(float(b) * scale, 4)] for a, b in t.values]
        D["series"][name] = ser
        ax.set_title(name, fontsize=11)
        ax.set_ylim(0, 1); ax.grid(alpha=.3)
    axes.flat[0].legend(fontsize=7, loc="lower left")
    fig.suptitle("Candidate 'disempowerment curves' 1900-2025 (all as fractions; union density not obtainable here)", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_D_curves.png"), dpi=150)
    plt.close(fig)
    # simple summary: change in each series 1980 -> latest
    summ = {}
    for name, ser in D["series"].items():
        summ[name] = {}
        for k, v in ser.items():
            dd = dict((a, b) for a, b in v)
            y0 = min(dd, key=lambda a: abs(a - 1980)); y1 = max(dd)
            summ[name][k] = {"from_year": y0, "from": dd[y0], "to_year": y1, "to": dd[y1]}
    D["summary_1980_to_latest"] = summ
    for n, v in summ.items():
        print(n, {k: (x["from_year"], x["from"], x["to_year"], x["to"]) for k, x in v.items()})
    R["D"] = D

# ----------------------------------------------------------------------------- main
def compact(o):
    if isinstance(o, dict):
        return {k: compact(v) for k, v in o.items()}
    if isinstance(o, list):
        return [compact(v) for v in o]
    if isinstance(o, float):
        return round(o, 5)
    return o


if __name__ == "__main__":
    df = load_all()
    R = {"data_sources": {
        "V-Dem v16 (vdeminstitute/vdemdata on GitHub)": "civil liberties, regimes, fiscal source, life expectancy, schooling, child mortality, Haber-Menaldo resource income, federalism, foreign movement",
        "Penn World Table 10.0 (OWID mirror on GitHub)": "GDP per capita, growth, labour share, trade openness, government consumption",
        "World Inequality Database pretax income (OWID mirror on GitHub)": "top-1% and bottom-50% shares",
        "OECD Global Revenue Statistics 2018 (OWID mirror)": "tax % GDP",
        "OEC Economic Complexity Index 2016 (OWID mirror)": "ECI",
        "OWID energy-data (GitHub)": "oil and gas production per capita"},
        "blocked_sources": "ourworldindata.org grapher, api.worldbank.org, v-dem.net, freedomhouse.org, wid.world, rug.nl (Maddison/PWT), dataverse.harvard.edu, zenodo.org, OECD, ILOSTAT: all refused by the container's egress proxy (HTTP 403 on CONNECT / no connection). World Bank resource-rent and tax-revenue series (NY.GDP.TOTL.RT.ZS, GC.TAX.TOTL.GD.ZS) therefore NOT used; proxies used instead.",
        "panel_size": {"countries": int(df.iso.nunique()), "years": [int(df.year.min()), int(df.year.max())]}}
    claim_A(df, R)
    claim_B(df, R)
    claim_C(df, R)
    claim_D(df, R)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(compact(R), f, separators=(",", ":"), default=str)
    print("results.json bytes", os.path.getsize(os.path.join(HERE, "results.json")))
