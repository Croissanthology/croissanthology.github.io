"""Download raw public datasets into ./raw/ (only GitHub-hosted mirrors were reachable
from the build container; see FINDINGS.md for the list of blocked hosts)."""
import os, sys, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)

OWID = "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/"
def owid(name):
    return OWID + urllib.parse.quote(f"{name}/{name}.csv")

FILES = {
    # V-Dem v16 (country-year, includes Maddison GDP, Haber-Menaldo resource income, life exp., education, FH)
    "vdem.RData": "https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/data/vdem.RData",
    "pwt10.csv": owid("Penn World Table version 10.0"),
    "wid_pretax.csv": owid("World Inequality Database (WID) - Pretax income"),
    "oecd_revenue.csv": owid("Global Revenue Statistics Database - OECD (2018)"),
    "eci.csv": owid("ECI Country Rankings (Observatory of Economic Complexity (2016) and the Atlas of Economic Complexity"),
    "pip.csv": owid("World Bank Poverty and Inequality Platform (PIP)"),
    "owid_energy.csv": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
}

def main(force=False):
    for fn, url in FILES.items():
        dest = os.path.join(RAW, fn)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000 and not force:
            print("have", fn); continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-script"})
            with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
                f.write(r.read())
            print("ok", fn, os.path.getsize(dest))
        except Exception as e:
            print("FAILED", fn, url, repr(e), file=sys.stderr)

if __name__ == "__main__":
    main(force="--force" in sys.argv)
