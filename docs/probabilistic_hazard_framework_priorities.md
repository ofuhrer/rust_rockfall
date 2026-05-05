# Probabilistic Hazard Framework Priorities

Status: planning plus low-complexity schema alignment. This document does not
implement weighted hazard layers, annual frequency modelling, block-population
sampling, Parquet/Arrow output, model-form uncertainty ensembles, or exposure
and risk layers.

## Purpose

The repository now has deterministic simulation, verification, validation,
Swiss pilot geodata scaffolding, hazard exceedance layers, benchmark-driven
columnar-output design, and a minimal `trajectory_metadata_table_v1` sidecar.
Those pieces are necessary but not sufficient for a true probabilistic rockfall
hazard framework.

The next design constraint is semantic discipline: a future hazard map must make
clear whether a layer is an unweighted ensemble diagnostic, a conditional
probability given a release scenario, a weighted Monte Carlo estimate, or an
annual exceedance frequency derived from source-frequency inputs.

## Part 1: Missing Framework Components

### 1. Probability Semantics / Scenario Model

Why it matters:

This is the highest-priority missing component. Without explicit probability
semantics, the same raster value could mean sample occupancy, conditional
probability, weighted probability, or annual frequency. Those are scientifically
different products.

Required before probabilistic hazard maps:

Yes. Weighted maps should not be implemented until the case and manifest schema
can state the probability mode, selected numerator, denominator, normalization
convention, and filter set.

Can be implemented now:

Partly. The current low-complexity step is to reserve terms and defaults:
`unweighted`, `sampling_weighted`, `physical_probability`, `annual_frequency`,
`conditioned_on_filter`, and `absolute_probability_mass`. Full probability
models should remain deferred.

Risk if postponed:

High. Ambiguous terminology would make early weighted layers difficult to audit
and could lead to double-counting probabilities.

### 2. Source-Zone Probability and Release-Frequency Model

Why it matters:

Probabilistic hazard maps eventually need a source model: which source zones are
active, how frequently they release, and how release probability is distributed
within each source zone.

Required before probabilistic hazard maps:

Required before physical probability or annual-frequency maps. It is not
required for current conditional or unweighted diagnostic maps.

Can be implemented now:

Only as metadata placeholders. The current release-zone pilot can carry
`source_zone_id`; it should not invent source probabilities without a documented
source model.

Risk if postponed:

Medium to high. Current maps remain conditional on the simulated release set and
cannot be interpreted as absolute hazard frequency.

### 3. Block Population Model

Why it matters:

Block size, mass, density, and future shape class strongly affect kinetic
energy, jump height, runout, impact diagnostics, and intensity-style map layers.

Required before probabilistic hazard maps:

Required for maps that integrate over a block population. Not required for
single-block scenario maps.

Can be implemented now:

Only metadata fields are low risk: `block_radius_m`, `block_mass_kg`,
`block_density_kgpm3`, and a `shape_class` placeholder. Distribution sampling
should be deferred until the source/scenario model is clearer.

Risk if postponed:

Medium. Single-block maps can be useful, but they cannot represent block-size
uncertainty or size-conditioned hazard.

### 4. Trajectory Metadata and Weights

Why it matters:

Hazard post-processing needs a stable join between trajectory samples, impact
events, deposition rows, release metadata, block metadata, and probability
weights.

Required before probabilistic hazard maps:

Yes. This is the immediate bridge between deterministic simulation output and
probabilistic post-processing.

Can be implemented now:

Mostly already implemented at minimal scope. `trajectory_metadata_table_v1`
exists as an opt-in CSV sidecar, with `trajectory_id`, release/source metadata,
block metadata, `sampling_weight = 1.0`, and `probability_model = "unweighted"`.

Risk if postponed:

High. Retrofitting metadata after Parquet/Arrow or weighted hazard layers would
create fragile joins and unclear provenance.

### 5. Weighted Hazard-Layer Generation

Why it matters:

Weighted reach, deposition, kinetic-energy exceedance, and jump-height
exceedance maps are the first true probabilistic hazard products beyond
unweighted diagnostics.

