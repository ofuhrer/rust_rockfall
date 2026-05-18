# Target-Area Physical Evidence Acquisition Pack

Status: planning-only acquisition pack for the Tschamut target area. This
document is not evidence, does not imply validation, and does not authorize
calibration, annual-frequency, physical-probability, risk, exposure,
vulnerability, or operational claims.

## Purpose

This pack makes the physical-credibility gap concrete enough for acquisition.
It separates the evidence that would support:

- observed runout/deposition intake;
- release-zone provenance;
- block-population or block-size census evidence;
- source-frequency and temporal-frequency evidence;
- calibration separation, if calibration is ever authorized later.

It stays aligned with the repository helpers that already report these
boundaries:

- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/assess_validation_calibration_evidence_gaps.py`

## Acquisition Triage

| Evidence class | Triage | First missing input | Next action |
| --- | --- | --- | --- |
| Field-supported release-zone provenance | candidate | `site_specific_release_zone_geometry_package` | Acquire a field-supported site-specific release-zone geometry/provenance package distinct from the conditional contract. |
| Block-population evidence | candidate | `block_size_survey_or_photogrammetry_census` | Acquire a block-size survey or photogrammetry census with survey-frame provenance. |
| Source-frequency records | defer | `historical_rockfall_event_catalogue` | Defer source-frequency records until a phase change explicitly authorizes frequency semantics; keep conditional sampling weights out of frequency claims. |

## Target-Area Checklist

### 1. Independent observed runout/deposition benchmark intake

Acquire a benchmark package that can be reviewed without reusing the same
material for model selection or calibration.

- benchmark manifest with a stable `event_id` and `site_id`;
- observed geometry for the runout axis line, deposition footprint, and any
  reference observation points;
- geometry CRS `EPSG:2056` and vertical datum `LN02`;
- provenance for the observation method, observer, and source reference frame;
- measurement uncertainty for geometry, position, timing, and QA coverage;
- separation note showing the intake was not reused for calibration or tuning.

### 2. Site-specific release-zone evidence

Acquire release-zone evidence that is distinct from the frozen conditional
contract and can be traced back to field or reference-data provenance.

- first missing input: `site_specific_release_zone_geometry_package`;
- release-zone geometry package with stable geometry identifiers;
- source polygon or equivalent release geometry role;
- provenance for the field reconnaissance, mapping, or reference basis;
- CRS and vertical-datum record matching the site-specific benchmark frame;
- source geometry reference that is separate from workflow-only candidate
  release-zone inputs.

### 3. Block-population or block-size evidence

Acquire the block-population evidence needed if the repository ever moves from
conditional sampling toward physical-probability semantics.

- first missing input: `block_size_survey_or_photogrammetry_census`;
- survey footprint geometry or census footprint for the observation frame;
- block-count or size-class record tied to a stable survey identifier;
- method note for photogrammetry, field census, or another defensible survey
  basis;
- provenance URI or citation for the survey record;
- explicit note that the record is not a source-frequency catalogue.

### 4. Source-frequency and temporal-frequency evidence

Acquire the evidence needed to distinguish scenario sampling from source
occurrence frequency.

- first missing input: `historical_rockfall_event_catalogue`;
- source-zone identifier and geometry version or hash;
- event-class definition and frequency unit;
- observation window, time window, or catalog period;
- rate provenance and uncertainty representation;
- source-zone overlap policy and any calibration / validation separation
  record required by the future gate.

### 5. Calibration separation, if later authorized

Keep calibration separate from benchmark intake.

- reserved calibration split;
- objective-function placeholder or fit record only if a future task
  explicitly authorizes calibration;
- holdout-validation separation record;
- no reuse of benchmark intake evidence for calibration selection.

## Dataset Roles

| Dataset role | Acquisition purpose | Required geometry and provenance fields | Claim boundary |
| --- | --- | --- | --- |
| Independent observed runout/deposition benchmark | Future benchmark intake for physical credibility review | `geometry_id`, `geometry_role`, `geometry_encoding`, `geometry_crs=EPSG:2056`, `geometry_value`, `event_id`, `event_date`, `site_id`, `source_id`, `source_name`, `observer`, `observation_method`, `provenance_uri`, `source_origin_description`, `source_reference_frame`, `source_geometry_reference`, `geometry_tolerance_m`, `position_tolerance_m`, `timing_tolerance_days`, `coverage_completeness`, `qa_status`, `uncertainty_notes` | May reduce the physical-credibility gap only; no calibration, annual-frequency, risk, or operational claim |
| Site-specific release-zone package | Physical provenance for release-zone interpretation | `geometry_id`, `geometry_role=source_polygon`, `geometry_encoding`, `geometry_crs`, `geometry_value`, `source_id`, `source_origin_description`, `source_reference_frame`, `source_geometry_reference`, `provenance_uri` | Physical interpretation only; not validation, calibration, or frequency evidence |
| Block-population survey or census | Block-size and block-population evidence for a future physical-probability phase | Survey footprint geometry, `survey_id`, `observer`, `observation_method`, `provenance_uri`, `block_count` or size-class fields, survey CRS and datum, sampling-frame description | Future physical-probability bridge only; annual-frequency claim remains blocked |
| Source-frequency catalogue | Source-occurrence evidence for a future frequency gate | `source_zone_id`, `source_geometry_version`, `source_event_class`, `frequency_model_id`, frequency unit, rate time window, observation period, `rate_provenance`, `rate_uncertainty`, `source_zone_overlap_policy`, `calibration_dataset_ids`, `validation_dataset_ids` | Deferred frequency evidence; no annual-frequency or operational claim |
| Reserved calibration split | Calibration separation only | Calibration dataset ids, validation dataset ids, split rules, objective-function placeholder fields, provenance for the split record | Calibration only, and only if a later task authorizes it |

## Claim-Boundary Mapping

| Evidence class | Current status | What it can support | What stays blocked |
| --- | --- | --- | --- |
| Observed runout/deposition benchmark intake | `blocked_missing_inputs` | Independent benchmark intake planning | Calibration, annual-frequency, risk, exposure, vulnerability, operational claims |
| Release-zone evidence | `partial` / future acquisition class | Site-specific physical provenance for release geometry | Validation, calibration, physical-probability claims |
| Block-population evidence | `missing` | Block-size and block-population acquisition planning | Annual-frequency and physical-probability claims |
| Source-frequency evidence | `deferred_unsupported` | Frequency acquisition planning only | Annual-frequency, physical-probability, operational claims |
| Calibration separation | `blocked_missing_inputs` | Future fit separation only | Benchmark intake reuse and tuning |

## Blocked Status Summary

The pack separates the blocked states so benchmark intake, calibration, and
frequency evidence do not collapse into one label:

- benchmark intake: `blocked_missing_inputs`, because the benchmark manifest
  and observed-geometry inputs are not staged;
- calibration: `blocked_missing_inputs`, because no calibration dataset is
  staged;
- source-frequency evidence: `deferred_unsupported`, because the repository
  still has conditional scenario weighting rather than a staged source-rate
  catalogue;
- block-population evidence: `missing`, because no census or survey-backed
  block-population record is staged.

## Acquisition Order

1. Stage the independent observed runout/deposition benchmark manifest and
   geometry.
2. Acquire site-specific release-zone provenance that is distinct from workflow
   heuristics.
3. Acquire block-population or block-size survey evidence if a later phase
   needs physical-probability semantics.
4. Defer source-frequency evidence until a later gate explicitly allows
   frequency semantics.
5. Keep calibration records separate from the benchmark intake and from any
   future frequency evidence.

## Current Boundary

This pack defines what to acquire next. It does not say the repository already
has:

- a validated benchmark;
- a calibration dataset;
- source-frequency or annual-frequency evidence;
- a physical-probability product;
- a risk, exposure, vulnerability, or operational workflow.
