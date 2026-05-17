# Public Real-Site Geodata Preparation

Status: Phase 1 preparation contract for a future public Swiss real-site pilot.
This document does not download swisstopo products, commit raw geodata, run
simulations, change physics, or create annual/physical probability products.

## Purpose

The real-case pilot needs a reproducible geodata package before source-zone,
block-scenario, ensemble, or hazard-layer work can be interpreted. The package
must make a small public Swiss pilot domain auditable from public inputs while
keeping raw swisstopo tiles and large processed crops out of git.

The preparation artifact is a manifest, not a hazard result. It records the
selected domain, required public datasets, source-tile inventory, local ignored
directory layout, preprocessing plan, checksums, CRS/vertical-datum assumptions,
and claim boundaries.

## Files

- Template manifest:
  `data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml`
- Selected-domain manifest:
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`
- Validator:
  `scripts/validate_public_real_site_geodata_manifest.py`
- Conditional pilot run-freeze template:
  `validation/templates/public_real_site_conditional_pilot_run_v1.yaml`
- Conditional pilot run-freeze validator:
  `scripts/validate_public_real_site_conditional_pilot_run.py`
- Report scaffold:
  `docs/public_real_site_conditional_pilot_report_template.md`

The checked-in template is intentionally `template_not_run`. A real local pilot
should copy it to an ignored working directory, fill in the selected domain and
tile inventory, and run the validator before deriving source zones or
simulation cases.

The first selected public pilot domain is the Tschamut 2014 public
release/deposition corridor. Its share-safe manifest is
`data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`. That manifest
binds the domain to public swissALTI3D tile `2696-1167`, EPSG:2056/LN02,
the expected 2 m ESRI ASCII crop extent, source and processed SHA-256 digests,
the deterministic preparation command, and the selected source-scenario policy
`validation/policies/tschamut_public_source_scenario_policy_v1.yaml`. It does
not commit the raw tile, processed DEM, generated cases, validation outputs, or
hazard outputs.

The Phase 6 run-freeze template is also intentionally not run. It records the
geodata manifest, source-zone/block-scenario policy, benchmark case, terrain
metadata, source-zone sidecar, scenario table, random seed, gate scale, target
scale, thresholds, explicit grid, output budget, and report classification
before any local pilot execution. Completed gate or target runs must also fill
the `run_evidence` block with share-safe paths, checksums, runtime, output
counts, and convergence-diagnostic status for the generated private artifacts.
It is the gate that prevents tuning or claim-language drift after outputs are
inspected.

## Ignored Local Layout

Recommended local paths:

```text
data/raw/swisstopo/<pilot_id>/
data/processed/swisstopo/<pilot_id>/
validation/private/<pilot_id>/
hazard/results/<pilot_id>/
```

For the selected Tschamut public pilot, the preparation command writes ignored
processed terrain artifacts under:

```text
data/processed/swisstopo/tschamut_public_pilot/
```

and uses the shared ignored public raw-data cache:

```text
data/raw/swisstopo/
data/raw/tschamut2014/
```

Raw swissALTI3D, SWISSIMAGE, swissSURFACE3D, swissTLM3D, GeoCover, Geological
Atlas, GeoMaps, and swissBUILDINGS3D products must remain ignored unless a
future commit explicitly adds a tiny license-compatible fixture.

## Minimum Manifest Content

The manifest must record:

- `pilot_id`, `pilot_status`, and `operational_status`;
- selected domain name, purpose, LV95 extent, CRS `EPSG:2056`, and vertical
  datum `LN02`;
- required swissALTI3D source tiles and optional context datasets;
- source URL, product version/date where known, license notes, and tile ids;
- raw and processed local paths, with raw files excluded from git;
- processed DEM path, format, resolution, dimensions, nodata policy, and
  checksum when a processed crop exists;
- preprocessing steps for tile selection, crop, CRS/datum checks, checksum
  calculation, DEM export, and metadata emission;
- DEM/terrain sensitivity status and visual QA status;
- claim boundaries that identify current products as diagnostic or conditional
  intensity-exceedance only.

`swisstopo_swissalti3d` is required for the first real-site pilot. Context
layers such as SWISSIMAGE, swissTLM3D, GeoCover, or swissSURFACE3D are optional
until a specific QA or source-zone policy needs them.

## Validation

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_geodata_manifest.py \
  data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml
```