Required before probabilistic hazard maps:

Yes, but only after probability semantics and metadata are explicit.

Can be implemented now:

Not yet. The metadata sidecar makes it possible later, but current hazard layers
should remain unweighted until denominator and normalization semantics are
implemented and tested.

Risk if postponed:

Medium. Current outputs remain useful for diagnostics and pilot workflows, but
they are not probability-weighted hazard products.

### 6. Uncertainty and Convergence Diagnostics

Why it matters:

Probabilistic layers need evidence that ensemble size is sufficient. Diagnostics
should quantify convergence of reach, deposition, exceedance, and high-energy
regions.

Required before probabilistic hazard maps:

Required before interpreting maps quantitatively. Not required for the first
weighted-layer prototype.

Can be implemented now:

Partly. Simple ensemble-size and bootstrap-style diagnostics can be designed
without changing physics, but they should follow the weighted-layer semantics.

Risk if postponed:

Medium. Maps may look stable while being dominated by sampling noise.

### 7. Calibration and Validation of Probabilistic Inputs

Why it matters:

Source probabilities, block-population distributions, and model parameters must
be calibrated or justified from data. Otherwise weighted maps can be precise but
not meaningful.

Required before probabilistic hazard maps:

Required for scientific credibility of physical probability or annual frequency.
Not required for conditional diagnostic maps.

Can be implemented now:

Only as a design and data-inventory step. The current calibration workflows are
impact- and trajectory-focused, not source-frequency models.

Risk if postponed:

High for operational interpretation, low for current research diagnostics.

### 8. Model-Form Uncertainty

Why it matters:

Different contact models, terrain-class assumptions, roughness settings, and
future shape models can produce different hazard layers. A probabilistic
framework must eventually distinguish aleatory variability from model-form
uncertainty.

Required before probabilistic hazard maps:

Important but not blocking for first conditional maps.

Can be implemented now:

Only through scenario identifiers and parameter-set metadata. Full model-form
ensembles should be deferred.

Risk if postponed:

Medium. Users may overinterpret one model configuration as the only plausible
hazard field.

### 9. Risk / Exposure / Vulnerability Layer

Why it matters:

Risk combines hazard with exposed assets and vulnerability. It is outside the
current simulator and requires additional datasets and assumptions.

Required before probabilistic hazard maps:

No. It is required only for risk products.

Can be implemented now:

No. The project should keep hazard and risk separate until hazard semantics are
stable.

Risk if postponed:

Low for hazard modelling, high if users expect risk maps. Documentation must
continue to state that hazard layers are not risk maps.

### 10. Production Formats and HPC Scaling

Why it matters:

Large ensembles and Swiss pilot domains require compact trajectory/event
storage, streaming accumulation, provenance manifests, and eventually
geospatial raster formats.

Required before probabilistic hazard maps:

Not required for small prototypes, but required for pilot-scale and larger
workflows.

Can be implemented now:

Columnar output can be implemented after schemas stabilize. GeoTIFF/COG and
distributed execution should wait until probability and table semantics are
clear.

Risk if postponed:

Medium. CSV is acceptable for small fixtures but will remain the bottleneck for
large impact-event and full-trajectory outputs.

## Part 2: Low-Hanging Implementation Steps

The following low-complexity steps are compatible with the current architecture
and do not change hazard semantics.

### A. Explicit Probability Terminology

Status: done in documentation. The docs now distinguish:

- conditional probability;
- weighted probability;
- annual frequency;
- sampling weight;
- physical occurrence probability.

This terminology should be used consistently in future case schemas, manifests,
and hazard reports.

### B. Reserved Metadata Fields

Status: minimally added to `trajectory_metadata_table_v1`.

Current metadata rows carry:

- `source_zone_id`;
- `release_probability`, currently null;
- `sampling_weight = 1.0`;
- `block_radius_m`;
- `block_mass_kg`;
- optional `block_density_kgpm3`;
- `scenario_id`;
- `probability_model = "unweighted"`.

This is enough for future joins and filtering without enabling weighted hazard
maps.

### C. Ambiguous Probability Configuration Rejection

Status: defer until weighted hazard configuration exists.

