# archiver 🐾

Personal web archiver for croissanthology. Captures every outbound link you
care about three ways — local self-contained HTML copy, Internet Archive,
archive.is — and once a month checks them all for rot. When a link dies,
the local copy gets surfaced on croissanthology.com (and you get an email
listing dead links inside Substack posts so you can patch those manually).

Inspired by https://gwern.net/archiving.

## Install on the MacBook

```sh
# in this repo
cd archiver
cargo build --release

# install monolith (the actual page-saver — does the single-file HTML magic)
brew install monolith

# put the binary on your PATH so `archiver` works from anywhere
ln -s "$PWD/target/release/archiver" /usr/local/bin/archiver
```

Then drop your Gmail SMTP creds into `~/.archiver.env`:

```sh
export ARCHIVER_SMTP_USER="margotwarrenbancquart@gmail.com"
export ARCHIVER_SMTP_PASS="abcd efgh ijkl mnop"   # Gmail app password
```

(Get an app password at https://myaccount.google.com/apppasswords.)

## Daily use

Just type:

```sh
archiver
```

Cat appears. Paste a URL. Done.

If the page is paywalled, append `/paywall` to the URL when prompted —
archiver will try 12ft.io → archive.is render → Googlebot UA in order.

Other commands:

| command | what it does |
| --- | --- |
| `archiver` | interactive prompt with cute cat |
| `archiver add <url>` | archive a single URL |
| `archiver add --paywall <url>` | …with bypass chain |
| `archiver post <url>` | if `<url>` is one of your own posts, archive every outbound link on it |
| `archiver scan` | walk every post in this repo + `subslop/`, archive every link not yet captured |
| `archiver check` | run a link-rot check on everything archived |
| `archiver rehost` | for dead links: rewrite source posts to add `[archived]`, queue Substack notices |
| `archiver maintain` | the full monthly pass — what launchd runs |
| `archiver list` | show what's archived and its status |

Pasting a croissanthology.com or croissanthology.substack.com URL is treated
as `archiver post <url>` — it fetches the post and archives every outbound link.

## First-run bulk archive

After you install, run once:

```sh
archiver scan
```

This walks `_posts/`, the root `.html` posts, and `subslop/` (your Substack
mirror), pulls out every outbound link, and archives the ones not yet
captured. Expect this to take a while the first time and to be approximately
free thereafter.

## Monthly automation (launchd)

```sh
# substitute your actual path
sed -i '' "s|REPLACE_ME_REPO_PATH|$PWD/..|g" launchd/com.croissanthology.archiver.plist

cp launchd/com.croissanthology.archiver.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.croissanthology.archiver.plist
```

This runs `archiver maintain` at 09:00 on the 1st of every month: check
every link, rehost dead ones, email about dead Substack links, commit the
result, push.

To trigger a one-off run without waiting:

```sh
launchctl start com.croissanthology.archiver
tail -f archiver/launchd/maintain.log
```

To uninstall:

```sh
launchctl unload ~/Library/LaunchAgents/com.croissanthology.archiver.plist
```

## Where things live

- `archiver/src/` — Rust source
- `archive/<slug>/index.html` — local copies (served by GitHub Pages at `croissanthology.com/archive/<slug>/`)
- `.archiver/index.json` — state: every known URL, its three archive locations, check history, dead/rehost flags
- `archiver/launchd/` — the macOS scheduler config + log

## Design notes

- A link is considered **dead** only after 3 consecutive failures with HTTP 404/410/451 or a DNS NXDOMAIN. 5xx, timeouts, network errors, and 401/403 are treated as transient and retried next month — never trigger a rehost.
- Tracking params (`utm_*`, `fbclid`, `gclid`, …) are stripped before archiving so the same article shared by two people doesn't get archived twice.
- Rehost rewrites in markdown posts add a `[[archived]](/archive/<slug>/)` link next to the dead one — original stays visible, archived copy is a sibling. HTML posts get the same `[archived]` anchor inserted after the dead `</a>`.
- Substack posts can't be auto-edited, so dead links inside them go into a monthly email.
- Your own domains (croissanthology.com, .substack.com, .github.io) are excluded from outbound-link extraction.

## Configuration

Edit `src/config.rs` if you ever want to change:

- `OWN_DOMAINS` — what counts as "your own site" (skipped during extraction)
- `NOTIFY_EMAIL` — where the monthly Substack-dead emails go
- `SITE_ORIGIN` — public URL prefix used in those emails
