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
- `guides.js` exercise form guides: gym versions by exercise id, home versions by home exercise name (`GB_HOME_MAP`). A guide with `u` is done one side at a time, and the card then spells out what a set means. `data-check.js` fails if any exercise in either profile lacks a gym or home guide.

Per repo: `profile.js` (who the phone belongs to, training plan, targets, theme), `sw.js`, `manifest.webmanifest`, icons, `README.md`.

Gym-Bro only: `tests/`, `tools/`, `firebase-rules.json`, this file.

## Rules that must not be broken

1. **No personal data in either repo.** Both are public. Body weight, waist, training logs, meals eaten and supplements live in each phone's localStorage. Never commit them, and never put them in the household sync area. The only way they leave a phone is the owner's own opt-in "Share my record with Claude" switch (below) or a backup file they choose to send.
2. **Never commit the household sync key or a review key.** Blue supplies them in chat when needed. They are not stored anywhere in the repos.
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

Commit as `Claude <noreply@anthropic.com>` and push to `main`. Then confirm it actually published, because GitHub
sometimes cancels the publishing run and the phones silently stay on the old version:

- `gh api repos/bluebaron42/<repo>/commits/main/check-runs` should show `deploy` completed with `success`.
- A web fetch of `https://bluebaron42.github.io/<repo>/sw.js?v=<anything new>` should show the `VERSION` you pushed
  (shell tools cannot reach `github.io`; the web fetch tool can).
- If the run was cancelled or skipped, push an empty commit to that repo to publish again.

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

- Breakfasts are built in whole pieces and are on the run sheet for all seven days. `pieces: true` = small ones: `ing` is one piece
  and each person has `HOUSE.people[x].pieces` of them (Blue 2, Harriett 1), with no other scaling. `whole: [ingredients]` = big ones,
  one each: the bread stays whole and the filling follows the person's usual scales. `scFor(id, who)` in `index.html` applies both.
  Shared parts (egg white sheet, patties, rashers, nacho cheese sauce, cheesecake batter) pool into one Sunday task by having the same label.
- `O`, `X`, `H` and `S` components may end with a list of ingredients whose weight the step shows (otherwise the main protein). An `H` label containing "one at a time"
  takes its minutes per portion.
- **Portion sizes.** `parts(r)` in `data.js` folds a dish's Sunday components into the parts that get portioned (a marinade into
  the tray it roasts on, veg into the pan they cook in, a sauce into what simmers in it), using the same `needs(r)` the run sheet
  schedules by, and `portion(part, scale, lots)` gives one person's weight of a part. Cooked weights are estimates from raw weights
  and the `COOKED` table, so they read "about". The run sheet shows them three ways: every box-up lists each person's portion of
  each part (raw weights for a head-start bag); shaping, breading and one-at-a-time steps say the size of each piece; and a dish
  with no box-up (treats, overnight oats) says its portion on the step that finishes each part. Cooked steps also say roughly what
  the batch should weigh. Blue asked for this: portion weights matter, batch totals alone are not enough.
- Every dish with components has `rest`: the ingredients no Sunday component handles. `data-check.js` fails unless it matches,
  so a new ingredient has to be put in a component (a seasoning list, or the list at the end of an `O`, `X`, `H` or `S`) or in `rest`.
  A `V` ending `"raw"` stays raw (salad veg). `after` also says what a sauce or pan takes in, not just what it waits for.
- Dinners have `type`: `fresh` (cooked on the night, nothing on Sunday), `head` (marinade, coating or sauce on
  Sunday, cooked on the night), `sunday` (cooked and boxed on Sunday).
  A head-start dinner may set `sun: [rice or potatoes]` to have that cooked or par-boiled on Sunday, and may have an `H` step
  whose label starts "Soften". On 7 Oct 2026 eight cook-fresh dinners became Sunday batches and two (fried rice, Philly) head starts. Every dinner with chips has them cut and par-boiled on Sunday, at Blue's request:
  give any new chips dinner `sun: ["potatoes"]` (or make it a Sunday batch).
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

