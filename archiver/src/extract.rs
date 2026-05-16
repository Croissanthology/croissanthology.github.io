use anyhow::Result;
use pulldown_cmark::{Event, Parser, Tag};
use scraper::{Html, Selector};
use std::collections::BTreeSet;
use std::path::Path;
use url::Url;

use crate::config;

pub fn from_markdown(md: &str) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    for event in Parser::new(md) {
        if let Event::Start(Tag::Link { dest_url, .. }) = event {
            if let Some(s) = normalize_outbound(&dest_url) {
                out.insert(s);
            }
        }
    }
    out
}

pub fn from_html(html: &str) -> BTreeSet<String> {
    let doc = Html::parse_document(html);
    let sel = Selector::parse("a[href]").unwrap();
    let mut out = BTreeSet::new();
    for a in doc.select(&sel) {
        if let Some(href) = a.value().attr("href") {
            if let Some(s) = normalize_outbound(href) {
                out.insert(s);
            }
        }
    }
    out
}

fn normalize_outbound(href: &str) -> Option<String> {
    let trimmed = href.trim();
    if trimmed.is_empty()
        || trimmed.starts_with('#')
        || trimmed.starts_with("mailto:")
        || trimmed.starts_with("javascript:")
        || trimmed.starts_with("tel:")
        || trimmed.starts_with("data:")
    {
        return None;
    }
    let u = Url::parse(trimmed).ok()?;
    if !matches!(u.scheme(), "http" | "https") {
        return None;
    }
    let host = u.host_str()?;
    if config::is_own_host(host) {
        return None;
    }
    Some(u.to_string())
}

pub fn from_file(path: &Path) -> Result<BTreeSet<String>> {
    let content = std::fs::read_to_string(path)?;
    let ext = path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .unwrap_or_default();
    Ok(match ext.as_str() {
        "md" | "markdown" => from_markdown(&content),
        _ => from_html(&content),
    })
}
