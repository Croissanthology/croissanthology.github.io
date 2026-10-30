//! Local copies of Bluesky posts.
//!
//! bsky.app is a JavaScript app, so monolith only ever saves an empty shell. Bluesky publishes
//! every post through its open AppView API (no account needed), so for a bsky.app post URL we
//! ask that API for the post and write a small self-contained page instead: author, text, date,
//! images (downloaded next to the page), a quoted post if there is one, and a link card.

use anyhow::{anyhow, Context, Result};
use serde_json::Value;
use std::fs;
use std::path::Path;

use crate::archive;

const API: &str = "https://public.api.bsky.app/xrpc";

/// (actor, rkey) for https://bsky.app/profile/<actor>/post/<rkey>
pub fn parse_post_url(url: &str) -> Option<(String, String)> {
    let parsed = url::Url::parse(url).ok()?;
    let host = parsed.host_str()?.to_lowercase();
    if host != "bsky.app" && host != "www.bsky.app" {
        return None;
    }
    let parts: Vec<&str> = parsed.path().trim_matches('/').split('/').collect();
    if parts.len() >= 4 && parts[0] == "profile" && parts[2] == "post" && !parts[1].is_empty() && !parts[3].is_empty() {
        return Some((parts[1].to_string(), parts[3].to_string()));
    }
    None
}

pub fn is_post_url(url: &str) -> bool {
    parse_post_url(url).is_some()
}

fn get_json(path: &str) -> Result<Value> {
    let resp = archive::client()
        .get(format!("{}/{}", API, path))
        .send()
        .with_context(|| format!("fetch {}", path))?;
    if !resp.status().is_success() {
        return Err(anyhow!("bluesky api returned {}", resp.status()));
    }
    let text = resp.text()?;
    Ok(serde_json::from_str(&text)?)
}

fn resolve_did(actor: &str) -> Result<String> {
    if actor.starts_with("did:") {
        return Ok(actor.to_string());
    }
    let v = get_json(&format!("com.atproto.identity.resolveHandle?handle={}", actor))?;
    v["did"]
        .as_str()
        .map(str::to_string)
        .ok_or_else(|| anyhow!("could not resolve handle {}", actor))
}

/// Save a local copy of a bsky.app post to `dest` (an index.html path).
pub fn save_post(url: &str, dest: &Path) -> Result<()> {
    let (actor, rkey) = parse_post_url(url).ok_or_else(|| anyhow!("not a bluesky post url"))?;
    let did = resolve_did(&actor)?;
    let uri = format!("at://{}/app.bsky.feed.post/{}", did, rkey);
    let thread = get_json(&format!(
        "app.bsky.feed.getPostThread?uri={}&depth=0&parentHeight=0",
        urlencode(&uri)
    ))?;
    let post = &thread["thread"]["post"];
    if post.is_null() {
        return Err(anyhow!("bluesky returned no post (deleted or blocked?)"));
    }
    let dir = dest.parent().ok_or_else(|| anyhow!("bad destination"))?;
    fs::create_dir_all(dir)?;
    let mut n = 0;
    let mut download = |remote: &str| -> Option<String> {
        let bytes = archive::client().get(remote).send().ok()?.bytes().ok()?;
        n += 1;
        let name = format!("image-{}.jpg", n);
        fs::write(dir.join(&name), &bytes).ok()?;
        Some(name)
    };
    let html = render_page(url, post, &mut download);
    fs::write(dest, html)?;
    Ok(())
}