There is currently no active weighted-hazard configuration to reject. The future
validator should reject cases where multiple probability columns are active
without an explicit probability mode, or where weighted output is requested
without a normalization convention.

### D. Manifest Placeholders

Status: minimally added for trajectory metadata.

When `outputs.trajectory_metadata_csv` is configured, `run_manifest_v1` records:

- metadata schema version;
- metadata path;
- row count;
- `probability_model = "unweighted"`;
- `probability_semantics = "sampling_weight_only"`;
- `normalization_convention = "unweighted_current_outputs"`;
- total sampling weight.

Hazard-layer manifests should later add layer-level probability semantics.

### E. Illustrative Metadata Fixtures

Status: defer.

Artificial probability fixtures are useful for tests, but adding them before
weighted-layer code exists would create a risk that illustrative values are
mistaken for calibrated probabilities.

## Part 3: Compatibility Review

### `trajectory_metadata_table_v1`

Compatible. It is the correct source-of-truth table for release, block, scenario,
and probability metadata. It already provides `trajectory_id` for joining to
trajectory samples, impact events, and deposition outputs.

Missing before weighted maps:

- explicit physical probability source documentation;
- case-level probability mode;
- normalization convention;
- validation for ambiguous probability fields.

### `impact_events_table_v1`

Compatible if it includes `trajectory_id` and optionally denormalized weight
fields. For efficient hazard accumulation, future impact-event Parquet readers
should be able to scan only position, impact significance, energy diagnostics,
and selected weight/probability columns.

Recommended approach:

- keep `trajectory_id` required;
- keep metadata as the source of truth;
- allow denormalized `sampling_weight` or `trajectory_probability` only when the
  manifest declares the source metadata table.

### `trajectory_samples_table_v1`

Compatible if every sample includes `trajectory_id`. Future weighted reach and
exceedance maps can either join samples to metadata or read denormalized weight
columns.

Recommended approach:

- store trajectory samples as high-volume fact rows;
- avoid duplicating all metadata fields;
- optionally denormalize only the chosen probability/weight fields and filter
  keys needed for streaming hazard accumulation.

### Future Weighted Hazard Accumulation

Compatible with the current design if the hazard builder adds an explicit mode:

- `unweighted`;
- `sampling_weighted`;
- `physical_probability`;
- `annual_frequency`.

For each layer, the builder must record:

- numerator definition;
- denominator definition;
- selected weight/probability column;
- filters;
- normalization convention;
- total input and filtered probability mass.

### Filtering by Source Zone, Block Size, Mass, Scenario, and Model Configuration

Compatible. The metadata table already contains the minimum source-zone,
scenario, radius, mass, density, and shape-class fields needed for filters. A
future parameter-set or model-configuration id should be added before model-form
uncertainty ensembles are treated as first-class hazard scenarios.

## Part 4: Recommendation

Immediate low-complexity implementation step (completed by the first prototype):

Keep default outputs unweighted, but allow opt-in sampling-weighted conditional
maps only when the hazard-layer configuration states `probability_model`,
`weight_column`, `normalization_convention`, filters, and metadata path
explicitly. The implemented prototype uses `trajectory_metadata_table_v1` and
`sampling_weight` for weighted reach and trajectory-level exceedance rasters;
physical probability and annual-frequency maps remain deferred.

Next scientific design step:

Design a scenario model document for conditional source-zone hazard maps. It
should define source-zone probability, release-frequency, block-population, and
scenario-filter semantics without yet implementing sampling or calibration.

Next engineering step:

Implement opt-in columnar impact-event output only after locking the table
schemas. Impact events are still the measured I/O bottleneck, and the columnar
schema should include `trajectory_id` plus optional denormalized weight fields
that reference `trajectory_metadata_table_v1`.

Explicitly defer:

- weighted hazard layers;
- annual exceedance frequency;
- source-frequency calibration;
- block-size distribution sampling;
- Parquet/Arrow trajectory samples;
- model-form uncertainty ensembles;
- exposure, vulnerability, and risk layers;
- production GeoTIFF/COG output beyond current design discussions.
