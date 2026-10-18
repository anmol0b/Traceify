import { describe, expect, it } from "vitest";
import { normalizeHandle } from "./handle";

// Same cases as backend/tests/test_profiles.py, so the two parsers stay in sync.
describe("normalizeHandle", () => {
  it.each([
    ["naval", "naval"],
    ["@naval", "naval"],
    ["  @naval  ", "naval"],
    ["https://x.com/naval", "naval"],
    ["x.com/naval/status/123", "naval"],
    ["https://twitter.com/jack?lang=en", "jack"],
    ["www.x.com/elonmusk/", "elonmusk"],
    ["a_b_C_123", "a_b_C_123"],
  ])("accepts %j", (raw, expected) => {
    expect(normalizeHandle(raw)).toBe(expected);
  });

  it.each(["", "   ", "bad handle!", "this_handle_is_way_too_long", "https://x.com/", "https://evil.com/x.com/naval"])(
    "rejects %j",
    (raw) => {
      expect(normalizeHandle(raw)).toBeNull();
    },
  );
});
