// Run with: node tests/data-check.js   Checks the recipe data hangs together.
global.window = {}; require("../data.js"); const D = window.BB_DATA; const R = D.RECIPES; let bad = 0;
const fail = (m) => { bad++; console.log("FAIL " + m); };
const SPRE = /^([\d.]+)\s*(g|ml|tsp|tbsp|clove|x|pinch)\s+(.+)$/, SIDX = { L: 4, M: 4, B: 3, X: 3, S: 2, H: 4, T: 3 }, IGNORE = { "water": 1, "hot water": 1 };
const ingUsed = new Set();
Object.values(R).forEach((r) => {
  r.ing.forEach(([i, g]) => { ingUsed.add(i); if (!D.ING[i]) fail(r.id + ": unknown ingredient " + i); if (!(g > 0)) fail(r.id + ": bad amount for " + i); });
  if (!(r.method && r.method.length)) fail(r.id + ": no method");
  if (r.slot === "dinner" && ["fresh", "head", "sunday"].indexOf(r.type) < 0) fail(r.id + ": dinner needs a type");
  if (r.slot === "dinner" && r.kind) fail(r.id + ": a shared dinner cannot be something one person skips");
  if (r.slot === "lunch" && ["freeze", "split", "no"].indexOf(r.late) < 0) fail(r.id + ": lunch needs late");
  if (r.type === "fresh" && (r.comp || r.finish)) fail(r.id + ": cook-fresh dinner has Sunday prep");
  if ((r.type === "head" || r.type === "sunday") && !(r.comp && r.finish)) fail(r.id + ": needs Sunday components and a finish step");
  if (r.type === "head" && r.comp.some((c) => "OHL".indexOf(c[0]) >= 0)) fail(r.id + ": head-start dinner is being cooked on Sunday");
  if (r.slot === "lunch" && r.id !== "l-onigiri" && !(r.comp && r.comp.some((c) => c[0] === "P") && r.finish)) fail(r.id + ": lunch needs a pack line and a finish step");
  // Run sheet: explicit dependencies point backwards at real components; anything assembled has something to assemble.
  Object.keys(r.after || {}).forEach((ci) => { if (!r.comp[ci]) fail(r.id + ": after refers to a missing component " + ci); r.after[ci].forEach((j) => { if (!(j < ci) || !r.comp[j]) fail(r.id + ": after must point at an earlier component"); }); });
  (r.comp || []).forEach((c, ci) => { if (c[0] === "X" && /^Build/.test(c[1]) && !r.comp.slice(0, ci).some((x) => "LHSO".indexOf(x[0]) >= 0)) fail(r.id + ": '" + c[1] + "' has nothing cooked before it"); });
  // Seasoning lists: every item is a known shopping ingredient or cupboard item, and the ingredient list covers what the lists use.
  const strs = []; (r.comp || []).forEach((t) => { const s = t[SIDX[t[0]]]; if (typeof s === "string" && s) strs.push(s); }); (r.sea || []).forEach((g) => strs.push(g[1]));
  const need = {}, zest = {};
  strs.forEach((s) => s.split(";").map((x) => x.trim()).filter(Boolean).forEach((x) => {
    const m = x.match(SPRE); if (!m) return fail(r.id + ": cannot read seasoning item '" + x + "'");
    const q = +m[1], u = m[2], n = m[3]; if (IGNORE[n]) return;
    const al = D.ALIAS[n]; if (!al) { if (!D.CUPBOARD[n]) fail(r.id + ": '" + n + "' is neither an ingredient nor a cupboard item"); return; }
    const per = (u === "g" || u === "ml") ? 1 : al[1][u]; if (per == null) return fail(r.id + ": no " + u + " weight for " + n);
    if (al[2] === "zest") zest[al[0]] = (zest[al[0]] || 0) + q * per; else need[al[0]] = (need[al[0]] || 0) + q * per;
  }));
  Object.keys(zest).forEach((k) => { need[k] = Math.max(need[k] || 0, zest[k]); });
  Object.keys(need).forEach((k) => { const e = r.ing.find((x) => x[0] === k); if (!e) fail(r.id + ": uses " + k + " but it is not in the ingredients"); else if (need[k] > e[1] * 1.03 + 0.3) fail(r.id + ": lists use " + need[k].toFixed(1) + " g " + k + " but the ingredients have " + e[1]); });
});
Object.keys(D.ING).forEach((i) => { if (!ingUsed.has(i)) fail("unused ingredient " + i); });
Object.keys(D.ALIAS).forEach((n) => { if (!D.ING[D.ALIAS[n][0]]) fail("alias " + n + " points at a missing ingredient"); });
["TRIM", "PACKS"].forEach((t) => Object.keys(D[t]).forEach((i) => { if (!D.ING[i]) fail(t + " has unknown ingredient " + i); }));
// The default week must be valid for the people eating it.
const H = D.HOUSE, ok = (id, slot, dow, who) => { const r = R[id]; if (!r || r.slot !== slot) return false; const eat = H.shared.indexOf(slot) >= 0 ? H.order : [who]; if (r.kind && eat.some((w) => H.people[w].skip.indexOf(r.kind) >= 0)) return false; return !(slot === "lunch" && dow >= 4 && r.late === "no"); };
["breakfast", "shake", "lunch", "dinner", "snack"].forEach((slot) => H.order.forEach((w) => [0, 1, 2, 3, 4, 5, 6].forEach((d) => { const id = H.shared.indexOf(slot) >= 0 ? D.DEFAULTS[slot][d] : D.DEFAULTS[slot][w][d]; if (!ok(id, slot, d, w)) fail("default " + slot + " day " + d + " for " + w + " is not allowed: " + id); })));
Object.keys(D.PRESETS || {}).forEach((wk) => {
  if ((Date.now() - new Date(wk).getTime()) / 864e5 > 21) fail("preset for the week of " + wk + " has passed: delete it from data.js");
  Object.keys(D.PRESETS[wk]).forEach((slot) => { const sh = H.shared.indexOf(slot) >= 0, sets = sh ? { all: D.PRESETS[wk][slot] } : D.PRESETS[wk][slot];
    Object.keys(sets).forEach((w) => Object.keys(sets[w]).forEach((d) => { const r = R[sets[w][d]]; if (!r || r.slot !== slot) fail("preset " + wk + " " + slot + " day " + d + ": bad dish " + sets[w][d]); })); });
});
// Training: every exercise in both apps has a form guide for the gym and for home, and one-sided ones say so.
require("../guides.js");
["../profile.js", "../../gym-gyal/profile.js"].forEach((f) => { delete require.cache[require.resolve(f)]; require(f); const P = window.GB_PROFILE;
  Object.values(P.days).forEach((d) => (d.ex || []).forEach((e) => {
    const gg = window.GB_GUIDES[e[0]], hk = window.GB_HOME_MAP[e[5]], hg = window.GB_HOME_GUIDES[hk] || window.GB_GUIDES[hk];
    if (!gg) fail(P.app + ": no gym guide for " + e[1]);
    if (!hg) fail(P.app + ": no home guide for '" + e[5] + "'");
    [[e[1], gg], [e[5], hg]].forEach(([name, g]) => { if (g && e[9] !== "m" && /one-arm|one-leg|single-leg|split squat|each side|each leg|kickback|step-up|pallof/i.test(name) && !g.u) fail(P.app + ": '" + name + "' is done one side at a time but its guide does not say so"); });
  })); });
Object.keys(window.GB_HOME_MAP).forEach((k) => { const v = window.GB_HOME_MAP[k]; if (!(window.GB_HOME_GUIDES[v] || window.GB_GUIDES[v])) fail("home guide map points at a missing guide: " + v); });
const n = (f) => Object.values(R).filter(f).length;
console.log("dinners " + n((r) => r.slot === "dinner") + " (fresh " + n((r) => r.type === "fresh") + ", head " + n((r) => r.type === "head") + ", sunday " + n((r) => r.type === "sunday") + "), lunches " + n((r) => r.slot === "lunch") + ", treats " + n((r) => r.slot === "snack"));
console.log(bad ? bad + " problem(s)" : "All checks passed"); process.exit(bad ? 1 : 0);
