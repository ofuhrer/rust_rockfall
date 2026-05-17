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
single-release-zone pilot track. That track now has a frozen minimal
demonstration contract, deterministic case and command planning, a working
single-node SLURM submission path, a measured Balfrin run root, a canonical
evidence bundle, a replay smoke helper, a live interruption/resume proof, a
post-run scientific interpretation layer, GIS/COG scope classification,
runtime/scaling frontier helpers, AOI/release/scenario dry-run automation, and
a second-site acquisition trigger matrix. The measured Balfrin run is:

- run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3`;
- SLURM job: `4326021`;
- node: `nid001226`;
- exit status: completed successfully with exit code `0`.

This is the first real Balfrin single-release-zone demonstration evidence in
the repository. It is still a bounded, non-operational conditional diagnostic
demonstration. It does not establish physical credibility, annual frequency,
risk, exposure, vulnerability, regulatory usability, or Swiss-wide scale-up.
The largest near-term gap has moved from "can the Balfrin demo execute?" and
"can an AOI dry run be composed?" to "which measured follow-up most reduces
the remaining scientific, physical-credibility, portability, and scaling
uncertainty?"

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
contract reporting, deterministic acquisition planning, a public-geodata cache
verification contract, fixture-backed AOI terrain preprocessing, deterministic
release-zone candidate sensitivity reporting, generic candidate-source-zone
scenario generation, a site-level AOI-to-prepared-pilot dry-run composition,
an optional ignored-root case-skeleton bundle, and explicit blocked/deferred
boundaries for missing public-context products.

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
   single-release-zone track now has measured execution, replayability, and live
   restartability evidence rather than only dry-run automation.
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
   files, and `729600` conditional-curve rows. The measured Balfrin evidence
   bundle now separates measured sections from fixture-backed sections, so
   output-tier, metrics, and restartability evidence are no longer conflated.
   Live interruption/resume evidence has now been recorded for the Balfrin
   demonstration path, while smaller fixture-backed tests remain useful for
   clean-checkout regression coverage.
4. Forest and obstacle context is no longer an absent-cache problem; it is a
   limiting interpretation problem. Public context is staged and measured at
   corridor level, and hazard-context overlap has been measured for a narrow
   broader envelope. The overlap remains unresolved and does not imply
   obstacle absence or obstacle physics.
5. Tschamut source-zone and block-scenario case regeneration is deterministic
   from committed records and processed public inputs. The portable semantics
   are now split from Tschamut-specific heuristics, and dry-run helpers define
   deterministic release-zone candidate generation and pragmatic
   block-scenario generation from public-input contracts. The terrain candidate
   helper now emits deterministic GIS-readable mask and polygon bundles with
   stable candidate IDs, frozen-footprint comparison metadata, and a bounded
   sensitivity report that compares small threshold and preprocessing
   perturbations. That report separates stable from heuristic-sensitive
   candidate regions, but it does not validate any release-zone output. The
   scenario-table helper can reproduce the committed Tschamut summary table and
   now also accepts generic candidate source-zone metadata plus a policy
   template, emitting provenance-aware manifests with stable ids and explicit
   conditional-only weighting semantics. These helpers do not generate
   production release zones, tune thresholds, fit block populations, or claim
   field evidence. The remaining automation gap is moving from fixture-backed
   dry-run contracts to a measured, public-context-backed second-site run only
   after real swisstopo context is staged.
6. Swiss-wide portability has a concrete Chant Sura / Fluelapass candidate, a
   multisite source/scenario contract audit, a reusable public-geodata workflow
   contract, deterministic acquisition planning, a public-geodata cache
   verifier, fixture-backed AOI terrain preprocessing, a tiny synthetic
   core-input staging path, a real-context readiness gate, a product readiness
   pack, a release-zone heuristic dry run, a release-plan dry run, an
   AOI-to-prepared-pilot dry-run orchestrator, and an optional ignored-root
   case-skeleton/command bundle that remains blocked from execution. The
   candidate now separates verified cache records, staged core fixtures,
   missing AOI/tile inputs, and deferred public-context products. No second-site
   ensemble or hazard build is authorized, and the synthetic inputs must not be
   represented as real swisstopo evidence.
7. Scaling direction is now anchored by both same-scale Tschamut evidence and a
   measured Balfrin single-release-zone run. The single-job Balfrin path is the
   current execution boundary; distributed execution stays deferred, and prior
   same-scale evidence still says validation output size is the dominant
   pressure rather than hazard-reducer parallelism. The measured Balfrin run
   produced a real run root and feeds the evidence bundle, scientific delta,
   ensemble-frontier, and Swiss-wide envelope helpers. The Balfrin metrics
   report now separates mandatory, ancillary, measured, unavailable, and
   blocked fields, so memory peak and split-output provenance are explicit
   rather than implied: the live run-root collector can recover split-output
   write kinds when the output summary is still present, while the canonical
   bundle marks those fields unavailable when the preserved summary does not
   retain the run-root scaling tree. The Swiss-wide envelope helper records the
   measured Balfrin demo run root
   `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3`,
   and now surfaces explicit `no_go`, `defer`, and `allowed_next_probe`
   labels for planning cases. The bounded next-ensemble probe now evaluates
   the complete optional-metadata contract and resolves to
   `deferred_pending_authorization` when the reduced-output fixture carries the
   required fields; missing optional metadata still fails closed. This does
   not authorize Swiss-wide execution.
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
   package roots. The canonical Balfrin evidence bundle now exposes a
   machine-readable `gis_cog_scope_report` with `full_scope`, `bounded_scope`,
   or `blocked_missing_inputs` semantics so demonstration GIS scope is explicit
   rather than implied. Spatial uncertainty confidence products now include
   deterministic diagnostic outputs for persistent hazard, unstable regions,
   support/nodata sensitivity, and shared-support magnitude sensitivity; these
   remain review products, not operational hazard maps.
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
    not the current user workflow. The missing pieces are public-data download
    and cache population beyond deterministic planning; real staged
    public-context products; production terrain/context preprocessing;
    field-supported release-zone identification; block-population/frequency
    semantics; automatic ensemble-size/convergence control; a measured
    second-site execution; and, most importantly, physical frequency semantics
    from source occurrence rates, block-population frequencies, uncertainty
    propagation, and validation/calibration evidence. Native rebuildable
    reduced output, first-class COG export, the conditional gridpoint curve
    contract, clean-checkout test hardening, AOI acquisition planning, cache
    verification contracts, AOI terrain preprocessing, release-zone stability
    reporting, generic scenario generation, AOI-to-prepared-pilot dry-run
    composition, blocked case-skeleton handoff bundles, the Balfrin pilot
    contract, case plan, measured single-release-zone run, metrics contract,
    evidence bundle, scientific interpretation layer, and Swiss-wide execution
    envelope now distinguish completed dry-run automation from measured
    execution evidence. True physical intensity-frequency curves remain
    deferred until the physical-probability layer exists.
11. Observed runout/deposition validation intake is specified but not
    populated. The contract records the required independent benchmark
    manifest, geometry, provenance, and objective-function placeholders. The
    intake requirements are executable as a dry-run readiness pack that writes
    an acquisition checklist, required dataset inventory, geometry/provenance
    templates, objective-function placeholders, a blocked no-evidence report,
    and validation summary files without claiming real evidence. Benchmark-
    intake readiness is now separated from calibration readiness, but actual
    benchmark data and objective-function evaluation remain absent.
12. Balfrin demonstration evidence has crossed from scaffolding into measured
    execution. TB-115 froze the canonical demonstration contract. TB-116 and
    TB-117 separated local scheduler failure from the SSH-accessible Balfrin
    scheduler path. TB-118 produced the measured Balfrin single-release-zone
    run after correcting an orchestration mistake in which an earlier worker
    cancelled a healthy cold-compile job too early. TB-119 built the canonical
    evidence bundle and section provenance model. TB-120 kept restartability
    honest by preserving live interruption/recovery as fixture-backed until a
    deliberate resume experiment was run. TB-121 added the canonical scientific
    delta interpretation, which currently leaves the inconclusive diagnostic
    interpretation unchanged. TB-122 made GIS/COG scope machine-readable.
    TB-123 through TB-125 advanced deterministic release-zone, scenario, and
    AOI-to-demonstration dry-run automation. TB-126 added the second-site
    public-context trigger matrix. TB-127 and TB-128 updated practical ensemble
    and Swiss-wide planning envelopes from measured Balfrin evidence. TB-129
    mapped the measured demo to physical-credibility gaps and kept physical
    credibility at `not_established`. TB-130 then added the live Balfrin
    interruption/resume proof; TB-131 tightened Balfrin metrics-contract
    coverage; TB-132 through TB-134 advanced AOI tile discovery, deterministic
    release-zone candidate products, and deterministic block-scenario table
    generation; TB-135 recorded the bounded next-ensemble probe as blocked;
    TB-136 added spatial confidence products; TB-137 and TB-138 produced
    second-site and benchmark acquisition readiness packs; TB-139 added the
    Balfrin replay smoke helper; TB-140 composed the site-level
    AOI-to-command-plan dry run; TB-141 hardened replay smoke provenance;
    TB-142 made metrics-contract completeness explicit; TB-143 and TB-144
    made the bounded next-ensemble feasibility path fail closed on missing
    optional probabilistic metadata; TB-145 added bounded-probe interpretation;
    TB-146 produced a compact management demonstration package; TB-147 hardened
    AOI tile discovery; TB-148 added public-geodata cache/provenance
    verification; TB-149 added fixture-backed AOI terrain preprocessing from
    staged tiles; TB-150 measured release-zone heuristic stability; TB-151
    generalized candidate-source-zone scenario generation; and TB-152 emitted
    an ignored AOI case-skeleton/command handoff bundle that remains blocked
    from execution.
13. Second-site realism remains deliberately deferred. TB-114 added
    `docs/chant_sura_fluelapass_real_context_acquisition_decision.md` and
    recorded a defer recommendation for real Chant Sura / Fluelapass public
    context. The decision pack lists the required products, cache/output roots,
    readiness impact, reproduction commands, and product-by-product stage/defer
    matrix, but no public context was downloaded and no second-site ensemble or
    hazard build was run.
14. Backlog and worker-context hygiene have improved materially. The active
    backlog is currently empty after TB-152 and `print_agent_task_context.py` reports
    `backlog_refill_needed=true`. The work log is chronological, archived
    history is separated, and repo consistency checks now reject unreachable or
    self-referential work-log commit hashes. File-backed worker logs reduced
    orchestration token pressure and exposed a concrete pitfall: workers must
    not cancel healthy Slurm jobs solely because cold compilation is quiet. The
    next backlog refill should start from this measured Balfrin maturity state
    rather than resurrecting stale same-scale-only or pre-execution Balfrin
    tasks.

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

Current high-value work after TB-152:

- refill the backlog from the measured Balfrin demo, explicit replay/metrics
  status, and completed AOI dry-run composition state, not from the older
  pre-execution plan;
- decide whether the next live Balfrin work should be a small bounded ensemble
  probe, additional measured metrics capture, or public-context-backed
  portability work;
- decide whether the next portability step is real Chant Sura public-context
  acquisition, a measured second-site dry run after staging, or further
  fixture-backed AOI automation;
- use the canonical evidence bundle and scientific delta report as the
  management-facing demonstration evidence, while keeping the closure status
  inconclusive and non-operational;
- close or explicitly defer remaining ancillary measured-metrics gaps while
  keeping fixture-backed regression evidence distinct from live measurements;
- treat the AOI case-skeleton bundle as a reproducible operator handoff, not as
  authorization to execute a second-site ensemble;
- keep the Chant Sura / Fluelapass real-context decision tied to the trigger
  matrix and measured evidence, not synthetic fixtures;
- keep physical credibility work tied to independent observed
  runout/deposition, release-zone, block-population, calibration, and holdout
  evidence rather than treating successful execution as validation.
