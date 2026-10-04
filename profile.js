// Gym-Bro profile: everything that is specific to this person's app.
// index.html, data.js and guides.js are shared with Gym-Gyal.
window.GB_PROFILE = {
  id: "bro",
  app: "Gym-Bro",
  slug: "gym-bro",
  legacySlugs: ["bane-build"],
  person: "Blue",
  partnerName: "Harriett",
  storage: "banebuild:",
  menuSet: "bro",
  // Portion scale by food group: p = protein and dairy, c = carbs, fats and sauces, v = fruit and veg.
  // Carbs trimmed slightly so the menu, morning shake included, lands near 2,750 kcal.
  scales: { p: 1, c: 0.88, v: 1 },
  exclude: [],
  protein: 200,
  planWeeks: 12,
  weightUnit: "kg",
  goalWeight: null,
  phases: [
    { until: 12, name: "Recomp", label: "Phase 1 recomp", kcal: 2750, trend: [-0.8, -0.2], trendText: "down 0.25–0.5 kg a week",
      low: "Faster than target: eat a little more", high: "Slower than target" },
    { name: "Lean bulk", label: "Phase 2 lean bulk", kcal: 3200, trend: [0.1, 0.5], trendText: "up 0.1–0.4 kg a week",
      low: "Not gaining yet", high: "Gaining fast: trim portions", mealNote: "Phase 2: add about 450 kcal a day, mostly rice, pasta and oats." }
  ],
  banner: { weeks: [12, 13], text: "<b>Checkpoint:</b> week 12 is here. Check your waist and switch to the lean bulk at about 3,200 kcal." },
  // [week, waist drop cm, weight drop kg, text]: hit when either drop is reached.
  checkpoints: [[4, 2, null, "Waist down 2 cm, weight down 1–2 kg"], [8, 3, null, "Waist down 3–4 cm, dumbbells feel light"], [12, 5, null, "Waist down 5–8 cm, around 92–94 kg. Switch to lean bulk"]],
  weekIntro: { title: "5 sessions", lead: "Chest and back, shoulders and arms, legs and deadlift, then chest and back, shoulders and traps." },
  backupWhere: "your Downloads folder",
  themeColor: null,
  theme: null,
  // [id, gym name, sets, lo, hi, home name, home lo, home hi, rest seconds, unit, "H" = heavy lift]
  days: {
  1:{title:"Chest + back", focus:"Heavy bench and pull-ups, then chest and back size work", ex:[
    ["bench","Barbell bench press",4,4,6,"DB floor press, 3-sec lowering",12,15,180,null,"H"],
    ["pullup","Weighted pull-up",4,4,6,"Pull-ups or band pulldowns",6,12,180,null,"H"],
    ["incline-press","Incline dumbbell press",3,8,12,"Incline DB press, 3-sec lowering",12,15,120],
    ["row","Chest-supported row",3,8,12,"One-arm DB row",12,15,120],
    ["fly","Cable fly",2,12,15,"DB fly on the floor",12,15,75],
    ["lateral-mon","Lateral raise",3,12,20,"DB lateral raise, 5–10 kg",12,20,60]]},
  2:{title:"Shoulders + arms", focus:"Heavy overhead press, then shoulders, traps and arms", ex:[
    ["ohp","Standing overhead press",4,4,6,"Standing DB press",10,15,180,null,"H"],
    ["shrug","Heavy barbell shrug",4,6,10,"DB shrug, 2-sec hold at top",20,25,120],
    ["cable-lateral","Cable lateral raise",4,12,20,"DB lateral raise, leaning away",12,20,60],
    ["cgbench","Close-grip bench press",3,6,10,"Diamond push-ups",10,20,120],
    ["incline-curl","Incline dumbbell curl",3,8,12,"Incline dumbbell curl",10,15,75],
    ["facepull","Face pull",3,15,20,"Band face pull or rear-delt fly",15,20,60],
    ["neck-a","Neck curl + extension (each)",2,15,20,"Neck curl + extension, towel resistance",15,20,60]]},
  3:{title:"Legs + deadlift", focus:"Heavy deadlift, then legs, grip, carries and an optional sled finisher", ex:[
    ["deadlift","Deadlift (barbell or trap bar)",4,3,5,"DB Romanian deadlift",12,15,210,null,"H"],
    ["squat","Back squat",3,6,8,"Goblet squat, 3-sec lowering",12,20,180],
    ["bss","Bulgarian split squat",3,8,10,"Bulgarian split squat with DBs",10,12,120],
    ["legcurl","Leg curl",2,10,12,"Single-leg glute bridge",12,15,75],
    ["calf","Standing calf raise",3,12,15,"One-leg calf raise holding a DB",15,20,60],
    ["carry","Heavy farmer's carry",4,30,40,"Farmer's carry, heaviest DBs",40,60,120,"m"],
    ["sled","Sled push (optional)",4,20,20,"Walking lunges with DBs (optional)",20,20,90,"m"]]},
  4:{rest:true, title:"Rest", focus:"8–10k steps, stretch, sleep"},
  5:{title:"Chest + back", focus:"Heavy dips and rows, then chest, back and arms", ex:[
    ["dips","Weighted dips",4,6,8,"Push-ups to failure",10,30,150,null,"H"],
    ["bb-row","Barbell row",4,6,8,"One-arm DB row, heavy",8,12,150,null,"H"],
    ["flat-db","Flat dumbbell press",3,8,12,"DB floor press, 3-sec lowering",12,15,120],
    ["pulldown","Neutral-grip lat pulldown",3,10,12,"Band pulldowns or pull-ups",8,15,90],
    ["pecdeck","Pec deck",2,12,15,"DB fly on the floor",12,15,60],
    ["reardelt","Rear-delt fly",3,15,20,"Bent-over DB fly",15,20,60],
    ["hammer","Hammer curl",2,10,15,"Hammer curl",12,15,60],
    ["neck-b","Neck curl + extension (each)",2,15,20,"Neck curl + extension, towel resistance",15,20,60]]},
  6:{title:"Shoulders + traps", focus:"Heavy rack pulls, then shoulders, traps and arms", ex:[
    ["rackpull","Rack pull from the knee",3,5,5,"Heavy DB shrug, slow",15,20,180,null,"H"],
    ["db-ohp","Seated dumbbell shoulder press",3,8,12,"Seated DB shoulder press",12,15,120],
    ["lateral-myo","Lateral raise (myo-reps)",4,15,20,"DB lateral raise, lighter",15,20,60],
    ["heavy-shrug","Dumbbell shrug",3,10,15,"DB shrug, slow",20,25,90],
    ["upright","Wide-grip upright row",3,12,12,"DB upright row to lower chest",12,15,75],
    ["ez-curl","EZ-bar curl",3,8,12,"DB curl, 3-sec lowering",10,15,75],
    ["skull","Skull crusher",3,10,12,"DB skull crusher",12,15,75]]},
  0:{rest:true, title:"Rest", focus:"8–10k steps, Sunday food prep"}
},
  mainLifts: [["bench","Bench press"],["ohp","Overhead press"],["deadlift","Deadlift"],["squat","Back squat"],["pullup","Pull-up (added kg)"],["dips","Dips (added kg)"],["bb-row","Barbell row"],["rackpull","Rack pull"]],
  e1rm: [["bench","Bench"],["ohp","Overhead press"],["deadlift","Deadlift"],["squat","Squat"]]
};
