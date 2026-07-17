# ink-ts-verify

TypeScript verifier primitives that mirror a narrow subset of the native receipt-verification surface.

This package is intentionally in-repo and non-shipping for the current release line. It exists to keep field ids, TLV primitives, and verifier-facing types aligned with the native Rust trust boundary without redefining that boundary.

## Commands

```bash
npm install
npm run generate:field-ids
npm run typecheck
npm test
npm run build
```
