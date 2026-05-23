use anyhow::{anyhow, Context, Result};
use reqwest::blocking::Client;
use std::time::Duration;

pub fn client() -> Client {
    Client::builder()
        .user_agent(
            "Mozilla/5.0 (compatible; croissanthology-archiver/0.1; +https://croissanthology.com)",
        )
        .timeout(Duration::from_secs(120))
        .redirect(reqwest::redirect::Policy::limited(20))
        .build()
        .expect("build reqwest client")
}

pub fn submit_wayback(url: &str) -> Result<String> {
    let c = client();
    let resp = c
        .get(format!("https://web.archive.org/save/{}", url))
        .header("Accept", "text/html")
        .send()
        .context("wayback save request")?;
    let final_url = resp.url().to_string();
    if final_url.contains("web.archive.org/web/") {
        return Ok(final_url);
    }
    if let Some(loc) = resp.headers().get("content-location").and_then(|v| v.to_str().ok()) {
        return Ok(format!("https://web.archive.org{}", loc));
    }
    if let Some(loc) = resp.headers().get("location").and_then(|v| v.to_str().ok()) {
        if loc.starts_with("http") {
            return Ok(loc.to_string());
        }
        return Ok(format!("https://web.archive.org{}", loc));
    }
    Err(anyhow!("wayback returned no snapshot URL (status {})", resp.status()))
}

pub fn submit_archive_is(url: &str) -> Result<String> {
    let c = client();
    let resp = c
        .post("https://archive.ph/submit/")
        .form(&[("url", url), ("anyway", "1")])
        .send()
        .context("archive.is submit")?;
    if let Some(refresh) = resp.headers().get("refresh").and_then(|v| v.to_str().ok()) {
        let lower = refresh.to_lowercase();
        if let Some(idx) = lower.find("url=") {
            return Ok(refresh[idx + 4..].trim().to_string());
        }
    }
    if let Some(loc) = resp.headers().get("location").and_then(|v| v.to_str().ok()) {
        if loc.starts_with("http") {
            return Ok(loc.to_string());
        }
    }
    let final_url = resp.url().to_string();
    if is_archive_is_snapshot(&final_url) {
        return Ok(final_url);
    }
    Err(anyhow!(
        "archive.is returned no snapshot URL (status {}, landed at {})",
        resp.status(),
        final_url
    ))
}

/// True iff `url` looks like an archive.ph / archive.is snapshot — host matches
/// and path is not the bare submit endpoint. archive.ph snapshot paths look
/// like `/abc12` or `/2026/01/01/...`. `/submit/` and `/` itself don't count.
fn is_archive_is_snapshot(url: &str) -> bool {
    let Ok(parsed) = url::Url::parse(url) else {
        return false;
    };
    let Some(host) = parsed.host_str() else {
        return false;
    };
    let host_matches = host.ends_with("archive.ph")
        || host.ends_with("archive.is")
        || host.ends_with("archive.today");
    if !host_matches {
        return false;
    }
    let path = parsed.path();
    path != "/" && !path.starts_with("/submit")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn snapshot_url_accepted() {
        assert!(is_archive_is_snapshot("https://archive.ph/abc12"));
        assert!(is_archive_is_snapshot("https://archive.is/2026/x"));
    }

    #[test]
    fn submit_endpoint_rejected() {
        // This was the bug: the submit landing page was claimed as a snapshot.
        assert!(!is_archive_is_snapshot("https://archive.ph/submit/"));
        assert!(!is_archive_is_snapshot("https://archive.ph/submit"));
    }

    #[test]
    fn bare_host_rejected() {
        assert!(!is_archive_is_snapshot("https://archive.ph/"));
    }

    #[test]
    fn other_hosts_rejected() {
        assert!(!is_archive_is_snapshot("https://example.com/abc"));
    }
}
