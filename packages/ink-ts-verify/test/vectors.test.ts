import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

test("public receipt vectors stay readable from the package-local test suite", () => {
  const vectorsPath = path.resolve(__dirname, "../../../../test-vectors/ink-vectors.json");
  const payload = JSON.parse(fs.readFileSync(vectorsPath, "utf8"));

  assert.equal(payload.schema, "ink.vectors.v1");
  assert.equal(Array.isArray(payload.vectors), true);
  assert.equal(payload.vectors.length > 0, true);

  const [firstVector] = payload.vectors;
  assert.equal(firstVector.expect_status, "valid");
  assert.equal(firstVector.receipt.policy.version, "1.0.0");
  assert.equal(firstVector.verify_policy.policy_id, "BANK_STRICT_POLICY");
});
