# Handover: Gym-Bro and Gym-Gyal

Read this first if you are picking the project up. It is written for an agent with no memory of the earlier work.

## What this is

Two installable phone web apps (static files on GitHub Pages) for one household:

| App | Person | Phone | Repo | Live |
|---|---|---|---|---|
| Gym-Bro | Blue | Android, Chrome | `bluebaron42/Gym-Bro` | https://bluebaron42.github.io/Gym-Bro/ |
| Gym-Gyal | Harriett | iPhone, Safari home-screen app | `bluebaron42/Gym-Gyal` | https://bluebaron42.github.io/Gym-Gyal/ |

Each app has training (Today, Week), food (menus, recipes, shopping, Sunday run sheet, sync, timers) and progress.
Blue is the cook and the person you talk to. He is a chef: be precise about quantities and kitchen workflow.

## Files

Shared, and must be byte-identical in both repos (edit in Gym-Bro, then copy across):

- `index.html` all UI and logic, vanilla JS in one script, no build step
- `data.js` ingredients, recipes, household, defaults, shopping tables, sync address
- `guides.js` exercise form guides

Per repo: `profile.js` (who the phone belongs to, training plan, targets, theme), `sw.js`, `manifest.webmanifest`, icons, `README.md`.

Gym-Bro only: `tests/`, `tools/`, `firebase-rules.json`, this file.

## Rules that must not be broken

1. **No personal data in either repo.** Both are public. Body weight, waist, training logs, meal ticks and supplements live only in each phone's localStorage. Never commit them, and never sync them.
2. **Never commit the household sync key.** Blue supplies it in chat when needed. It is not stored anywhere in the repos.
3. **Shared files stay identical.** After any change: `cp index.html data.js guides.js ../gym-gyal/` and check with `cmp`.
4. **Bump `VERSION` in both `sw.js` files on every push**, or phones keep the old version.
5. **Run both checks before every push** (see below). Do not push on a failure.
6. **Remove what a change makes redundant.** Blue has asked for this explicitly: do not leave old features, duplicate text or dead code behind.
7. **Suggest first, then act** on design questions. Blue likes a short proposal, then a go-ahead. Push every change to both apps unless told otherwise. Keep reports short and honest about what was not verified.

## Working on it

```
# clone both repos side by side, e.g. /home/claude/gym-bro and /home/claude/gym-gyal
node gym-bro/tests/data-check.js            # recipe data consistency
python3 gym-bro/tests/app-check.py          # headless browser: both apps, run from the folder holding both repos
```

`app-check.py` needs Playwright with Chromium. It serves the repos locally and uses `tests/mock-db.py` as a stand-in
for the sync database. It covers: shopping totals for every view against an independent calculation, every recipe
card, week isolation, the run sheet (dependency order, one job per cook, kit limits), sync between two phones
(including offline and conflicting edits), timers, and the pinned-week rules.

Commit as `Claude <noreply@anthropic.com>` and push to `main`. GitHub Pages takes a few minutes; the sandbox
usually cannot reach `github.io`, so say plainly that the live site was not checked.

## How the food side works

**Household** (`HOUSE` in `data.js`): two people with portion scales (`p` protein and dairy, `c` carbs, fats and
sauces, `v` veg). Dinners and treats are shared (one choice, two portions). Breakfast, shake and lunch are per person.
Blue skips curries, so curries are lunch-only and only Harriett can pick them. No pork anywhere.

**Menus** are stored per week (`menus[mondayDate]`). Own and shared slots are keyed `slot+day` (`dinner1`, 0 = Sunday);
the other person's are prefixed `p:`. A meal resolves in this order: chosen for that week, a one-off `PRESETS` entry
for that week, what the week before had, then `DEFAULTS`. The first edit to a week freezes the whole week as shown.

**Recipes**: `ing` is grams per full portion and is the only source for shopping and macros. Seasoning lists live in
`comp` (Sunday components) and `sea` (anything else), as `"1 tsp cumin; 30 g greek yoghurt"`. Names in `ALIAS` are
the same food as an ingredient and must be covered by `ing`; `data-check.js` fails if they are not. Other names must
be in `CUPBOARD`. Methods carry no amounts.

- Dinners have `type`: `fresh` (cooked on the night, nothing on Sunday), `head` (marinade, coating or sauce on
  Sunday, cooked on the night), `sunday` (cooked and boxed on Sunday).
- Lunches have `late`: `freeze`, `split` (freeze the cooked part), or `no` (Monday to Wednesday only).

**Shopping list**: Household by default, or one person. Adds `TRIM` (peel and trim allowance) and shows a `PACKS`
guide. Pack sizes are typical UK sizes and have not been checked against a supermarket. Cupboard seasonings are a
checklist whose ticks persist.

**Sunday run sheet** (`runSheet` in `index.html`): turns every Sunday component of the chosen dishes into tasks with
hands-on minutes, unattended minutes, kit and dependencies, then schedules them on one or two cooks. Kit limits are
two oven trays at one temperature, four hob rings, one Instant Pot. The oven runs at 180°C or 200°C only. Dependencies
are derived from component order by kind; `after` on a recipe adds exceptions. Task durations are estimates that have
not been measured in a real prep session.

**Kitchen kit**: fan oven, four induction rings, Instant Pot (pressure, steam, rice, small air fryer), microwave, blender.

**Sync**: Firebase Realtime Database over plain REST and `EventSource`, no SDK. Address in `SYNC_URL`. Data sits under
`h/<household key>/`: `m` menus, `r` week resets, `s` ticks, `p` cupboard, `c` cooks, `t` timers. Every value carries
its time and the newest wins. Rules are in `firebase-rules.json` and are pasted into the Firebase console by Blue
(project `gym-app-6c933`). The sandbox can read the database with the key through a web fetch but cannot write to it.

**Timers**: ticking a timed run-sheet step starts a shared timer. The alarm is reliable only while the app is in
front, so the app keeps the screen awake. Lock-screen notifications are best effort; a guaranteed one would need a push server.

**Ordering the shop**: Blue gives the household key in chat, you read `h/<key>.json`, save it to a file, and run
`python3 gym-bro/tools/shop-from-sync.py state.json <monday> house` to get the list from the app's own logic.
Blue shops at Asda home delivery. Building the basket in a browser has not been done yet.

## State on 4 October 2026

Done: dish list rework, household menus, single ingredient source, household shopping, run sheet, sync, timers,
screen-awake, body weight in pounds for Harriett (stored in kg).

Open items:

- `PRESETS` in `data.js` pins the week of 5 Oct 2026 to what was already prepped. Delete it after that week;
  `data-check.js` starts failing three weeks later as a reminder.
- Run-sheet task times need tuning after a real prep session. Ask Blue which steps ran long.
- Screen-awake is unconfirmed on Harriett's iPhone.
- Build the Asda basket from the shopping list when Blue asks.
- The one-time migration of the old single `menu` storage key in `allMenus()` can be removed once both phones have opened a recent version.
- Earlier plan document and artifact are superseded; the apps are the source of truth.
