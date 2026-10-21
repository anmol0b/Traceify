import { describe, expect, it } from "vitest";
import { linkCitations } from "./citations";
import type { Tweet } from "./types";

const tweet = (id: string, text = "hello"): Tweet => ({
  id,
  text,
  likes: 0,
  views: 0,
  retweets: 0,
  created_at: "",
  has_media: false,
});

describe("linkCitations", () => {
  const tweets = [tweet("111", 'Say "hi"\nthere'), tweet("222")];

  it("links valid citations to the tweet", () => {
    expect(linkCitations("Rust [T2].", tweets, "maya")).toBe(
      'Rust [T2](https://x.com/maya/status/222 "hello").',
    );
  });

  it("handles adjacent, bold and full-width citations", () => {
    const out = linkCitations("a [T1][T2] b [**T1**] c 【T2】", tweets, "maya");
    expect(out.match(/https:\/\/x\.com\/maya\/status\//g)).toHaveLength(4);
    expect(out).toContain(`"Say 'hi' there"`);
  });

  it("leaves unknown IDs and existing links alone", () => {
    expect(linkCitations("[T9] and [T1](https://example.com)", tweets, "maya")).toBe(
      "[T9] and [T1](https://example.com)",
    );
  });
});
