use anyhow::Result;
use std::fs;
use std::path::Path;

use crate::config;
use crate::state::State;

pub struct RehostReport {
    pub rewritten: Vec<(String, String)>,    // (source_post, dead_url)
    pub substack_pending: Vec<(String, String, String)>, // (post_path, dead_url, archive_url)
    pub skipped: Vec<String>,
}

pub fn rehost_dead(state: &mut State) -> Result<RehostReport> {
    let repo = config::repo_root();
    let mut report = RehostReport {
        rewritten: vec![],
        substack_pending: vec![],
        skipped: vec![],
    };

    let keys: Vec<String> = state.archives.keys().cloned().collect();
    for k in keys {
        let entry = state.archives.get_mut(&k).unwrap();
        if !entry.dead {
            continue;
        }
        let Some(local_rel) = entry.local_path.clone() else {
            report
                .skipped
                .push(format!("no local copy: {}", entry.canonical_url));
            continue;
        };
        let local_abs = repo.join(&local_rel);
        if !local_abs.exists() {
            report
                .skipped
                .push(format!("local copy missing on disk: {}", local_rel));
            continue;
        }

        let archive_url = format!("/{}", local_rel.trim_start_matches('/'));

        for src in entry.source_posts.clone() {
            let src_abs = repo.join(&src);
            if !src_abs.exists() {
                continue;
            }
            if src.contains("subslop/") || src.contains("subslop\\") {
                let post_slug = std::path::Path::new(&src)
                    .parent()
                    .and_then(|p| p.file_name())
                    .and_then(|n| n.to_str())
                    .unwrap_or("")
                    .to_string();
                let pub_url = format!(
                    "https://croissanthology.substack.com/p/{}",
                    post_slug
                );
                let archive_public =
                    format!("{}{}", config::SITE_ORIGIN, archive_url);
                report.substack_pending.push((
                    pub_url,
                    entry.canonical_url.clone(),
                    archive_public,
                ));
                continue;
            }
            if rewrite_post(&src_abs, &entry.canonical_url, &archive_url)? {
                report
                    .rewritten
                    .push((src.clone(), entry.canonical_url.clone()));
            }
        }
        entry.rehosted = true;
    }

    Ok(report)
}

/// Append a small `[archived]` link next to every occurrence of `dead_url`
/// in the markdown/html post. Returns true if anything changed.
fn rewrite_post(path: &Path, dead_url: &str, archive_url: &str) -> Result<bool> {
    let original = fs::read_to_string(path)?;
    let ext = path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .unwrap_or_default();

    let updated = match ext.as_str() {
        "md" | "markdown" => rewrite_markdown(&original, dead_url, archive_url),
        _ => rewrite_html(&original, dead_url, archive_url),
    };

    if updated != original {
        fs::write(path, updated)?;
        Ok(true)
    } else {
        Ok(false)
    }
}

fn rewrite_markdown(content: &str, dead_url: &str, archive_url: &str) -> String {
    let needle = format!("]({})", dead_url);
    let marker = format!("]({}) [[archived]]({})", dead_url, archive_url);
    if content.contains(&format!("[[archived]]({})", archive_url)) {
        return content.to_string();
    }
    content.replace(&needle, &marker)
}

fn rewrite_html(content: &str, dead_url: &str, archive_url: &str) -> String {
    let marker = format!(
        r#" <a class="archiver-rehost" href="{}" title="local archive of dead link">[archived]</a>"#,
        archive_url
    );
    if content.contains(&marker) {
        return content.to_string();
    }
    // Conservative replacement: only patch anchors whose href exactly matches dead_url,
    // appending the marker right after their closing </a>.
    let patterns = [
        format!(r#"href="{}""#, dead_url),
        format!(r#"href='{}'"#, dead_url),
    ];
    let mut out = content.to_string();
    for pat in &patterns {
        if !out.contains(pat.as_str()) {
            continue;
        }
        let mut rebuilt = String::with_capacity(out.len() + 256);
        let mut cursor = 0;
        while let Some(pos) = out[cursor..].find(pat.as_str()) {
            let abs_pos = cursor + pos;
            // find the </a> after the matched href
            if let Some(close_rel) = out[abs_pos..].find("</a>") {
                let close_abs = abs_pos + close_rel + "</a>".len();
                rebuilt.push_str(&out[cursor..close_abs]);
                rebuilt.push_str(&marker);
                cursor = close_abs;
            } else {
                rebuilt.push_str(&out[cursor..]);
                cursor = out.len();
                break;
            }
        }
        rebuilt.push_str(&out[cursor..]);
        out = rebuilt;
    }
    out
}
