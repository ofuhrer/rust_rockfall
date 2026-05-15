# Output Budget And Reducer Scaling Gate

Status: DT-08 fail-closed gate for selected public Swiss pilot domains. This
gate defines the minimum evidence needed before a real-site pilot can be
treated as output-budget safe for larger selected-domain runs. It does not
change physics, reducer behavior, output defaults, or operational claims.

Maintenance note: this is the completed DT-08 evidence contract. It is not a
current target list. Routine target sequencing and current gap assessment live
only in `docs/task_backlog.md`; update this file only when the
output-budget/reducer gate itself changes.

## Scope

This gate applies to:

- the selected Tschamut public pilot;
- future Swiss public-data pilots that use the same conditional hazard-map
  and reducer families.

The gate is fail-closed. If the output budget is incomplete, ambiguous, or
exceeds the recorded bounds, the pilot must remain `blocked` or `diagnostic`.
It is a no-tuning/no-physics/no-output-default-change/no-operational boundary.

## Required Evidence

The following evidence categories must be present before a real-site
output/reducer artifact can be treated as accepted for larger execution:

- output file-count budget evidence;
- output byte-count budget evidence;
- inode/file-family budget evidence;
- summary-only conditional curve requirements for scalable runs;
- grid CSV suppression requirements for scalable runs;
- reducer state-size and dense-grid accumulator risk classification;
- reducer chunk/restart manifest requirements;
- checksum and hash requirements for reducer outputs and sidecars.

## Output File-Count Budget

The record must state the file-count budget for both the validation and hazard
trees.

Required fields:

- validation output file count;
- hazard output file count;
- target file-count ceiling or blocker status;
- explicit note if the validation output budget remains a blocker for any
  larger scale-up.

For the selected Tschamut pilot, the current recorded evidence keeps the
validation-side output tree as the dominant budget pressure. The gate is not
passed until that budget is explicitly accepted or reduced.

## Output Byte-Count Budget

The record must state the byte-count budget for both validation and hazard
outputs.

Required fields:

- validation output bytes;
- hazard output bytes;
- sidecar or manifest byte counts where relevant;
- explicit note if the current byte budget is only diagnostic rather than a
  pass condition.

The output-byte budget must remain explicit so future larger runs cannot
silently exceed the validated local storage envelope.

## Inode And File-Family Budget

The gate must record inode use and file-family pressure:

- file-family counts by broad output class;
- inode or path-count pressure where it matters;
- whether the run is bounded by debug/sidecar proliferation rather than the
  hazard rasters themselves.

The gate must treat inode/file-family growth as a real scaling limit rather
than an afterthought.

## Summary-Only Conditional Curves

Scalable runs must keep conditional curves summary-only.

Required controls:

- `--conditional-curve-export summary-only`;
- no full per-cell conditional-curve CSV table in the scalable profile;
- a share-safe note if the current evidence still reflects a legacy or mixed
  output profile rather than a fully proven scalable profile.

## Grid CSV Suppression

Scalable runs must suppress grid CSV output.

Required controls:

- `--grid-csv-export none`;
- no full-grid CSV as a scalable default;
- explicit note if the selected target-gate evidence does not yet prove grid
  CSV suppression from the recorded command evidence.

## Reducer Scaling And Dense-Grid Risk

The gate must classify reducer state-size and dense-grid accumulator risk
explicitly.

Required fields:

- reducer mode;
- reducer worker count;
- chunk count;
- merge order;
- reducer parity or repeatability status;
- dense-grid accumulator risk status;
- whether reducer restart state and merge state remain limited to the current
  local single-job boundary.

The gate must record whether reducer state is still safely bounded for the
current selected pilot or whether the dense-grid accumulator/restart state
requires a stricter no-go before scale-up.

## Reducer Chunk / Restart Evidence

The record must include chunk and restart-manifest evidence:

- chunk manifests;
- reducer execution index manifest;
- reducer merge state manifest;
- deterministic chunk-id policy;
- local restartability or replay status.

This gate does not implement distributed reducers. It only records the
current local single-job reducer/restart contract so future execution choices
stay auditable.
These are the reducer chunk/restart manifest requirements for DT-08.

## Checksum Evidence

The gate must include checksum and hash evidence for reducer outputs and
sidecars:

- validation manifest checksum;
- hazard manifest checksum;
- reducer-sidecar checksum or hash where available;
- explicit note if the checksum evidence is tied to ignored local outputs.

## Local / Distributed Boundary

This gate is about the current local single-job output and reducer boundary.
Distributed execution remains a later DT-09 concern.

The gate must explicitly record that:

- local single-job evidence is current;
- distributed reducers, SLURM arrays, MPI, and GPU execution are not being
  introduced here;
- future distributed execution is only a follow-on if measured output/reducer
  bottlenecks justify it.

## Classification States

- `passed`: all required output/reducer evidence is complete and current;
- `diagnostic`: evidence is documented but not yet sufficient for acceptance;
- `blocked`: evidence is missing, stale, or inconsistent;
- `no_go`: evidence contains an unrecoverable output or reducer problem.

The selected Tschamut pilot should remain `blocked` or `diagnostic` until the
required evidence is complete and locally verified.

## No-Tuning And Claim Boundary

This gate does not authorize:

- tuning to absorb output or reducer issues;
- physics changes;
- reducer-behavior changes;
- output-default changes;
- ensemble-size increases;
- annual frequency, physical probability, return periods, risk, exposure, or
  vulnerability claims;
- operational hazard-map claims.

## Minimum Acceptance Rule

A real-site output/reducer artifact is acceptable for larger pilot
interpretation only when the record can show all of the following:

- validation and hazard output budgets are explicit;
- summary-only conditional curves are required for scalable runs;
- grid CSV suppression is required for scalable runs;
- reducer state-size and dense-grid risk are explicitly classified;
- chunk/restart manifests are recorded;
- checksum and hash evidence is present;
- the local single-job versus future distributed boundary is explicit;
- claim boundaries remain conservative.
