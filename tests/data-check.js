// Run with: node tests/data-check.js   Checks the recipe data hangs together.
global.window = {}; require("../data.js"); const D = window.BB_DATA; const R = D.RECIPES; let bad = 0;
const fail = (m) => { bad++; console.log("FAIL " + m); };
const used = new Set(), ingUsed = new Set();
["bro", "gyal"].forEach((set) => Object.keys(D.OPTIONS[set]).forEach((slot) => Object.keys(D.OPTIONS[set][slot]).forEach((d) => D.OPTIONS[set][slot][d].forEach((id) => {
  used.add(id);
  if (!R[id]) return fail(set + " " + slot + " " + d + ": unknown recipe " + id);
  if (R[id].slot !== slot) fail(id + " is on the " + slot + " menu but is a " + R[id].slot);
  if (slot === "lunch" && d >= 4 && R[id].late === "no") fail(id + " cannot be a Thursday to Saturday lunch (" + set + ")");
}))));
Object.values(R).forEach((r) => {
  if (!used.has(r.id)) fail(r.id + " is on no menu");
  r.ing.forEach(([i, g]) => { ingUsed.add(i); if (!D.ING[i]) fail(r.id + ": unknown ingredient " + i); if (!(g > 0)) fail(r.id + ": bad amount for " + i); });
  if (r.slot === "dinner" && ["fresh", "head", "sunday"].indexOf(r.type) < 0) fail(r.id + ": dinner needs a type");
  if (r.slot === "lunch" && ["freeze", "split", "no"].indexOf(r.late) < 0) fail(r.id + ": lunch needs late");
  if (r.slot === "dinner" && D.TAGS.pork.some((i) => r.ing.some((x) => x[0] === i))) fail(r.id + ": pork in a dinner");
  const prep = D.PREP[r.id], comp = D.COMP[r.id];
  if (r.type === "fresh" && comp) fail(r.id + ": cook-fresh dinner has Sunday components");
  if (r.type === "fresh" && !(prep && prep[0] === "" && prep[1])) fail(r.id + ": cook-fresh dinner needs an on-the-day recipe");
  if ((r.type === "head" || r.type === "sunday") && !(comp && prep && prep[0] && prep[1])) fail(r.id + ": needs Sunday components and both prep texts");
  if (r.type === "head" && comp.some((c) => "OHL".indexOf(c[0]) >= 0)) fail(r.id + ": head-start dinner is being cooked on Sunday");
  if (r.slot === "lunch" && r.id !== "l-onigiri" && !(comp && comp.some((c) => c[0] === "P"))) fail(r.id + ": lunch needs a pack line");
});
["PREP", "COMP"].forEach((k) => Object.keys(D[k]).forEach((id) => { if (!R[id]) fail(k + " has an entry for a missing recipe: " + id); }));
Object.keys(D.ING).forEach((i) => { if (!ingUsed.has(i)) fail("unused ingredient " + i); });
const n = (f) => Object.values(R).filter(f).length;
console.log("dinners " + n((r) => r.slot === "dinner") + " (fresh " + n((r) => r.type === "fresh") + ", head " + n((r) => r.type === "head") + ", sunday " + n((r) => r.type === "sunday") + "), lunches " + n((r) => r.slot === "lunch") + ", treats " + n((r) => r.slot === "snack"));
console.log(bad ? bad + " problem(s)" : "All checks passed"); process.exit(bad ? 1 : 0);