Validate the selected Tschamut public pilot manifest:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_geodata_manifest.py \
  data/processed/swisstopo/tschamut_public_pilot_manifest.yaml
```

The validator checks the share-safe contract only. It verifies CRS/datum,
dataset roles, required boundaries, local path conventions, source-tile
identity, product version/date, source and processed SHA-256 digests, processed
DEM dimensions, nodata, crop extent, and that template manifests do not pretend
raw or processed geodata are present.

For a local real pilot, use the same validator after the manifest records real
tile ids, raw checksums, processed DEM metadata, and QA statuses. The validator
does not prove scientific skill; it only gates provenance and claim hygiene.

## Selected Tschamut Public Pilot Preparation

The selected-domain manifest can be reproduced from a clean checkout plus
public downloads with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/prepare_tschamut_public_benchmark.py \
  --output-root data/processed/swisstopo/tschamut_public_pilot \
  --padding-m 250 \
  --force
```

The script downloads public Tschamut 2014 EnviDat resources and the public
swissALTI3D tile into ignored raw caches when absent, transforms the selected
Tschamut release/deposition rows to LV95, crops the 2 m swissALTI3D tile to the
manifested extent, writes the ESRI ASCII DEM and terrain metadata sidecar, and
records checksums. If network access is unavailable, place the files listed in
the manifest at the ignored raw paths and rerun the same command. A missing or
checksum-mismatched download is an explicit no-go for Priority 1 reproduction.

Only the selected-domain manifest is committed. The raw public downloads,
processed crop, generated cases, validation outputs, and later hazard outputs
remain ignored. The Tschamut terrain package is input geodata for workflow
development; it is not validation evidence by itself.

The selected public pilot cache contract is expressed by
`public_geodata_cache_contract` in the preflight helper output. It fixes the
ignored raw cache root, processed input/context roots, the cache-manifest path,
the deterministic stage command, and the verification command
`scripts/verify_public_geodata_cache.py`. That verifier checks source URL/id,
product version, checksum, CRS, resolution, tile id, crop extent, and
license/provenance note fields before staged public products are consumed.

The same-scale hazard outputs are now also audited as GIS packages. The
current roots have complete map-package and pilot-GIS manifests with GeoTIFFs
present, but the audited GeoTIFF layout is still strip-organized with no
overviews, so COG readiness remains blocked even though the package metadata
itself is complete.

A bounded proof-of-concept conversion path is now available through
`scripts/prototype_cog_conversion.py`. It converts one existing same-scale
GeoTIFF to a scratch output path under `/tmp`, verifies the result with
`gdalinfo`, and confirms the sample is tiled, has overviews, and reports a COG
layout.

That proof now extends to an ignored same-scale package-level result at
`hazard/results/tschamut_public_pilot/gate_v1_cog_export`. The converted root
audits as `cog_package_ready` with `cloud_optimized: true` metadata, while the
committed same-scale outputs still truthfully report
`gis_package_ready_cog_blocked`.
The converted root is intentionally scope-reduced relative to the standard
`gate_v1` inventory: it carries 20 raster layers and omits
`jump_height_exceedance_0p5m` and
`weighted_jump_height_exceedance_0p5m`, because the export command that
produced it only requested the 1 m and 2 m jump-height thresholds.

The GIS/COG audit now also accepts explicit converted-sample paths and ignored
converted package roots while keeping the current committed packages marked as
COG-blocked.

AOI handoff reports now carry a separate machine-readable GIS scope summary
that names planned raster/vector products, template-only downstream export
expectations, and unavailable inputs. That summary is a planning artifact, not
a generated hazard-map output, and it should not be read as evidence that any
hazard layers were produced.

