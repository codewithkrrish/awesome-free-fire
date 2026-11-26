# Contributing

Thanks for wanting to make the list better. The rules are short and they are all there for a reason.

## What belongs here

- A tool, site, app or community that a Free Fire player would genuinely use: stat trackers, tournament platforms, settings guides, content tools, wikis, news.
- Legit only. No mods, injectors, panels, diamond generators, or anything that breaks Garena's terms. If it can get someone's account banned, it does not go in, no matter how popular it is.
- Free, or free with a clearly labelled paid tier. If the useful part is paywalled, say so in the cost label.

## What does not belong here

- Mod APKs, "free diamond" sites, account sellers, boosting services.
- Anything that asks for a Free Fire password. A stats lookup that wants your login is a phishing page.
- Dead or parked domains, and sites you have not opened yourself.

## How to add an entry

1. Open the link yourself. Read the page. If you would not send it to a friend, do not add it.
2. Add one entry to `links.json`: `name`, `url`, `category`, `cost`, `note`.
   - `category` must be one of the existing categories in `links.json`.
   - `cost` must be `Free`, `Free to join`, or `Free with paid tier`.
   - `note` is one honest line, 40–280 characters, saying what the thing is actually good for. Not marketing copy.
3. Add the same entry to the matching section of `README.md`, with the same URL.
4. Run the checks before you send the PR:

   ```bash
   python -m pytest tests/ -q
   python scripts/check_links.py
   ```

   The tests fail if the README and `links.json` disagree, or if a banned word sneaks in. The link checker fails if your link is dead.

## Reporting a dead link

Open an issue with the link and what you saw. Or run the checker, fix `links.json`, and send a PR. Either way works.
