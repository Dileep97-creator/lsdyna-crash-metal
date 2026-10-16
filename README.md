# LS-DYNA Crashworthiness and Sheet Metal Studies

Four LS-DYNA studies demonstrating explicit crash simulation, damage calibration, sheet metal forming, springback, and spot weld failure.

The repository combines Python-generated meshes, reusable keyword formatting, automated model checks, and scripted post-processing to make simulation workflows reproducible.

## Studies

| Study | Engineering focus | Current status |
|---|---|---|
| [01 — Crash box axial crushing](01_crashbox_axial/) | Energy absorption, mesh sensitivity, mass scaling, hourglass control, SEA and CFE | Solver runs completed |
| [02 — GISSMO damage calibration](02_gissmo_calibration/) | Coupon simulations, failure-locus fitting, mesh regularisation | Calibration workflow demonstrated using bundled sample data |
| [03 — Deep drawing and springback](03_deepdraw_springback/) | MAT_036 Barlat, explicit-to-implicit transfer, springback and forming-limit evaluation | Decks generated and checked; solver runs pending |
| [04 — Spot weld failure envelope](04_spotweld_coupons/) | MAT_100 failure calibration using a load-angle sweep | Calibration workflow demonstrated using bundled sample data |

> Material inputs are representative demonstration values. Results illustrate the modelling workflow and do not establish validated properties for a particular commercial material.

## Crash Box Results

Axial crushing under an initial impact condition of **100 kg at 12 m/s**, corresponding to **7.2 kJ of initial kinetic energy**.

![Crash box force–crush response](01_crashbox_axial/results/force_crush.png)

| DP600 thickness | Mesh size | Peak force [kN] | Mean force [kN] | CFE [-] | SEA [kJ/kg] |
|---|---|---|---|---|---|
| 1.2 mm | 5 mm | 109 | 77 | 0.71 | 26.3 |
| 1.5 mm | 5 mm | 154 | 106 | 0.69 | 29.0 |
| 1.8 mm | 5 mm | 206 | 139 | 0.67 | 31.5 |

The reported runs pass the configured energy checks. Mean crush force differs by less than 0.5% between the evaluated 5 mm and 7.5 mm meshes. This comparison applies to mean force; local strain and failure predictions require separate mesh-sensitivity assessment.

An AA6060-T6 variant with a thickness of 2.5 mm produces approximately 55 kN mean force over a 130 mm crushing stroke.

See [Study 01](01_crashbox_axial/) for the evaluation method, model assumptions, comparisons, and run diagnostics.

## Engineering Workflow

### Parametric model generation

Each study uses `build.py` to generate the mesh and LS-DYNA input deck from parameters. Geometry, thickness, mesh size, and material variations can be regenerated consistently without manual meshing.

### Shared keyword formatting

`tools/kfile.py` provides reusable fixed-format keyword writing to keep deck formatting consistent across studies.

### Checks before execution

- `tools/validate_k.py`: field overflow, duplicate IDs, reference consistency, and include-file checks.
- `tools/mesh_quality.py`: aspect ratio, corner angles, warpage, and estimated critical timestep.
- Automated deck and mesh checks run through the repository’s CI workflow.

### Checks after execution

`tools/energy_check.py` evaluates configured numerical acceptance criteria and returns a non-zero exit status when a check fails.

| Quantity | Project screening criterion |
|---|---|
| Energy-balance drift | Below 1% |
| Hourglass energy relative to internal energy | Below 5% |
| Added mass relative to initial mass | Below 5% |
| Sliding/contact energy | Review against the configured 10% screening threshold and expected contact behaviour |

These are project screening criteria, not universal guarantees of accuracy. Evaluation intervals, normalisation, and exceptions are documented in the [verification checklist](docs/verification_checklist.md). Frictional dissipation is assessed in relation to the physical problem.

### Calibration workflows

Studies 02 and 04 fit damage and weld-failure parameters using bundled sample datasets and export material cards for subsequent modelling workflows.

Calibration using illustrative data demonstrates the method. Experimental validation requires independently measured data and comparison with the corresponding physical tests.