/// Turn one post view (from getPostThread) into a standalone HTML page.
/// `download` fetches an image and returns its local file name.
pub fn render_page(url: &str, post: &Value, download: &mut dyn FnMut(&str) -> Option<String>) -> String {
    let author = &post["author"];
    let name = author["displayName"].as_str().filter(|s| !s.is_empty())
        .or_else(|| author["handle"].as_str()).unwrap_or("");
    let handle = author["handle"].as_str().unwrap_or("");
    let text = post["record"]["text"].as_str().unwrap_or("");
    let created = post["record"]["createdAt"].as_str().unwrap_or("");
    let date = created.get(..10).unwrap_or(created);

    let mut body = String::new();
    body.push_str(&format!(
        "<p class=\"who\"><strong>{}</strong> <span>@{}</span></p>\n<p class=\"text\">{}</p>\n",
        esc(name), esc(handle), esc(text).replace('\n', "<br>")
    ));
    body.push_str(&render_embed(&post["embed"], download));
    body.push_str(&format!(
        "<p class=\"meta\">Posted {} on Bluesky · <a href=\"{}\">original</a> · saved by croissanthology.com's archiver</p>\n",
        esc(date), esc(url)
    ));

    format!(
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\
<title>{} on Bluesky: {}</title>\
<style>body{{font:17px/1.5 -apple-system,Helvetica,Arial,sans-serif;max-width:36rem;margin:2rem auto;padding:0 1rem;color:#1b1b1f;background:#fff}}\
.who span,.meta{{color:#6b6b76}}.meta{{font-size:.85rem;margin-top:1.5rem}}\
img{{max-width:100%;height:auto;border-radius:8px;display:block;margin:.6rem 0}}\
blockquote{{margin:1rem 0;padding:.6rem .9rem;border:1px solid #ddd;border-radius:10px}}\
.card{{display:block;margin:1rem 0;padding:.6rem .9rem;border:1px solid #ddd;border-radius:10px;color:inherit}}</style>\
</head><body>\n{}</body></html>\n",
        esc(name),
        esc(&text.chars().take(80).collect::<String>()),
        body
    )
}

fn render_embed(embed: &Value, download: &mut dyn FnMut(&str) -> Option<String>) -> String {
    let mut out = String::new();
    if embed.is_null() {
        return out;
    }
    if let Some(images) = embed["images"].as_array() {
        for img in images {
            let remote = img["fullsize"].as_str().or_else(|| img["thumb"].as_str()).unwrap_or("");
            let alt = img["alt"].as_str().unwrap_or("");
            let src = download(remote).unwrap_or_else(|| remote.to_string());
            out.push_str(&format!("<img src=\"{}\" alt=\"{}\">\n", esc(&src), esc(alt)));
        }
    }
    let ext = &embed["external"];
    if ext.is_object() {
        out.push_str(&format!(
            "<a class=\"card\" href=\"{}\"><strong>{}</strong><br>{}</a>\n",
            esc(ext["uri"].as_str().unwrap_or("")),
            esc(ext["title"].as_str().unwrap_or("")),
            esc(ext["description"].as_str().unwrap_or(""))
        ));
    }
    // a quoted post: embed.record (view) or embed.record.record (recordWithMedia)
    let rec = if embed["record"]["record"].is_object() && embed["record"]["record"]["author"].is_object() {
        &embed["record"]["record"]
    } else {
        &embed["record"]
    };
    if rec["author"].is_object() {
        let qa = &rec["author"];
        let qt = rec["value"]["text"].as_str().unwrap_or("");
        out.push_str(&format!(
            "<blockquote><p class=\"who\"><strong>{}</strong> <span>@{}</span></p><p>{}</p></blockquote>\n",
            esc(qa["displayName"].as_str().unwrap_or("")),
            esc(qa["handle"].as_str().unwrap_or("")),
            esc(qt).replace('\n', "<br>")
        ));
    }
    if embed["media"].is_object() {
        out.push_str(&render_embed(&embed["media"], download));
    }
    out
}

fn esc(s: &str) -> String {
    s.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;").replace('"', "&quot;")
}

fn urlencode(s: &str) -> String {
    url::form_urlencoded::byte_serialize(s.as_bytes()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn parses_post_urls() {
        assert_eq!(
            parse_post_url("https://bsky.app/profile/minimaxir.bsky.social/post/3myhzaeul422m"),
            Some(("minimaxir.bsky.social".into(), "3myhzaeul422m".into()))
        );
        assert_eq!(
            parse_post_url("https://bsky.app/profile/did:plc:abc/post/xyz?ref=1"),
            Some(("did:plc:abc".into(), "xyz".into()))
        );
        assert!(parse_post_url("https://bsky.app/profile/someone").is_none());
        assert!(parse_post_url("https://example.com/profile/a/post/b").is_none());
    }

    #[test]
    fn renders_text_images_and_quote() {
        let post = json!({
            "author": {"handle": "lefttheprairie.bsky.social", "displayName": "Emily"},
            "record": {"text": "We all gathered around\nto bully a <robot>", "createdAt": "2026-02-16T00:06:33.410Z"},
            "embed": {
                "$type": "app.bsky.embed.recordWithMedia#view",
                "media": {"images": [{"fullsize": "https://cdn.bsky.app/a.jpg", "alt": "robot"}]},
                "record": {"record": {"author": {"handle": "q.bsky.social", "displayName": "Q"},
                                      "value": {"text": "quoted"}}}
            }
        });
        let mut fetched = vec![];
        let html = render_page("https://bsky.app/profile/x/post/y", &post, &mut |u| {
            fetched.push(u.to_string());
            Some("image-1.jpg".into())
        });
        assert!(html.contains("We all gathered around<br>to bully a &lt;robot&gt;"));
        assert!(html.contains("<img src=\"image-1.jpg\" alt=\"robot\">"));
        assert!(html.contains("<blockquote>"));
        assert!(html.contains("2026-02-16"));
        assert_eq!(fetched, vec!["https://cdn.bsky.app/a.jpg".to_string()]);
    }
}
