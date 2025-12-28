# Alumni Blogroll Generator

An RSS aggregator that creates a beautiful static HTML page displaying recent blog posts from your camp alumni. Inspired by [inkhaven.blog](https://inkhaven.blog).

## Features

- 📡 Aggregates RSS feeds from multiple blogs
- 📅 Filters posts from the last 60 days (configurable)
- 🎨 Beautiful CRT-inspired aesthetic matching your site design
- 📝 Groups posts by month
- 🔄 Auto-regenerates via GitHub Actions (optional)
- 🚀 Pure static HTML - no server required

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Feeds

Edit `alumni-feeds.yaml` and add your alumni's RSS feeds:

```yaml
feeds:
  - name: "Alice Chen"
    blog_title: "Thoughts on AI"
    feed_url: "https://alice.substack.com/feed"

  - name: "Bob Smith"
    blog_title: "Writing from Nowhere"
    feed_url: "https://bobsmith.com/rss"

config:
  days_back: 60
  output_file: "alumni-blogroll.html"
  page_title: "Camp Alumni Blogroll"
  background_image: "alsoimages/joan.jpg"
  header_description: "Recent posts from our camp alumni"
```

### 3. Generate the Blogroll

```bash
python generate-blogroll.py
```

This will create `alumni-blogroll.html` with all recent posts from your configured feeds.

### 4. Deploy

Just commit and push the generated HTML file. It's a static page that works anywhere.

## Getting RSS Feeds from Alumni

Most blogging platforms have RSS by default:

- **Substack**: `https://username.substack.com/feed`
- **Ghost**: `https://blog.com/rss/`
- **WordPress**: `https://blog.com/feed/`
- **Medium**: `https://medium.com/@username/feed`

For custom sites without RSS, you can help them add a feed.xml file. It's usually just 20-30 lines of code.

## Auto-Regeneration with GitHub Actions

The included GitHub Action (`.github/workflows/update-blogroll.yml`) automatically regenerates the blogroll every 6 hours.

**To enable:**

1. The workflow is already configured
2. Ensure `alumni-feeds.yaml` is committed
3. GitHub Actions will run automatically

**To disable:**

Remove or comment out the schedule in `.github/workflows/update-blogroll.yml`.

## Configuration Options

### `alumni-feeds.yaml`

**Feeds:**
- `name`: Author's name
- `blog_title`: Title of their blog
- `feed_url`: RSS feed URL

**Config:**
- `days_back`: How many days back to fetch posts (default: 60)
- `output_file`: Output HTML filename (default: "alumni-blogroll.html")
- `page_title`: Title shown on the page
- `background_image`: Path to background image
- `header_description`: Optional description below title

## Customizing the Style

The generated HTML uses the same aesthetic as your site:
- Fixed background with vignette effect
- CRT scan lines and flicker
- Inter font
- Orange accent links (#FF8A3C)

To customize, edit the CSS in `generate-blogroll.py` (look for the `html_template` variable).

## Troubleshooting

**"No posts found"**
- Check that the RSS feed URL is correct
- Some feeds may be slow to respond
- Try visiting the feed URL in your browser to verify it works

**"Feed may have parsing issues"**
- The feed might have minor XML issues but usually still works
- Check the output to see if posts were still fetched

**"Config file not found"**
- Ensure `alumni-feeds.yaml` exists in the same directory
- Check the filename spelling

## Manual Regeneration

You can manually regenerate anytime:

```bash
python generate-blogroll.py
```

The script will:
1. Fetch all configured RSS feeds
2. Filter posts from the last N days
3. Sort by publication date (newest first)
4. Generate a fresh HTML file

## Newsletter Workflow

Once set up, your newsletter workflow becomes:

1. Open `alumni-blogroll.html` (auto-generated every 6 hours)
2. Scan recent posts since your last newsletter
3. Pick the interesting ones
4. Write your newsletter with links and commentary

The ratio of hunting-for-posts to curating-and-writing shifts from 10:1 to 1:10. 🎯

## Advanced: Feed-of-Feeds

Want to let people subscribe to your aggregator via RSS? You could extend the script to generate an RSS feed of the aggregated posts. This creates a "meta-feed" that people can subscribe to.

## License

Do whatever you want with this. It's yours.
