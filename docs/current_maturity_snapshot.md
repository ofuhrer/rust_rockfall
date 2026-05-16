# Current Maturity Snapshot

This snapshot preserves the detailed project objective, capability-gap analysis,
and backlog-quality assessment that previously lived in `docs/task_backlog.md`.
Keep `docs/task_backlog.md` compact and executable; update this snapshot during
orchestrator/backlog-refill work when the maturity framing changes materially.

---
## Project Objective

The repository is trying to become an automated, reproducible rockfall
hazard-map workflow for Switzerland's Alpine terrain using public geodata,
primarily swisstopo. The current execution focus is the Balfrin
single-release-zone pilot track. That track now has a frozen pilot contract, a
deterministic large-case dry-run plan, a generate-only SLURM submission package,
a metrics-collection contract, a conditional gridpoint-curve product contract,
a post-run interpretation gate, and a conservative Swiss-wide runtime/storage
envelope helper. These are execution scaffolds and interpretation gates, not a
completed measured Balfrin pilot. The remaining near-term gap is the measured
Balfrin execution itself and the post-run evidence bundle needed to decide
whether that run is a usable conditional diagnostic artifact.

Medium-term objectives are to make the conditional pilot scientifically
interpretable, reproducible on Balfrin/CSCS-style infrastructure, and scalable
toward larger release-zone ensembles and eventually many Swiss AOIs. True
physical or annual
intensity-frequency products remain deferred until source occurrence rates,
block-population frequencies, uncertainty propagation, and validation or
calibration evidence exist.

The selected Tschamut target-scale evidence remains `inconclusive`. The
same-scale artifact chain is reproducible and measured, and the repository now
has multi-seed uncertainty, spatial uncertainty interpretation, stability
zoning, closure-gap deltas, hotspot persistence and provenance summaries,
closure criteria, GIS/package audits, command plans, native rebuildable reduced
output, first-class COG export, conditional gridpoint-curve semantics, and
bounded runtime/output evidence. Larger selected-domain runs remain blocked
until the dominant uncertainty and physical-credibility gaps below are reduced
with measured evidence. Second-site pilots remain non-executed, but Chant Sura
/ Fluelapass now has a concrete candidate manifest, reusable public-geodata
contract reporting, deterministic acquisition planning, a tiny synthetic
core-input staging helper, AOI-to-prepared-pilot dry-run composition, and an
explicit `deferred_public_context_inputs` boundary for the missing public
context products.

Non-goals for current backlog work: operational warning systems, regulatory
approval, risk/exposure/vulnerability modelling, annual return-period claims,
parameter tuning to fit the pilot, and new contact/terrain physics unless a
separate falsifiable implementation task is explicitly authorized.

## Capability Gap Analysis

The most important gaps between the current repository and the project
objective are:

1. Conditional pilot evidence is still inconclusive, but the same-scale
   Tschamut workflow is no longer blocked on missing local artifacts. The
   readiness preflight, deterministic case regeneration, restored gate/target
   manifests, portable command plan, measured convergence diagnostics, closure
   criteria, spatial uncertainty products, native reduced-output mode, COG
   export path, and bounded runtime/output summaries now form an executable
   evidence chain. The earlier `Balfrin target-gate reproduction` remains
   useful single-job execution evidence, and the newer Balfrin
   single-release-zone track is ready as dry-run automation rather than as
   measured post-run evidence.
2. Target-vs-gate convergence remains the dominant scientific uncertainty. The
   restored Tschamut gate and target hazard manifests expose 22 shared
   cell-wise layers. TB-024 ruled out grid/CRS and scenario/source path
   mismatch as dominant drivers. TB-031 expanded the evidence into six
   pairwise comparisons across gate, target, and two bounded 12-trajectory
   probes. `max_kinetic_energy` remains dominant with pairwise
   `l1_abs_diff` from `92903.17436309032` to `190718.90391041967`,
   `linf_abs_diff` from `1797.8665432400003` to `4484.5620665999995`, and
   nonzero Jaccard fixed at `1.0`. `max_jump_height` remains limited by
   support/nodata sensitivity with nonzero Jaccard from
   `0.7598039215686274` to `0.8579234972677595`.
   Spatial uncertainty is now measured from the same artifacts: the dominant
   uncertainty is localized rather than diffuse, stability zones and persistent
   conditional-hazard regions are named, and hotspot persistence is counted
   across the six pairwise artifact comparisons. `max_kinetic_energy` remains a
   closure-limiting layer with high-uncertainty cells dominated by
   shared-support magnitude variation, while `max_jump_height` remains mixed
   between shared-support magnitude and support/nodata sensitivity. Hotspot
   provenance now ties disagreement back to source/scenario/support evidence
   without changing the closure outcome. The closure matrix still treats both
   dominant layers as closure-limiting.
