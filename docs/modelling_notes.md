# Modelling notes

Short answers to the questions these models tend to raise.

## Why type 16 shells everywhere

Fully integrated shells cost roughly twice an under-integrated element
per cycle but need almost no hourglass stabilisation. Crush and forming
are both dominated by plastic bending with severe in-plane distortion,
and the stabilisation energy of an under-integrated mesh contaminates the
internal energy in exactly the region the result is read from. The
exception is a very large model where cost matters more than local
accuracy; there, type 2 with `IHQ=4` and a monitored hourglass fraction
is the usual compromise.

## Mass scaling

A negative `DT2MS` means "add mass to reach this timestep". The value is
chosen just under the natural timestep of the intended mesh, so almost
nothing is added at the baseline and refinement makes the cost visible.
Setting it far above the natural timestep is what produces models that
run fast and are wrong: the added mass lands on the smallest, most
distorted elements and shows up as inertial resistance right where the
deformation is.

Always check where the mass went, not just how much. Two percent
concentrated in twenty elements at the fold line is worse than four
percent spread evenly.

## SOFT=1 contact

Penalty stiffness based on the stability of the contacting elements
rather than on their material bulk modulus. Necessary whenever contacting
parts have very different stiffness or mesh size, which in a folding
crash box is the case between adjacent folds. `SOFT=2`, segment based, is
better again for surface-to-surface between flat parallel parts, at
higher cost.

## Strain rate

Cowper-Symonds on `*MAT_024` scales the yield surface with plastic strain
rate. The `C` values in `tools/materials.py` are quoted in the literature
in 1/s and converted to the 1/ms time unit inside the module - the kind
of detail that silently breaks a model when it is done by hand in a deck.
Aluminium is treated as rate independent, which is standard.

Rate sensitivity is not a small effect in a crash box. Run it once with
and once without so you know how much of the answer it is carrying.

## Springback and integration points

The residual stress gradient through the thickness after bending and
unbending over a die radius is what drives springback. Five points
under-resolves it. Seven is the forming minimum, and where the ratio of
die radius to sheet thickness is small, nine or eleven is worth the cost.
This is the cheapest sensitivity study in the repository: one number in
`*SECTION_SHELL`, a large effect on the curl radius.

## Explicit forming speed

The punch in study 03 runs at 5 m/s, roughly a thousand times faster than
a real press. That is standard practice for explicit forming and it is a
compromise, not a free lunch. It has to be checked: kinetic energy should
stay a small fraction of internal energy throughout the draw. If it does
not, slow the punch or lean harder on mass scaling, and re-check.

## GISSMO versus a constant failure strain

A constant `FAIL` on `*MAT_024` deletes an element at one plastic strain
regardless of stress state. Real metal fails at very different strains in
shear, uniaxial tension and plane strain - typically a factor of two
across that range. GISSMO accumulates damage against a triaxiality
dependent locus and fades the stress out rather than deleting instantly,
which also removes the force discontinuity that instant deletion causes.

The cost is calibration effort, which is what study 02 automates.

## Why the meshes are generated rather than imported

Three reasons, in order of how much they matter in practice. A generated
mesh is reproducible, so a reviewer can regenerate it and get the same
model. A parameter study becomes a loop rather than an afternoon of
clicking. And the repository stays free of binary files, which means the
diff of a model change is readable.

The limitation is real and worth stating: this only works for geometry
that can be described parametrically. A real body-in-white part comes
from CAD and gets meshed in a pre-processor. The pipeline here is the
right tool for benchmarks, coupons and parameter studies, not a
replacement for one.
