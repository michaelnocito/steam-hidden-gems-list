# Steam Hidden Gems — the list

A browsable, shareable front-end for **175 highly-rated Steam games that almost
nobody has played** — cheap, beloved, and under the radar.

**Live site:** https://michaelnocito.github.io/steam-hidden-gems-list/

Visitors can browse the picks (with cover art, ratings, and a one-line pitch),
jump straight to each game on Steam, and **vote on whether each pick really is a
hidden gem**.

## This repo vs. the methodology repo

- **This repo** — the fun, public-facing list. Static single-page site.
- **[steam-hidden-gems](https://github.com/michaelnocito/steam-hidden-gems)** — the
  *how*: the SQL, the 125,000-game dataset, the real-world data bug that had to be
  fixed first, and how the results were validated. That's the analyst story; this
  is the showcase.

## How the list was built (short version)

Out of ~125,000 games in the [FronkonGames Steam dataset](https://www.kaggle.com/datasets/fronkongames/steam-games-dataset),
exactly **175** clear every bar: **2,000+ reviews, 95%+ positive, priced ≤ $20,
and a small audience (under ~200k owners)**. Full write-up in the methodology repo.

## Files
| File | What it is |
|------|-----------|
| `index.html` | The whole site (single file). |
| `games.json` | The game list + ratings + pitches. Edit here to change the list. |
| `SETUP.md` | How to turn on live shared voting (free Supabase backend). |

## Editing the list
Everything shown comes from `games.json`. Add/remove a game or tweak a pitch there
and it updates on the next load — no code changes needed.

## Voting
Runs in local **preview mode** out of the box (votes stored per-browser). See
[`SETUP.md`](SETUP.md) to connect a free database and make voting live and shared.

---

Data: Steam Games Dataset by FronkonGames (Kaggle). Built by
[Michael Nocito](https://michaelnocito.github.io), data analyst.
