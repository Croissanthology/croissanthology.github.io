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
    if final_url.contains("archive.ph") || final_url.contains("archive.is") {
        return Ok(final_url);
    }
    Err(anyhow!("archive.is returned no archive URL (status {})", resp.status()))
}
