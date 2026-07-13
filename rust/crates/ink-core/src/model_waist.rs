use crate::error::Error;
use crate::limits::{MAX_MODEL_SLUG_LEN, MAX_PLUGIN_ID_HINT_LEN};
use crate::types::{BoundedBytes, Sha256Digest};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ModelWaist<'a> {
    pub identity: ModelIdentityClaim<'a>,
    pub invocation: ModelInvocationClaim,
    pub observation: ModelObservationClaim,
    pub runtime: RuntimeClaim,
    pub plugin: PluginClaim<'a>,
}

impl<'a> ModelWaist<'a> {
    pub fn validate(&self) -> Result<(), Error> {
        self.runtime.validate()?;
        self.invocation.validate()?;
        self.observation.validate()?;
        match self.identity.model_class {
            ModelClass::DeterministicDemo => {
                if !matches!(self.identity.identity_evidence, IdentityEvidence::Declared)
                    || self.runtime.runtime_kind != RuntimeKind::DeterministicDemo
                    || self.runtime.execution_topology != ExecutionTopology::RuleBasedLocal
                    || self.runtime.replay_strength != ReplayStrength::FullyReplayable
                    || !self.runtime.determinism.deterministic
                    || !self.runtime.determinism.seed_bound
                {
                    return Err(Error::InvalidModelShape);
                }
            }
            ModelClass::Replay => {
                if self.runtime.runtime_kind != RuntimeKind::ReplayOnly {
                    return Err(Error::InvalidModelShape);
                }
            }
            _ => {}
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ModelIdentityClaim<'a> {
    pub model_class: ModelClass,
    pub model_ref_hash: Sha256Digest,
    pub model_slug: BoundedBytes<'a, MAX_MODEL_SLUG_LEN>,
    pub identity_evidence: IdentityEvidence,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ModelClass {
    OpenWeight,
    ClosedWeight,
    HostedApi,
    Replay,
    DeterministicDemo,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IdentityEvidence {
    Declared,
    ProviderDeclared {
        provider_model_id_hash: Sha256Digest,
    },
    LocalFilesHashed {
        weights_hash: Sha256Digest,
        tokenizer_hash: Option<Sha256Digest>,
        config_hash: Option<Sha256Digest>,
    },
    ContainerHashed {
        image_hash: Sha256Digest,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ModelInvocationClaim {
    pub action_hash: Sha256Digest,
    pub messages_hash: Sha256Digest,
    pub system_prompt_hash: Option<Sha256Digest>,
    pub tool_spec_hash: Option<Sha256Digest>,
    pub response_schema_hash: Option<Sha256Digest>,
    pub parameters_hash: Sha256Digest,
    pub requested_output: RequestedOutput,
}

impl ModelInvocationClaim {
    pub fn validate(&self) -> Result<(), Error> {
        match self.requested_output {
            RequestedOutput::FreeText => Ok(()),
            RequestedOutput::JsonSchema { schema_hash } => {
                if self.response_schema_hash == Some(schema_hash) {
                    Ok(())
                } else {
                    Err(Error::InvalidRequestedOutputShape)
                }
            }
            RequestedOutput::ToolCall { tool_spec_hash } => {
                if self.tool_spec_hash == Some(tool_spec_hash) {
                    Ok(())
                } else {
                    Err(Error::InvalidRequestedOutputShape)
                }
            }
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RequestedOutput {
    FreeText,
    JsonSchema { schema_hash: Sha256Digest },
    ToolCall { tool_spec_hash: Sha256Digest },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ModelObservationClaim {
    pub output_text_hash: Option<Sha256Digest>,
    pub structured_output_hash: Option<Sha256Digest>,
    pub provider_metadata_hash: Option<Sha256Digest>,
    pub finish_reason: FinishReason,
    pub usage: TokenUsage,
}

impl ModelObservationClaim {
    pub fn validate(&self) -> Result<(), Error> {
        self.usage.validate()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FinishReason {
    Stop,
    Length,
    ToolCall,
    ContentFilter,
    Error,
    Unknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TokenUsage {
    pub input_tokens: Option<u32>,
    pub output_tokens: Option<u32>,
    pub total_tokens: Option<u32>,
}

impl TokenUsage {
    pub fn validate(&self) -> Result<(), Error> {
        if let (Some(input), Some(output), Some(total)) =
            (self.input_tokens, self.output_tokens, self.total_tokens)
        {
            if input.saturating_add(output) > total {
                return Err(Error::InvalidTokenUsageTotals);
            }
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RuntimeClaim {
    pub runtime_kind: RuntimeKind,
    pub execution_topology: ExecutionTopology,
    pub replay_strength: ReplayStrength,
    pub determinism: DeterminismClaim,
    pub isolation: IsolationClaim,
    pub provider_routing: ProviderRoutingClaim,
}

impl RuntimeClaim {
    pub fn validate(&self) -> Result<(), Error> {
        if self.determinism.seed_bound && !self.determinism.deterministic {
            return Err(Error::InvalidRuntimeShape);
        }
        match self.runtime_kind {
            RuntimeKind::DeterministicDemo => {
                if !matches!(self.execution_topology, ExecutionTopology::RuleBasedLocal)
                    || self.replay_strength != ReplayStrength::FullyReplayable
                    || !self.determinism.deterministic
                    || !self.determinism.seed_bound
                {
                    return Err(Error::InvalidRuntimeShape);
                }
            }
            RuntimeKind::LocalOpenWeightModel | RuntimeKind::LocalClosedWeightModel => {
                if !matches!(
                    self.execution_topology,
                    ExecutionTopology::LocalProcess | ExecutionTopology::LocalContainer
                ) {
                    return Err(Error::InvalidRuntimeShape);
                }
            }
            RuntimeKind::HostedModelApi => {
                if !matches!(self.execution_topology, ExecutionTopology::RemoteProvider) {
                    return Err(Error::InvalidRuntimeShape);
                }
            }
            RuntimeKind::HostedModelGateway => {
                if !matches!(self.execution_topology, ExecutionTopology::RemoteGateway) {
                    return Err(Error::InvalidRuntimeShape);
                }
            }
            RuntimeKind::ExternalProcess => {
                if !matches!(
                    self.execution_topology,
                    ExecutionTopology::ExternalSubprocess
                ) {
                    return Err(Error::InvalidRuntimeShape);
                }
            }
            RuntimeKind::ReplayOnly => {
                if !matches!(self.execution_topology, ExecutionTopology::ReplayFile) {
                    return Err(Error::InvalidRuntimeShape);
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RuntimeKind {
    DeterministicDemo,
    LocalOpenWeightModel,
    LocalClosedWeightModel,
    HostedModelApi,
    HostedModelGateway,
    ExternalProcess,
    ReplayOnly,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExecutionTopology {
    RuleBasedLocal,
    LocalProcess,
    LocalContainer,
    RemoteProvider,
    RemoteGateway,
    ExternalSubprocess,
    ReplayFile,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum ReplayStrength {
    FullyReplayable,
    InputWeightsConfigBound,
    RequestResponseBound,
    DeclaredOnly,
    NotReplayable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DeterminismClaim {
    pub deterministic: bool,
    pub seed_bound: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct IsolationClaim {
    pub process_isolated: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ProviderRoutingClaim {
    pub fallbacks_allowed: bool,
    pub provider_pinned: bool,
    pub data_collection_policy: DataCollectionPolicy,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DataCollectionPolicy {
    DeclaredAllow,
    DeclaredDeny,
    Unknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PluginClaim<'a> {
    pub plugin_id_hash: Sha256Digest,
    pub plugin_version_hash: Sha256Digest,
    pub plugin_api_version: PluginApiVersion,
    pub maintainer_class: MaintainerClass,
    pub normalization: NormalizationClaim,
    pub plugin_manifest_hash: Sha256Digest,
    pub plugin_id_hint: BoundedBytes<'a, MAX_PLUGIN_ID_HINT_LEN>,
    pub trust_level: PluginTrustLevel,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PluginApiVersion {
    V1,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MaintainerClass {
    FirstPartyReference,
    ThirdParty,
    UserLocal,
    Unknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NormalizationClaim {
    pub input_normalized: bool,
    pub output_normalized: bool,
    pub raw_request_preserved: bool,
    pub raw_response_preserved: bool,
    pub secrets_redacted: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PluginTrustLevel {
    Untrusted,
    LocallyAllowed,
    FirstPartyReference,
    ThirdPartyTrusted,
    ReproduciblyBuilt,
}
