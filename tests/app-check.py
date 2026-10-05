# Run from the folder that holds both repos:  python3 gym-bro/tests/app-check.py
# Loads both apps in a headless browser and checks menus, shopping totals, recipe cards, the run sheet, sync and timers.
import subprocess, time, json, random, sys, os, urllib.request
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
srv = subprocess.Popen(["python3", "-m", "http.server", "8765"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
db = subprocess.Popen(["python3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock-db.py"), "8766"]); time.sleep(1)
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
            # Sunday run sheet: order, dependencies, one job per cook at a time, kit never double-booked
            prepped = set(rid for w in (me, other) for k, rid in menu[w].items() if not k.endswith("0") and k[:-1] in ("lunch", "dinner") and D["RECIPES"][rid].get("comp") and D["RECIPES"][rid].get("type") != "fresh")
            for cooks in ("2", "1"):
                if not pg.query_selector(f'[data-cooks="{cooks}"]'): continue
                pg.click(f'[data-cooks="{cooks}"]')
                st = pg.eval_on_selector_all("[data-step]", "els=>els.map(e=>({id:e.dataset.step,s:+e.dataset.s,e:+e.dataset.e,d:+e.dataset.d,who:e.dataset.by,kit:e.dataset.kit,temp:e.dataset.temp,needs:e.dataset.needs?e.dataset.needs.split('~'):[]}))")
                tag = f"{app} run sheet ({cooks} cook, round {rounds})"; by = {x["id"]: x for x in st}
                if len(by) != len(st): fail(f"{tag}: duplicate steps")
                if any(st[i]["s"] > st[i + 1]["s"] + 1e-6 for i in range(len(st) - 1)): fail(f"{tag}: steps are not in time order")
                for x in st:
                    for n in x["needs"]:
                        if n not in by: fail(f"{tag}: {x['id']} needs {n}, which is not on the sheet")
                        elif by[n]["d"] > x["s"] + 1e-6: fail(f"{tag}: {x['id']} starts at {x['s']} before {n} is done at {by[n]['d']}")
                    if x["id"].startswith("P|") and not x["needs"]: fail(f"{tag}: {x['id']} boxes food that nothing made")
                    if cooks == "1" and x["who"] != "chef": fail(f"{tag}: a step is given to a second cook")
                for who in ("chef", "helper"):
                    mine = sorted([x for x in st if x["who"] == who and x["e"] > x["s"]], key=lambda x: x["s"])
                    for i in range(len(mine) - 1):
                        if mine[i]["e"] > mine[i + 1]["s"] + 1e-6: fail(f"{tag}: {who} has {mine[i]['id']} and {mine[i+1]['id']} at the same time")
                for kit, cap in (("oven", 2), ("hob", 4), ("ip", 1)):
                    ks = [x for x in st if x["kit"] == kit]
                    for x in ks:
                        live = [y for y in ks if y["s"] < x["d"] and y["d"] > x["s"]]
                        if len([y for y in live if y["s"] <= x["s"]]) > cap: fail(f"{tag}: {kit} over capacity at {x['id']}")
                        if kit == "oven" and any(y["temp"] != x["temp"] for y in live): fail(f"{tag}: oven at two temperatures at once ({x['id']})")
                timed = pg.eval_on_selector_all("[data-timer]", "els=>els.map(e=>e.dataset.kit+'|'+e.dataset.step)")
                for x in timed:
                    if x.split("|")[0] not in ("oven", "hob"): fail(f"{tag}: a timer is offered for something not on the hob or in the oven: {x}")
                missing = [r for r in prepped if any(c[0] == "P" for c in D["RECIPES"][r]["comp"]) and ("P|" + r) not in by]
                if missing: fail(f"{tag}: no boxing step for {missing}")
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
        if errs: fail(f"{app}: page errors {errs}")
        print(app, "rounds", rounds, "recipes exercised", len(seen))
    # a one-off preset week beats what would be copied from the week before, and the first edit freezes the week as shown
    pg = b.new_context(service_workers="block").new_page(); pg.clock.install(time="2026-10-06T09:00:00"); pg.goto("http://localhost:8765/gym-bro/index.html")
    pg.evaluate("localStorage.setItem('banebuild:menus',JSON.stringify({'2026-09-28':{dinner5:'d-pizza',snack1:'s-crumble',lunch2:'l-shawarma','p:lunch2':'l-caesar'}}))"); pg.reload(); pg.click('[data-tab="food"]')
    seen_now = pg.eval_on_selector_all("#view [data-recipe][data-slot]", "els=>els.map(e=>e.dataset.slot+e.dataset.dow+'='+e.dataset.recipe)")
    for want in ("dinner5=d-bigmac", "snack1=s-choc-mousse", "lunch2=l-bulgogi"):
        if want not in seen_now: fail(f"preset week: expected {want}")
    pg.click('[data-who="harriett"]')
    if "lunch2=l-caesar" not in pg.eval_on_selector_all("#view [data-recipe][data-slot]", "els=>els.map(e=>e.dataset.slot+e.dataset.dow+'='+e.dataset.recipe)"): fail("a new week did not start from last week's choice where there is no preset")
    pg.click('[data-who="blue"]'); pg.click('[data-swap="dinner"][data-dow="1"]'); pg.locator('#sheet [data-choose="d-ragu"]').first.click()
    wkm = json.loads(pg.evaluate("localStorage.getItem('banebuild:menus')"))["2026-10-05"]
    if wkm.get("dinner5") != "d-bigmac" or wkm.get("dinner1") != "d-ragu" or wkm.get("p:lunch2") != "l-caesar": fail(f"first edit did not freeze the week as shown: {wkm}")
    # ---- sync between the two phones, against the stand-in database
    def phone(app):
        ctx = b.new_context(viewport={"width": 400, "height": 850}, service_workers="block"); ctx.add_init_script("window.GB_SYNC_URL='http://localhost:8766'")
        pg = ctx.new_page(); er = []; pg.on("pageerror", lambda e: er.append(str(e) + " " + (e.stack or "")[:300])); pg.clock.install(time="2026-10-13T09:00:00"); pg.goto(f"http://localhost:8765/{app}/index.html"); pg.click('[data-tab="food"]'); return ctx, pg, er
    def stored(pg, pre, k): return json.loads(pg.evaluate("([k])=>localStorage.getItem(k)", [pre + k]) or "null")
    def until(what, fn, ms=6000):
        t0 = time.time()
        while time.time() - t0 < ms / 1000:
            try:
                if fn(): return True
            except Exception: pass
            time.sleep(0.15)
        fail("sync: " + what); return False
    WK = "2026-10-12"
    ca, A, ea = phone("gym-bro"); cb, B, eb = phone("gym-gyal")
    A.click('[data-swap="dinner"][data-dow="2"]'); A.locator('#sheet [data-choose="d-pizza"]').first.click()      # chosen before sync exists
    A.click("#sy-new"); key = stored(A, "banebuild:", "sync")["key"]
    if len(key) < 24: fail("sync: household key too short")
    B.click("#sy-join"); B.fill("#sy-text", "GYMSYNC:" + key); B.click("#sy-go")
    until("Harriett's phone did not receive the dinner Blue had already chosen", lambda: stored(B, "gymgyal:", "menus")[WK].get("dinner2") == "d-pizza")
    B.click('[data-swap="lunch"][data-dow="1"]'); B.locator('#sheet [data-choose="l-caesar"][data-days="1,2,3"]').click()
    until("Blue's phone did not receive Harriett's lunches", lambda: [stored(A, "banebuild:", "menus")[WK].get("p:lunch" + str(d)) for d in (1, 2, 3)] == ["l-caesar"] * 3)
    if "lunch1" in stored(A, "banebuild:", "menus")[WK] and stored(A, "banebuild:", "menus")[WK]["lunch1"] == "l-caesar": fail("sync: Harriett's lunch overwrote Blue's own lunch")
    A.locator('[data-shop^="i:"]').first.click(); tick = A.locator('[data-shop^="i:"]').first.get_attribute("data-shop")
    until("shopping tick did not reach the other phone", lambda: stored(B, "gymgyal:", "shops")[WK]["t"].get(tick) is True)
    B.locator("[data-pantry]").first.click(); pk = B.locator("[data-pantry]").first.get_attribute("data-pantry")
    until("cupboard tick did not reach the other phone", lambda: stored(A, "banebuild:", "pantry").get(pk) == 1)
    # last change wins on both phones
    A.click('[data-swap="dinner"][data-dow="3"]'); A.locator('#sheet [data-choose="d-rigatoni"]').first.click(); time.sleep(0.3); B.clock.fast_forward(60000)  # the two test clocks start a moment apart
    B.click('[data-swap="dinner"][data-dow="3"]'); B.locator('#sheet [data-choose="d-smash"]').first.click()
    until("phones disagree after both changed the same dinner", lambda: stored(A, "banebuild:", "menus")[WK].get("dinner3") == "d-smash" and stored(B, "gymgyal:", "menus")[WK].get("dinner3") == "d-smash")
    # offline changes are held and sent later
    ca.set_offline(True); A.click('[data-swap="dinner"][data-dow="4"]'); A.locator('#sheet [data-choose="d-quesadilla"]').first.click(); time.sleep(0.6)
    if stored(B, "gymgyal:", "menus")[WK].get("dinner4") == "d-quesadilla": fail("sync: an offline change arrived while offline")
    ca.set_offline(False); A.evaluate("window.dispatchEvent(new Event('online'))")
    until("offline change was not sent after reconnecting", lambda: stored(B, "gymgyal:", "menus")[WK].get("dinner4") == "d-quesadilla")
    # timers: ticking a timed step starts it on both phones, it rings when due, and dismissing clears both
    step = A.locator("[data-timer]").first; tid = step.get_attribute("data-shop"); mins = int(step.get_attribute("data-timer")); step.click()
    if A.locator("[data-step]").count() < 3: fail("sync: the run sheet vanished after ticking a step")
    until("timer did not start on the phone that ticked the step", lambda: A.locator("#ktimers .kt").count() == 1)
    until("timer did not appear on the other phone", lambda: B.locator("#ktimers .kt").count() == 1)
    # several timers still take one slim bar; the full list opens in a sheet
    steps2 = A.locator('[data-timer]:not(.on)'); n2 = min(2, steps2.count())
    for _ in range(n2): A.locator('[data-timer]:not(.on)').first.click()
    until("extra timers did not reach the other phone", lambda: "more" in B.inner_text("#ktimers") if n2 else True)
    if A.locator("#ktimers .kt").count() != 1: fail("timers: the bar is stacking instead of staying one row")
    if A.evaluate("document.querySelector('#ktimers').getBoundingClientRect().height") > 70: fail("timers: the bar is taller than one row")
    A.click("[data-ktopen]")
    if A.locator("#sheet .kt-row").count() != 1 + n2: fail("timers: the list does not show every timer")
    for _ in range(n2): A.locator("#sheet .kt-row [data-kt]").last.click()
    A.evaluate("document.querySelector('#sheet .x-btn').click()")
    until("cancelled timers did not clear on the other phone", lambda: B.locator("#ktimers .kt").count() == 1 and "more" not in B.inner_text("#ktimers"))
    B.clock.fast_forward((mins + 1) * 60000)
    until("timer did not ring when due", lambda: B.locator("#ktimers .kt.done").count() == 1)
    B.click("#ktimers [data-kt]")
    until("dismissing the timer did not clear it on both phones", lambda: A.locator("#ktimers .kt").count() == 0 and B.locator("#ktimers .kt").count() == 0)
    # reset reaches the other phone
    B.click("#menu-reset"); B.click("#menu-reset")
    until("menu reset did not reach the other phone", lambda: "dinner2" not in stored(A, "banebuild:", "menus")[WK])
    # only menu, tick and timer data is ever sent
    state = json.loads(urllib.request.urlopen("http://localhost:8766/__state").read())
    hh = state.get("h", {}).get(key, {})
    if not hh or set(hh) - set("mrspct"): fail(f"sync: unexpected data in the database: {list(hh)}")
    if any(w in json.dumps(state) for w in ["progress", "waist", "ex-", "meals", "supp"]): fail("sync: personal data was sent")
    # ---- the record: full history on the phone, and the opt-in private copy for review
    def dbstate(): return json.loads(urllib.request.urlopen("http://localhost:8766/__state").read())
    A.click('[data-tab="today"]'); A.locator("[data-meal]").first.click()
    row = A.locator(".excard .set").first; row.locator('[data-f="w"]').fill("42.5"); row.locator('[data-f="r"]').fill("9"); row.locator("[data-tick]").click()
    mh = stored(A, "banebuild:", "mealhist")
    if not mh or "2026-10-13" not in mh or not mh["2026-10-13"]["k"] > 0: fail(f"record: the meal tick was not written to the meal history: {mh}")
    A.locator("[data-meal]").first.click()
    if "2026-10-13" in (stored(A, "banebuild:", "mealhist") or {}): fail("record: unticking the only meal left a meal-history entry behind")
    A.locator("[data-meal]").first.click()
    A.evaluate("localStorage.setItem('banebuild:progress',JSON.stringify({e:[{d:'2026-10-13',w:96.4,waist:91},{d:'2026-09-01',w:97.2}]}))"); A.reload()
    if "x" in dbstate(): fail("record: something was uploaded before sharing was switched on")
    A.click('[data-tab="progress"]'); A.click('[data-review="1"]'); rk = stored(A, "banebuild:", "review")["key"]
    until("the record was not uploaded after switching sharing on", lambda: "2026-10-12" in dbstate().get("x", {}).get(rk, {}).get("w", {}))
    rec = dbstate()["x"][rk]; wk = rec["w"]["2026-10-12"]
    if wk.get("body", {}).get("2026-10-13", {}).get("kg") != 96.4: fail(f"record: weigh-in missing from the uploaded week: {wk.get('body')}")
    if "42.5x9" not in json.dumps(wk.get("sets", {})): fail(f"record: logged set missing from the uploaded week: {wk.get('sets')}")
    if not wk.get("meals", {}).get("2026-10-13", {}).get("kcal"): fail("record: meals eaten missing from the uploaded week")
    if "2026-08-31" not in rec["w"] or "2026-08-31" not in rec["about"]["weeks"]: fail("record: an older week was not uploaded")
    if rk == key or rk in json.dumps(dbstate().get("h", {})) or "kg" in json.dumps(dbstate().get("h", {})): fail("record: personal data or its key leaked into the household area")
    A.click('[data-tab="today"]'); row = A.locator(".excard .set").nth(1); row.locator('[data-f="w"]').fill("45"); row.locator('[data-f="r"]').fill("8"); row.locator("[data-tick]").click()
    until("a new set did not reach the uploaded copy", lambda: "45x8" in json.dumps(dbstate()["x"][rk]["w"]["2026-10-12"].get("sets", {})), 9000)
    A.click('[data-tab="progress"]')
    if "Back up now" not in A.inner_text("#view"): fail("record: no backup reminder although there has never been a backup")
    A.click('[data-review="0"]')
    until("switching sharing off did not delete the uploaded copy", lambda: rk not in dbstate().get("x", {}))
    if ea or eb: fail(f"sync: page errors {ea} {eb}")
    b.close()
finally:
    srv.terminate(); db.terminate()
print("%d problem(s)" % len(bad) if bad else "All app checks passed"); sys.exit(1 if bad else 0)
