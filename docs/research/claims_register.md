# Research Claims Register

This register tracks actuarial-annotation claims derived from the Duke/Bankabil computational actuarial geometry proposal. These claims are research-only and must not be treated as receipt-kernel semantics, legal conclusions, actuarial opinions, insurance determinations, reserve formulas, or regulatory compliance statements.

| Claim | Status | Evidence Required | Boundary |
| --- | --- | --- | --- |
| Receipt completeness can be represented as a bounded score over required evidence coordinates. | Research claim | Paper 3 validator with positive/negative fixtures and stable domain-profile weights. | May appear only as `ink.actuarial_annotation.v1`; never as a receipt TLV field or product receipt field. |
| Evidence defects can be classified into missing, corrupted, delayed, contradictory, unverifiable, or suppressed coordinates. | Research claim | Paper 3 validator plus reviewed defect taxonomy mapped to real receipt examples. | Defects are interpretation of receipt data; they do not define receipt validity. |
| A defensibility score can summarize receipt observability, authority evidence, human review, verification presence, controls, and transparent exception handling. | Research claim | Paper 3 validator plus Paper 5 pilot review of whether the score helps reviewers without overstating legal/insurance meaning. | Must be badged `Research / unvalidated`; must not drive `renewal_ready` or customer-facing readiness booleans. |
| Evidence penalty can model observability loss from incomplete or unverifiable receipts. | Research claim | Paper 4 simulation showing sensitivity under transparent assumptions. | Research-only signal; not a capital, reserve, premium, solvency, or regulatory formula. |
| Reserve sensitivity may vary with completeness, defensibility, exception frequency, and verification status in synthetic portfolios. | Research claim | Paper 4 simulation results with documented assumptions and stress scenarios. | Simulation result only until externally validated by actuarial review and real evidence. |

Graduation requires both a stable Paper 3 validator and Paper 4 simulation evidence. Until then, annotations remain opt-in, unvalidated research outputs outside the receipt trust boundary.
