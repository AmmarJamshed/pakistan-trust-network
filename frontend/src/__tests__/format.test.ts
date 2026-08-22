import { describe, expect, it } from "vitest";
import { formatDate, truncateHash } from "../lib/format";

describe("formatDate", () => {
  it("formats a valid ISO date", () => {
    const result = formatDate("2024-06-15T12:00:00.000Z");
    expect(result).toMatch(/2024/);
    expect(result).toMatch(/Jun|June|15/);
  });

  it("returns em dash for null or invalid", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
    expect(formatDate("not-a-date")).toBe("—");
  });
});

describe("truncateHash", () => {
  it("truncates long hashes", () => {
    const hash = "abcdef0123456789abcdef0123456789";
    expect(truncateHash(hash, 4)).toBe("abcd…6789");
  });
});
