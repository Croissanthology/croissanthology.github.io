#!/usr/bin/env python3
"""
Alumni Blogroll Generator
Aggregates RSS feeds from camp alumni and generates a static HTML page.
"""

import feedparser
import yaml
from datetime import datetime, timedelta
from typing import List, Dict
import html
import sys


def load_config(config_file: str = "alumni-feeds.yaml") -> Dict:
    """Load the YAML configuration file."""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)


def fetch_feed(feed_url: str, name: str, blog_title: str) -> List[Dict]:
    """Fetch and parse a single RSS feed."""
    print(f"Fetching feed for {name} ({blog_title})...")

    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo:  # feedparser sets bozo=1 if there's a parsing error
            print(f"  Warning: Feed may have parsing issues: {feed_url}")

        posts = []
        for entry in feed.entries:
            # Try to get publication date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])

            # Get description/summary
            description = ""
            if hasattr(entry, 'summary'):
                description = entry.summary
            elif hasattr(entry, 'description'):
                description = entry.description

            # Strip HTML tags from description and truncate
            description = strip_html_tags(description)
            if len(description) > 300:
                description = description[:300] + "..."

            posts.append({
                'title': entry.get('title', 'Untitled'),
                'link': entry.get('link', ''),
                'pub_date': pub_date,
                'description': description,
                'author': name,
                'blog_title': blog_title
            })

        print(f"  Found {len(posts)} posts")
        return posts

    except Exception as e:
        print(f"  Error fetching feed: {e}")
        return []


def strip_html_tags(text: str) -> str:
    """Strip HTML tags from text."""
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Clean up whitespace
    text = ' '.join(text.split())
    return text


def filter_recent_posts(posts: List[Dict], days_back: int) -> List[Dict]:
    """Filter posts to only include those from the last N days."""
    cutoff_date = datetime.now() - timedelta(days=days_back)

    recent_posts = []
    for post in posts:
        if post['pub_date'] and post['pub_date'] >= cutoff_date:
            recent_posts.append(post)

    return recent_posts


def sort_posts_by_date(posts: List[Dict]) -> List[Dict]:
    """Sort posts by publication date, newest first."""
    # Filter out posts without dates
    posts_with_dates = [p for p in posts if p['pub_date']]
    return sorted(posts_with_dates, key=lambda x: x['pub_date'], reverse=True)


