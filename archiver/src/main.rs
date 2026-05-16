mod archive;
mod check;
mod cli;
mod config;
mod extract;
mod local;
mod notify;
mod paywall;
mod rehost;
mod state;
mod ui;

fn main() -> anyhow::Result<()> {
    cli::run()
}
