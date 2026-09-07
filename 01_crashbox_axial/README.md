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
`DT2MS` is set to `-8.0e-4` ms, just under the natural timestep of the
5 mm mesh, so almost no mass is added at the baseline. On the 3.5 mm mesh
the same setting starts adding mass, and how much shows up in the added
mass check - which is the honest way to see the cost of refinement.

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

## What to report

Run each model, convert the output and fill in the table.

```bash
ls-dyna i=models/crashbox_t1.5_h5_DP600.k ncpu=8
l2a binout*
python3 ../tools/energy_check.py glstat
python3 postproc.py --run runs/* --compare
```

| variant | peak force [kN] | mean force [kN] | CFE | absorbed [J] | SEA [J/kg] | HG [%] | added mass [%] |
|---|---|---|---|---|---|---|---|
| t1.5 h5.0 DP600 | | | | | | | |
| t1.5 h7.5 DP600 | | | | | | | |
| t1.5 h3.5 DP600 | | | | | | | |
| t1.2 h5.0 DP600 | | | | | | | |
| t1.8 h5.0 DP600 | | | | | | | |
| t1.5 h5.0 HC340LA | | | | | | | |
| t2.5 h5.0 AA6060-T6 | | | | | | | |
| t1.5 h5.0 DP600 + GISSMO | | | | | | | |

Crush force efficiency (mean / peak) is the number to lead with. A box
that absorbs the right energy with a CFE of 0.5 spikes hard on first
contact and is a worse design than one with the same SEA and a CFE of
0.75.

Expect the mesh study to show peak force converging faster than fold
count. If 7.5 mm and 5 mm agree on mean force but disagree on the number
of folds, say so - that is the useful finding, not a defect.
