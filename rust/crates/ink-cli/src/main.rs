use std::path::PathBuf;

use clap::{Parser, Subcommand};
use ink_core::bounded::{IssuerId, PublicKeyId};
use ink_verify::{ReceiptStatus, TrustedIssuerKey, VerificationPolicy};

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
    /// Verify a canonical kernel receipt artifact.
    KernelReceipt {
        #[arg(long)]
        receipt: PathBuf,
        #[arg(long)]
        issuer_id: Option<String>,
        #[arg(long)]
        public_key_id: Option<String>,
        #[arg(long)]
        public_key_hex: Option<String>,
        #[arg(long, default_value_t = false)]
        allow_unsigned: bool,
        #[arg(long)]
        current_sequence: Option<u64>,
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
        Commands::KernelReceipt {
            receipt,
            issuer_id,
            public_key_id,
            public_key_hex,
            allow_unsigned,
            current_sequence,
        } => {
            let receipt = ink_core::canon::decode_receipt(&std::fs::read(&receipt)?)
                .map_err(|err| std::io::Error::other(err.to_string()))?;
            let trusted_key = build_trusted_key(issuer_id, public_key_id, public_key_hex)?;
            let trusted_keys = trusted_key.iter().copied().collect::<Vec<_>>();
            let report = ink_verify::verify_receipt(
                &receipt,
                &trusted_keys,
                VerificationPolicy {
                    allow_unsigned,
                    current_sequence,
                },
            )
            .map_err(|err| std::io::Error::other(format!("{err:?}")))?;
            println!(
                "{}",
                serde_json::to_string_pretty(&serde_json::json!({
                    "structural_valid": report.core.valid,
                    "status": report.status.as_str(),
                    "code": report.code.as_str(),
                }))?
            );
            let accepted = report.core.valid
                && matches!(
                    report.status,
                    ReceiptStatus::SignatureValid | ReceiptStatus::StructuralValidUnsigned
                );
            if !accepted {
                std::process::exit(1);
            }
        }
    }
    Ok(())
}

fn read_optional(path: &Option<PathBuf>) -> Result<Option<Vec<u8>>, std::io::Error> {
    path.as_ref()
        .map(|value| std::fs::read(value.as_path()))
        .transpose()
}

fn build_trusted_key(
    issuer_id: Option<String>,
    public_key_id: Option<String>,
    public_key_hex: Option<String>,
) -> Result<Option<TrustedIssuerKey>, Box<dyn std::error::Error>> {
    match (issuer_id, public_key_id, public_key_hex) {
        (None, None, None) => Ok(None),
        (Some(issuer_id), Some(public_key_id), Some(public_key_hex)) => {
            let public_key = hex::decode(public_key_hex)?;
            let public_key: [u8; 32] = public_key
                .try_into()
                .map_err(|_| "expected 32-byte public key hex")?;
            Ok(Some(TrustedIssuerKey {
                issuer_id: IssuerId::from_str(&issuer_id)
                    .map_err(|err| std::io::Error::other(err.to_string()))?,
                public_key_id: PublicKeyId::from_str(&public_key_id)
                    .map_err(|err| std::io::Error::other(err.to_string()))?,
                public_key: ink_core::Ed25519PublicKey(public_key),
            }))
        }
        _ => Err("provide all of --issuer-id, --public-key-id, and --public-key-hex".into()),
    }
}
