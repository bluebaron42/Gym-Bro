# Prints the household shopping list for a week from a saved copy of the sync data, using the app's own logic.
#   python3 gym-bro/tools/shop-from-sync.py state.json 2026-10-12 [house|blue|harriett]
# state.json is the JSON read from the sync database for the household. The household key is never stored in this repo.
import json, sys, os, subprocess, time, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
state = json.load(open(sys.argv[1])) or {}; wk = sys.argv[2]; view = sys.argv[3] if len(sys.argv) > 3 else "house"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
menus = {}
for w, fields in (state.get("m") or {}).items():
    reset = abs((state.get("r") or {}).get(w, 0)); m = {}
    for c, v in fields.items():
        rid, _, ts = str(v).partition("@")
        if not rid or float(ts or 0) < reset: continue
        who, _, rest = c.rpartition(":"); m[("" if who in ("", "blue") else "p:") + rest] = rid
    menus[w] = m
pantry = {unquote(k): 1 for k, v in (state.get("p") or {}).items() if v > 0}
tue = (datetime.date.fromisoformat(wk) + datetime.timedelta(days=1)).isoformat() + "T09:00:00"
srv = subprocess.Popen(["python3", "-m", "http.server", "8767"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(service_workers="block"); ctx.grant_permissions(["clipboard-read", "clipboard-write"]); pg = ctx.new_page(); pg.clock.install(time=tue)
        pg.goto("http://localhost:8767/gym-bro/index.html")
        pg.evaluate("([m,p])=>{localStorage.setItem('banebuild:menus',m);localStorage.setItem('banebuild:pantry',p)}", [json.dumps(menus), json.dumps(pantry)]); pg.reload(); pg.click('[data-tab="food"]')
        for who in ("blue", "harriett"):
            pg.click(f'[data-who="{who}"]'); rows = pg.eval_on_selector_all("#view .mrow [data-recipe]", "els=>els.map(e=>e.dataset.slot+e.dataset.dow+': '+e.textContent)")
            print(("Blue" if who == "blue" else "Harriett") + "'s week: " + "; ".join(r for r in rows if not r.startswith(("breakfast", "shake")))); print()
        pg.click(f'[data-sv="{view}"]'); pg.click("#shop-copy"); time.sleep(0.3); print(pg.evaluate("navigator.clipboard.readText()")); b.close()
finally:
    srv.terminate()
