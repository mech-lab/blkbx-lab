const input = document.getElementById("receipt-input");
const output = document.getElementById("verify-output");
const button = document.getElementById("verify-button");

button.addEventListener("click", () => {
  const raw = input.value.trim();
  if (!raw) {
    output.textContent = "Provide a receipt JSON artifact to inspect locally.";
    return;
  }

  try {
    const parsed = JSON.parse(raw);
    const summary = {
      status: "local-structure-check",
      schema: parsed.schema || null,
      receipt_id: parsed.receipt_id || null,
      issued_at: parsed.issued_at || null,
      has_integrity: Boolean(parsed.integrity)
    };
    output.textContent = JSON.stringify(summary, null, 2);
  } catch (error) {
    output.textContent = `Invalid JSON: ${error.message}`;
  }
});
