//! ProofMail hosted workflow for MAND8
//!
//! This module provides a hosted workflow for delivering MAND8 receipts and
//! verification packets via email with full audit trail and immutable hashing.

use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// ProofMail packet manifest - describes the complete packet being sent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PacketManifest {
    pub packet_id: String,
    pub schema: String,
    pub created_at: u64,
    pub issuer: String,
    pub receipt_id: String,
    pub receipt_hash: String,
    pub attachments: Vec<AttachmentRef>,
    pub integrity: PacketIntegrity,
}

/// Reference to an attachment in the packet
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AttachmentRef {
    pub name: String,
    pub content_type: String,
    pub size_bytes: u64,
    pub sha256: String,
}

/// Integrity hash of the entire packet
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PacketIntegrity {
    pub algorithm: String,
    pub hash: String,
}

/// Recipient manifest - describes who receives the packet
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecipientManifest {
    pub manifest_id: String,
    pub schema: String,
    pub packet_id: String,
    pub recipients: Vec<Recipient>,
    pub delivery_policy: DeliveryPolicy,
}

/// Individual recipient entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recipient {
    pub recipient_id: String,
    pub email: String,
    pub name: Option<String>,
    pub role: RecipientRole,
    pub delivery_status: DeliveryStatus,
}

/// Role of the recipient in the workflow
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RecipientRole {
    PrimaryReviewer,
    SecondaryReviewer,
    ComplianceOfficer,
    Auditor,
    Regulator,
    Other(String),
}

/// Delivery status tracking
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum DeliveryStatus {
    Pending,
    Sent,
    Delivered,
    Opened,
    Failed,
    Bounced,
}

/// Delivery policy configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeliveryPolicy {
    pub require_tls: bool,
    pub retry_policy: RetryPolicy,
    pub tracking_enabled: bool,
    pub encryption: EncryptionPolicy,
}

/// Retry policy for failed deliveries
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub initial_delay_seconds: u64,
    pub max_delay_seconds: u64,
    pub backoff_multiplier: f64,
}

/// Encryption policy for email content
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum EncryptionPolicy {
    None,
    TlsOnly,
    Pgp { key_id: String },
    Smime { cert_path: String },
}

/// Delivery audit entry - immutable record of each delivery attempt
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeliveryAuditEntry {
    pub audit_id: String,
    pub packet_id: String,
    pub recipient_id: String,
    pub timestamp: u64,
    pub attempt: u32,
    pub status: DeliveryStatus,
    pub smtp_response: Option<SmtpResponse>,
    pub error: Option<String>,
    pub message_id: Option<String>,
}

/// SMTP response details
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmtpResponse {
    pub code: u16,
    pub message: String,
    pub server: String,
}

/// Send status summary for a packet
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SendStatus {
    pub packet_id: String,
    pub total_recipients: usize,
    pub sent_count: usize,
    pub delivered_count: usize,
    pub failed_count: usize,
    pub pending_count: usize,
    pub last_updated: u64,
    pub recipient_statuses: HashMap<String, DeliveryStatus>,
}

/// ProofMail packet - the complete deliverable unit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProofMailPacket {
    pub manifest: PacketManifest,
    pub recipient_manifest: RecipientManifest,
    pub receipt_json: serde_json::Value,
    pub attachments: HashMap<String, Vec<u8>>,
}

/// Email adapter trait for pluggable delivery backends
pub trait EmailAdapter: Send + Sync {
    /// Send an email with attachments
    fn send(
        &self,
        to: &[String],
        _subject: &str,
        _body: &str,
        _attachments: &[EmailAttachment],
    ) -> Result<EmailSendResult, EmailError>;

    /// Health check for the adapter
    fn health(&self) -> Result<AdapterHealth, EmailError>;
}

/// Email attachment structure
#[derive(Debug, Clone)]
pub struct EmailAttachment {
    pub filename: String,
    pub content_type: String,
    pub data: Vec<u8>,
}

/// Result of an email send operation
#[derive(Debug, Clone)]
pub struct EmailSendResult {
    pub message_id: String,
    pub accepted_recipients: Vec<String>,
    pub rejected_recipients: Vec<String>,
}

/// Adapter health status
#[derive(Debug, Clone)]
pub struct AdapterHealth {
    pub healthy: bool,
    pub latency_ms: u64,
    pub detail: String,
}