The portable command plan now exposes the canonical package-level conversion
path directly, including the standard audit command, the `--export-cog`
builder path to the ignored `gate_v1_cog_export` package, and the
converted-package audit command, so future workers can recover the proof
without scraping prose notes.

## Second-Site Portability Preflight

`scripts/check_second_site_public_geodata_preflight.py` is a metadata-only
helper for a future Swiss site. It does not download geodata or run an
ensemble. Instead, it reports which public geodata products, terrain metadata,
source-zone/scenario records, extent definitions, and ignored output roots must
exist before the Tschamut workflow can be ported to a second site.

The preflight also distinguishes what is reusable from the current Tschamut
workflow, including readiness checks, case regeneration, convergence, output
profiling, context inspection, overlap diagnostics, and the uncertainty
envelope summary. It is a portability helper, not a gate or an acceptance
decision.

A staged placeholder candidate manifest lives at
`tests/fixtures/second_site_public_geodata_preflight/candidate_placeholder_site.yaml`.
Running the preflight against that manifest is expected to remain blocked until
actual second-site terrain, context, source-zone, and scenario inputs are
staged under the candidate roots.

A more concrete example manifest also lives at
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`.
It uses Chant Sura / Flüelapass as the candidate Swiss site because the repo
already carries Chant Sura benchmark metadata and fixtures, but it still
remains metadata-only and blocked until public terrain, source-zone, scenario,
and context inputs are actually staged.

The candidate now also has a committed acquisition/staging manifest at
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`.
That manifest names the expected swissALTI3D terrain crop, SWISSIMAGE,
swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, swissBUILDINGS3D, source
zone, scenario, and ignored output roots, while keeping the candidate blocked
until the actual staged inputs exist locally.

The second-site preflight and AOI planner also emit a reusable
`public_geodata_workflow_contract` summary. It names the required AOI
metadata, CRS/grid assumptions, swisstopo product classes, cache paths,
provenance requirements, and deferred optional context so later preprocessing
and release planning can target one contract instead of inferring site rules
from Tschamut-specific fixtures.

The second-site preflight and AOI planner now surface a deterministic dry-run
acquisition summary from that manifest. The summary names the expected staging
roots and metadata contracts for SWISSIMAGE, swissTLM3D, swissSURFACE3D,
swissSURFACE3D Raster, and swissBUILDINGS3D, but it still marks the public
context as deferred until real products are staged. No downloads occur during
that summary pass.

`scripts/plan_aoi_terrain_preprocessing.py` extends that contract with a
fixture-backed AOI terrain preprocessing report. It records the staged crop
extent, resolution, CRS, nodata policy, source tile ids, and deterministic
output roots, then feeds those fields into the release-zone candidate planner
when a local AOI tile catalog is present.

The current decision pack for the Chant Sura / Flüelapass candidate lives at
`docs/chant_sura_fluelapass_real_context_acquisition_decision.md`. It records a
defer recommendation, the cache/output roots, the required public-context
products, and the exact helper commands needed to reproduce the current
readiness boundary without downloading real public context. The same decision
pack now carries the Balfrin trigger matrix: measured
`balfrin_post_run_interpretation_gate_v1` evidence moves each public-context
product from defer to proceed, inconclusive evidence keeps the product rows
deferred, and missing evidence keeps them blocked.

