/*
 * TypeScript implementation of TLV primitives.
 * These functions mirror the Rust implementation in ink-core/src/tlv.rs
 * and must produce byte-exact output for verification parity.
 */

export class TLVEncoder {
  private buffer: Uint8Array;
  private position: number;

  constructor(initialCapacity = 1024) {
    this.buffer = new Uint8Array(initialCapacity);
    this.position = 0;
  }

  private ensureCapacity(required: number): void {
    if (this.buffer.length - this.position < required) {
      const newSize = Math.max(this.buffer.length * 2, this.position + required);
      const newBuffer = new Uint8Array(newSize);
      newBuffer.set(this.buffer);
      this.buffer = newBuffer;
    }
  }

  private writeByte(value: number): void {
    this.ensureCapacity(1);
    this.buffer[this.position++] = value;
  }

  private writeU8(value: number): void {
    this.writeByte(value);
  }

  private writeU16(value: number): void {
    this.writeByte((value >> 8) & 0xFF);
    this.writeByte(value & 0xFF);
  }

  private writeU32(value: number): void {
    this.writeByte((value >> 24) & 0xFF);
    this.writeByte((value >> 16) & 0xFF);
    this.writeByte((value >> 8) & 0xFF);
    this.writeByte(value & 0xFF);
  }

  private writeU64(value: number | bigint): void {
    const normalized = BigInt(value);
    for (let i = 0; i < 8; i++) {
      const shift = BigInt(56 - i * 8);
      this.writeByte(Number((normalized >> shift) & 0xFFn));
    }
  }

  private writeI64(value: number | bigint): void {
    this.writeU64(BigInt.asUintN(64, BigInt(value)));
  }

  private writeBool(value: boolean): void {
    this.writeByte(value ? 0x01 : 0x00);
  }

  private writeDigest(digest: Uint8Array): void {
    if (digest.length !== 32) {
      throw new Error(`Invalid digest length: ${digest.length}, expected 32`);
    }
    this.writeU8(0x20); // Tag for digest (assumed from Rust)
    this.writeU8(0x20); // Length of digest
    this.writeRawBytes(digest);
  }

  private writeRawBytes(data: Uint8Array): void {
    this.ensureCapacity(data.length);
    this.buffer.set(data, this.position);
    this.position += data.length;
  }

  private writeBytes(data: Uint8Array): void {
    if (data.length > 0xFF) {
      throw new Error(`Data too long to encode length: ${data.length}`);
    }
    this.writeByte(data.length);
    this.writeRawBytes(data);
  }

  private writeOptionalField(tag: number, length: number, value: Uint8Array): void {
    this.writeByte(tag);
    this.writeByte(length);
    if (length > 0) {
      this.writeRawBytes(value);
    }
  }

  private writeField(tag: number, value: Uint8Array): void {
    const length = value.length;
    if (length <= 0x7F) {
      this.writeByte(tag | length);
    } else if (length <= 0xFFFF) {
      this.writeByte(tag | 0x80);
      this.writeU8((length >> 8) & 0xFF);
      this.writeByte(length & 0xFF);
    } else {
      throw new Error(`Field value too long to encode: ${length}`);
    }
    this.writeRawBytes(value);
  }

  public finalize(): Uint8Array {
    const result = new Uint8Array(this.position);
    result.set(this.buffer.subarray(0, this.position));
    return result;
  }
}
