# Run from the folder that holds both repos:  python3 gym-bro/tests/app-check.py
# Loads both apps in a headless browser and checks menus, shopping totals, recipe cards, prep and sharing.
import subprocess, time, json, random, sys, os
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
srv = subprocess.Popen(["python3", "-m", "http.server", "8765"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
bad = []
def fail(m): bad.append(m); print("FAIL", m)
EXPECT = """(arg)=>{const D=window.BB_DATA,H=D.HOUSE,CAT={"Protein":"p","Dairy and eggs":"p","Carbs":"c","Sauces and cupboard":"c","Fruit and veg":"v"};
  const sc=(i,s)=>{const n=D.ING[i];return n[8]==="fixed"?1:n[8]==="aroma"?(s.p+s.c)/2:s[CAT[n[1]]]};const out={};
  arg.people.forEach(w=>{const s=H.people[w].scales;Object.keys(arg.menu[w]).forEach(k=>{D.RECIPES[arg.menu[w][k]].ing.forEach(([i,g])=>{out[i]=(out[i]||0)+g*sc(i,s)})})});return out}"""
def allowed(D, rid, slot, dow, who):
    r = D["RECIPES"].get(rid); H = D["HOUSE"]
    if not r or r["slot"] != slot: return False
    eat = H["order"] if slot in H["shared"] else [who]
    if r.get("kind") and any(r["kind"] in H["people"][w]["skip"] for w in eat): return False
    return not (slot == "lunch" and dow >= 4 and r.get("late") == "no")
SLOTS = ["breakfast", "shake", "lunch", "dinner", "snack"]
try:
  with sync_playwright() as p:
    b = p.chromium.launch(); codes = {}
    for app, pre in [("gym-bro", "banebuild:"), ("gym-gyal", "gymgyal:")]:
        pg = b.new_context(viewport={"width": 400, "height": 850}, service_workers="block").new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.clock.install(time="2026-10-06T09:00:00"); url = f"http://localhost:8765/{app}/index.html"; pg.goto(url)
        D = pg.evaluate("window.BB_DATA"); me = pg.evaluate("window.GB_PROFILE.me"); other = [w for w in D["HOUSE"]["order"] if w != me][0]
        rng = random.Random(7); seen = set(); rounds = 0
        while rounds < 12 and (rounds < 4 or len(seen) < len(D["RECIPES"])):
            rounds += 1; stored = {}; menu = {me: {}, other: {}}
            for slot in SLOTS:
                for dow in range(7):
                    for who in ([me] if slot in D["HOUSE"]["shared"] else [me, other]):
                        opts = [r for r in D["RECIPES"] if allowed(D, r, slot, dow, who)]
                        fresh = [r for r in opts if r not in seen]; rid = rng.choice(fresh or opts); seen.add(rid)
                        stored[("" if who == me else "p:") + slot + str(dow)] = rid
                        for w in (D["HOUSE"]["order"] if slot in D["HOUSE"]["shared"] else [who]): menu[w][slot + str(dow)] = rid
            pg.evaluate("([k,v])=>localStorage.setItem(k,v)", [pre + "menus", json.dumps({"2026-10-05": stored})]); pg.reload(); pg.click('[data-tab="food"]')
            for view, people in [("house", [me, other]), (me, [me]), (other, [other])]:
                pg.click(f'[data-sv="{view}"]')
                got = {}
                for t in pg.eval_on_selector_all("[data-need]", "els=>els.map(e=>e.dataset.need)"):
                    k, v = t.split("|"); got[k] = float(v)
                exp = pg.evaluate(EXPECT, {"people": people, "menu": menu})
                for k, v in exp.items():
                    if k not in got: fail(f"{app} {view}: {k} missing from the shopping list")
                    elif abs(got[k] - v) > 0.2: fail(f"{app} {view}: {k} listed {got[k]} g, expected {v:.1f} g")
                for k in got:
                    if k not in exp: fail(f"{app} {view}: {k} on the list but in no meal")
            txt = pg.inner_text("#view")
            for w in ["undefined", "NaN", "null"]:
                if w in txt: fail(f"{app}: '{w}' on the Food tab (round {rounds})")
        if len(seen) < len(D["RECIPES"]): fail(f"{app}: only {len(seen)} of {len(D['RECIPES'])} recipes exercised")
        # every recipe card, as each person
        pg.evaluate("([k])=>localStorage.removeItem(k)", [pre + "menus"]); pg.reload(); pg.click('[data-tab="food"]')
        for who in [me, other]:
            for rid in D["RECIPES"]:
                pg.evaluate("([id,w])=>{const e=document.querySelector('[data-recipe=\"'+id+'\"]');e.dataset.who=w;e.click()}", [rid, who])
                body = pg.inner_text("#sheet-body")
                if any(w in body for w in ["undefined", "NaN"]): fail(f"{app}: bad recipe card {rid} for {who}")
                pg.evaluate("document.querySelector('#sheet .x-btn').click()")
        # planning next week leaves this week alone; swapping a shared dinner; lunch block button
        this_before = pg.inner_text("#view"); pg.click('[data-wk="2026-10-12"]')
        pg.click('[data-swap="dinner"][data-dow="2"]'); pg.locator('#sheet [data-choose="d-pizza"]').first.click()
        pg.click('[data-swap="lunch"][data-dow="1"]'); pg.locator('#sheet [data-choose="l-bulgogi"][data-days="1,2,3"]').click()
        st = json.loads(pg.evaluate("([k])=>localStorage.getItem(k)", [pre + "menus"]))
        if st.get("2026-10-12", {}).get("dinner2") != "d-pizza" or [st["2026-10-12"].get("lunch" + str(d)) for d in (1, 2, 3)] != ["l-bulgogi"] * 3: fail(f"{app}: next-week choices not saved: {st}")
        if "2026-10-05" in st: fail(f"{app}: planning next week wrote to this week")
        pg.click('[data-wk="2026-10-05"]')
        if pg.inner_text("#view") != this_before: fail(f"{app}: this week's page changed after planning next week")
        # share code out
        pg.click('[data-wk="2026-10-12"]'); pg.context.grant_permissions(["clipboard-read", "clipboard-write"]); pg.click("#sh-copy"); pg.wait_for_timeout(200); codes[app] = pg.evaluate("navigator.clipboard.readText()")
        if "GYMMENU:" not in codes[app]: fail(f"{app}: no share code produced")
        if errs: fail(f"{app}: page errors {errs}")
        print(app, "rounds", rounds, "recipes exercised", len(seen))
    # share code in: Harriett's phone takes Blue's dinners, treats and his own meals
    pg = b.new_context(viewport={"width": 400, "height": 850}, service_workers="block").new_page(); pg.clock.install(time="2026-10-06T09:00:00")
    pg.goto("http://localhost:8765/gym-gyal/index.html"); pg.click('[data-tab="food"]'); pg.click("#sh-paste"); pg.fill("#sh-text", codes["gym-bro"]); pg.click("#sh-load"); pg.wait_for_timeout(200)
    st = json.loads(pg.evaluate("localStorage.getItem('gymgyal:menus')"))["2026-10-12"]
    if st.get("dinner2") != "d-pizza" or st.get("p:lunch1") != "l-bulgogi" or "lunch1" in st: fail(f"share: Harriett's phone did not take Blue's menu correctly: {st}")
    pg.click("#sh-paste"); pg.fill("#sh-text", codes["gym-gyal"]); pg.click("#sh-load")
    if "your own" not in pg.inner_text("#sh-msg"): fail("share: own code was not refused")
    b.close()
finally:
    srv.terminate()
print("%d problem(s)" % len(bad) if bad else "All app checks passed"); sys.exit(1 if bad else 0)
