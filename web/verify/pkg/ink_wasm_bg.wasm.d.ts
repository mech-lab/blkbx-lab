/* tslint:disable */
/* eslint-disable */
export const memory: WebAssembly.Memory;
export const compare_receipts: (a: number, b: number, c: number, d: number) => [number, number];
export const replay_receipt: (a: number, b: number, c: number, d: number) => [number, number];
export const verify_artifacts: (a: number, b: number) => [number, number];
export const verify_bundle: (a: number, b: number) => [number, number];
export const verify_receipt: (a: number, b: number) => [number, number];
export const verify_receipt_with_context: (a: number, b: number, c: number, d: number, e: bigint) => [number, number];
export const verify_receipt_with_policy: (a: number, b: number, c: number) => [number, number];
export const verify_receipt_with_trusted_key: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => [number, number];
export const verify_receipt_with_trusted_key_and_context: (a: number, b: number, c: number, d: number, e: bigint, f: number, g: number, h: number, i: number, j: number, k: number) => [number, number];
export const __wbindgen_externrefs: WebAssembly.Table;
export const __wbindgen_malloc: (a: number, b: number) => number;
export const __wbindgen_free: (a: number, b: number, c: number) => void;
export const __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
export const __wbindgen_start: () => void;
