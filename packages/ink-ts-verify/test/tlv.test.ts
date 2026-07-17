import assert from "node:assert/strict";
import test from "node:test";

import { TLVEncoder } from "../src";

type EncoderInternals = {
  writeBool(value: boolean): void;
  writeField(tag: number, value: Uint8Array): void;
  writeI64(value: number | bigint): void;
  writeU16(value: number): void;
  writeU32(value: number): void;
  writeU64(value: number | bigint): void;
};

test("TLVEncoder writes fixed-width integers without truncation", () => {
  const encoder = new TLVEncoder();
  const raw = encoder as unknown as EncoderInternals;

  raw.writeU16(0x1234);
  raw.writeU32(0x01020304);
  raw.writeU64(0x0102030405060708n);
  raw.writeBool(true);
  raw.writeI64(-1n);

  assert.deepEqual(Array.from(encoder.finalize()), [
    0x12,
    0x34,
    0x01,
    0x02,
    0x03,
    0x04,
    0x01,
    0x02,
    0x03,
    0x04,
    0x05,
    0x06,
    0x07,
    0x08,
    0x01,
    0xff,
    0xff,
    0xff,
    0xff,
    0xff,
    0xff,
    0xff,
    0xff
  ]);
});

test("TLVEncoder field framing matches the Rust TLV contract", () => {
  const shortEncoder = new TLVEncoder();
  const longEncoder = new TLVEncoder();
  const shortRaw = shortEncoder as unknown as EncoderInternals;
  const longRaw = longEncoder as unknown as EncoderInternals;

  shortRaw.writeField(0x20, new Uint8Array([0xaa, 0xbb]));
  longRaw.writeField(0x20, new Uint8Array(130).fill(0x55));

  assert.deepEqual(Array.from(shortEncoder.finalize()), [0x22, 0xaa, 0xbb]);

  const longBytes = Array.from(longEncoder.finalize());
  assert.deepEqual(longBytes.slice(0, 3), [0xa0, 0x00, 0x82]);
  assert.equal(longBytes.length, 133);
  assert(longBytes.slice(3).every((value) => value === 0x55));
});
