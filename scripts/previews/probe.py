"""Temporary: asks a few public endpoints what they send, so the indexer can be written against the truth."""
import json, os, subprocess, sys
import requests
UA = "croissanthology-link-previews/1.0 (+https://croissanthology.com)"
s = requests.Session(); s.headers["User-Agent"] = UA
out = "probe-out"; os.makedirs(out, exist_ok=True)

def show(label, url, save=None, **kw):
    try:
        r = s.get(url, timeout=20, **kw)
    except Exception as e:
        print(f"## {label}: ERROR {e!r}"); return None
    h = {k.lower(): v for k, v in r.headers.items()}
    keep = {k: h[k][:300] for k in ("content-type", "x-frame-options", "content-security-policy", "access-control-allow-origin", "x-robots-tag", "content-length") if k in h}
    print(f"## {label}: {r.status_code} {url}\n   {json.dumps(keep)}\n   body[:300]={r.text[:300]!r}")
    if save:
        open(f"{out}/{save}", "w").write(r.text)
    return r

def token(i):
    return subprocess.run(["node", "-e", f"console.log(((Number('{i}')/1e15)*Math.PI).toString(36).replace(/(0+|\\.)/g,''))"], capture_output=True, text=True).stdout.strip()

for tid in ("2119399591602753703", "2110395820537217372", "1766196118420148430", "1989854621532369121", "2014756695021650241"):
    t = token(tid)
    show(f"tweet {tid} token={t}", f"https://cdn.syndication.twimg.com/tweet-result?id={tid}&token={t}&lang=en", save=f"tweet-{tid}.json")
show("tweet fixed token", "https://cdn.syndication.twimg.com/tweet-result?id=2119399591602753703&token=a&lang=en")
show("tweet robots", "https://cdn.syndication.twimg.com/robots.txt")
show("profile timeline", "https://syndication.twitter.com/srv/timeline-profile/screen-name/gwern", save="profile-gwern.html")
show("profile oembed", "https://publish.twitter.com/oembed?url=https://twitter.com/gwern&omit_script=1", save="profile-oembed.json")
show("profile follow info", "https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names=gwern")
show("profile page", "https://x.com/gwern")
show("x robots", "https://x.com/robots.txt")
for u in ("https://www.astralcodexten.com/p/against-against-handover", "https://www.theargumentmag.com/p/against-the-smartphone-theory-of", "https://importai.substack.com/p/import-ai-476-creativity-and-rsi", "https://thezvi.substack.com/p/claude-opus-45-is-the-best-model"):
    show("substack page", u)
show("substack api", "https://www.astralcodexten.com/api/v1/posts/against-against-handover", headers={"Origin": "https://croissanthology.com"}, save="substack-post.json")
show("substack robots", "https://www.astralcodexten.com/robots.txt", save="substack-robots.txt")
show("substack embed", "https://www.astralcodexten.com/embed/p/against-against-handover")
show("wiki html", "https://en.wikipedia.org/api/rest_v1/page/html/Toy_Story", headers={"Origin": "https://croissanthology.com"}, save="wiki-Toy_Story.html")
show("wiki html 2", "https://en.wikipedia.org/api/rest_v1/page/html/AT_Protocol", headers={"Origin": "https://croissanthology.com"}, save="wiki-AT_Protocol.html")
show("wiki html redirect", "https://en.wikipedia.org/api/rest_v1/page/html/Mona_Lisa_(painting)?redirect=true", headers={"Origin": "https://croissanthology.com"})
show("lesswrong", "https://www.lesswrong.com/posts/YoFLDnAmMoFj76HPN/preview-on-hover")
