# ink-ts-verify

TypeScript verifier primitives that mirror a narrow subset of the Rust receipt-verification surface.

This package is intentionally in-repo and non-shipping for the `1.0.0` release line. It exists to keep field ids, TLV primitives, and public vector handling aligned with the native verifier without changing the public trust boundary.

## Commands

```bash
npm install
npm run generate:field-ids
npm run typecheck
npm test
npm run build
```
