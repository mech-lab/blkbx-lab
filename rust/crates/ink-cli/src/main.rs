use std::path::PathBuf;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "ink", about = "INK independent verifier CLI")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Verify a current public ink_receipt.v2.json artifact.
    Receipt {
        #[arg(long)]
        receipt: PathBuf,
        #[arg(long)]
        manifest: Option<PathBuf>,
        #[arg(long)]
        controls: Option<PathBuf>,
        #[arg(long)]
        trust_registry: Option<PathBuf>,
        #[arg(long)]
        revocation_list: Option<PathBuf>,
        #[arg(long)]
        policy: Option<PathBuf>,
        #[arg(long)]
        pinned_key: Option<String>,
    },
    /// Verify a receipt plus any supplied supporting artifacts as a portable bundle.
    Bundle {
        #[arg(long)]
        receipt: PathBuf,
        #[arg(long)]
        manifest: Option<PathBuf>,
        #[arg(long)]
        controls: Option<PathBuf>,
        #[arg(long)]
        trust_registry: Option<PathBuf>,
        #[arg(long)]
        revocation_list: Option<PathBuf>,
        #[arg(long)]
        policy: Option<PathBuf>,
        #[arg(long)]
        pinned_key: Option<String>,
    },
    /// Load and validate an ink.verify-policy.v1 file.
    Policy {
        #[arg(long)]
        policy: PathBuf,
    },
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Receipt {
            receipt,
            manifest,
            controls,
            trust_registry,
            revocation_list,
            policy,
            pinned_key,
        } => {
            let report = ink_receipt_v2::verify_receipt(
                &std::fs::read(&receipt)?,
                read_optional(&manifest)?.as_deref(),
                read_optional(&controls)?.as_deref(),
                read_optional(&trust_registry)?.as_deref(),
                read_optional(&revocation_list)?.as_deref(),
                read_optional(&policy)?.as_deref(),
                pinned_key.as_deref(),
            )?;
            println!("{}", serde_json::to_string_pretty(&report)?);
            if report.status != "valid" {
                std::process::exit(1);
            }
        }
        Commands::Bundle {
            receipt,
            manifest,
            controls,
            trust_registry,
            revocation_list,
            policy,
            pinned_key,
        } => {
            let report = ink_receipt_v2::verify_bundle(
                &std::fs::read(&receipt)?,
                read_optional(&manifest)?.as_deref(),
                read_optional(&controls)?.as_deref(),
                read_optional(&trust_registry)?.as_deref(),
                read_optional(&revocation_list)?.as_deref(),
                read_optional(&policy)?.as_deref(),
                pinned_key.as_deref(),
            )?;
            println!("{}", serde_json::to_string_pretty(&report)?);
            if report.status != "valid" {
                std::process::exit(1);
            }
        }
        Commands::Policy { policy } => {
            let loaded = ink_receipt_v2::load_verify_policy(&std::fs::read(policy)?)?;
            println!("{}", serde_json::to_string_pretty(&loaded)?);
        }
    }
    Ok(())
}

fn read_optional(path: &Option<PathBuf>) -> Result<Option<Vec<u8>>, std::io::Error> {
    path.as_ref().map(|value| std::fs::read(value.as_path())).transpose()
}
