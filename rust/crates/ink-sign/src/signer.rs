//! Production signer abstraction layer for MAND8.
//!
//! This module provides a provider-neutral signer contract with the operations
//! required for production issuance:
//! - `health` — liveness/readiness probe for the signer backend
//! - `key_metadata` — public key id, algorithm, and rotation state
//! - `sign_digest` — produce a signature over a precomputed digest
//! - `rotation_status` — current key rotation state
//! - `revoke_key` — mark a key as revoked in the trust registry
//!
//! Demo issuance uses the in-process [`LocalSigner`]; production issuance uses a
//! remote adapter (e.g. HSM, KMS, or hosted signer) that implements
//! [`SignerProvider`].

use std::collections::HashMap;
use std::fmt;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

/// Errors returned by signer operations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SignerError {
    /// Signer backend is unreachable or failed a health check.
    Unhealthy(String),
    /// Requested key is revoked and must not be used.
    KeyRevoked(String),
    /// Key rotation is in progress; signing is temporarily blocked.
    RotationInProgress(String),
    /// Cryptographic operation failed.
    CryptoFailure(String),
    /// Backend returned an unexpected response.
    Backend(String),
}

impl fmt::Display for SignerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SignerError::Unhealthy(m) => write!(f, "signer unhealthy: {m}"),
            SignerError::KeyRevoked(m) => write!(f, "key revoked: {m}"),
            SignerError::RotationInProgress(m) => write!(f, "rotation in progress: {m}"),
            SignerError::CryptoFailure(m) => write!(f, "crypto failure: {m}"),
            SignerError::Backend(m) => write!(f, "backend error: {m}"),
        }
    }
}

impl std::error::Error for SignerError {}

/// Health state of a signer backend.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HealthStatus {
    Healthy,
    Degraded,
    Unhealthy,
}

impl HealthStatus {
    pub fn is_usable(&self) -> bool {
        matches!(self, HealthStatus::Healthy | HealthStatus::Degraded)
    }
}

/// Key rotation state.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RotationState {
    Stable,
    InProgress,
    Failed,
}

/// Public metadata for a signing key.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KeyMetadata {
    pub key_id: String,
    pub algorithm: String,
    pub public_key_pem: String,
    pub rotation: RotationState,
    pub revoked: bool,
    pub created_at: u64,
    pub last_rotated_at: Option<u64>,
}

/// Health probe result.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HealthReport {
    pub status: HealthStatus,
    pub latency_ms: u64,
    pub detail: String,
}

/// Provider-neutral signer contract.
pub trait SignerProvider: Send + Sync {
    /// Return a health report for the backend.
    fn health(&self) -> Result<HealthReport, SignerError>;

    /// Return metadata for the active (or named) key.
    fn key_metadata(&self, key_id: &str) -> Result<KeyMetadata, SignerError>;

    /// Sign a precomputed digest, returning the raw signature bytes.
    fn sign_digest(&self, key_id: &str, digest: &[u8]) -> Result<Vec<u8>, SignerError>;

    /// Return the current rotation state for a key.
    fn rotation_status(&self, key_id: &str) -> Result<RotationState, SignerError>;

    /// Revoke a key, recording the revocation in the trust registry.
    fn revoke_key(&self, key_id: &str, reason: &str) -> Result<(), SignerError>;
}

/// In-process demo signer. Uses a deterministic stub signature so demo issuance
/// never touches a production backend.
pub struct LocalSigner {
    key_id: String,
    algorithm: String,
    public_key_pem: String,
    created_at: u64,
    rotation: RotationState,
    revoked: bool,
}

impl LocalSigner {
    pub fn new(key_id: &str) -> Self {
        let created_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        LocalSigner {
            key_id: key_id.to_string(),
            algorithm: "ed25519".to_string(),
            public_key_pem: "-----BEGIN PUBLIC KEY-----\nDEMO\n-----END PUBLIC KEY-----".to_string(),
            created_at,
            rotation: RotationState::Stable,
            revoked: false,
        }
    }
}

impl SignerProvider for LocalSigner {
    fn health(&self) -> Result<HealthReport, SignerError> {
        Ok(HealthReport {
            status: HealthStatus::Healthy,
            latency_ms: 0,
            detail: "local demo signer".to_string(),
        })
    }

    fn key_metadata(&self, key_id: &str) -> Result<KeyMetadata, SignerError> {
        if key_id != self.key_id {
            return Err(SignerError::Backend(format!("unknown key {key_id}")));
        }
        Ok(KeyMetadata {
            key_id: self.key_id.clone(),
            algorithm: self.algorithm.clone(),
            public_key_pem: self.public_key_pem.clone(),
            rotation: self.rotation,
            revoked: self.revoked,
            created_at: self.created_at,
            last_rotated_at: None,
        })
    }

