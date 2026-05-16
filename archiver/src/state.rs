use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;
use url::Url;

#[derive(Serialize, Deserialize, Debug)]
pub struct State {
    pub version: u32,
    #[serde(default)]
    pub archives: BTreeMap<String, Entry>,
}

impl Default for State {
    fn default() -> Self {
        Self { version: 1, archives: BTreeMap::new() }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Entry {
    pub url: String,
    pub canonical_url: String,
    pub slug: String,
    pub first_archived_at: DateTime<Utc>,
    #[serde(default)]
    pub local_path: Option<String>,
    #[serde(default)]
    pub wayback_url: Option<String>,
    #[serde(default)]
    pub archive_is_url: Option<String>,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub paywalled: bool,
    #[serde(default)]
    pub source_posts: Vec<String>,
    #[serde(default)]
    pub checks: Vec<Check>,
    #[serde(default)]
    pub dead: bool,
    #[serde(default)]
    pub rehosted: bool,
    #[serde(default)]
    pub notified: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Check {
    pub at: DateTime<Utc>,
    pub status: CheckStatus,
    #[serde(default)]
    pub http: Option<u16>,
    #[serde(default)]
    pub note: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
pub enum CheckStatus {
    Ok,
    Dead,
    Transient,
    Unknown,
}

impl State {
    pub fn load(path: &Path) -> Result<Self> {
        if !path.exists() {
            return Ok(Self::default());
        }
        let s = fs::read_to_string(path).context("read state file")?;
        if s.trim().is_empty() {
            return Ok(Self::default());
        }
        serde_json::from_str(&s).context("parse state file")
    }

    pub fn save(&self, path: &Path) -> Result<()> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).context("create state dir")?;
        }
        let s = serde_json::to_string_pretty(self)?;
        fs::write(path, s).context("write state file")?;
        Ok(())
    }

    pub fn upsert(&mut self, url: &str) -> Result<&mut Entry> {
        let canon = canonicalize(url)?;
        if !self.archives.contains_key(&canon) {
            let slug = make_slug(&canon);
            let entry = Entry {
                url: url.to_string(),
                canonical_url: canon.clone(),
                slug,
                first_archived_at: Utc::now(),
                local_path: None,
                wayback_url: None,
                archive_is_url: None,
                title: None,
                paywalled: false,
                source_posts: vec![],
                checks: vec![],
                dead: false,
                rehosted: false,
                notified: false,
            };
            self.archives.insert(canon.clone(), entry);
        }
        Ok(self.archives.get_mut(&canon).unwrap())
    }
}

pub fn canonicalize(input: &str) -> Result<String> {
    let mut u = Url::parse(input).context("parse url")?;
    u.set_fragment(None);
    let pairs: Vec<(String, String)> = u
        .query_pairs()
        .filter(|(k, _)| !is_tracking_param(k))
        .map(|(k, v)| (k.into_owned(), v.into_owned()))
        .collect();
    if pairs.is_empty() {
        u.set_query(None);
    } else {
        let mut q = u.query_pairs_mut();
        q.clear();
        for (k, v) in &pairs {
            q.append_pair(k, v);
        }
        drop(q);
    }
    if let Some(host) = u.host_str().map(|s| s.to_lowercase()) {
        let _ = u.set_host(Some(&host));
    }
    Ok(u.to_string())
}

fn is_tracking_param(k: &str) -> bool {
    matches!(
        k,
        "utm_source"
            | "utm_medium"
            | "utm_campaign"
            | "utm_term"
            | "utm_content"
            | "fbclid"
            | "gclid"
            | "ref"
            | "ref_src"
            | "ref_url"
            | "mc_cid"
            | "mc_eid"
            | "_hsenc"
            | "_hsmi"
    )
}

pub fn make_slug(url: &str) -> String {
    let parsed = Url::parse(url).ok();
    let host = parsed
        .as_ref()
        .and_then(|u| u.host_str())
        .unwrap_or("unknown")
        .to_string();
    let path_seg = parsed
        .as_ref()
        .map(|u| u.path().trim_matches('/').replace('/', "-"))
        .unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(url.as_bytes());
    let hash = format!("{:x}", hasher.finalize());
    let short_hash = &hash[..8];
    let host_clean = host.replace('.', "-");
    let path_clean: String = path_seg
        .chars()
        .filter(|c| c.is_alphanumeric() || *c == '-' || *c == '_')
        .take(60)
        .collect();
    if path_clean.is_empty() {
        format!("{}-{}", host_clean, short_hash)
    } else {
        format!("{}-{}-{}", host_clean, path_clean, short_hash)
    }
}