3. Output volume is measured and now has a canonical native rebuildable reduced
   execution mode. Target validation output remains the dominant measured
   pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially but
   remains non-rebuildable. The native `rebuildable_reduced_output` mode now
   writes the builder-facing trajectory, deposition, impact-event, diagnostics,
   trajectory-metadata, and stop-state artifacts directly and is exposed in the
   same-scale and Balfrin planning paths. The legacy derivation helper remains
   available only as a compatibility and proof fallback. The current execution
   scaffolding assumes native reduced output for the next Balfrin pilot;
   `scripts/summarize_balfrin_output_tier_audit.py` now records the measured
   reduced-output family counts, output bytes, restartability metadata, and
   conditional curve counts from an actual Balfrin run, and the measured tier
   is classified as sufficient for the current demo boundary without changing
   the no-scale-up boundary.
4. Forest and obstacle context is no longer an absent-cache problem; it is a
   limiting interpretation problem. Public context is staged and measured at
   corridor level, and hazard-context overlap has been measured for a narrow
   broader envelope. The overlap remains unresolved and does not imply
   obstacle absence or obstacle physics.
5. Tschamut source-zone and block-scenario case regeneration is deterministic
   from committed records and processed public inputs. The portable semantics
   are now split from Tschamut-specific heuristics, and dry-run helpers define
   deterministic release-zone candidate generation and pragmatic
   block-scenario generation from public-input contracts. These helpers do not
   generate production release zones, tune thresholds, or claim field evidence.
   The remaining automation gap is moving from dry-run contracts to a measured,
   public-context-backed second-site run only after real swisstopo context is
   staged.
6. Swiss-wide portability has a concrete Chant Sura / Fluelapass candidate, a
   multisite source/scenario contract audit, a reusable public-geodata workflow
   contract, deterministic acquisition planning, a tiny synthetic core-input
   staging path, a real-context readiness gate, a release-zone heuristic dry
   run, a release-plan dry run, an AOI-to-prepared-pilot dry-run orchestrator,
   and a blocked second-site case skeleton. The candidate now separates core
   readiness from `deferred_public_context_inputs`. No second-site ensemble or
   hazard build is authorized, and the synthetic inputs must not be represented
   as real swisstopo evidence.
7. Scaling direction is measured for the current same-scale set. The
   single-job Balfrin path remains sufficient for the next single-release-zone
   pilot, distributed execution stays deferred, and the dominant bottleneck is
   validation output size rather than hazard-reducer parallelism. The Balfrin
   submission package can be generated without submitting a job, and the
   metrics contract defines the wall-time, memory, output-volume,
   reduced-family, conditional-curve, and restartability evidence required
   after execution. The read-only Swiss-wide envelope helper projects runtime,
   storage, file-count, and job-count bands from measured coefficients; for a
   26-AOI Swiss-wide planning case it reports
   `no_go_extrapolated_beyond_measured_evidence` and keeps
   `scale_up_authorized=false`.
8. GIS package manifests are complete and declared GeoTIFF outputs are present
   for the same-scale artifacts. COG readiness is blocked for the committed
   standard roots by the current strip-organized raster layout, missing
   overviews, and `cloud_optimized: false` metadata, not by missing package
   manifests. The first-class `--export-cog` path now writes an ignored
   `gate_v1_cog_export` package that audits as COG-ready, proving the
   package-level export path without changing the committed roots. The
   conditional gridpoint curve product is now auditable from the hazard
   manifest and documentation: per-cell threshold semantics, denominator
   semantics, and non-annual/non-physical flags are explicit. The remaining GIS
   workflow gap is export-scope parity: the proof path is ready, but workers
   still need an explicit full-layer-scope COG command or a machine-readable
   scope-delta classification when thresholds are intentionally omitted.