/// Email adapter errors
#[derive(Debug, thiserror::Error)]
pub enum EmailError {
    #[error("SMTP error: {0}")]
    Smtp(String),
    #[error("Connection error: {0}")]
    Connection(String),
    #[error("Authentication error: {0}")]
    Auth(String),
    #[error("Invalid recipient: {0}")]
    InvalidRecipient(String),
    #[error("Attachment error: {0}")]
    Attachment(String),
    #[error("Configuration error: {0}")]
    Config(String),
}

/// SMTP email adapter implementation
pub struct SmtpAdapter {
    pub host: String,
    pub port: u16,
    pub username: String,
    pub password: String,
    pub use_tls: bool,
    pub timeout_seconds: u64,
}

impl EmailAdapter for SmtpAdapter {
    fn send(
        &self,
        to: &[String],
        _subject: &str,
        _body: &str,
        _attachments: &[EmailAttachment],
    ) -> Result<EmailSendResult, EmailError> {
        // TODO: Implement actual SMTP sending using lettre or similar
        // For now, return a stub result
        Ok(EmailSendResult {
            message_id: format!(
                "<{}-{}@proofmail.local>",
                uuid::Uuid::new_v4(),
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs()
            ),
            accepted_recipients: to.to_vec(),
            rejected_recipients: vec![],
        })
    }

    fn health(&self) -> Result<AdapterHealth, EmailError> {
        // TODO: Implement actual SMTP health check
        Ok(AdapterHealth {
            healthy: true,
            latency_ms: 0,
            detail: format!("SMTP adapter for {}:{}", self.host, self.port),
        })
    }
}

/// Transactional email adapter (SendGrid, Mailgun, SES, etc.)
pub struct TransactionalEmailAdapter {
    pub provider: TransactionalProvider,
    pub api_key: String,
    pub from_email: String,
    pub from_name: String,
    pub timeout_seconds: u64,
}

/// Supported transactional email providers
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TransactionalProvider {
    SendGrid,
    Mailgun,
    AmazonSes,
    Postmark,
    Resend,
}

impl EmailAdapter for TransactionalEmailAdapter {
    fn send(
        &self,
        to: &[String],
        _subject: &str,
        _body: &str,
        _attachments: &[EmailAttachment],
    ) -> Result<EmailSendResult, EmailError> {
        // TODO: Implement provider-specific API calls
        Ok(EmailSendResult {
            message_id: format!(
                "<{}-{}@proofmail.local>",
                uuid::Uuid::new_v4(),
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs()
            ),
            accepted_recipients: to.to_vec(),
            rejected_recipients: vec![],
        })
    }

    fn health(&self) -> Result<AdapterHealth, EmailError> {
        Ok(AdapterHealth {
            healthy: true,
            latency_ms: 0,
            detail: format!("Transactional adapter: {:?}", self.provider),
        })
    }
}

/// ProofMail service - orchestrates packet creation, delivery, and audit
pub struct ProofMailService {
    adapter: Box<dyn EmailAdapter>,
    audit_store: Box<dyn AuditStore>,
    packet_store: Box<dyn PacketStore>,
}

/// Trait for storing audit entries (immutable)
pub trait AuditStore: Send + Sync {
    fn append(&self, entry: &DeliveryAuditEntry) -> Result<(), AuditError>;
    fn get_for_packet(&self, packet_id: &str) -> Result<Vec<DeliveryAuditEntry>, AuditError>;
    fn get_for_recipient(&self, recipient_id: &str) -> Result<Vec<DeliveryAuditEntry>, AuditError>;
}

/// Trait for storing packets and their immutable hashes
pub trait PacketStore: Send + Sync {
    fn store(&self, packet: &ProofMailPacket) -> Result<String, PacketError>;
    fn get(&self, packet_id: &str) -> Result<Option<ProofMailPacket>, PacketError>;
    fn get_hash(&self, packet_id: &str) -> Result<Option<String>, PacketError>;
}

/// Audit store errors
#[derive(Debug, thiserror::Error)]
pub enum AuditError {
    #[error("Storage error: {0}")]
    Storage(String),
    #[error("Not found: {0}")]
    NotFound(String),
}

/// Packet store errors
#[derive(Debug, thiserror::Error)]
pub enum PacketError {
    #[error("Storage error: {0}")]
    Storage(String),
    #[error("Not found: {0}")]
    NotFound(String),
    #[error("Hash mismatch: {0}")]
    HashMismatch(String),
}

