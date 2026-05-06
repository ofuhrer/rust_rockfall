# Unified Public Benchmark Framework

Status: design and lightweight ingestion scaffold. This no-tuning framework standardizes
how public benchmark datasets enter the repository. It does not tune
parameters, change simulator physics, change defaults, or claim operational
hazard validity.

## Purpose

No single public rockfall dataset constrains the whole model. The repository
therefore treats each benchmark as evidence for a specific scientific question:

| Benchmark | Public source | Repository benchmark ID | Primary role | Not used for |
| --- | --- | --- | --- | --- |
| Tschamut 2014 | EnviDat DOI [10.16904/envidat.34](https://doi.org/10.16904/envidat.34) | `tschamut` | Deposition/runout realism, grouped failure-mode analysis, public registration workflow | Contact calibration, shape-contact validation by itself, operational hazard assessment |
| Chant Sura | EnviDat DOI [10.16904/envidat.174](https://doi.org/10.16904/envidat.174) | `chant_sura` | Trajectory/contact realism, impact timing proxies, jump-height and energy evolution | Deposition/runout skill for the full slope, parameter tuning |
| Chant Sura EOTA221 | EOTA resource inside EnviDat DOI [10.16904/envidat.174](https://doi.org/10.16904/envidat.174) and the published shape study | `chant_sura_eota221` | Passive shape/orientation metadata, future shape-contact evaluation, orientation-sensitive diagnostics | Current physics validation as a shape-aware model; the simulator remains spherical unless a future active shape-contact model is implemented |
| Mel de la Niva | Zenodo DOI [10.5281/zenodo.7257979](https://doi.org/10.5281/zenodo.7257979) and the open Landslides back-analysis paper | `mel_de_la_niva` | External high-energy/generalization benchmark, extreme-event trajectory and impact-path checks | Calibration of small-block field-experiment parameters, operational hazard zoning |

The strict rule is that benchmark preparation must be reproducible before any
model interpretation is made. Registration, run selection, exclusions, metadata
joins, and coordinate transforms are benchmark outputs, not hidden analyst
choices.

## Public Dataset Inventory

| Benchmark | License | Available public files | CRS / coordinate notes | DEM / terrain | Trajectory / deposition | Block / shape metadata | Main uncertainty |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tschamut 2014 | ODbL with DbCL | slope and block laser scans, test overview, LPS trajectories, jump/impact tables | slope scans in CH-1903/LV03; LPS trajectories in a local frame that requires documented registration | public slope scan and public swissALTI3D terrain crop in the current reproduction workflow | more than 80 LPS trajectories and test overview deposition/runout rows | six scanned blocks; committed passive sidecars for blocks 1, 2, and 4 | local-to-Swiss registration and terrain/source representation |
| Chant Sura | WSL Data Policy | `Input`, `Output`, `ExperimentalRuns`, `Video`, and `EOTA` archives plus published ESurf tables | reconstructed outputs and RF16 DEM fixtures use LV95-scale coordinates; fixture metadata records EPSG:2056 where available | UAS DEM/orthophoto in `Input`; tiny RF16 DEM contact crops are checked in | 82 reconstructed trajectories are publicly described; checked-in fixtures use small deterministic subsets | EOTA111/EOTA221 shapes, masses, StoneNode streams, and derived shape summaries | small contact fixtures and segment-boundary contact proxies |
| Chant Sura EOTA221 | WSL Data Policy through Chant Sura | EOTA point files and shape classes within the Chant Sura dataset | same site coordinate context as Chant Sura; shape point files are local object geometry | terrain comes from Chant Sura, not from EOTA shape files | not a standalone trajectory/deposition dataset; joins to Chant Sura runs by block class where metadata allow | EOTA221 wheel-shaped geometry and EOTA111/equant contrast | passive metadata does not represent active shape-contact physics |
| Mel de la Niva | CC BY 4.0 | reconstructed 3D trajectories, block 3D shapes, GIS paths/deposited blocks, SfM rasters/orthophotos, videos, simulation benchmark resources | public archive filenames indicate EPSG:21781/LV03 | SfM DSM and orthophoto rasters; no checked-in terrain crop yet | 2015 event trajectories and deposited-block/path GIS shapes | block 3D shapes for high-energy fragments | event scale, large archives, and CRS strategy must be handled before runnable cases |

## Standard Directory Contract

Tracked scaffolds live under `validation/benchmarks/<benchmark_id>/`. Large raw
archives and generated benchmark packages stay ignored.

```text
validation/benchmarks/
  tschamut/
  chant_sura/
  chant_sura_eota221/
  mel_de_la_niva/

data/raw/<dataset_id>/                         # ignored public raw cache
data/processed/<dataset_id>/                   # small committed derived fixtures only
validation/results/public_benchmarks/<id>/     # ignored generated cases, manifests, QA
hazard/results/public_benchmarks/<id>/         # ignored generated hazard products
```

Each benchmark preparation script should write a preparation manifest under the
ignored result directory. The manifest is the boundary between public data
preprocessing and validation execution.

Required manifest fields:

- `benchmark_id`, `dataset_id`, `schema_version`;
- public source URL, DOI, license, citation;
- raw input archives used, checksums when available, and download status;
- processed input paths and whether each file is committed or generated;
- CRS, vertical datum, coordinate transforms, and registration QA;
- terrain provenance, release provenance, observed-deposition or trajectory
  provenance, and shape metadata provenance where available;
- deterministic seed policy and selected trajectory/run IDs;
- excluded runs with reproducible reasons;
- generated validation cases, hazard commands, and manifest paths;
- grouped metric plan and limitations.

## Dataset-Specific Ingestion State

### Tschamut 2014

The current public workflow is the most mature benchmark. The preparation script
downloads public EnviDat LPS trajectories, slope scans, and a public
swissALTI3D tile into ignored raw paths, applies the documented
`scan_surface_fit_v1` registration, generates baseline and
`sphere_rotational_v1` cases, and writes QA overlays and a preparation
manifest.

Current role:

- runout/deposition mismatch;
- grouped failure modes by block, runout class, impact count, trajectory
  length, and contact model;
- passive shape sidecar validation for single-block subsets.

Critical limitations:

- no tuning is allowed after seeing results;
- passive shape sidecars do not affect dynamics;
- the public observations and terrain require explicit registration QA before
  scientific interpretation.

### Chant Sura

The checked-in fixtures already include first-flight and DEM-backed contact
subsets derived from the public EnviDat `Output` and `Input` archives. The
standard public-benchmark scaffold records those fixtures as a trajectory and
contact-validation package rather than as a deposition benchmark.

Current role:

- trajectory shape and energy evolution;
- DEM-backed segment/contact proxies;
- held-out contact generalization;
- comparison between `translational_v0` and opt-in `sphere_rotational_v1`.

Critical limitations:

- the contact fixtures are small RF16 subsets;
- segment boundaries are proxies for contact/rebound events;
- shape files are passive metadata only in the current simulator.

### Chant Sura EOTA221

The EOTA221 benchmark is a shape-readiness benchmark, not an active
shape-contact benchmark. Public EOTA point files and published shape classes are
used to validate passive metadata handling, block dimensions, and future
orientation-aware diagnostic plans.

Current role:

- verify shape metadata provenance;
- preserve the distinction between EOTA111 and EOTA221;
- prepare future tests for shape/orientation effects without pretending the
  current spherical dynamics can model them.

Critical limitations:

- no non-spherical contact points are implemented;
- no shape-dependent restitution, friction, or tumbling solver is implemented;
- any validation run using these sidecars should be numerically identical to the
  matching equivalent-sphere run unless a future version explicitly changes
  physics.

### Mel de la Niva

Mel de la Niva is the external generalization benchmark. The public Zenodo
dataset contains LV03/EPSG:21781 3D trajectories, block shapes, GIS path and
deposition shapefiles, SfM rasters/orthophotos, videos, and simulation
benchmark resources. The checked-in repository records metadata and a
preparation scaffold only; it does not download the roughly gigabyte-scale raw
package.

Current role:

- high-energy/extreme-event sanity check after the smaller public benchmarks
  are stable;
- external trajectory-path and impact-path generalization;
- future shape and terrain-interaction stress test.

Critical limitations:

- raw archives are large and remain ignored;
- first ingestion must define an explicit LV03-to-LV95 transform or keep LV03
  consistently through the generated package;
- the event scale differs from the small-block validation datasets, so it must
  not be used as a hidden parameter-tuning target.

## Grouped Validation Contract

All public benchmark reports should use the same vocabulary even when a dataset
does not support every metric:

- runout error and deposition overlap where deposition data exist;
- lateral spread and reach-envelope width where trajectories or deposition
  clouds exist;
- impact count and significant-impact density where instrumented impacts or
  model impact ledgers exist;
- trajectory length, shape error, and path topology where reconstructed
  trajectories exist;
- jump-height and kinetic-energy evolution where the observation supports those
  quantities;
- block ID, mass, equivalent radius, principal-dimension class, shape class, and
  contact model as grouping columns where available.

Missing metrics must be reported as unavailable, not inferred from unrelated
fields.

## No-Tuning and Leakage Controls

The benchmark framework separates:

- public raw cache under ignored `data/raw/`;
- committed small derived fixtures under `data/processed/` or
  `validation/data/processed/`;
- generated cases and outputs under ignored `validation/results/` and
  `hazard/results/`;
- calibration experiments under `calibration/`.

Rules:

- do not tune restitution, friction, roughness, scarring, shape, release, or
  terrain-class parameters inside validation preparation scripts;
- do not retroactively filter runs because a model performed poorly;
- record all run exclusions before interpreting model results;
- record registration uncertainty and keep fallback transforms auditable;
- keep passive shape metadata passive until a versioned active shape-contact
  model exists;
- never describe hazard layers as risk maps unless exposure and vulnerability
  inputs are explicitly included.

## Preparation Commands

Metadata-only or fixture-backed public benchmark manifests:

```bash
python3 scripts/prepare_chant_sura_public_benchmark.py
python3 scripts/prepare_chant_sura_eota221_benchmark.py
python3 scripts/prepare_mel_de_la_niva_benchmark.py
```

Full public Tschamut package generation, including public raw downloads:

```bash
python3 scripts/prepare_tschamut_public_benchmark.py --force
```

Generated outputs are ignored. A successful preparation manifest does not mean
the model is scientifically validated; it means the benchmark package is
reproducible enough to run and inspect.

## Implementation Roadmap

1. Keep Tschamut as the deposition/runout benchmark and finish all-usable-run
   grouped analysis before new physics.
2. Expand Chant Sura contact reporting only when it improves independent
   trajectory/contact evidence without changing calibration boundaries.
3. Use EOTA221 metadata to design active shape-contact tests, but keep current
   sidecars passive.
4. Add Mel de la Niva after the raw public archives are downloaded locally and a
   CRS-consistent package can be generated without hidden assumptions.
5. Only after these benchmark contracts are stable should the project add
   additional production formats or active shape-contact physics.
