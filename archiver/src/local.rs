use anyhow::{anyhow, Context, Result};
use std::path::{Path, PathBuf};
use std::process::Command;

pub fn save_local(url: &str, dest: &Path, user_agent: Option<&str>) -> Result<PathBuf> {
    if let Some(parent) = dest.parent() {
        std::fs::create_dir_all(parent).context("create archive output dir")?;
    }
    let mut cmd = Command::new("monolith");
    cmd.arg(url)
        .arg("-o")
        .arg(dest)
        .arg("--no-audio")
        .arg("--no-video")
        .arg("--silent");
    if let Some(ua) = user_agent {
        cmd.arg("--user-agent").arg(ua);
    }
    let status = cmd
        .status()
        .context("run `monolith` (install with `brew install monolith` on macOS)")?;
    if !status.success() {
        return Err(anyhow!("monolith exited with {}", status));
    }
    Ok(dest.to_path_buf())
}
