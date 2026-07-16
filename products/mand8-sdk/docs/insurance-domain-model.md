# Insurance Domain Model

MAND8 keeps the shared receipt envelope but speaks in insurance-native terms.

## Core Objects

- Risk Receipt: the main evidence object for an AI-assisted underwriting or monitoring action
- Exposure Unit: the insurable unit bound to a policy reference or binder reference
- Authority Receipt: evidence that the AI-assisted action stayed within delegated authority
- Control Receipt: evidence that required risk controls were checked
- Incident Receipt: evidence for anomaly, review, or claims-defensibility events
- Override Receipt: evidence that a human override occurred or was not required

## UK-First Frame

The UK-first frame is not cosmetic. Delegated authority, binder references, managing agents, coverholders, and FCA or PRA defensibility are first-class concepts in the product language.

The Authority Receipt maps to:

- delegated-authority terms
- binder logic
- managing-agent oversight
- auditability for FCA and PRA review

## Bundle Audiences

- Lloyd's underwriter
- managing agent
- MGA or coverholder
- reinsurer
- accelerator reviewer