/// In-memory audit store for testing/demo
pub struct InMemoryAuditStore {
    entries: std::sync::Mutex<Vec<DeliveryAuditEntry>>,
}

impl InMemoryAuditStore {
    pub fn new() -> Self {
        Self {
            entries: std::sync::Mutex::new(Vec::new()),
        }
    }
}

impl AuditStore for InMemoryAuditStore {
    fn append(&self, entry: &DeliveryAuditEntry) -> Result<(), AuditError> {
        self.entries.lock().unwrap().push(entry.clone());
        Ok(())
    }

    fn get_for_packet(&self, packet_id: &str) -> Result<Vec<DeliveryAuditEntry>, AuditError> {
        Ok(self
            .entries
            .lock()
            .unwrap()
            .iter()
            .filter(|e| e.packet_id == packet_id)
            .cloned()
            .collect())
    }

    fn get_for_recipient(&self, recipient_id: &str) -> Result<Vec<DeliveryAuditEntry>, AuditError> {
        Ok(self
            .entries
            .lock()
            .unwrap()
            .iter()
            .filter(|e| e.recipient_id == recipient_id)
            .cloned()
            .collect())
    }
}

/// In-memory packet store for testing/demo
pub struct InMemoryPacketStore {
    packets: std::sync::Mutex<HashMap<String, ProofMailPacket>>,
    hashes: std::sync::Mutex<HashMap<String, String>>,
}

impl InMemoryPacketStore {
    pub fn new() -> Self {
        Self {
            packets: std::sync::Mutex::new(HashMap::new()),
            hashes: std::sync::Mutex::new(HashMap::new()),
        }
    }
}

impl PacketStore for InMemoryPacketStore {
    fn store(&self, packet: &ProofMailPacket) -> Result<String, PacketError> {
        let packet_id = packet.manifest.packet_id.clone();
        let hash = compute_packet_hash(packet);

        self.packets
            .lock()
            .unwrap()
            .insert(packet_id.clone(), packet.clone());
        self.hashes
            .lock()
            .unwrap()
            .insert(packet_id.clone(), hash.clone());

        Ok(packet_id)
    }

    fn get(&self, packet_id: &str) -> Result<Option<ProofMailPacket>, PacketError> {
        Ok(self.packets.lock().unwrap().get(packet_id).cloned())
    }

    fn get_hash(&self, packet_id: &str) -> Result<Option<String>, PacketError> {
        Ok(self.hashes.lock().unwrap().get(packet_id).cloned())
    }
}

/// Compute immutable hash of a ProofMail packet
fn compute_packet_hash(packet: &ProofMailPacket) -> String {
    let mut hasher = Sha256::new();

    // The packet hash commits to every manifest field except the hash field itself.
    let mut manifest = packet.manifest.clone();
    manifest.integrity.hash.clear();
    let manifest_bytes = serde_json::to_vec(&manifest).unwrap_or_default();
    hasher.update(&manifest_bytes);

    // Hash the recipient manifest
    let recipient_bytes = serde_json::to_vec(&packet.recipient_manifest).unwrap_or_default();
    hasher.update(&recipient_bytes);

    // Hash the receipt
    let receipt_bytes = serde_json::to_vec(&packet.receipt_json).unwrap_or_default();
    hasher.update(&receipt_bytes);

    // Hash attachments in deterministic order
    let mut attachment_names: Vec<_> = packet.attachments.keys().collect();
    attachment_names.sort();
    for name in attachment_names {
        if let Some(data) = packet.attachments.get(name) {
            hasher.update(data);
        }
    }

    format!("sha256:{}", hex::encode(hasher.finalize()))
}