def generate_html(posts: List[Dict], config: Dict) -> str:
    """Generate the HTML page."""

    page_config = config.get('config', {})
    page_title = page_config.get('page_title', 'Alumni Blogroll')
    background_image = page_config.get('background_image', 'alsoimages/joan.jpg')
    header_description = page_config.get('header_description', '')

    # Generate post HTML
    posts_html = ""
    current_month = None

    for post in posts:
        # Add month separator
        post_month = post['pub_date'].strftime('%B %Y')
        if post_month != current_month:
            if current_month is not None:
                posts_html += "        </div>\n\n"
            posts_html += f'        <h2>{post_month}</h2>\n'
            posts_html += '        <div class="posts-section">\n'
            current_month = post_month

        date_str = post['pub_date'].strftime('%b %d, %Y')

        posts_html += f'''            <div class="post">
                <div class="post-meta">
                    <span class="post-date">{date_str}</span>
                    <span class="post-author">{html.escape(post['author'])} · {html.escape(post['blog_title'])}</span>
                </div>
                <h3 class="post-title"><a href="{html.escape(post['link'])}" target="_blank">{html.escape(post['title'])}</a></h3>
                <p class="post-description">{html.escape(post['description'])}</p>
            </div>
'''

    if current_month is not None:
        posts_html += "        </div>\n"

    # Generate full HTML
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(page_title)}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            color: white;
            overflow-x: hidden;
            width: 100%;
        }}
        .container {{
            min-height: 100vh;
            width: 100%;
            background: url('{background_image}') center/cover;
            position: relative;
            background-attachment: fixed;
        }}
        .vignette {{
            position: absolute;
            inset: 0;
            background: radial-gradient(circle, transparent 30%, rgba(0,0,0,0.7));
            pointer-events: none;
            position: fixed;
        }}
        .gradient-overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(to bottom, rgba(0,0,0,0.8), rgba(0,0,0,0.6));
            position: fixed;
        }}
        .crt-lines {{
            position: fixed;
            inset: 0;
            background: linear-gradient(transparent 50%, rgba(0,0,0,0.05) 50%);
            background-size: 100% 4px;
            opacity: 0.5;
            pointer-events: none;
        }}
        .crt-flicker {{
            position: fixed;
            inset: 0;
            background: rgba(255,255,255,0.01);
            opacity: 0;
            pointer-events: none;
            animation: flicker 0.15s infinite;
        }}
        @keyframes flicker {{
            0% {{ opacity: 0.1; }}
            50% {{ opacity: 0; }}
            100% {{ opacity: 0.1; }}
        }}
        .content {{
            position: relative;
            z-index: 10;
            max-width: 48rem;
            margin: 0 auto;
            padding: 2rem;
        }}
        .header {{
            margin-bottom: 3rem;
        }}
        .date {{
            opacity: 0.6;
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }}
        h1 {{
            font-size: 2.5rem;
            margin: 0;
            font-weight: 500;
        }}
        .header-description {{
            font-size: 1.2rem;
            opacity: 0.8;
            margin-top: 0.5rem;
        }}
        h2 {{
            font-size: 1.8rem;
            margin: 2.5rem 0 1rem;
            font-weight: 500;
            border-bottom: 1px dotted rgba(255,255,255,0.3);
            padding-bottom: 0.5rem;
        }}
        .posts-section {{
            margin-bottom: 2rem;
        }}
        .post {{
            margin: 1.5rem 0;
            padding: 1.5rem;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 4px;
            border-left: 3px solid #FF8A3C;
        }}
        .post-meta {{
            font-size: 0.95rem;
            opacity: 0.7;
            margin-bottom: 0.5rem;
        }}
        .post-date {{
            margin-right: 1rem;
        }}
        .post-author {{
            font-style: italic;
        }}
        .post-title {{
            font-size: 1.4rem;
            margin: 0.5rem 0;
            font-weight: 500;
        }}
        .post-title a {{
            color: #FF8A3C;
            text-decoration: none;
        }}
        .post-title a:hover {{
            color: #FF9F5B;
        }}
        .post-description {{
            margin: 0.75rem 0 0 0;
            line-height: 1.5;
            opacity: 0.9;
        }}
        .footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px dotted rgba(255,255,255,0.3);
            font-size: 1rem;
            opacity: 0.6;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="vignette"></div>
        <div class="gradient-overlay"></div>
        <div class="crt-lines"></div>
        <div class="crt-flicker"></div>

        <div class="content">
            <div class="header">
                <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
                <h1>{html.escape(page_title)}</h1>
                {f'<div class="header-description">{html.escape(header_description)}</div>' if header_description else ''}
            </div>

{posts_html}

            <div class="footer">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')} · {len(posts)} posts from {page_config.get('days_back', 60)} days
            </div>
        </div>
    </div>
</body>
</html>'''

    return html_template


def main():
    """Main function."""
    print("=== Alumni Blogroll Generator ===\n")

    # Load configuration
    config = load_config()
    feeds = config.get('feeds', [])
    page_config = config.get('config', {})

    days_back = page_config.get('days_back', 60)
    output_file = page_config.get('output_file', 'alumni-blogroll.html')

    print(f"Configuration loaded: {len(feeds)} feeds, {days_back} days lookback\n")

    # Fetch all feeds
    all_posts = []
    for feed_info in feeds:
        name = feed_info.get('name', 'Unknown')
        blog_title = feed_info.get('blog_title', 'Blog')
        feed_url = feed_info.get('feed_url', '')

        if not feed_url:
            print(f"Warning: No feed URL for {name}, skipping...")
            continue

        posts = fetch_feed(feed_url, name, blog_title)
        all_posts.extend(posts)

    print(f"\nTotal posts fetched: {len(all_posts)}")

    # Filter to recent posts
    recent_posts = filter_recent_posts(all_posts, days_back)
    print(f"Posts from last {days_back} days: {len(recent_posts)}")

    # Sort by date
    sorted_posts = sort_posts_by_date(recent_posts)

    # Generate HTML
    print(f"\nGenerating HTML...")
    html_output = generate_html(sorted_posts, config)

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"✓ Blogroll generated: {output_file}")
    print(f"  {len(sorted_posts)} posts included")


if __name__ == "__main__":
    main()
