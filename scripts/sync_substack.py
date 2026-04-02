import feedparser
import re
from pathlib import Path

FEED_URL = "https://croissanthology.substack.com/feed"
OUTPUT_DIR = Path("subslop")


def slugify(title):
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug.strip('-')


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    feed = feedparser.parse(FEED_URL)

    for entry in feed.entries:
        title = entry.get('title', 'untitled')
        slug = slugify(title)
        post_dir = OUTPUT_DIR / slug
        filepath = post_dir / "index.html"

        if filepath.exists():
            print(f"skip: {slug}")
            continue

        post_dir.mkdir(exist_ok=True)

        content = entry.get('content', [{}])[0].get('value', '')
        if not content:
            content = entry.get('summary', '')

        link = entry.get('link', 'https://croissanthology.substack.com')

        # Escape quotes in title for YAML front matter
        safe_title = title.replace('"', '\\"')

        html = f"""---
layout: default
title: "{safe_title}"
---

<p style="margin-bottom: 2em;">
  <strong>Croissanthology</strong> &middot;
  <a href="{link}">read on Substack</a>
</p>

<article>
{content}
</article>
"""
        filepath.write_text(html)
        print(f"created: {slug}")


if __name__ == "__main__":
    main()
