/*
 * This file is generated from Rust's field_ids.rs. Do not modify directly.
 * Use packages/ink-ts-verify/scripts/generate-field-ids.mjs to update.
 */

// Rust field IDs from ink-core/src/field_ids.rs

export const runtimeClaim = {
  DOMAIN: 1,
  RUNTIME_KIND: 2,
  EXECUTION_TOPOLOGY: 3,
  REPLAY_STRENGTH: 4,
  DETERMINISTIC: 5,
  SEED_BOUND: 6,
  PROCESS_ISOLATED: 7,
  FALLBACKS_ALLOWED: 8,
  PROVIDER_PINNED: 9,
  DATA_COLLECTION_POLICY: 10,
} as const;

export const pluginClaim = {
  PLUGIN_ID_HASH: 1,
  PLUGIN_VERSION_HASH: 2,
  PLUGIN_API_VERSION: 3,
  MAINTAINER_CLASS: 4,
  INPUT_NORMALIZED: 5,
  OUTPUT_NORMALIZED: 6,
  RAW_REQUEST_PRESERVED: 7,
  RAW_RESPONSE_PRESERVED: 8,
  SECRETS_REDACTED: 9,
  PLUGIN_MANIFEST_HASH: 10,
  PLUGIN_ID_HINT: 11,
  TRUST_LEVEL: 12,
} as const;

export const policyFacts = {
  DOMAIN: 1,
  RISK_CLASS: 2,
  REQUIRES_HUMAN_REVIEW: 3,
  BINDING_EFFECT_PRESENT: 4,
  PROVIDER_FALLBACKS_ALLOWED: 5,
  PLUGIN_TRUST_LEVEL: 6,
  RUNTIME_KIND: 7,
  REPLAY_STRENGTH: 8,
  MODEL_CLASS: 9,
} as const;

export const modelWaist = {
  DOMAIN: 1,
  MODEL_CLASS: 2,
  MODEL_REF_HASH: 3,
  MODEL_SLUG: 4,
  IDENTITY_EVIDENCE_KIND: 5,
  IDENTITY_EVIDENCE_DIGEST_A: 6,
  IDENTITY_EVIDENCE_DIGEST_B: 7,
  IDENTITY_EVIDENCE_DIGEST_C: 8,
  ACTION_HASH: 9,
  MESSAGES_HASH: 10,
  SYSTEM_PROMPT_HASH: 11,
  TOOL_SPEC_HASH: 12,
  RESPONSE_SCHEMA_HASH: 13,
  PARAMETERS_HASH: 14,
  REQUESTED_OUTPUT_KIND: 15,
  REQUESTED_OUTPUT_DIGEST: 16,
  OUTPUT_TEXT_HASH: 17,
  STRUCTURED_OUTPUT_HASH: 18,
  PROVIDER_METADATA_HASH: 19,
  FINISH_REASON: 20,
  INPUT_TOKENS: 21,
  OUTPUT_TOKENS: 22,
  TOTAL_TOKENS: 23,
  RUNTIME_HASH: 24,
  PLUGIN_HASH: 25,
} as const;

export const receiptTlvLegacyV1 = {
  DOMAIN: 1,
  SCHEMA_VERSION: 2,
  RECEIPT_ID: 3,
  RECEIPT_PROFILE: 4,
  ACTION_ID: 5,
  ISSUED_AT_SECONDS: 6,
  ISSUED_AT_NANOS: 7,
  ISSUER_NAME: 8,
  KEY_ID: 9,
  PUBLIC_KEY: 10,
  MANIFEST_HASH: 11,
  POLICY_ID: 12,
  POLICY_VERSION: 13,
  POLICY_HASH: 14,
  RUNTIME_HASH: 15,
  MODEL_HASH: 16,
  FACTS_HASH: 17,
  DECISION: 18,
  REASON: 19,
  EVIDENCE_SUMMARY_HASH: 20,
  CONTROLS_SUMMARY_HASH: 21,
} as const;

export const receiptTlvV2 = {
  DOMAIN: 1,
  SCHEMA_VERSION: 2,
  RECEIPT_ID: 3,
  RECEIPT_PROFILE: 4,
  ACTION_ID: 5,
  ISSUED_AT_SECONDS: 6,
  ISSUED_AT_NANOS: 7,
  ISSUER_NAME: 8,
  KEY_ID: 9,
  PUBLIC_KEY: 10,
  MANIFEST_HASH: 11,
  POLICY_ID: 12,
  POLICY_VERSION: 13,
  POLICY_HASH: 14,
  RUNTIME_HASH: 15,
  MODEL_HASH: 16,
  FACTS_HASH: 17,
  DECISION: 18,
  REASON_COUNT: 19,
  REASON_BASE: 20,
  EVIDENCE_SUMMARY_HASH: 52,
  CONTROLS_SUMMARY_HASH: 53,
} as const;

export const fieldIds = {
  runtimeClaim,
  pluginClaim,
  policyFacts,
  modelWaist,
  receiptTlvLegacyV1,
  receiptTlvV2,
} as const;

export type RuntimeClaimFieldIds = typeof runtimeClaim;
export type PluginClaimFieldIds = typeof pluginClaim;
export type PolicyFactsFieldIds = typeof policyFacts;
export type ModelWaistFieldIds = typeof modelWaist;
export type ReceiptTlvLegacyV1FieldIds = typeof receiptTlvLegacyV1;
export type ReceiptTlvV2FieldIds = typeof receiptTlvV2;
export type FieldIds = typeof fieldIds;