**The record**: everything measured is kept with no time limit (sets, weigh-ins, waist, supplements, and a `mealhist`
line per day of what was ticked as eaten). "Copy data for Claude" gives the last 12 weeks in detail plus weekly averages;
the backup file holds everything. With "Share my record with Claude" on (Progress tab, off by default, per phone), the
phone keeps a copy under `x/<review key>/` in the same database: `about` lists the weeks, and each week is at
`w/<monday date>` with `body`, `sets`, `meals` and `supplements` by date. To review, ask for the review key
(`GYMREVIEW:...`), fetch `x/<key>/about.json`, then one `w/<monday>.json` at a time: large reads through the fetch tool
are unreliable. Switching the option off deletes the online copy.

**Timers**: ticking an oven or hob run-sheet step starts a shared timer (nothing for marinating, cooling, cold jobs or the Instant Pot, which has its own). The alarm is reliable only while the app is in
front, so the app keeps the screen awake. Lock-screen notifications are best effort; a guaranteed one would need a push server.

**Ordering the shop**: Blue gives the household key in chat, you read `h/<key>.json`, save it to a file, and run
`python3 gym-bro/tools/shop-from-sync.py state.json <monday> house` to get the list from the app's own logic.
Blue shops at Asda home delivery. Building the basket in a browser has not been done yet.

## State on 4 October 2026

Done: dish list rework, household menus, single ingredient source, household shopping, run sheet, sync, timers,
screen-awake, body weight in pounds for Harriett (stored in kg), home form guides, full history with the opt-in online record.

Open items:

- `PRESETS` in `data.js` pins the week of 5 Oct 2026 to what was already prepped (breakfast shows Weetabix, because the old egg and oat breakfasts were removed mid-week). Delete it after that week;
  `data-check.js` starts failing three weeks later as a reminder.
- Blue cannot yet do a bodyweight pull-up, so his Monday slot is "Wide-grip lat pulldown" at his request. If he later wants pull-ups back, the weighted pull-up slot and guide are in git history before 6 Oct 2026, along with its line in `mainLifts`.
- Training reviews happen when Blue asks for one (not on a schedule). Weights and exercises are both adjusted in the review, in conversation; he declined an automatic "drop the weight" prompt in the app, so do not build one. Read his record, and swap an exercise only when it is clearly not working: below the rep range two sessions running despite less weight, or he cannot do the movement. Swap to an easier version of the same movement using kit NRG has, change at most two exercises a week, and tell him what changed and why.
- Blue trains at NRG Gym Lewisham: Life Fitness kit, with Hammer Strength plate-loaded machines, Insignia pin-loaded machines and free weights. An assisted pull-up machine there is not confirmed.
- The Tasty Shreds recipes (added 7 Oct 2026: 8 breakfasts, 7 treats, 12 lunches, 12 dinners) are converted from a US book and
  have not been test-cooked. Portions were sized up to match the rest of the app, US products were swapped for UK ones (panko for
  cornflakes, smoked paprika and orange juice for achiote, chipotle paste, home-made ranch and nacho sauce), and Claude chose which
  are lunches and which are dinners. The brookie (skyr in place of banana) and the cheesecake bake time at 180°C are the least
  certain. Macros for the new ingredients are typical UK label values, not checked against Asda. The burrito lunches come out
  around 500 kcal for Blue, lighter than the rice-bowl lunches. Overnight oats is kept as a breakfast because Harriett likes them.
- Portion weights for cooked mixtures (curries, ragù, fillings, bakes) are estimates that have not been weighed in a real prep.
  Ask Blue how the batch weights compared and adjust `COOKED` in `data.js`.
- Run-sheet task times need tuning after a real prep session. Ask Blue which steps ran long.
- Screen-awake is unconfirmed on Harriett's iPhone.
- Build the Asda basket from the shopping list when Blue asks.
- The one-time migration of the old single `menu` storage key in `allMenus()` can be removed once both phones have opened a recent version.
- Earlier plan document and artifact are superseded; the apps are the source of truth.
