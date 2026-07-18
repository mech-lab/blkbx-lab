/* tslint:disable */
/* eslint-disable */

export function compare_receipts(old_bytes: Uint8Array, new_bytes: Uint8Array): string;

export function replay_receipt(receipt_bytes: Uint8Array, _evidence_bytes: Uint8Array): string;

export function verify_artifacts(input_json: string): string;

export function verify_bundle(bytes: Uint8Array): string;

export function verify_receipt(bytes: Uint8Array): string;

export function verify_receipt_with_context(bytes: Uint8Array, allow_unsigned: boolean, current_sequence?: bigint | null): string;

export function verify_receipt_with_policy(bytes: Uint8Array, allow_unsigned: boolean): string;

export function verify_receipt_with_trusted_key(bytes: Uint8Array, allow_unsigned: boolean, issuer_id: string, public_key_id: string, public_key_hex: string): string;

export function verify_receipt_with_trusted_key_and_context(bytes: Uint8Array, allow_unsigned: boolean, current_sequence: bigint | null | undefined, issuer_id: string, public_key_id: string, public_key_hex: string): string;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly compare_receipts: (a: number, b: number, c: number, d: number) => [number, number];
    readonly replay_receipt: (a: number, b: number, c: number, d: number) => [number, number];
    readonly verify_artifacts: (a: number, b: number) => [number, number];
    readonly verify_bundle: (a: number, b: number) => [number, number];
    readonly verify_receipt: (a: number, b: number) => [number, number];
    readonly verify_receipt_with_context: (a: number, b: number, c: number, d: number, e: bigint) => [number, number];
    readonly verify_receipt_with_policy: (a: number, b: number, c: number) => [number, number];
    readonly verify_receipt_with_trusted_key: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number) => [number, number];
    readonly verify_receipt_with_trusted_key_and_context: (a: number, b: number, c: number, d: number, e: bigint, f: number, g: number, h: number, i: number, j: number, k: number) => [number, number];
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
