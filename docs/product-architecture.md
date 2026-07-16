# Product Architecture

Black Box Labs builds receipt-native infrastructure for high-assurance AI.

The umbrella story is:

> INK Receipts are the proof primitive. BLKBXS applies them to banking. MAND8 applies them to insurance. DUE applies them to legal defensibility.

## Current Repo Shape

The current shipped OSS runtime remains the root `mechlab-sdk` distribution:

- package: `mechlab-sdk`
- CLIs: `blkbx-lab`, `mechlab`
- Python namespaces: `blkbx_lab`, `mech_lab`
- stable product imports: `blkbxs`, `mand8`, `due`

This pass keeps the single-wheel install story while using sibling product slices as the source organization model.

```text
blkbx-lab/
  python/
    blkbxs/
    mand8/
    due/
  products/
    mand8-sdk/
    due-sdk/
```

## Product Roles

- `BLKBXS SDK`: banking-facing developer product
- `MAND8 SDK`: insurance-facing developer product
- `DUE SDK`: legal-facing developer product
- `INK Receipts`: shared proof primitive
- `Black Box Labs`: lab umbrella and repository

## MAND8

MAND8 asks:

> Can this AI risk be priced, underwritten, monitored, renewed, and defended?

MAND8 is UK-first by design. Delegated authority is a Lloyd's-native construct, and the Authority Receipt maps onto the binder logic that London market managing agents already operate, audit, and defend to the FCA and PRA. It is not positioned as a US insurance SDK retro-fitted for the UK.

## DUE

DUE asks:

> Can this AI-assisted action survive dispute, discovery, privilege review, disclosure review, and liability scrutiny?

DUE owns legal defensibility directly. It is not framed as “MAND8 for legal.”

## Integration Path

- Keep product language distinct by market.
- Keep integrity/signing lightweight for now through stub interfaces.
- Keep research and experimental helpers under umbrella namespaces with opt-in extras.
- Bind both slices to shared `packages/*` primitives in a later pass.
