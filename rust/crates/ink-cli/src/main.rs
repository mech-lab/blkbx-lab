use std::fs;
use std::path::{Path, PathBuf};

use ink_core::bounded::{DomainTag, IssuerId, SchemaAuthority, SchemaId, SubjectId};
use ink_core::{
    canon, compare, Claim, Digest, Evidence, ParentHashes, Policy, PolicyDecision, ReceiptEnvelope,
    Schema,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
struct CreateInput {
    schema_id: String,
    schema_authority: String,
    domain_tag: String,
    subject_id: String,
    issuer_id: String,
    sequence: u64,
    claim: String,
    evidence: String,
    policy: String,
    trace_hash_hex: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ReceiptJson {
    version: u32,
    schema_id: String,
    schema_hash_hex: String,
    schema_authority: String,
    domain_tag: String,
    subject_hash_hex: String,
    issuer_id: String,
    sequence: u64,
    claim_hash_hex: String,
    evidence_hash_hex: String,
    policy_hash_hex: String,
    trace_hash_hex: String,
    parent_hashes_hex: Vec<String>,
    lifecycle_state: String,
    canonical_hash_hex: String,
}

#[derive(Debug, Deserialize)]
struct ReplayInput {
    receipt_path: String,
    claim: String,
    evidence: String,
    policy: String,
}

fn main() -> Result<(), String> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        return Err("usage: ink <create|seal|verify|replay|compare> <input> [args]".to_string());
    }
    match args[1].as_str() {
        "create" => create(Path::new(&args[2]), args.get(3).map(Path::new)),
        "seal" => seal(Path::new(&args[2]), args.get(3).map(Path::new)),
        "verify" => verify(Path::new(&args[2])),
        "replay" => replay(Path::new(&args[2])),
        "compare" => {
            if args.len() < 4 {
                return Err("usage: ink compare <left> <right>".to_string());
            }
            compare_receipts(Path::new(&args[2]), Path::new(&args[3]))
        }
        other => Err(format!("unknown command: {other}")),
    }
}

fn create(input_path: &Path, output: Option<&Path>) -> Result<(), String> {
    let raw = fs::read_to_string(input_path).map_err(|err| err.to_string())?;
    let input: CreateInput = serde_json::from_str(&raw).map_err(|err| err.to_string())?;
    let schema = Schema::from_slice(
        SchemaId::from_str(&input.schema_id).map_err(|err| err.to_string())?,
        SchemaAuthority::from_str(&input.schema_authority).map_err(|err| err.to_string())?,
        DomainTag::from_str(&input.domain_tag).map_err(|err| err.to_string())?,
        1,
        b"{}",
    )
    .map_err(|err| err.to_string())?;
    let claim = Claim::from_slice(
        schema.id,
        SubjectId::from_str(&input.subject_id).map_err(|err| err.to_string())?,
        input.claim.as_bytes(),
    )
    .map_err(|err| err.to_string())?;
    let evidence = Evidence::from_slice(schema.id, input.evidence.as_bytes())
        .map_err(|err| err.to_string())?;
    let policy = Policy::from_slice(schema.id, PolicyDecision::Pass, input.policy.as_bytes())
        .map_err(|err| err.to_string())?;
    let trace_hash = parse_digest_hex(&input.trace_hash_hex)?;
    let receipt = ReceiptEnvelope::create(
        schema.id,
        schema.compute_hash().map_err(|err| err.to_string())?,
        schema.authority,
        schema.domain_tag,
        claim.compute_hash().map_err(|err| err.to_string())?,
        IssuerId::from_str(&input.issuer_id).map_err(|err| err.to_string())?,
        input.sequence,
        claim.compute_hash().map_err(|err| err.to_string())?,
        evidence.compute_hash().map_err(|err| err.to_string())?,
        policy.compute_hash().map_err(|err| err.to_string())?,
        trace_hash,
        ParentHashes::new(),
    );
    let json = receipt_to_json(&receipt);
    write_json(output.unwrap_or_else(|| Path::new("receipt.json")), &json)
}

