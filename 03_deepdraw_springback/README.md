# 03 - U-channel deep draw and springback

A long narrow strip drawn into a U-channel over a radiused die, then
released. The classic 2D draw-bend benchmark, chosen because it is the
cheapest experiment that produces all three springback modes at once -
sidewall curl, flange opening and the change in punch corner radius.

## Model

| | |
|---|---|
| blank | 350 × 35 × 0.8 mm, DC04 |
| material | MAT_036 3-parameter Barlat, R00 1.80 / R45 1.45 / R90 2.10 |
| punch | 50 mm wide, nose radius 5 mm |
| die | shoulder radius 5 mm, clearance 0.05 mm per side over thickness |
| draw depth | 70 mm |
| blankholder force | 2.45 / 10.0 / 19.6 kN |
| element | 2 mm, type 16 shell, 7 integration points through thickness |
| friction | 0.125 Coulomb, forming one-way contacts, blank always the slave |

`build.py` writes two decks per case: `forming_*.k` (explicit draw) and
`springback_*.k` (implicit release).

## Why MAT_036 and not MAT_024

Deep drawing is anisotropic. A deep-drawing steel has an r-value near 1.8
in the rolling direction, which means it thins far less than an isotropic
model predicts and draws in differently around the perimeter. Using an
isotropic von Mises model for a drawing study gets the punch force
roughly right and the earing, thinning and springback wrong.

## Why seven integration points

Springback is driven by the through-thickness stress gradient left after
bending and unbending over the die radius. Five points is the crash
default and is not enough to resolve that gradient; seven is the usual
forming minimum, and for a tight radius over thickness ratio nine or
eleven is better. This is worth testing directly - it is a one-line
change and the effect on the curl radius is large.

## The explicit to implicit handover

```bash
# 1. explicit draw. Ends by writing dynain through
#    *INTERFACE_SPRINGBACK_LSDYNA
ls-dyna i=models/forming_bhf2.45.k ncpu=8
cp dynain dynain_formed

# 2. implicit release. Reads dynain, which carries the deformed shape,
#    the thinned thickness and the residual stress through thickness
ls-dyna i=models/springback_bhf2.45.k ncpu=8
cp dynain dynain_sprung

# 3. evaluate
python3 postproc_springback.py --formed dynain_formed --released dynain_sprung
```

Rigid body modes in the springback run are removed with a three-node
minimal constraint, not by clamping an edge. Clamping suppresses exactly
the deformation the model exists to measure - a common and easy mistake
that produces suspiciously small springback.

## A note on punch speed

The punch runs at 5 m/s, which is roughly a thousand times faster than a
real press. That is standard practice for explicit forming and it is a
compromise, not a free lunch. It has to be checked: kinetic energy should
stay a small fraction of internal energy throughout the draw. If it does
not, slow the punch down or increase mass scaling instead, and re-check.
`tools/energy_check.py` reports the ratio.

## What to report

| BHF [kN] | flange angle θ1 [°] | sidewall angle θ2 [°] | curl radius ρ [mm] | max thinning [%] | KE/IE peak [%] |
|---|---|---|---|---|---|
| 2.45 | | | | | |
| 10.0 | | | | | |
| 19.6 | | | | | |

Springback should fall sharply as blankholder force rises, because higher
restraining force means more tension through the sidewall and a smaller
residual bending moment. Showing that trend, with the mechanism, is worth
more than a single number.

## Forming limit evaluation

```bash
# export in-plane principal strains from LS-PrePost to CSV, then
python3 postproc_fld.py --strains strains.csv --t 0.8 --n 0.23
```

The FLC is a Keeler-Brazier estimate from thickness and hardening
exponent. It is a design-stage tool, not a substitute for a measured
Nakajima curve, and the script says so in its output.
