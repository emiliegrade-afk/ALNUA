import { describe, expect, it } from "vitest";

import { PASTE_AS_FILE_THRESHOLD, shouldConvertPasteToFile } from "@/lib/hub-files-api";

describe("hub-files paste threshold", () => {
  it("converts long paste only", () => {
    expect(shouldConvertPasteToFile(PASTE_AS_FILE_THRESHOLD - 1)).toBe(false);
    expect(shouldConvertPasteToFile(PASTE_AS_FILE_THRESHOLD)).toBe(true);
  });
});