fn seal(input_path: &Path, output: Option<&Path>) -> Result<(), String> {
    let receipt = read_receipt_json(input_path)?
        .seal()
        .map_err(|err| err.to_string())?;
    let mut bytes = [0u8; 512];
    let len = canon::encode_receipt(&receipt, &mut bytes).map_err(|err| err.to_string())?;
    let out = output
        .map(PathBuf::from)
        .unwrap_or_else(|| input_path.with_extension("ink"));
    fs::write(out, &bytes[..len]).map_err(|err| err.to_string())
}

fn verify(path: &Path) -> Result<(), String> {
    let receipt = read_receipt(path)?;
    let report = ink_verify::verify_receipt(&receipt).map_err(|err| err.to_string())?;
    println!(
        "{}",
        serde_json::json!({
            "valid": report.core.valid,
            "hash_valid": report.core.hash_valid,
            "schema_valid": report.core.schema_valid,
            "lifecycle_valid": report.core.lifecycle_valid,
            "attestation": format!("{:?}", report.attestation),
        })
    );
    Ok(())
}

fn replay(input_path: &Path) -> Result<(), String> {
    let raw = fs::read_to_string(input_path).map_err(|err| err.to_string())?;
    let input: ReplayInput = serde_json::from_str(&raw).map_err(|err| err.to_string())?;
    let receipt = read_receipt(Path::new(&input.receipt_path))?;
    let schema_id = receipt.schema_id;
    let claim = Claim::from_slice(
        schema_id,
        SubjectId::from_str("subject-replay").map_err(|err| err.to_string())?,
        input.claim.as_bytes(),
    )
    .map_err(|err| err.to_string())?;
    let evidence = Evidence::from_slice(schema_id, input.evidence.as_bytes())
        .map_err(|err| err.to_string())?;
    let policy = Policy::from_slice(schema_id, PolicyDecision::Pass, input.policy.as_bytes())
        .map_err(|err| err.to_string())?;
    let report = ink_core::replay::replay_receipt(&receipt, &claim, &evidence, &policy, &[])
        .map_err(|err| err.to_string())?;
    println!(
        "{}",
        serde_json::json!({
            "valid": report.valid,
            "claim_match": report.claim_match,
            "evidence_match": report.evidence_match,
            "policy_match": report.policy_match,
            "trace_match": report.trace_match,
        })
    );
    Ok(())
}

fn compare_receipts(left: &Path, right: &Path) -> Result<(), String> {
    let left = read_receipt(left)?;
    let right = read_receipt(right)?;
    let diff = compare::compare_receipts(&left, &right).map_err(|err| err.to_string())?;
    println!(
        "{}",
        serde_json::json!({
            "comparable": diff.comparable,
            "same_hash": diff.same_hash,
            "kind": format!("{:?}", diff.kind),
            "schema_changed": diff.schema_changed,
            "claim_changed": diff.claim_changed,
            "evidence_changed": diff.evidence_changed,
            "policy_changed": diff.policy_changed,
            "trace_changed": diff.trace_changed,
            "parent_changed": diff.parent_changed,
            "lifecycle_changed": diff.lifecycle_changed,
        })
    );
    Ok(())
}

fn read_receipt(path: &Path) -> Result<ReceiptEnvelope, String> {
    let bytes = fs::read(path).map_err(|err| err.to_string())?;
    if bytes.first().copied() == Some(b'{') {
        Ok(read_receipt_json(path)?)
    } else {
        canon::decode_receipt(&bytes).map_err(|err| err.to_string())
    }
}

