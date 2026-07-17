import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import {
  fieldIds,
  modelWaist,
  pluginClaim,
  policyFacts,
  receiptTlvLegacyV1,
  receiptTlvV2,
  runtimeClaim
} from "../src";

function parseRustFieldIds() {
  const rustPath = path.resolve(__dirname, "../../../../rust/crates/ink-core/src/field_ids.rs");
  const source = fs.readFileSync(rustPath, "utf8");
  const moduleRegex = /pub mod ([a-z0-9_]+) \{([\s\S]*?)\n\}/g;
  const constantRegex = /pub const ([A-Z0-9_]+): u16 = (\d+);/g;
  const result = new Map<string, Record<string, number>>();

  for (const match of source.matchAll(moduleRegex)) {
    const constants: Record<string, number> = {};
    for (const constantMatch of match[2].matchAll(constantRegex)) {
      constants[constantMatch[1]] = Number(constantMatch[2]);
    }
    result.set(match[1], constants);
  }

  return result;
}

test("generated field ids stay in sync with Rust", () => {
  const rust = parseRustFieldIds();

  assert.deepEqual(runtimeClaim, rust.get("runtime_claim"));
  assert.deepEqual(pluginClaim, rust.get("plugin_claim"));
  assert.deepEqual(policyFacts, rust.get("policy_facts"));
  assert.deepEqual(modelWaist, rust.get("model_waist"));
  assert.deepEqual(receiptTlvLegacyV1, rust.get("receipt_tlv_legacy_v1"));
  assert.deepEqual(receiptTlvV2, rust.get("receipt_tlv_v2"));
  assert.equal(fieldIds.receiptTlvV2.REASON_BASE, 20);
});
