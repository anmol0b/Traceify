import type { Tweet } from "./types";

// [T4], plus the variants models produce: 【T4】 and [**T4**].
const CITATION = /(?:\[|【)\**T(\d+)\**(?:\]|】)(?!\()/g;

/** Turn [T4] citations into markdown links to the tweet on X. Unknown IDs are left as plain text. */
export function linkCitations(markdown: string, tweets: Tweet[], handle: string): string {
  return markdown.replace(CITATION, (match, n: string) => {
    const tweet = tweets[Number(n) - 1];
    if (!tweet) return match;
    return `[T${n}](https://x.com/${handle}/status/${tweet.id} "${tweetTitle(tweet)}")`;
  });
}

function tweetTitle(tweet: Tweet): string {
  const text = tweet.text.replace(/\s+/g, " ").replace(/["\\]/g, "'");
  return text.length > 120 ? `${text.slice(0, 119)}…` : text;
}