The tiny synthetic staging fixture under
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/`
is a local scaffolding helper only. It exercises the contract and staging
paths without public downloads, but it is not public-geodata evidence and must
not be read as readiness for real SWISSIMAGE or swissTLM3D content.

Observed runout/deposition evidence remains a separate future intake contract,
not a public-context geodata product. The repo now carries a blocked
read-only contract summary at
`scripts/summarize_observed_runout_deposition_intake_contract.py` so future
benchmark intake can name the required geometry, event/source metadata,
uncertainty, and objective placeholders without implying that a calibration
dataset is already available. That helper now separates benchmark intake
readiness, which depends on the benchmark manifest and geometry only, from
calibration readiness, which is reported independently. The current
repository state is still blocked on independent benchmark evidence, and the
same helper can now emit a dry-run readiness pack into a caller-provided
temporary directory with a template manifest, required geometry inventory,
provenance checklist, and validation summary that are explicitly marked as
non-evidence artifacts.

The Chant Sura real-context readiness gate,
`scripts/check_chant_sura_real_context_readiness_gate.py`, layers on top of
that summary. It compares the deterministic acquisition plan with the locally
staged core inputs and supporting roots, then keeps the deferred public-context
products explicit so synthetic terrain, source-zone, and scenario fixtures are
never mistaken for public-context evidence.

The AOI-to-swisstopo dry-run planner,
`scripts/plan_swisstopo_aoi_acquisition.py`, is the first step before any real
staging. It reads the small AOI/site config and emits the required public
swisstopo product categories, expected staging paths, and unresolved
acquisition decisions so the future staging choice stays explicit before
downloads or copies are attempted.

The follow-on dry-run helper,
`scripts/plan_release_zone_heuristic_dry_run.py`, keeps the same Chant Sura /
Flüelapass fixture-backed site config but shifts the report from acquisition to
release-zone screening. It enumerates the deterministic heuristic
requirements, the concrete terrain and source/scenario inputs that are already
staged, and the public-context products that remain blocked or deferred. The
helper is intentionally not a release-zone interpretation: it stops at the dry
run boundary and reports `deferred_public_context_inputs` when real context is
absent.

The AOI-to-prepared-pilot dry-run helper,
`scripts/plan_aoi_to_prepared_pilot_dry_run.py`, composes the acquisition,
context, release-plan, and portable command-plan dry-run helpers into one
preparation scaffold. Its report names the terrain manifests, public-context
manifests, release/scenario placeholders, command-plan hooks, and ignored
output roots that a future demonstration workflow would need, while still
stopping short of any ensemble execution or public-context download. In its
optional ignored-root output mode it writes a deterministic case skeleton,
command manifest, expected-output-roots record, and blocked-execution record so
operators can inspect the handoff bundle before any run is authorized.

The next dry-run helper,
`scripts/plan_release_plan_dry_run.py`, turns the same fixture-backed candidate
source-zone record into deterministic release rows and block-scenario rows
before any ensemble is authorized. Its report keeps three machine-readable
sections separate: reusable semantics such as table shapes and probability
language, site-specific inputs such as the candidate source-zone metadata and
scenario rows, and Tschamut-only heuristics such as the frozen seed policy and
reference block classes. The helper is still a dry run and does not authorize
the future second-site execution template.

The same helper now also emits a scenario-generation contract block that makes
the dry-run boundary explicit: block-size bins and conditional weights are
listed separately from portable semantics, release rows are linked to
deterministic release-cell ids, required metadata is enumerated, and
unsupported physical-frequency fields are called out as out of scope. If
terrain or source-zone evidence is missing, the helper stays blocked rather
than synthesizing a scenario table from incomplete inputs.

For lower-level scenario-table generation,
`scripts/generate_tschamut_block_scenario_tables.py` now has a generic
candidate-source-zone path alongside the Tschamut compatibility wrapper. It can
combine candidate source-zone metadata with a policy template to emit stable
scenario ids, a provenance-aware manifest, and conditional-only weighting
semantics without introducing annual frequency or block-population fitting.
The conditional-only weights remain sampling weights, not physical probability
or annual-frequency claims.

The public-credibility boundary is now also machine-readable via
`scripts/map_physical_credibility_evidence_requirements.py`. That helper keeps
Chant Sura / Flüelapass public-context acquisition separate from physical
credibility evidence and points future acquisition work at concrete source
classes such as block-population surveys, source-frequency catalogues, and
independent holdout benchmarks rather than treating the synthetic staging
fixtures as validation evidence.

The same candidate also has a synthetic source-zone / scenario policy fixture
at
`validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml`.
That policy file is a contract fixture only. It defines the portable shape of
the candidate source-zone and scenario contract, but it is not physical
validation evidence and it does not imply that the deferred public-context
products have been staged.

`scripts/check_second_site_public_geodata_preflight.py` now makes the
Chant Sura public-context boundary explicit and machine-readable. Its report
separates the staged synthetic core fixtures from the deferred public-context
products, lists the expected local paths and metadata requirements for
SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and
swissBUILDINGS3D, and records the blocked second-site command templates so the
candidate stays honestly at `deferred_public_context_inputs` until real public
context is staged.

A tiny staging helper,
`scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`, copies the
synthetic core fixture set from
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/`
into the ignored Chant Sura paths. It is intentionally limited to terrain,
source-zone, scenario, and policy files plus the ignored roots that the
preflight checks for existence. It also creates the empty processed-context
root so the preflight can distinguish a missing core root from an intentionally
deferred public-context boundary. SWISSIMAGE, swissTLM3D, swissSURFACE3D,
swissSURFACE3D Raster, and swissBUILDINGS3D remain deferred and are still
reported explicitly by the preflight as `deferred_public_context_inputs`.
That helper stages synthetic core readiness only; it is not a real-context
readiness step and must not be treated as evidence that public geodata has been
acquired.

