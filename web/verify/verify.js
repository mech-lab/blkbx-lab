import init, { verify_artifacts } from "./pkg/ink_wasm.js";

const artifactUrlInput = document.getElementById("artifact-url");
const receiptInput = document.getElementById("receipt-input");
const manifestInput = document.getElementById("manifest-input");
const policyInput = document.getElementById("policy-input");
const registryInput = document.getElementById("registry-input");
const revocationsInput = document.getElementById("revocations-input");
const contextOutput = document.getElementById("context-output");
const reportOutput = document.getElementById("report-output");
const summaryCard = document.getElementById("summary-card");
const summaryStatus = document.getElementById("summary-status");
const summaryCode = document.getElementById("summary-code");
const summaryText = document.getElementById("summary-text");
const summaryScope = document.getElementById("summary-scope");
const summaryEngine = document.getElementById("summary-engine");
const loadArtifactsButton = document.getElementById("load-artifacts");
const verifyButton = document.getElementById("verify-button");
const clearButton = document.getElementById("clear-button");

let wasmReady;
let currentContext = null;

function readJsonField(input) {
  const value = input.value.trim();
  if (!value) {
    return null;
  }
  return JSON.parse(value);
}

function writeJsonField(input, value) {
  input.value = value ? JSON.stringify(value, null, 2) : "";
}

function setSummary(report) {
  const status = report?.summary_status || "idle";
  const label = status === "pass" ? "Pass" : status === "warning" ? "Warning" : status === "fail" ? "Fail" : "Idle";
  summaryCard.dataset.status = status;
  summaryStatus.textContent = label;
  summaryCode.textContent = report?.code || "Awaiting verification input.";
  summaryText.textContent = report?.summary_text || "Load a verifier handoff or paste a portable receipt to run verification locally.";
  summaryScope.textContent = report?.scope || "n/a";
  summaryEngine.textContent = report?.verification_engine || "Rust ink-wasm";
}

function setContext(context) {
  currentContext = context || null;
  contextOutput.textContent = currentContext
    ? JSON.stringify(currentContext, null, 2)
    : "No handoff context loaded.";
}

function clearInputs() {
  artifactUrlInput.value = "";
  writeJsonField(receiptInput, null);
  writeJsonField(manifestInput, null);
  writeJsonField(policyInput, null);
  writeJsonField(registryInput, null);
  writeJsonField(revocationsInput, null);
  setContext(null);
  reportOutput.textContent = "Awaiting local verification input.";
  setSummary(null);
}

async function loadArtifacts(url) {
  const response = await fetch(url, { credentials: "same-origin" });
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Artifact handoff unavailable. The selected workspace context does not carry a portable ink.receipt.v2 companion.");
    }
    if (response.status === 422) {
      throw new Error("Artifact handoff rejected. The selected workspace is not a MAND8 workspace.");
    }
    throw new Error(`Failed to load artifact handoff: ${response.status}`);
  }
  const payload = await response.json();
  writeJsonField(receiptInput, payload.receipt);
  writeJsonField(manifestInput, payload.manifest);
  writeJsonField(policyInput, payload.verification_policy);
  writeJsonField(registryInput, payload.trust_registry);
  writeJsonField(revocationsInput, payload.revocations);
  setContext(payload.context || null);
  return payload;
}

async function runVerification() {
  await wasmReady;
  const payload = {
    receipt: readJsonField(receiptInput),
    manifest: readJsonField(manifestInput),
    verification_policy: readJsonField(policyInput),
    trust_registry: readJsonField(registryInput),
    revocations: readJsonField(revocationsInput),
  };
  const rawReport = verify_artifacts(JSON.stringify(payload));
  const report = JSON.parse(rawReport);
  reportOutput.textContent = JSON.stringify(report, null, 2);
  setSummary(report);
}

loadArtifactsButton.addEventListener("click", async () => {
  const url = artifactUrlInput.value.trim();
  if (!url) {
    reportOutput.textContent = "Provide an artifact handoff URL first.";
    setSummary({
      summary_status: "fail",
      code: "ARTIFACT_URL_REQUIRED",
      summary_text: "Artifact URL is required to load a verifier handoff.",
      scope: "receipt-only",
      verification_engine: "Rust ink-wasm",
    });
    return;
  }

  try {
    await loadArtifacts(url);
    reportOutput.textContent = "Artifact handoff loaded. Run verification to render the Rust report.";
    setSummary({
      summary_status: "warning",
      code: "HANDOFF_READY",
      summary_text: "Artifact handoff loaded. Run verification to evaluate the supplied receipt and evidence inputs.",
      scope: "receipt-only",
      verification_engine: "Rust ink-wasm",
    });
  } catch (error) {
    reportOutput.textContent = error.message;
    setSummary({
      summary_status: "fail",
      code: "HANDOFF_LOAD_FAILED",
      summary_text: error.message,
      scope: "receipt-only",
      verification_engine: "Rust ink-wasm",
    });
  }
});

verifyButton.addEventListener("click", async () => {
  try {
    await runVerification();
  } catch (error) {
    reportOutput.textContent = error.message;
    setSummary({
      summary_status: "fail",
      code: "VERIFY_UI_ERROR",
      summary_text: error.message,
      scope: "receipt-only",
      verification_engine: "Rust ink-wasm",
    });
  }
});

clearButton.addEventListener("click", clearInputs);

wasmReady = init().then(async () => {
  const params = new URLSearchParams(window.location.search);
  const artifactUrl = params.get("artifact_url");
  if (artifactUrl) {
    artifactUrlInput.value = artifactUrl;
    try {
      await loadArtifacts(artifactUrl);
      await runVerification();
    } catch (error) {
      reportOutput.textContent = error.message;
      setSummary({
        summary_status: "fail",
        code: "AUTOLOAD_FAILED",
        summary_text: error.message,
        scope: "receipt-only",
        verification_engine: "Rust ink-wasm",
      });
    }
  }
});
