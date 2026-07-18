//! Production signer abstraction layer for MAND8.
//!
//! Re-exports the provider-neutral signer contract and the demo/remote adapters
//! from [`signer`].

mod signer;

pub use signer::{
    create_signer, HealthReport, HealthStatus, IssuanceMode, KeyMetadata, LocalSigner,
    RemoteSigner, RotationState, SignerError, SignerProvider,
};