/// Create a ProofMail packet from a MAND8 receipt
pub fn create_packet(
    receipt_json: serde_json::Value,
    issuer: &str,
    recipients: Vec<Recipient>,
    attachments: HashMap<String, Vec<u8>>,
) -> ProofMailPacket {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    let packet_id = format!(
        "urn:proofmail:packet:{}:{}",
        now,
        uuid::Uuid::new_v4().simple()
    );

    // Compute receipt hash
    let receipt_bytes = serde_json::to_vec(&receipt_json).unwrap_or_default();
    let receipt_hash = format!("sha256:{}", hex::encode(Sha256::digest(&receipt_bytes)));

    // Build attachment refs
    let mut attachment_entries: Vec<_> = attachments.iter().collect();
    attachment_entries.sort_by(|left, right| left.0.cmp(right.0));

    let mut attachment_refs = Vec::new();
    for (name, data) in attachment_entries {
        let hash = format!("sha256:{}", hex::encode(Sha256::digest(data)));
        attachment_refs.push(AttachmentRef {
            name: (*name).clone(),
            content_type: mime_guess::from_path(name)
                .first_or_octet_stream()
                .to_string(),
            size_bytes: data.len() as u64,
            sha256: hash,
        });
    }

    // Create packet manifest
    let manifest = PacketManifest {
        packet_id: packet_id.clone(),
        schema: "proofmail.packet.v1".to_string(),
        created_at: now,
        issuer: issuer.to_string(),
        receipt_id: receipt_json
            .get("receipt_id")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string(),
        receipt_hash,
        attachments: attachment_refs,
        integrity: PacketIntegrity {
            algorithm: "sha256".to_string(),
            hash: String::new(), // Will be filled after packet creation
        },
    };

    // Create recipient manifest
    let recipient_manifest = RecipientManifest {
        manifest_id: format!(
            "urn:proofmail:recipients:{}:{}",
            now,
            uuid::Uuid::new_v4().simple()
        ),
        schema: "proofmail.recipients.v1".to_string(),
        packet_id: packet_id.clone(),
        recipients,
        delivery_policy: DeliveryPolicy {
            require_tls: true,
            retry_policy: RetryPolicy {
                max_attempts: 3,
                initial_delay_seconds: 60,
                max_delay_seconds: 3600,
                backoff_multiplier: 2.0,
            },
            tracking_enabled: true,
            encryption: EncryptionPolicy::TlsOnly,
        },
    };

    let mut packet = ProofMailPacket {
        manifest,
        recipient_manifest,
        receipt_json,
        attachments,
    };

    // Compute and set the integrity hash
    let hash = compute_packet_hash(&packet);
    packet.manifest.integrity.hash = hash;

    packet
}

/// Send a ProofMail packet to all recipients
pub fn send_packet(
    service: &ProofMailService,
    packet: &ProofMailPacket,
) -> Result<SendStatus, ProofMailError> {
    let mut status = SendStatus {
        packet_id: packet.manifest.packet_id.clone(),
        total_recipients: packet.recipient_manifest.recipients.len(),
        sent_count: 0,
        delivered_count: 0,
        failed_count: 0,
        pending_count: packet.recipient_manifest.recipients.len(),
        last_updated: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs(),
        recipient_statuses: HashMap::new(),
    };

    // Store packet with immutable hash
    service.packet_store.store(packet)?;

    // Prepare email content
    let subject = format!("MAND8 Verification Packet: {}", packet.manifest.receipt_id);
    let body = build_email_body(packet);

    // Prepare attachments
    let email_attachments: Vec<EmailAttachment> = packet
        .attachments
        .iter()
        .map(|(name, data)| EmailAttachment {
            filename: name.clone(),
            content_type: mime_guess::from_path(name)
                .first_or_octet_stream()
                .to_string(),
            data: data.clone(),
        })
        .collect();

    // Add receipt JSON as attachment
    let receipt_bytes = serde_json::to_vec_pretty(&packet.receipt_json).unwrap_or_default();
    let mut all_attachments = email_attachments;
    all_attachments.push(EmailAttachment {
        filename: "mand8-receipt.json".to_string(),
        content_type: "application/json".to_string(),
        data: receipt_bytes,
    });

    // Send to each recipient
    for recipient in &packet.recipient_manifest.recipients {
        let recipient_emails = vec![recipient.email.clone()];

        let audit_entry = DeliveryAuditEntry {
            audit_id: format!(
                "urn:proofmail:audit:{}:{}",
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs(),
                uuid::Uuid::new_v4().simple()
            ),
            packet_id: packet.manifest.packet_id.clone(),
            recipient_id: recipient.recipient_id.clone(),
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            attempt: 1,
            status: DeliveryStatus::Pending,
            smtp_response: None,
            error: None,
            message_id: None,
        };

        // Record initial audit entry
        service.audit_store.append(&audit_entry)?;

        // Send email
        match service
            .adapter
            .send(&recipient_emails, &subject, &body, &all_attachments)
        {
            Ok(result) => {
                status.sent_count += 1;
                status.pending_count -= 1;

                // Update audit entry with success
                let mut updated_entry = audit_entry;
                updated_entry.status = DeliveryStatus::Sent;
                updated_entry.message_id = Some(result.message_id);
                updated_entry.smtp_response = Some(SmtpResponse {
                    code: 250,
                    message: "OK".to_string(),
                    server: "proofmail".to_string(),
                });
                service.audit_store.append(&updated_entry)?;

                status
                    .recipient_statuses
                    .insert(recipient.recipient_id.clone(), DeliveryStatus::Sent);
            }
            Err(e) => {
                status.failed_count += 1;
                status.pending_count -= 1;

                // Update audit entry with failure
                let mut updated_entry = audit_entry;
                updated_entry.status = DeliveryStatus::Failed;
                updated_entry.error = Some(e.to_string());
                service.audit_store.append(&updated_entry)?;

                status
                    .recipient_statuses
                    .insert(recipient.recipient_id.clone(), DeliveryStatus::Failed);
            }
        }
    }

    status.last_updated = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    Ok(status)
}

