# Talking about this work

Notes for turning the repository into CV lines and interview answers.
Fill in the bracketed numbers once you have run the models.

## CV bullets

- Built a scripted LS-DYNA modelling pipeline in Python that generates
  meshes and keyword decks from parameters, with automated deck syntax
  validation, mesh quality checks and energy-balance acceptance criteria
  running in continuous integration.
- Calibrated a GISSMO damage model across five stress states from pure
  shear to plane strain, including the mesh regularisation curve,
  quantifying a [x] % over-prediction of ductility when a coupon-scale
  failure locus is applied unregularised to a crash-scale mesh.
- Ran an axial crush study on a thin-walled crash box across eight
  variants covering mesh convergence, wall thickness and three materials,
  reporting specific energy absorption and crush force efficiency against
  hourglass and added-mass acceptance limits.
- Set up a U-channel deep drawing and springback study with MAT_036
  Barlat anisotropic plasticity and an explicit-to-implicit handover,
  evaluating flange angle, sidewall angle and curl radius against
  blankholder force.
- Calibrated a spot weld resultant failure envelope from a load-angle
  sweep and produced the MAT_100 card for use in body-in-white models.

Pick three. Five bullets on one project reads as padding; three reads as
depth.

## Questions this work should let you answer well

**"How do you know your crash result is right?"** Start with the energy
balance: drift, hourglass fraction, added mass, sliding energy, and where
the added mass ended up. Then mesh convergence. Then the fact that the
acceptance criteria are automated, so they cannot be skipped when a
deadline is close.

**"How much mass scaling is acceptable?"** Under 5 % globally is the
usual guideline, but location matters more than the number. Concentrated
added mass at the fold line changes the answer; the same amount spread
evenly does not.

**"Why does a damage model not transfer between meshes?"** Because
failure strain in a shell model is mesh dependent - strain localises into
whatever element size you gave it. That is what LCREGD exists for, and
study 02 shows the size of the effect for a specific case.

**"Why MAT_036 rather than MAT_024 for forming?"** r-values. A deep
drawing steel thins far less than an isotropic model predicts and draws
in differently around the perimeter. Isotropic plasticity gets punch
force roughly right and earing, thinning and springback wrong.

**"What is crush force efficiency and why lead with it?"** Mean crush
force over peak force. Two boxes absorbing the same energy are not
equally good: the one that spikes hard on first contact sends a worse
pulse into the structure and the occupant.

**"What would you do differently with more time?"** Good answer to have
ready. Honest options: run the coupon set against real tensile data
rather than placeholders; add a solid-element spot weld variant and
compare it against the beam; extend the crash box study to an oblique
load case, where the collapse mode changes from axial folding to global
bending and the SEA drops sharply.

## What to say about the limits

Be direct. The material data are representative published-range values,
the decks are generated and statically checked but the results tables are
yours to fill in, and the forming limit curve is a Keeler-Brazier
estimate rather than a measured Nakajima curve. Stating limits precisely
is itself a signal: engineers who cannot say what their model does not
cover are the ones who get trusted least.

## Presenting the repository

Lead with study 02. Crash boxes are common in portfolios; damage
calibration with mesh regularisation is a skill service firms bill for
and almost nobody demonstrates. The root README table is ordered
01 to 04 for narrative flow, but in a cover letter or an interview,
open with the calibration workflow and let the crash box be the thing it
feeds into.
