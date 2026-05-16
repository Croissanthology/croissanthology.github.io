use std::path::PathBuf;

pub const OWN_DOMAINS: &[&str] = &[
    "croissanthology.com",
    "www.croissanthology.com",
    "croissanthology.github.io",
    "croissanthology.substack.com",
];

pub const NOTIFY_EMAIL: &str = "margotwarrenbancquart@gmail.com";

pub const SITE_ORIGIN: &str = "https://croissanthology.com";

pub fn repo_root() -> PathBuf {
    let start = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let mut p = start.clone();
    loop {
        if p.join(".git").exists() {
            return p;
        }
        if !p.pop() {
            return start;
        }
    }
}

pub fn state_path() -> PathBuf {
    repo_root().join(".archiver").join("index.json")
}

pub fn is_own_host(host: &str) -> bool {
    let h = host.to_lowercase();
    OWN_DOMAINS
        .iter()
        .any(|d| h == *d || h.ends_with(&format!(".{}", d)))
}
