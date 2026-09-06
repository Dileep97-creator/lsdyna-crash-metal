# Verification checklist

Run through this before reporting any result from any of these models.
It is the difference between a simulation and a number someone can act
on. The automated parts are covered by `tools/validate_k.py`,
`tools/mesh_quality.py` and `tools/energy_check.py`.

## Before the run

- [ ] Units consistent throughout (mm / ms / kg / kN / GPa here)
- [ ] `validate_k.py` clean - no field overflow, no duplicate IDs, no
      dangling section, material or part references
- [ ] `mesh_quality.py` clean - aspect ratio under 5, corner angle over
      30 degrees, warpage under 5 %, no degenerate elements
- [ ] Critical timestep reported by `mesh_quality.py` consistent with the
      `DT2MS` target set in the deck
- [ ] Contact definitions cover every surface pair that can touch,
      including self-contact where a part folds onto itself
- [ ] Initial penetrations in `messag` reviewed and fixed, not suppressed
- [ ] Boundary conditions do not over-constrain: nothing is clamped that
      is supposed to move, especially in a springback run
- [ ] Material curve extends past the strain the model will actually
      reach - extrapolation beyond the last point is flat and will
      quietly under-predict load
- [ ] Rigid body constraint codes checked; a rigid impactor that is free
      in a direction it should not be will not announce itself

## After the run

- [ ] Normal termination, not an error termination or a timestep collapse
- [ ] Total energy drift under 1 %
- [ ] Hourglass energy under 5 % of internal energy, and not concentrated
      in the region the answer is read from
- [ ] Added mass under 5 % of model mass, and located where it does not
      matter - check the added mass fringe in `d3plot`, not just the
      global figure
- [ ] Sliding interface energy under 10 % of internal energy and not
      strongly negative; negative sliding energy means contact is doing
      work on the model
- [ ] Kinetic energy small relative to internal energy in any
      quasi-static run (forming, coupon pull)
- [ ] Eroded energy accounted for; silent element deletion looks like
      energy absorption that is not there
- [ ] Rigid body motion of parts that should be fixed is zero
- [ ] Deformation mode physically plausible and repeatable between the
      two finest meshes

## Convergence and sensitivity

- [ ] Mesh refined at least once; report what changed and what did not
- [ ] Through-thickness integration points varied for any bending-driven
      result, springback especially
- [ ] Friction coefficient perturbed - forming results are more sensitive
      to it than to most material parameters
- [ ] Strain rate model switched off once, to see how much of the answer
      it is carrying
- [ ] Timestep scale factor reduced once; if the answer moves, the
      baseline was marginal

## Reporting

- [ ] Every quoted metric traceable to a specific run and deck version
- [ ] Placeholder or literature material data labelled as such
- [ ] Limits of validity stated: what load case, what range, what was not
      modelled
