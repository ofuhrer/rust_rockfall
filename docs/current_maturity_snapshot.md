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
single-release-zone pilot track. That track now has a minimal demonstration
contract, a deterministic large-case dry-run plan, a generate-only SLURM
submission package, a metrics-collection contract, a conditional
gridpoint-curve product contract, a post-run interpretation gate, a canonical
evidence-bundle helper, fixture-backed restartability and output-tier reports,
a failure taxonomy/playbook, a runtime/scaling frontier helper, and a
second-site acquisition defer decision. These are execution scaffolds,
fixture-backed demonstrations, blocked-state reports, and interpretation
gates. They are not a completed measured Balfrin pilot. The largest near-term
gap remains the actual Balfrin single-release-zone execution, followed by the
post-run evidence bundle needed to decide whether that run is a usable
conditional diagnostic artifact.

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
3. Output volume is measured for the same-scale Tschamut set and now has a
   canonical native rebuildable reduced execution mode. Target validation output remains the dominant measured
   pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially but
   remains non-rebuildable. The native `rebuildable_reduced_output` mode now
   writes the builder-facing trajectory, deposition, impact-event, diagnostics,
   trajectory-metadata, and stop-state artifacts directly and is exposed in the
   same-scale and Balfrin planning paths. The legacy derivation helper remains
   available only as a compatibility and proof fallback. The current execution
   scaffolding assumes native reduced output for the next Balfrin pilot;
   `scripts/summarize_balfrin_output_tier_audit.py` now classifies collected
   Balfrin evidence provenance as measured, fixture-backed, or blocked, and its
   current regression evidence uses the synthetic
   `tests/fixtures/balfrin_probe_metrics_contract/complete_run_root` fixture.
   That fixture-backed audit reports `audit_status=fixture_backed`,
   `rebuildability_status=sufficient`, `571377719` validation bytes,
   `16613900` hazard-output bytes, `2005` validation files, `46` hazard-output
   files, and `729600` conditional-curve rows. This proves the audit contract
   and expected reduced-output shape, but it is not a live Balfrin measurement.
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
7. Scaling direction is measured for the current same-scale set, but the
   Balfrin pilot track is still pre-execution. The single-job Balfrin path is
   the intended near-term execution boundary; distributed execution stays
   deferred, and prior same-scale evidence says validation output size is the
   dominant pressure rather than hazard-reducer parallelism. The Balfrin
   submission package can be generated without submitting a job, and the
   metrics contract defines the wall-time, memory, output-volume,
   reduced-family, conditional-curve, and restartability evidence required
   after execution. The post-run gate currently reports
   `blocked_missing_inputs` when no post-run evidence bundle is supplied. The
   Swiss-wide envelope helper has a blocked-report path for missing measured
   Balfrin evidence and a conservative no-go path for extrapolated planning
   cases; it does not authorize Swiss-wide execution.
8. GIS package manifests are complete and declared GeoTIFF outputs are present
   for the same-scale artifacts. COG readiness is blocked for the committed
   standard roots by the current strip-organized raster layout, missing
   overviews, and `cloud_optimized: false` metadata, not by missing package
   manifests. The first-class `--export-cog` path now writes an ignored
   `gate_v1_cog_export` package that audits as COG-ready, proving the
   package-level export path without changing the committed roots. The
   conditional gridpoint curve product is now auditable from the hazard
   manifest and documentation: per-cell threshold semantics, denominator
   semantics, and non-annual/non-physical flags are explicit. The current
   converted package audits as `cog_package_ready_with_scope_delta` when the
   ignored `gate_v1_cog_export` root is supplied. That is useful demonstration
   evidence, but it is still scope-limited relative to the standard same-scale
   package roots.
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
12. Balfrin demonstration evidence is better organized, but not all TB-101
    through TB-120 work represents completed execution. TB-101, TB-103, TB-105,
    TB-107, TB-110, TB-112, and TB-113 strengthened contracts, runbooks,
    report generators, claim checks, failure taxonomy, and scaling helpers.
    TB-106 and TB-108 are fixture-backed demonstrations, not live Balfrin
    interruption or output-tier measurements. TB-109 records GIS/COG parity
    semantics but still exposes a converted-package scope delta. TB-111 can
    compare Balfrin results to same-scale uncertainty only after measured
    Balfrin results exist. TB-102 did not execute the Balfrin pilot: it
    produced a blocked execution report because the Balfrin readiness helper
    originally rejected
    `validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml`
    with `pilot manifest validation failed: schema_version must be public_real_site_conditional_pilot_run_v1`.
    TB-115 freezes the canonical Balfrin demonstration contract and teaches
    the readiness helper to accept that contract schema without weakening the
    non-operational boundary. TB-120 keeps restartability recovery honest by
    classifying fixture-backed evidence as fixture-backed rather than live
    measured output-tier evidence until a fresh live interruption/resume proof
    exists.
13. Second-site realism remains deliberately deferred. TB-114 added
    `docs/chant_sura_fluelapass_real_context_acquisition_decision.md` and
    recorded a defer recommendation for real Chant Sura / Fluelapass public
    context. The decision pack lists the required products, cache/output roots,
    readiness impact, and reproduction commands, but no public context was
    downloaded and no second-site ensemble or hazard build was run.
14. Backlog and worker-context hygiene have improved materially. The active
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

Current high-value work after TB-114:

- keep the frozen Balfrin demonstration contract and readiness gate aligned so
  the minimal demo remains reproducible and bounded without claiming closure;
- execute the Balfrin single-release-zone pilot from the corrected contract and
  generated submission package, then collect the required metrics bundle;
- run the Balfrin post-run interpretation gate on measured evidence and update
  this snapshot with the measured state;
- keep the pilot non-operational even if the post-run gate accepts a
  conditional diagnostic artifact;
- convert fixture-backed Balfrin restartability and output-tier reports into
  measured reports only after a real run root exists;
- resolve or explicitly preserve the COG converted-package scope delta before
  using the GIS package as demonstration evidence;
- stage real public context for Chant Sura / Fluelapass before any second-site
  hazard execution, or keep the documented defer decision active;
- keep physical credibility work tied to independent observed
  runout/deposition evidence rather than adding more empty validators.
