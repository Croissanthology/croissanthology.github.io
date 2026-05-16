use anyhow::{Context, Result};
use lettre::message::header::ContentType;
use lettre::transport::smtp::authentication::Credentials;
use lettre::{Message, SmtpTransport, Transport};

use crate::config::NOTIFY_EMAIL;

/// items: (post_url, dead_url, archive_url)
pub fn email_substack_dead(items: &[(String, String, String)]) -> Result<()> {
    if items.is_empty() {
        return Ok(());
    }
    let user = std::env::var("ARCHIVER_SMTP_USER")
        .context("ARCHIVER_SMTP_USER not set (e.g. your gmail address)")?;
    let pass = std::env::var("ARCHIVER_SMTP_PASS")
        .context("ARCHIVER_SMTP_PASS not set (gmail app password)")?;
    let host = std::env::var("ARCHIVER_SMTP_HOST")
        .unwrap_or_else(|_| "smtp.gmail.com".to_string());

    let mut body = String::new();
    body.push_str("hi margot — these substack posts cite links that have gone dead.\n");
    body.push_str("your archiver has saved local copies and rehosted them; update substack manually:\n\n");
    for (post, dead, archive) in items {
        body.push_str(&format!(
            "  post:    {}\n  dead:    {}\n  archive: {}\n\n",
            post, dead, archive
        ));
    }
    body.push_str("— archiver 🐾\n");

    let email = Message::builder()
        .from(user.parse().context("parse from address")?)
        .to(NOTIFY_EMAIL.parse().context("parse to address")?)
        .subject(format!(
            "[archiver] {} dead substack link(s) need manual fix",
            items.len()
        ))
        .header(ContentType::TEXT_PLAIN)
        .body(body)?;

    let mailer = SmtpTransport::relay(&host)?
        .credentials(Credentials::new(user, pass))
        .build();
    mailer.send(&email)?;
    Ok(())
}

pub fn terminal_bell() {
    print!("\x07");
}
