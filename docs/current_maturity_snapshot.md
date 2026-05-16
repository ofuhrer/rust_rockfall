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
single-release-zone pilot track: contract, case plan, generate-only submission
package, metrics contract, post-run interpretation gate, and envelope helpers
are in place as dry-run automation, while the remaining gap is the measured
Balfrin execution itself and its post-run evidence.

Medium-term objectives are to make the conditional pilot scientifically
interpretable, reproducible on Balfrin/CSCS-style infrastructure, and scalable
toward larger release-zone ensembles and eventually many Swiss AOIs. True
physical or annual
intensity-frequency products remain deferred until source occurrence rates,
block-population frequencies, uncertainty propagation, and validation or
calibration evidence exist.

The selected Tschamut target-scale evidence remains `inconclusive`. The
same-scale artifact chain is reproducible and measured, and the repository now
has multi-seed uncertainty, spatial uncertainty interpretation, closure-gap
deltas, hotspot persistence summaries, closure criteria, GIS/package,
command-plan, native rebuildable reduced-output, first-class COG export, and
bounded runtime/output evidence. Larger selected-domain runs remain blocked
until the dominant uncertainty and physical-credibility gaps below are reduced
with measured evidence. Second-site pilots remain non-executed, but Chant Sura
/ Flüelapass now has a concrete candidate manifest, a deterministic
acquisition plan, a tiny synthetic core-input staging helper, and an explicit
`deferred_public_context_inputs` boundary for the missing public context
products.

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
   manifests, target-side `summary_only` output profile, portable command
   plan, measured convergence diagnostics, closure criteria, spatial
   uncertainty summary, and bounded runtime/output summaries now form an
   executable evidence chain. The earlier
   `Balfrin target-gate reproduction` remains useful single-job execution
   evidence.
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
   uncertainty is localized rather than diffuse, and hotspot persistence is
   counted across the six pairwise artifact comparisons. `max_kinetic_energy`
   remains a closure-limiting layer with high-uncertainty cells dominated by
   shared-support magnitude variation, while `max_jump_height` remains mixed
   between shared-support magnitude and support/nodata sensitivity. The closure
   matrix still treats both dominant layers as closure-limiting.
3. Output volume is measured and now has a canonical native rebuildable reduced
   execution mode.
   Target validation output remains the dominant measured pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially but
   remains non-rebuildable. The native `rebuildable_reduced_output` mode now
   writes the builder-facing trajectory, deposition, impact-event, diagnostics,
   trajectory-metadata, and stop-state artifacts directly and is exposed in the
   same-scale command plan. The legacy derivation helper remains available only
   as a compatibility and proof fallback. The remaining workflow gap is making
   downstream synthesis, clean-checkout tests, and CI consistently distinguish
   the old non-rebuildable `summary_only` profile from the valid native reduced
   mode.
4. Forest and obstacle context is no longer an absent-cache problem; it is a
   limiting interpretation problem. Public context is staged and measured at
   corridor level, and hazard-context overlap has been measured for a narrow
   broader envelope. The overlap remains unresolved and does not imply
   obstacle absence or obstacle physics.
5. Tschamut source-zone and block-scenario case regeneration is now
   deterministic from committed records and processed public inputs. The same
   pattern has only been audited, not implemented, for a non-Tschamut site with
   its own extent, terrain crop, source-zone metadata, scenario table, and
   context products.
6. Swiss-wide portability has a concrete Chant Sura / Flüelapass candidate, a
   multisite source/scenario contract audit, a deterministic acquisition plan,
   and a tiny synthetic core-input staging path. The candidate now has the
   ignored terrain, source-zone, scenario, processed-input, validation-root, and
   hazard-root inputs needed to separate core readiness from
   `deferred_public_context_inputs`. No second-site ensemble or hazard build is
   authorized, and the synthetic inputs must not be represented as real
   swisstopo evidence. The remaining portability gap is a real-context readiness
   gate plus dry-run AOI, release-zone, and release-plan automation that can
   execute without pretending public context has been acquired.
7. Scaling direction is measured for the current same-scale set. The
   single-job Balfrin path remains sufficient for the next same-scale step,
   distributed execution stays deferred, and the dominant bottleneck is
   validation output size rather than hazard-reducer parallelism. The
   read-only Swiss-wide envelope helper now projects runtime, storage,
   file-count, and job-count bands from those measured coefficients. It labels
   multi-AOI or larger release-zone requests as extrapolated no-go planning
   cases rather than authorizing scale-up.
8. GIS package manifests are complete and declared GeoTIFF outputs are present
   for the same-scale artifacts. COG readiness is blocked for the committed
   standard roots by the current strip-organized raster layout, missing
   overviews, and `cloud_optimized: false` metadata, not by missing package
   manifests. The first-class `--export-cog` path now writes an ignored
   `gate_v1_cog_export` package that audits as COG-ready, proving the
   package-level export path without changing the committed roots. The
   remaining GIS workflow gap is export-scope parity: the proof path is ready,
   but workers still need an explicit full-layer-scope COG command or a
   machine-readable scope-delta classification when thresholds are intentionally
   omitted.
9. Physical/annual frequency semantics, risk, exposure, vulnerability, and
   operational claims remain out of scope until conditional diagnostic
   convergence, source-frequency semantics, and validation/calibration
   evidence mature. The validation/calibration gap assessment reports
   `physical_credibility_status=not_established`, `calibration_status=missing`,
   and `validation_status=partial`.
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
    dry-run planning, release-plan dry-run planning, the Balfrin pilot
    contract, submission package, metrics contract, and post-run gate now
    distinguish completed dry-run automation from the remaining execution gap.
    The next measurable execution phase is to run the Balfrin
    single-release-zone pilot and collect its measured post-run evidence; true
    physical intensity-frequency curves remain deferred until the
    physical-probability layer exists.
11. Observed runout/deposition validation intake is now specified but not
    populated. The contract records the required independent benchmark
    manifest, geometry, provenance, and objective-function placeholders. The
    remaining boundary work is to keep benchmark-intake readiness separate from
    calibration readiness; the intake requirements are now executable as a
    dry-run readiness pack that writes template manifest, geometry inventory,
    provenance checklist, and validation summary files without claiming real
    evidence.

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

Underrepresented high-value work after TB-080:

- hardening the bounded next-ensemble feasibility helper so it reports a
  conservative planning status on reduced-output fixtures instead of assuming
  full probabilistic case metadata;
- separating observed benchmark intake readiness from calibration readiness,
  then emitting a dry-run readiness pack for future independent
  runout/deposition evidence;
- proving full-scope COG export parity, or explicitly labelling bounded proof
  packages when their layer scope differs from the standard roots;
- tracing closure-limiting uncertainty hotspots to source/scenario/support
  evidence and extracting persistent conditional-hazard confidence regions;
- combining same-scale uncertainty, runtime, and output-size evidence into a
  bounded ensemble-stability frontier before any additional probe is run;
- executing the Balfrin single-release-zone pilot and consolidating its
  measured post-run evidence into the compact maturity snapshot;
- generating blocked second-site case skeletons that expose missing real public
  context without allowing a synthetic fixture to masquerade as executable
  evidence.