## Requirements

- Python 3 and the packages listed in `requirements.txt`
- GNU Make for the convenience commands below
- A separately installed and licensed LS-DYNA solver
- LS-PrePost or equivalent software for visual inspection
- `l2a` for the binary-to-ASCII conversion workflow shown below

Study 01 was run using **LS-DYNA R16.1**. Solver executable names and parallel execution options depend on the local installation.

## Quick Start

From the repository root:

```bash
python -m venv .venv
```

Activate the environment on Linux or macOS:

```bash
source .venv/bin/activate
```

Or on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies and prepare the models:

```bash
python -m pip install -r requirements.txt

# Generate model meshes and input decks
make build

# Check deck syntax and mesh quality
make check

# Run calibration workflows using bundled sample data
make calibrate
```

### Run a crash box model

The following example assumes the solver is available as `ls-dyna`:

```bash
cd 01_crashbox_axial/models
ls-dyna i=crashbox_t1.5_h5_DP600.k ncpu=8 memory=200m
```

Convert the required binary output and run the energy checks:

```bash
l2a binout*
python ../../tools/energy_check.py glstat
```

See each study’s README for its execution and post-processing instructions.

## Unit System

All models use a consistent **mm–ms–kg–kN** unit system.

| Quantity | Unit |
|---|---|
| Length | mm |
| Time | ms |
| Mass | kg |
| Force | kN |
| Stress and elastic modulus | GPa |
| Energy | kN·mm = J |
| Density | kg/mm³ |
| Velocity | mm/ms = m/s |

Example steel properties in this system:

```text
Density:          7.85e-6 kg/mm³
Young’s modulus:  210 GPa
```

Material definitions are managed in `tools/materials.py`.

## Performance Metrics

Crashworthiness metrics are evaluated over the documented crushing interval:

- **Absorbed energy:** integral of force with respect to crushing displacement.
- **Mean crush force:** absorbed energy divided by the evaluated crushing stroke.
- **Crush force efficiency (CFE):** mean crush force divided by peak crush force.
- **Specific energy absorption (SEA):** absorbed energy divided by absorber mass.

The study documentation defines the integration interval, force processing, and mass used in each calculation.

## Repository Structure

```text
tools/
  kfile.py                 Shared keyword formatting
  mesh.py                  Parametric mesh generation
  materials.py             Material definitions and unit conventions
  validate_k.py            Static deck checks
  mesh_quality.py          Mesh quality and timestep estimates
  energy_check.py          Numerical acceptance checks
  postproc/                Output readers and processing utilities

01_crashbox_axial/
  build.py
  postproc.py
  models/
  results/

02_gissmo_calibration/
  build.py
  calibrate.py
  data/
  models/

03_deepdraw_springback/
  build.py
  postproc_springback.py
  postproc_fld.py

04_spotweld_coupons/
  build.py
  calibrate.py
  data/
  models/

docs/
  verification_checklist.md
  modelling_notes.md
  troubleshooting.md
  cv_bullets.md
```

## Reproducibility and Limitations

- Study 01 contains completed solver results; Study 03 has not yet been run.
- Studies 02 and 04 demonstrate calibration using bundled sample data.
- Flow curves, anisotropy parameters, failure strains, and weld strengths are representative inputs rather than a validated material database.
- Numerical verification checks support model assessment but do not replace experimental validation.
- Large solver outputs are excluded from version control. `collect_results.py` rebuilds result tables from a run directory.
- Results can depend on solver version, element formulation, contact settings, mesh size, loading rate, and mass scaling.

## Documentation

- [Verification checklist](docs/verification_checklist.md) — acceptance checks before reporting results.
- [Modelling notes](docs/modelling_notes.md) — assumptions, modelling choices, and applicability.
- [Troubleshooting](docs/troubleshooting.md) — solver issues and diagnostic approaches.
- [Discussing the project](docs/cv_bullets.md) — technical talking points and portfolio descriptions.

## Licence

Repository code is released under the [MIT Licence](LICENSE).

Third-party material data and references remain subject to their original licences and attribution requirements.