The canonical diagnostic interpretation helper
`scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
cross-references this portability boundary without promoting it to validation
evidence. It keeps Chant Sura public context in the deferred bucket until the
corresponding products are actually staged.

The new evidence-gap helper
`scripts/assess_validation_calibration_evidence_gaps.py` keeps the current
Tschamut evidence in the diagnostic category: observed deposition/runout,
release-zone, terrain/context, holdout, and multisite transfer evidence are
only partial, while calibration and block-population evidence remain missing.
That helper is read-only and does not tune the model or change acceptance
status.

The portable source-zone / scenario contract audit lives at
`scripts/audit_multisite_source_scenario_contract.py`. It compares the frozen
Tschamut source-zone and block-scenario records against the staged Chant Sura /
Flüelapass candidate manifest so future workers can see which fields are
portable contract shape, which are site-specific inputs, and which are still
Tschamut-specific heuristics.

Before the first conditional pilot run, also run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_conditional_pilot_run.py \
  validation/templates/public_real_site_conditional_pilot_run_v1.yaml
```

For a real local run, copy the template to an ignored pilot directory and use
the same validator after all freeze fields are populated. The validator requires
frozen inputs, nonnegative thresholds, explicit grid metadata, local output
budgets, and pass/no-go/inconclusive gate statuses. When a run is marked
`gate_run_completed` or `target_run_completed`, it also requires `run_evidence`
paths under the ignored validation/hazard output roots, recorded runtime and
output-volume metrics, convergence notes, and SHA-256 digests for the generated
manifests/tables. It does not run the simulator or hazard builder and does not
create or commit generated products.

After a non-template freeze file validates, print the portable command plan:

```bash
PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py \
  --site tschamut_same_scale --format text

PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py \
  --site chant_sura_fluelapass \
  --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml \
  --format json
```

The command-plan helper consolidates the Tschamut readiness preflight, case
generation, validation, hazard-layer building, convergence comparison,
output-profile checks, context inspection, overlap diagnostics, uncertainty
summary, and second-site portability templates. It is read-only and does not
execute commands by default; generated outputs remain under ignored validation
and hazard result roots when the listed commands are run intentionally.

## Claim Boundary

Phase 1 artifacts may claim:

- public geodata inventory is predeclared;
- CRS, vertical datum, extent, resolution, and provenance are recorded;
- raw and processed local paths are ignored or share-safe;
- future conditional pilot inputs are ready for review when all gates pass.

Phase 1 artifacts must not claim:

- annual frequency, return-period, or physical probability semantics;
- operational hazard-map validation;
- risk-map meaning;
- calibrated source frequency or block-population probability;
- validation evidence from swisstopo terrain by itself.