/// Build email body for ProofMail delivery
fn build_email_body(packet: &ProofMailPacket) -> String {
    format!(
        r#"MAND8 Verification Packet Delivery

Packet ID: {}
Receipt ID: {}
Issuer: {}
Created: {}

This email contains a MAND8 verification packet for your review. The attached files include:

1. mand8-receipt.json - The signed MAND8 receipt (ink.receipt.v2)
2. Additional evidence attachments as referenced in the packet manifest

Packet Integrity: {}
Attachments: {}

Please verify the receipt using the MAND8 verifier:
    ink-cli verify --receipt mand8-receipt.json

This is an automated delivery from the BLKBX Lab ProofMail service.
"#,
        packet.manifest.packet_id,
        packet.manifest.receipt_id,
        packet.manifest.issuer,
        chrono::DateTime::from_timestamp(packet.manifest.created_at as i64, 0)
            .map(|dt| dt.to_rfc3339())
            .unwrap_or_else(|| "unknown".to_string()),
        packet.manifest.integrity.hash,
        packet.manifest.attachments.len()
    )
}

/// ProofMail service errors
#[derive(Debug, thiserror::Error)]
pub enum ProofMailError {
    #[error("Email adapter error: {0}")]
    Adapter(#[from] EmailError),
    #[error("Audit store error: {0}")]
    Audit(#[from] AuditError),
    #[error("Packet store error: {0}")]
    Packet(#[from] PacketError),
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("Invalid packet: {0}")]
    InvalidPacket(String),
}

impl ProofMailService {
    pub fn new(
        adapter: Box<dyn EmailAdapter>,
        audit_store: Box<dyn AuditStore>,
        packet_store: Box<dyn PacketStore>,
    ) -> Self {
        Self {
            adapter,
            audit_store,
            packet_store,
        }
    }

    pub fn create_and_send(
        &self,
        receipt_json: serde_json::Value,
        issuer: &str,
        recipients: Vec<Recipient>,
        attachments: HashMap<String, Vec<u8>>,
    ) -> Result<SendStatus, ProofMailError> {
        let packet = create_packet(receipt_json, issuer, recipients, attachments);
        send_packet(self, &packet)
    }

    pub fn get_send_status(&self, packet_id: &str) -> Result<Option<SendStatus>, ProofMailError> {
        // Reconstruct status from audit entries
        let entries = self.audit_store.get_for_packet(packet_id)?;
        if entries.is_empty() {
            return Ok(None);
        }

        let mut statuses = HashMap::new();
        let mut sent = 0;
        let mut delivered = 0;
        let mut failed = 0;
        let mut pending = 0;

        for entry in &entries {
            // Use the latest status for each recipient
            if entry.timestamp > 0 {
                // Always true, but keeps logic clear
                statuses.insert(entry.recipient_id.clone(), entry.status.clone());
            }
        }

        for status in statuses.values() {
            match status {
                DeliveryStatus::Sent | DeliveryStatus::Delivered | DeliveryStatus::Opened => {
                    sent += 1;
                    if matches!(status, DeliveryStatus::Delivered | DeliveryStatus::Opened) {
                        delivered += 1;
                    }
                }
                DeliveryStatus::Failed | DeliveryStatus::Bounced => failed += 1,
                DeliveryStatus::Pending => pending += 1,
            }
        }

        Ok(Some(SendStatus {
            packet_id: packet_id.to_string(),
            total_recipients: statuses.len(),
            sent_count: sent,
            delivered_count: delivered,
            failed_count: failed,
            pending_count: pending,
            last_updated: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            recipient_statuses: statuses,
        }))
    }

    pub fn get_audit_trail(
        &self,
        packet_id: &str,
    ) -> Result<Vec<DeliveryAuditEntry>, ProofMailError> {
        Ok(self.audit_store.get_for_packet(packet_id)?)
    }

    pub fn verify_packet_integrity(&self, packet_id: &str) -> Result<bool, ProofMailError> {
        let packet = self
            .packet_store
            .get(packet_id)?
            .ok_or_else(|| ProofMailError::InvalidPacket("Packet not found".to_string()))?;
        let stored_hash = self
            .packet_store
            .get_hash(packet_id)?
            .ok_or_else(|| ProofMailError::InvalidPacket("Hash not found".to_string()))?;
        let computed_hash = compute_packet_hash(&packet);
        Ok(stored_hash == computed_hash)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_create_packet() {
        let receipt = json!({
            "schema": "ink.receipt.v2",
            "receipt_id": "urn:ink:receipt:test-123",
            "action_id": "test-action",
            "decision": "pass"
        });

        let recipients = vec![Recipient {
            recipient_id: "rec-1".to_string(),
            email: "reviewer@example.com".to_string(),
            name: Some("Primary Reviewer".to_string()),
            role: RecipientRole::PrimaryReviewer,
            delivery_status: DeliveryStatus::Pending,
        }];

        let mut attachments = HashMap::new();
        attachments.insert("evidence.pdf".to_string(), b"fake pdf content".to_vec());

        let packet = create_packet(receipt, "test-issuer", recipients, attachments);

        assert_eq!(packet.manifest.schema, "proofmail.packet.v1");
        assert_eq!(packet.manifest.receipt_id, "urn:ink:receipt:test-123");
        assert_eq!(packet.manifest.attachments.len(), 1);
        assert!(!packet.manifest.integrity.hash.is_empty());
    }

    #[test]
    fn test_packet_integrity_hash_is_stable_for_the_packet() {
        let receipt = json!({
            "schema": "ink.receipt.v2",
            "receipt_id": "urn:ink:receipt:test-123",
        });

        let recipients = vec![Recipient {
            recipient_id: "rec-1".to_string(),
            email: "a@example.com".to_string(),
            name: None,
            role: RecipientRole::PrimaryReviewer,
            delivery_status: DeliveryStatus::Pending,
        }];

        let mut attachments = HashMap::new();
        attachments.insert("a.txt".to_string(), b"content a".to_vec());
        attachments.insert("b.txt".to_string(), b"content b".to_vec());

        let packet = create_packet(receipt, "issuer", recipients, attachments);
        assert_eq!(packet.manifest.integrity.hash, compute_packet_hash(&packet));

        let mut tampered = packet.clone();
        tampered
            .attachments
            .insert("c.txt".to_string(), b"content c".to_vec());
        assert_ne!(
            packet.manifest.integrity.hash,
            compute_packet_hash(&tampered)
        );
    }

    #[test]
    fn test_in_memory_stores() {
        let packet_store = InMemoryPacketStore::new();

        let receipt = json!({"receipt_id": "test"});
        let recipients = vec![Recipient {
            recipient_id: "rec-1".to_string(),
            email: "test@example.com".to_string(),
            name: None,
            role: RecipientRole::PrimaryReviewer,
            delivery_status: DeliveryStatus::Pending,
        }];
        let mut attachments = HashMap::new();
        attachments.insert("test.txt".to_string(), b"test".to_vec());

        let packet = create_packet(receipt, "issuer", recipients, attachments);
        let packet_id = packet.manifest.packet_id.clone();

        // Store packet
        let stored_id = packet_store.store(&packet).unwrap();
        assert_eq!(stored_id, packet_id);

        // Verify hash
        let hash = packet_store.get_hash(&packet_id).unwrap().unwrap();
        assert_eq!(hash, packet.manifest.integrity.hash);

        // Retrieve packet
        let retrieved = packet_store.get(&packet_id).unwrap().unwrap();
        assert_eq!(retrieved.manifest.packet_id, packet_id);
    }
}
