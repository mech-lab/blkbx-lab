pub mod runtime_claim {
    pub const DOMAIN: u16 = 1;
    pub const RUNTIME_KIND: u16 = 2;
    pub const EXECUTION_TOPOLOGY: u16 = 3;
    pub const REPLAY_STRENGTH: u16 = 4;
    pub const DETERMINISTIC: u16 = 5;
    pub const SEED_BOUND: u16 = 6;
    pub const PROCESS_ISOLATED: u16 = 7;
    pub const FALLBACKS_ALLOWED: u16 = 8;
    pub const PROVIDER_PINNED: u16 = 9;
    pub const DATA_COLLECTION_POLICY: u16 = 10;
}

pub mod plugin_claim {
    pub const PLUGIN_ID_HASH: u16 = 1;
    pub const PLUGIN_VERSION_HASH: u16 = 2;
    pub const PLUGIN_API_VERSION: u16 = 3;
    pub const MAINTAINER_CLASS: u16 = 4;
    pub const INPUT_NORMALIZED: u16 = 5;
    pub const OUTPUT_NORMALIZED: u16 = 6;
    pub const RAW_REQUEST_PRESERVED: u16 = 7;
    pub const RAW_RESPONSE_PRESERVED: u16 = 8;
    pub const SECRETS_REDACTED: u16 = 9;
    pub const PLUGIN_MANIFEST_HASH: u16 = 10;
    pub const PLUGIN_ID_HINT: u16 = 11;
    pub const TRUST_LEVEL: u16 = 12;
}

pub mod policy_facts {
    pub const DOMAIN: u16 = 1;
    pub const RISK_CLASS: u16 = 2;
    pub const REQUIRES_HUMAN_REVIEW: u16 = 3;
    pub const BINDING_EFFECT_PRESENT: u16 = 4;
    pub const PROVIDER_FALLBACKS_ALLOWED: u16 = 5;
    pub const PLUGIN_TRUST_LEVEL: u16 = 6;
    pub const RUNTIME_KIND: u16 = 7;
    pub const REPLAY_STRENGTH: u16 = 8;
    pub const MODEL_CLASS: u16 = 9;
}

pub mod model_waist {
    pub const DOMAIN: u16 = 1;
    pub const MODEL_CLASS: u16 = 2;
    pub const MODEL_REF_HASH: u16 = 3;
    pub const MODEL_SLUG: u16 = 4;
    pub const IDENTITY_EVIDENCE_KIND: u16 = 5;
    pub const IDENTITY_EVIDENCE_DIGEST_A: u16 = 6;
    pub const IDENTITY_EVIDENCE_DIGEST_B: u16 = 7;
    pub const IDENTITY_EVIDENCE_DIGEST_C: u16 = 8;
    pub const ACTION_HASH: u16 = 9;
    pub const MESSAGES_HASH: u16 = 10;
    pub const SYSTEM_PROMPT_HASH: u16 = 11;
    pub const TOOL_SPEC_HASH: u16 = 12;
    pub const RESPONSE_SCHEMA_HASH: u16 = 13;
    pub const PARAMETERS_HASH: u16 = 14;
    pub const REQUESTED_OUTPUT_KIND: u16 = 15;
    pub const REQUESTED_OUTPUT_DIGEST: u16 = 16;
    pub const OUTPUT_TEXT_HASH: u16 = 17;
    pub const STRUCTURED_OUTPUT_HASH: u16 = 18;
    pub const PROVIDER_METADATA_HASH: u16 = 19;
    pub const FINISH_REASON: u16 = 20;
    pub const INPUT_TOKENS: u16 = 21;
    pub const OUTPUT_TOKENS: u16 = 22;
    pub const TOTAL_TOKENS: u16 = 23;
    pub const RUNTIME_HASH: u16 = 24;
    pub const PLUGIN_HASH: u16 = 25;
}

pub mod receipt_tlv_legacy_v1 {
    pub const DOMAIN: u16 = 1;
    pub const SCHEMA_VERSION: u16 = 2;
    pub const RECEIPT_ID: u16 = 3;
    pub const RECEIPT_PROFILE: u16 = 4;
    pub const ACTION_ID: u16 = 5;
    pub const ISSUED_AT_SECONDS: u16 = 6;
    pub const ISSUED_AT_NANOS: u16 = 7;
    pub const ISSUER_NAME: u16 = 8;
    pub const KEY_ID: u16 = 9;
    pub const PUBLIC_KEY: u16 = 10;
    pub const MANIFEST_HASH: u16 = 11;
    pub const POLICY_ID: u16 = 12;
    pub const POLICY_VERSION: u16 = 13;
    pub const POLICY_HASH: u16 = 14;
    pub const RUNTIME_HASH: u16 = 15;
    pub const MODEL_HASH: u16 = 16;
    pub const FACTS_HASH: u16 = 17;
    pub const DECISION: u16 = 18;
    pub const REASON: u16 = 19;
    pub const EVIDENCE_SUMMARY_HASH: u16 = 20;
    pub const CONTROLS_SUMMARY_HASH: u16 = 21;
}

pub mod receipt_tlv_v2 {
    pub const DOMAIN: u16 = 1;
    pub const SCHEMA_VERSION: u16 = 2;
    pub const RECEIPT_ID: u16 = 3;
    pub const RECEIPT_PROFILE: u16 = 4;
    pub const ACTION_ID: u16 = 5;
    pub const ISSUED_AT_SECONDS: u16 = 6;
    pub const ISSUED_AT_NANOS: u16 = 7;
    pub const ISSUER_NAME: u16 = 8;
    pub const KEY_ID: u16 = 9;
    pub const PUBLIC_KEY: u16 = 10;
    pub const MANIFEST_HASH: u16 = 11;
    pub const POLICY_ID: u16 = 12;
    pub const POLICY_VERSION: u16 = 13;
    pub const POLICY_HASH: u16 = 14;
    pub const RUNTIME_HASH: u16 = 15;
    pub const MODEL_HASH: u16 = 16;
    pub const FACTS_HASH: u16 = 17;
    pub const DECISION: u16 = 18;
    pub const REASON_COUNT: u16 = 19;
    pub const REASON_BASE: u16 = 20;
    pub const EVIDENCE_SUMMARY_HASH: u16 = 52;
    pub const CONTROLS_SUMMARY_HASH: u16 = 53;
}