fn read_receipt_json(path: &Path) -> Result<ReceiptEnvelope, String> {
    let raw = fs::read_to_string(path).map_err(|err| err.to_string())?;
    let json: ReceiptJson = serde_json::from_str(&raw).map_err(|err| err.to_string())?;
    let mut parents = ParentHashes::new();
    for parent in json.parent_hashes_hex {
        parents
            .push(parse_digest_hex(&parent)?)
            .map_err(|err| err.to_string())?;
    }
    Ok(ReceiptEnvelope {
        version: json.version,
        schema_id: SchemaId::from_str(&json.schema_id).map_err(|err| err.to_string())?,
        schema_hash: parse_digest_hex(&json.schema_hash_hex)?,
        schema_authority: SchemaAuthority::from_str(&json.schema_authority)
            .map_err(|err| err.to_string())?,
        domain_tag: DomainTag::from_str(&json.domain_tag).map_err(|err| err.to_string())?,
        subject_hash: parse_digest_hex(&json.subject_hash_hex)?,
        issuer_id: IssuerId::from_str(&json.issuer_id).map_err(|err| err.to_string())?,
        sequence: json.sequence,
        claim_hash: parse_digest_hex(&json.claim_hash_hex)?,
        evidence_hash: parse_digest_hex(&json.evidence_hash_hex)?,
        policy_hash: parse_digest_hex(&json.policy_hash_hex)?,
        trace_hash: parse_digest_hex(&json.trace_hash_hex)?,
        parent_hashes: parents,
        lifecycle_state: match json.lifecycle_state.as_str() {
            "Draft" => ink_core::LifecycleState::Draft,
            "Observed" => ink_core::LifecycleState::Observed,
            "Validated" => ink_core::LifecycleState::Validated,
            "Attested" => ink_core::LifecycleState::Attested,
            "Sealed" => ink_core::LifecycleState::Sealed,
            "Superseded" => ink_core::LifecycleState::Superseded,
            "Revoked" => ink_core::LifecycleState::Revoked,
            "Expired" => ink_core::LifecycleState::Expired,
            "Renewed" => ink_core::LifecycleState::Renewed,
            _ => return Err("invalid lifecycle_state".to_string()),
        },
        canonical_hash: parse_digest_hex(&json.canonical_hash_hex)?,
        attestation: None,
    })
}

fn receipt_to_json(receipt: &ReceiptEnvelope) -> ReceiptJson {
    ReceiptJson {
        version: receipt.version,
        schema_id: receipt.schema_id.as_str().unwrap_or("").to_string(),
        schema_hash_hex: hex::encode(receipt.schema_hash.0),
        schema_authority: receipt.schema_authority.as_str().unwrap_or("").to_string(),
        domain_tag: receipt.domain_tag.as_str().unwrap_or("").to_string(),
        subject_hash_hex: hex::encode(receipt.subject_hash.0),
        issuer_id: receipt.issuer_id.as_str().unwrap_or("").to_string(),
        sequence: receipt.sequence,
        claim_hash_hex: hex::encode(receipt.claim_hash.0),
        evidence_hash_hex: hex::encode(receipt.evidence_hash.0),
        policy_hash_hex: hex::encode(receipt.policy_hash.0),
        trace_hash_hex: hex::encode(receipt.trace_hash.0),
        parent_hashes_hex: receipt
            .parent_hashes
            .as_slice()
            .iter()
            .map(|digest| hex::encode(digest.0))
            .collect(),
        lifecycle_state: format!("{:?}", receipt.lifecycle_state),
        canonical_hash_hex: hex::encode(receipt.canonical_hash.0),
    }
}

fn parse_digest_hex(value: &str) -> Result<Digest, String> {
    let bytes = hex::decode(value).map_err(|err| err.to_string())?;
    if bytes.len() != 32 {
        return Err("digest must be 32 bytes".to_string());
    }
    let mut digest = [0u8; 32];
    digest.copy_from_slice(&bytes);
    Ok(Digest(digest))
}

fn write_json(path: &Path, payload: &ReceiptJson) -> Result<(), String> {
    let bytes = serde_json::to_vec_pretty(payload).map_err(|err| err.to_string())?;
    fs::write(path, bytes).map_err(|err| err.to_string())
}
