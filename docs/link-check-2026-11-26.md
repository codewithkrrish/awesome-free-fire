# Link check — 2026-11-26

Checked with `python scripts/check_links.py`. 28 links total.

## Result

- 24 OK — the site answered 200
- 4 guarded — the site blocks automated checks (403/429) but was confirmed by hand
- 0 dead

## Guarded links (confirmed by hand, not dead)

| Link | What was seen |
| --- | --- |
| Garena player support (`ffsupport.garena.com`) | 403 to scripts; Garena's real support portal, confirmed via search |
| Canva (`canva.com`) | 403 to scripts; the real Canva homepage |
| Free Fire Wiki (`freefire.fandom.com`) | 403 to scripts; page fetched and read in full via browser on 2026-11-26 |
| Liquipedia Free Fire (`liquipedia.net`) | 429 to scripts; rate-limited, the real Liquipedia Free Fire portal |

## Method

Each URL in `links.json` was opened with a browser user agent. Anything
returning 404, 500, a timeout or a DNS failure counts as dead and fails
the check. Guarded links do not fail it — they are re-confirmed by hand
when the list is reviewed.