9. Physical/annual frequency semantics, risk, exposure, vulnerability, and
   operational claims remain out of scope until conditional diagnostic
   convergence, source-frequency semantics, and validation/calibration
   evidence mature. The validation/calibration gap assessment reports
   `physical_credibility_status=not_established`, `calibration_status=missing`,
   and `validation_status=partial`. The observed runout/deposition intake
   contract and readiness pack now define what independent benchmark evidence
   must provide, but they do not populate the evidence or calibrate the model.
10. The fully automated "user supplies an AOI and receives an
    intensity-frequency hazard map" workflow is still a future product shape,
    not the current user workflow. The missing pieces are AOI-to-swisstopo tile
    discovery and download/cache management; generic terrain and context
    preprocessing; heuristic release-zone identification; pragmatic release
    and block-scenario plan generation; automatic ensemble-size/convergence
    control; a site-level orchestrator that chains those steps; and, most
    importantly, physical frequency semantics from source occurrence rates,
    block-population frequencies, uncertainty propagation, and
    validation/calibration evidence. Native rebuildable reduced output,
    first-class COG export, the conditional gridpoint curve contract,
    clean-checkout test hardening, AOI acquisition planning, release-zone
    dry-run planning, release-plan dry-run planning, AOI-to-prepared-pilot
    dry-run composition, blocked second-site case skeletons, the Balfrin pilot
    contract, case plan, generate-only submission package, metrics contract,
    post-run interpretation gate, and Swiss-wide execution envelope now
    distinguish completed dry-run automation from the remaining execution gap.
    The next measurable execution phase is to run the Balfrin
    single-release-zone pilot and collect its measured post-run evidence; true
    physical intensity-frequency curves remain deferred until the
    physical-probability layer exists.
11. Observed runout/deposition validation intake is specified but not
    populated. The contract records the required independent benchmark
    manifest, geometry, provenance, and objective-function placeholders. The
    intake requirements are executable as a dry-run readiness pack that writes
    template manifest, geometry inventory, provenance checklist, and validation
    summary files without claiming real evidence. Benchmark-intake readiness is
    now conceptually separate from calibration readiness, but actual benchmark
    data and objective-function evaluation remain absent.
12. Backlog and worker-context hygiene have improved materially. The active
    backlog is currently empty and `print_agent_task_context.py` reports
    `backlog_refill_needed=true` plus the Balfrin single-release-zone execution
    focus. The work log is chronological, archived history is separated, and
    repo consistency checks now reject unreachable or self-referential work-log
    commit hashes. The next backlog refill should start from this maturity
    state rather than resurrecting stale same-scale-only tasks.

## Backlog Quality Assessment

The current backlog should be judged by whether it creates new measurements,
analysis capabilities, reproducibility, or execution capacity. The strongest
tasks are those that turn the existing Tschamut/Balfrin artifacts into
actionable scientific evidence or remove a measured execution blocker.

Over-procedural areas to avoid:

- repeated reclassification of the same `inconclusive` evidence without a new
  analysis or run;
- additional YAML records or validators that do not enable execution,
  measurement, or reproducibility;
- roadmap/status maintenance that does not change what a worker can run or
  learn;
- secondary GIS/QGIS bookkeeping when the main conditional hazard-map evidence
  remains unresolved.

Current high-value work after TB-100:

- execute the Balfrin single-release-zone pilot from the frozen contract and
  generated submission package, then collect the required metrics bundle;
- run the Balfrin post-run interpretation gate on measured evidence and update
  this snapshot with the measured state;
- keep the pilot non-operational even if the post-run gate accepts a
  conditional diagnostic artifact;
- use measured Balfrin evidence to decide whether the next task should be
  stability/convergence follow-up, output-pressure mitigation, GIS/COG parity,
  or another bounded execution probe;
- stage real public context for Chant Sura / Fluelapass before any
  second-site hazard execution;
- keep physical credibility work tied to independent observed
  runout/deposition evidence rather than adding more empty validators.