    fn sign_digest(&self, key_id: &str, digest: &[u8]) -> Result<Vec<u8>, SignerError> {
        if self.revoked {
            return Err(SignerError::KeyRevoked(self.key_id.clone()));
        }
        if self.rotation == RotationState::InProgress {
            return Err(SignerError::RotationInProgress(self.key_id.clone()));
        }
        if key_id != self.key_id {
            return Err(SignerError::Backend(format!("unknown key {key_id}")));
        }
        // Demo stub: signature is the digest length prefixed to the digest.
        let mut sig = vec![digest.len() as u8];
        sig.extend_from_slice(digest);
        Ok(sig)
    }

    fn rotation_status(&self, key_id: &str) -> Result<RotationState, SignerError> {
        if key_id != self.key_id {
            return Err(SignerError::Backend(format!("unknown key {key_id}")));
        }
        Ok(self.rotation)
    }

    fn revoke_key(&self, key_id: &str, _reason: &str) -> Result<(), SignerError> {
        if key_id != self.key_id {
            return Err(SignerError::Backend(format!("unknown key {key_id}")));
        }
        // LocalSigner is immutable; revocation is tracked by the caller.
        Ok(())
    }
}

/// Remote signer adapter stub. Production wiring replaces the HTTP client with a
/// real HSM/KMS/transactional signer endpoint.
pub struct RemoteSigner {
    pub endpoint: String,
    pub api_key: String,
    pub timeout: Duration,
}

impl SignerProvider for RemoteSigner {
    fn health(&self) -> Result<HealthReport, SignerError> {
        // TODO: replace with real probe.
        Ok(HealthReport {
            status: HealthStatus::Healthy,
            latency_ms: 0,
            detail: format!("remote signer at {}", self.endpoint),
        })
    }

    fn key_metadata(&self, key_id: &str) -> Result<KeyMetadata, SignerError> {
        // TODO: fetch from remote registry.
        Err(SignerError::Backend(format!(
            "remote key_metadata not wired for {key_id}"
        )))
    }

    fn sign_digest(&self, key_id: &str, _digest: &[u8]) -> Result<Vec<u8>, SignerError> {
        // TODO: POST to remote signer.
        Err(SignerError::Backend(format!(
            "remote sign_digest not wired for {key_id}"
        )))
    }

    fn rotation_status(&self, key_id: &str) -> Result<RotationState, SignerError> {
        // TODO: fetch rotation state.
        Err(SignerError::Backend(format!(
            "remote rotation_status not wired for {key_id}"
        )))
    }

    fn revoke_key(&self, key_id: &str, _reason: &str) -> Result<(), SignerError> {
        // TODO: POST revocation to trust registry.
        Err(SignerError::Backend(format!(
            "remote revoke_key not wired for {key_id}"
        )))
    }
}

/// Selects the appropriate signer based on issuance mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IssuanceMode {
    Demo,
    Production,
}

/// Factory that returns the signer provider for a given mode.
pub fn signer_for_mode(mode: IssuanceMode, remote: Option<RemoteSigner>) -> Box<dyn SignerProvider> {
    match mode {
        IssuanceMode::Demo => Box::new(LocalSigner::new("demo-signer")),
        IssuanceMode::Production => {
            let remote = remote.unwrap_or(RemoteSigner {
                endpoint: "https://signer.example.com".to_string(),
                api_key: String::new(),
                timeout: Duration::from_secs(10),
            });
            Box::new(remote)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn demo_signer_health_ok() {
        let s = LocalSigner::new("k1");
        let h = s.health().unwrap();
        assert_eq!(h.status, HealthStatus::Healthy);
    }

    #[test]
    fn demo_signer_signs_digest() {
        let s = LocalSigner::new("k1");
        let digest = b"abc";
        let sig = s.sign_digest("k1", digest).unwrap();
        assert_eq!(sig, vec![3, b'a', b'b', b'c']);
    }

    #[test]
    fn demo_signer_rejects_unknown_key() {
        let s = LocalSigner::new("k1");
        assert!(s.sign_digest("k2", b"x").is_err());
    }

    #[test]
    fn factory_returns_local_for_demo() {
        let boxed = signer_for_mode(IssuanceMode::Demo, None);
        assert!(boxed.health().unwrap().status.is_usable());
    }
}
