import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(packageRoot, "..", "..");
const rustSource = path.join(repoRoot, "rust", "crates", "ink-core", "src", "field_ids.rs");
const outputPath = path.join(packageRoot, "src", "generated", "fieldIds.ts");

const moduleNameMap = new Map([
  ["runtime_claim", "runtimeClaim"],
  ["plugin_claim", "pluginClaim"],
  ["policy_facts", "policyFacts"],
  ["model_waist", "modelWaist"],
  ["receipt_tlv_legacy_v1", "receiptTlvLegacyV1"],
  ["receipt_tlv_v2", "receiptTlvV2"]
]);

function pascalCase(name) {
  return name.charAt(0).toUpperCase() + name.slice(1);
}

function parseRustModules(source) {
  const moduleRegex = /pub mod ([a-z0-9_]+) \{([\s\S]*?)\n\}/g;
  const constantRegex = /pub const ([A-Z0-9_]+): u16 = (\d+);/g;
  const modules = [];

  for (const match of source.matchAll(moduleRegex)) {
    const rustName = match[1];
    const jsName = moduleNameMap.get(rustName);
    if (!jsName) {
      continue;
    }

    const constants = [];
    for (const constantMatch of match[2].matchAll(constantRegex)) {
      constants.push({
        name: constantMatch[1],
        value: Number(constantMatch[2])
      });
    }
    modules.push({ rustName, jsName, constants });
  }

  return modules;
}

function render(modules) {
  const lines = [
    "/*",
    " * This file is generated from Rust's field_ids.rs. Do not modify directly.",
    " * Use packages/ink-ts-verify/scripts/generate-field-ids.mjs to update.",
    " */",
    "",
    "// Rust field IDs from ink-core/src/field_ids.rs",
    ""
  ];

  for (const module of modules) {
    lines.push(`export const ${module.jsName} = {`);
    for (const constant of module.constants) {
      lines.push(`  ${constant.name}: ${constant.value},`);
    }
    lines.push("} as const;", "");
  }

  lines.push("export const fieldIds = {");
  for (const module of modules) {
    lines.push(`  ${module.jsName},`);
  }
  lines.push("} as const;", "");

  for (const module of modules) {
    lines.push(
      `export type ${pascalCase(module.jsName)}FieldIds = typeof ${module.jsName};`
    );
  }
  lines.push("export type FieldIds = typeof fieldIds;", "");

  return `${lines.join("\n")}`;
}

const source = fs.readFileSync(rustSource, "utf8");
const rendered = render(parseRustModules(source));
const checkOnly = process.argv.includes("--check");

if (checkOnly) {
  const current = fs.readFileSync(outputPath, "utf8");
  if (current !== rendered) {
    console.error("generated field ids are out of date");
    process.exit(1);
  }
  process.exit(0);
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, rendered);
