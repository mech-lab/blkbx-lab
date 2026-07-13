use crate::error::Error;
use crate::limits::{MAX_ARTIFACTS, MAX_PATH_HINT_LEN};
use crate::types::{ActionId, BoundedBytes, Sha256Digest};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ArtifactType {
    ActionProposal,
    Prompt,
    PolicySpec,
    PolicyCompilation,
    ControlSet,
    Other,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MediaType {
    ApplicationJson,
    TextPlain,
    ApplicationYaml,
    ApplicationOctetStream,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ArtifactRef<'a> {
    pub artifact_type: ArtifactType,
    pub media_type: MediaType,
    pub path_hash: Sha256Digest,
    pub size_bytes: u64,
    pub content_hash: Sha256Digest,
    pub schema_hash: Option<Sha256Digest>,
    pub path_hint: BoundedBytes<'a, MAX_PATH_HINT_LEN>,
}

impl<'a> ArtifactRef<'a> {
    pub fn validate(&self) -> Result<(), Error> {
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ManifestBinding<'a> {
    pub action_id: ActionId<'a>,
    pub manifest_hash: Sha256Digest,
    pub artifacts: &'a [ArtifactRef<'a>],
}

impl<'a> ManifestBinding<'a> {
    pub fn validate(&self) -> Result<(), Error> {
        if self.artifacts.is_empty() {
            return Err(Error::EmptyValue);
        }
        if self.artifacts.len() > MAX_ARTIFACTS {
            return Err(Error::TooManyArtifacts);
        }
        for artifact in self.artifacts {
            artifact.validate()?;
        }
        Ok(())
    }
}
