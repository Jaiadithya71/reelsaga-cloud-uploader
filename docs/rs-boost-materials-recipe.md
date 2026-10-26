# RS Boost materials download recipe (verified 2026-10-26)

Legitimate, portal-offered route for free promotional episode files. Zero spend; never
touch paywalled episodes. Do not commit downloaded media to this repo (it is public).

## Route

1. Sign in at https://cps.reelshort.com (session in the cloud browser profile).
2. Title detail page loads directly by URL (Content Hub cards do not route on click):
   `https://cps.reelshort.com/resource-square/detail/<book_id>?app=reelshort&book_type=1`
3. "Download Free Contents" picker lists exactly the free episodes (e.g. 1-8 of 56).
4. Click an episode number -> "Episode N" modal -> "Download to Local".
   The handler creates a temporary anchor with a fresh signed aliyun OSS URL
   (`v-out.oss-accelerate.aliyuncs.com/vod-112094/...-hd.mp4?...OSS4-HMAC-SHA256`,
   ~470 chars, ~2h expiry) and clicks it. The window.open popup lands on about:blank
   and is ignorable; the anchor href is the real link.
5. Capture the href in-page (prototype patch on HTMLAnchorElement.click) and fetch
   the file directly; verify bytes + sha256 against a recorded expectation before use.

## Verified file facts

- Escape Velocity EP1 (book_id 6ad4bcb96edae56c7c0b0ff5): 68,991,083 bytes,
  1080x1920 H.264 + stereo AAC 44.1 kHz, 189.0 s,
  sha256 49e5a0049adf319ea7dd6f8d9339d37fb2c382b9f39105acdf6269c1fe9cb6a9.
  Burned-in ReelShort logo (must not be removed under program terms).
- Catalog API (read-only, session bearer): POST /api/v1/book/all-book
  body {"app":"reelshort","sort":"time","language":"en","limit":40,page|cursor}.
  English catalog 800+ titles; no explicit AI flag in catalog data.

## Free ranges (as of 2026-10-26)

- Escape Velocity: 56 episodes, first 8 free. Release date 2026-10-22.
- The Stranded Astronaut vs. The Alien Pit (book_id 6ad5778787aba35f0b083f77):
  45 episodes, first 10 free.

A run from this source covers only the free range, never the full story; captions and
series framing must not claim full-series completion.

## AI-candidate cluster (frame-verified synthetic production, no vendor "AI" label)

- Escape Velocity (56 eps) - CGI/AI frames verified from the actual EP1 file.
- The Stranded Astronaut vs. The Alien Pit (45 eps) - CGI/AI frame verified on the
  public reelshort.com player.
- Same visual cluster, not frame-verified: They Enslaved Their CEO in the Deadliest
  Mine (6ad4c1a5f94521314309da39), Lost the Elf Crown, Found the Human Emperor
  (6ad5e1edc9be74c2020b2d8f).
