# 01 - Crash box axial crushing

A thin-walled rounded-square tube crushed axially by a 100 kg rigid mass
at 12 m/s, the way a crash box is characterised on a sled or drop tower.
The box has to absorb a defined amount of energy inside a defined stroke
without letting the peak force through to the structure behind it.

![status](https://img.shields.io/badge/decks-generated%20and%20checked-blue)

## Model

| | |
|---|---|
| section | 80 × 80 mm, corner radius 6 mm |
| length | 300 mm free crush length |
| thickness | 1.2 / 1.5 / 1.8 mm steel, 2.5 mm aluminium |
| material | DP600, HC340LA, AA6060-T6 (MAT_024 with tabulated flow curve) |
| impactor | 100 kg rigid, 12 m/s (7.2 kJ), constrained to axial translation |
| standoff | 4 mm, clearing both shell contact thicknesses |
| element formulation | type 16 fully integrated shell, 5 through-thickness points |
| contact | AUTOMATIC_SINGLE_SURFACE for the folds, SURFACE_TO_SURFACE for the impactor, both SOFT=1 |
| trigger | two circumferential beads, 0.6 mm deep |

## The run matrix

```
python3 build.py --list
```

Eight models: a baseline, a three-point mesh convergence study, a
thickness sweep, two alternative materials, and one variant with GISSMO
damage and element erosion using the locus fitted in study 02.

## Modelling decisions worth defending in an interview

**Why a trigger.** Without an imperfection the collapse mode of a
perfect tube is decided by round-off, so peak force and fold pattern are
not repeatable between mesh sizes or between machines. The two beads make
the first fold form where it is supposed to, which is also what the real
part does - the bead is stamped in deliberately.

**Why fully integrated shells.** A crash box folds by plastic bending
with severe in-plane distortion. Under-integrated elements need heavy
hourglass stabilisation there, and the stabilisation energy contaminates
the internal energy exactly where the answer is being read.

**Why mass scaling by target timestep and not by a fixed factor.**
`DT2MS` is set to `-8.0e-4` ms, close to the natural timestep of the
5 mm mesh. Measured against the whole model the added mass is tiny
(0.1 %), because the 100 kg impactor dominates - but measured against the
1.1 kg tube it is 9-15 % on the 5 mm mesh and about 1 % on 7.5 mm. The
results table reports both, because only the second one tells you how
much inertia was added to the part that is actually folding. On the
3.5 mm mesh the same setting adds 147 % of the tube mass, which is the
cost of refinement made visible - and the reason that point is not
directly comparable with the other two.

**Why the impactor is 100 kg and not 500 kg.** The energy has to be
sized against what the tube can absorb. The Wierzbicki-Abramowicz mean
crush force for an 80 mm square DP600 tube is roughly

    P_m = 13.06 * sigma_0 * t^(5/3) * c^(1/3)

which is about 55 kN at t = 1.5 mm, or 11.5 kJ over an effective crush
length of 0.7 x 300 mm. The thinnest variant manages about 8 kJ. The
impactor carries 7.2 kJ, deliberately below that, so every variant in the
matrix crushes between 45 % and 90 % of its usable stroke and none of
them bottoms out.

Oversizing the impactor is not the conservative choice it looks like. Run
this model at 500 kg and 15 m/s and the tube flattens completely, the
folded material is squeezed between the impactor and the base, the
timestep collapses, and mass scaling adds twenty percent in a tenth of a
millisecond. `ENDMAS` on `*CONTROL_TERMINATION` now stops the run if that
ever happens rather than burning queue time on a result nobody can use.

**Why the aluminium variant is 2.5 mm and not 1.5 mm.** Comparing
AA6060-T6 against DP600 at the same wall thickness compares nothing
useful - the aluminium box is simply weaker. The thickness is set so the
mean crush force is comparable, which is the trade an engineer actually
evaluates: match the performance, then compare the mass.

**Why the standoff is 4 mm.** Contact acts on shell surfaces, not
mid-surfaces, so the gap has to clear half the impactor thickness plus
half the tube thickness. `build.py` asserts this. Too small and the
solver reports initial penetration and pushes the tube's top ring down to
resolve it, deforming the part before the first cycle.

**Why corner fillets rather than sharp corners.** Sharp corners
concentrate hourglass energy and bias the fold wavelength. The corners
carry most of the axial load in a square tube, so getting them wrong
moves the mean crush force.

## Results

Extracted from the solver output with `collect_results.py`, which checks
each run before reading a number from it (normal termination, energy
drift < 1 %, hourglass < 5 %, added mass < 5 %, sliding < 10 %, and
force-displacement energy agreeing with the tube's internal energy).
LS-DYNA R16.1 SMP, 4 threads. Material data are placeholders - see the
top-level README.

<!-- RESULTS:START -->
| variant | peak CFC600 [kN] | mean [kN] | CFE | absorbed [J] | stroke [mm] | SEA [kJ/kg] | HG [%] | added mass [% model] | added mass [% tube] | status |
|---|---|---|---|---|---|---|---|---|---|---|
| t1.5 h5 DP600 | 154.4 | 106.2 | 0.69 | 7138 | 67.5 | 29.0 | 0.00 | 0.13 | 12.0 | valid |
| t1.5 h7.5 DP600 | 161.8 | 105.7 | 0.65 | 7144 | 67.8 | 28.9 | 0.00 | 0.01 | 1.1 | valid |
| t1.5 h3.5 DP600 | 171.3 | 95.1 | 0.55 | 7583 | 75.4 | 27.6 | 0.00 | 1.59 | 147.0 | **CHECK** - one energy step of 6.9 % at 3.35 ms, flat afterwards; full history reported |
| t1.2 h5 DP600 | 109.1 | 77.1 | 0.71 | 7146 | 93.1 | 26.3 | 0.00 | 0.12 | 13.3 | valid |
| t1.8 h5 DP600 | 206.0 | 138.6 | 0.67 | 7114 | 51.6 | 31.5 | 0.00 | 0.12 | 9.0 | valid |
| t1.5 h5 HC340LA | 127.6 | 84.3 | 0.66 | 7153 | 85.1 | 23.1 | 0.00 | 0.17 | 15.3 | valid |
| t2.5 h5 AA6060-T6 | 89.6 | 55.4 | 0.62 | 6964 | 129.7 | 25.7 | 0.00 | 0.19 | 29.7 | valid |
| t1.5 h5 DP600 + GISSMO | 154.4 | 34.2 | 0.22 | 4954 | 191.9 | 7.1 | 0.00 | 0.06 | 5.9 | **CHECK** - energy balance clean (0.12 % drift) but sliding energy is 33 % of internal; 267 elements eroded |
<!-- RESULTS:END -->

![force vs crush](results/force_crush.png)

Peak force is the impactor contact force filtered at CFC 600. SEA is
absorbed energy per kilogram of *crushed* tube (perimeter x thickness x
stroke x density), so a variant that barely crushed is not flattered.
Full histories and the unfiltered peaks are in
[`results/crashbox_results.csv`](results/crashbox_results.csv).

### What the results show

- **Mesh convergence.** 5 mm and 7.5 mm agree on mean crush force within
  0.5 % and on absorbed energy within 0.1 %. Peak force differs by 5 %,
  and the second fold forms about 5 mm earlier on the coarse mesh - mean
  force converges faster than the fold pattern does, which is the
  expected order. The 3.5 mm point cannot be compared with them: at that
  element size `DT2MS = -8.0e-4` adds 1.5 kg, which is 147 % of the
  tube's own 1.1 kg, so the refined model is no longer the same problem.
  Its lower mean force (95 kN) is that added inertia, not convergence.
  A meaningful third point needs `DT2MS` reduced to roughly -4e-4 (and
  about twice the cycles), which is the real cost of that refinement.
- **Wall thickness.** Mean force rises from 77 to 139 kN between 1.2 and
  1.8 mm, close to the t^(5/3) scaling of the Wierzbicki-Abramowicz
  estimate (ratio 1.80 measured, 1.97 predicted). SEA improves from
  26.3 to 31.5 kJ/kg while CFE stays at 0.67-0.71, so the thicker box
  is more mass-efficient without a worse initial spike.
- **Material.** HC340LA at the same thickness gives 21 % less mean force
  and 20 % lower SEA than DP600, and uses 26 % more stroke.
- **Damage changes the answer completely.** With GISSMO active the peak
  force is unchanged at 154 kN - damage does nothing before the first
  fold - but the mean crush force falls from 106 to 34 kN and CFE from
  0.69 to 0.22. Elements start eroding at 1.56 ms, 267 are deleted, and
  the tube tears instead of folding: it takes 192 mm of stroke and the
  impactor is still moving at 3.5 m/s at the end, so the box no longer
  arrests the mass within its length. Of the 7.2 kJ, 5.0 kJ ends up as
  internal energy (2.2 kJ of it inside deleted elements) and 1.6 kJ as
  contact friction. Read the damage row as "what an uncalibrated failure
  locus does to a crash result", not as the performance of this box -
  see the note under the run list below.
- **Aluminium.** The 2.5 mm AA6060-T6 box was sized for a mean crush
  force comparable to the 1.5 mm steel, and it does not reach it: 55 kN
  against 106 kN. It absorbs the same 7 kJ over 130 mm instead of 68 mm,
  which is 43 % of the free length, and its SEA is 25.7 kJ/kg against
  29.0. Matching the steel would need roughly 3.5 mm of wall - which is
  the honest version of the trade, and a better comparison to make than
  the one the sizing assumed.
- **Stroke is short.** Every steel variant stops within 17-31 % of the
  free length, and the mean force is roughly twice the quasi-static
  hand estimate below. Most of the difference is strain-rate hardening
  (Cowper-Symonds C = 10 /ms, p = 5 is active at 12 m/s) plus the
  dynamic fold. The impactor energy could be raised to use more of the
  tube; it was kept at 7.2 kJ so the comparison with the earlier sizing
  stays valid.

### Runs that failed first time, and why

Kept here on purpose - diagnosing them is as much part of the job as the
runs that worked.

- **GISSMO variant: every tube element eroded on cycle 1.** messag
  showed `min pressure 0.0 < failure crit 0.0` (SOL+487) for all 3840
  elements, the impactor passed straight through with zero force, and
  the run still reported normal termination. Cause: `*MAT_ADD_EROSION`
  had `EXCL = -999` but `0.0` in the unused criteria. With EXCL set, a
  criterion is only switched off if it holds the EXCL value, so
  `MNPRES = 0.0` was a live "delete when pressure <= 0" criterion.
  Fixed in `tools/materials.py` - all unused fields now carry -999.
  Lesson: "normal termination" says nothing about whether the result is
  physical; the zero contact force did.
- **GISSMO: fixed, and now showing a modelling problem instead of a
  card error.** With -999 in the unused erosion fields the tube survives
  to 1.56 ms and the run completes with a clean energy balance (0.12 %
  drift). But two things say the damage model is not calibrated for this
  mesh: sliding energy reaches 33 % of internal energy, far past the
  10 % guideline, because erosion leaves free edges that grind through
  the contact; and the box loses most of its load-carrying ability.
  The cause is in `build.py`: the damage variant still uses the
  hard-coded `DEFAULT_TRIAX_CURVE`, a representative locus for 2.5 mm
  elements, with `LCREGD = 0` - no mesh regularisation - on a 5 mm mesh.
  Study 02 exists precisely to replace that: it fits the locus and the
  regularisation curve and writes them to
  `02_gissmo_calibration/results/gissmo_dp600.k`. Wiring that card in
  and rerunning is the next step, and the before/after is the argument
  for why regularisation is not optional.
- **Aluminium: fixed.** Segment-based contact (`SOFT=2`, `SBOPT=3`,
  `DEPTH=5`) took the run through the point where it used to break. It
  now reaches 30 ms with 0.19 % added mass and no energy drift, against
  a 10 % mass increase and a terminated run before. Thick shells folding
  onto themselves were the problem, exactly as the mass-increase
  locations suggested.
- **3.5 mm mesh: runs, with two things to note.** Besides the mass
  scaling above, the energy ratio takes a single 6.9 % step at 3.35 ms
  and is then flat to the end - one discrete event, not a runaway, so
  the numbers are reported but marked CHECK. Worth chasing in `sleout`
  and the contact forces at that instant before the number is quoted.
- **3.5 mm mesh: originally stopped in the keyword reader.** About 15 000
  STR+388/389 errors: "thin shell element 1 has an invalid material 1
  that exceeds the number of materials defined, 0". The job had been
  launched with `i=mesh_h3.5.k` - the mesh include - instead of the deck
  that defines the parts, sections and materials and pulls the mesh in
  through `*INCLUDE`. The mesh file on its own is nodes and elements
  referring to parts that do not exist in it, which is exactly what the
  error says. Run the deck: `i=crashbox_t1.5_h3.5_DP600.k`.
- **AA6060-T6: energy balance lost at 6.7 ms.** Energy ratio went 1.003
  -> 1.30 -> 30 within 0.15 ms, mass scaling added 10 % and `ENDMAS`
  stopped the run. The largest mass increases were around the trigger
  beads (z = 75-105 mm) and next to the clamped base: the 2.5 mm shells were
  stacking in the folds and the penalty contact stiffness drove the
  timestep down. The aluminium case now uses segment-based contact
  (`SOFT=2`, `SBOPT=3`, `DEPTH=5`), the standard remedy for thick shells
  folding onto themselves. Until it is rerun, the table shows its values
  up to 6.65 ms only.

### Reproduce

```bash
python3 build.py                 # regenerate decks and meshes
# copy each deck and its mesh_h*.k include into its own run folder,
# e.g. models/t1.5_h5/DP/, and run it there
ls-dyna i=crashbox_t1.5_h5_DP600.k ncpu=4
python3 collect_results.py       # checks, table, plot, README update
```

## Hand estimate used to size the impactor

The Wierzbicki-Abramowicz mean crush force used above is the quasi-static
value `P_m = 13.06 sigma_0 t^(5/3) c^(1/3)`; it ignores strain rate, which
is why the simulated mean force is higher.
