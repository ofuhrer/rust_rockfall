# Current Maturity Snapshot

This snapshot preserves the detailed project objective, capability-gap analysis,
and backlog-quality assessment that previously lived in `docs/task_backlog.md`.
Keep `docs/task_backlog.md` compact and executable; update this snapshot during
orchestrator/backlog-refill work when the maturity framing changes materially.

This is historical context, not active process control. Prefer the current
backlog and orchestration strategy for what to do next. Older wording about
blocked states, gates, and claim boundaries should be read as evidence history,
not as a reason to add more process before running useful measurements.

---
## Project Objective

The repository is trying to become an automated, reproducible rockfall
hazard-map workflow for Switzerland's Alpine terrain using public geodata,
primarily swisstopo. TB-222 through TB-359 have now completed the latest
post-review, scale-synthesis, and real-AOI automation queue: Balfrin next-action and metrics-completion preflights were
sharpened; read-only target-area metric and spatial-artifact recovery paths
were added; multi-zone handoff budgets and authorization gates were refreshed;
blocked metrics-completion and multi-zone Balfrin attempts were integrated
without promoting them as measured evidence; the TB-307 target-area
metrics-completion rerun measured peak memory and split validation/hazard
outputs; TB-312 measured an exact four-zone post-processing/reducer package on
Balfrin `postproc`; TB-313 rejected the accumulator micro-optimization; TB-314
refreshed the local 1/2/4/8/12-zone ladder; TB-332 failed closed before
`sbatch` on the four-zone hazard branch; TB-333 integrated that blocked
hazard outcome into the scale dashboard and next-run ranking; TB-315 through
TB-318 built and polished the user-AOI guided review path; and TB-319
refreshed the authoritative status surfaces after those evidence changes. TB-338
then added a measured-evidence Swiss-scale feasibility projection, and TB-339
packaged the measured, projection-only, failed-closed, fixture-backed, blocked,
and deferred Balfrin scale-demonstration evidence into one management-facing
surface. TB-340 through TB-430 extended the next workflow layer: real-AOI
public-geodata acquisition planning, cache-integrity gates, real-AOI
terrain/context preprocessing, release-zone candidate sweep/stability/review
tooling, candidate scenario pressure checks, an AOI prepared-pilot compiler,
large-AOI GIS manifest repair, regenerated multi-zone Balfrin submit contracts,
fail-closed smallest/four-zone submit records, measured four-zone
postproc/reducer pressure, hazard-throughput no-op boundaries, adjacent
candidate review, source-zone search refinement, RAMMS/OpenNHM-inspired design
review, and a refreshed Swiss-scale projection. TB-431 through
TB-445 then compacted the regional split submission package, failed closed the
first live regional split attempt before `sbatch`, integrated the remote-hygiene
cleanup and retry ranking, hardened AOI/QGIS review coverage, and refreshed the
management-facing feasibility summary. The current
architectural answer is: a 10-zone single-AOI workflow is
feasible under the current single-node/postproc boundary; a 100-zone workflow is
conditionally feasible as a deferred planning case; the bounded regional split
probe is now measured, but broader regional workflows still remain out of reach
as scale capability; and Swiss-wide execution remains out of reach under
current single-node/postproc constraints. These updates clarified the regional
split comparison path, AOI/QGIS review readiness, candidate and scenario
separation, and the next ranked executable milestone without changing the
measured scale boundary.
TB-462 through TB-470 added a local-only scientific audit layer for work that
does not require Balfrin: `scripts/recommend_local_scientific_backlog.py --report progress`,
`scripts/audit_conditional_denominator_provenance.py`,
`scripts/audit_trajectory_deposition_traceability.py`,
`scripts/rank_local_hazard_layer_fragility.py`,
`scripts/summarize_extreme_layer_sensitivity_smoke.py`,
`scripts/inventory_second_site_local_blockers.py`,
`scripts/audit_chant_sura_holdout_split.py`,
`scripts/check_calibration_separation_preflight.py`, and
`scripts/recommend_local_scientific_backlog.py`. These surfaces make the
conditional denominator, trajectory/deposition traceability, extreme-layer
fragility, Chant Sura second-site blockers, holdout split independence, and
calibration/validation separation executable locally. They remain diagnostic
and routing evidence only: they do not establish physical probability, annual
frequency, operational use, risk/exposure/vulnerability, scale-up, distributed
execution, or Balfrin authorization. After the 24-zone diagnostic scale push,
`scripts/assess_validation_calibration_evidence_gaps.py` now makes that split
explicit and ranks the next concrete scientific work as independent holdout
deposition/runout evidence, source-frequency evidence, block-population
evidence, calibration-design evidence, and second-site public-geodata staging.
It also reports source-frequency intake status and an explicit
calibration/holdout separation check, so stronger scientific conclusions fail
closed when holdout labels are missing or calibration and validation evidence
share a dataset, event, or sample identifier. Site-only reuse is allowed only
for explicitly labelled holdout-validation records.

The Chant Sura real-input gate distinguishes real, fixture-backed, partial, missing, and
metadata-mismatched inputs; the prepared-pilot dry run fails closed unless real
core inputs are ready; and physical-evidence intake separates observed
benchmark candidates, accepted/rejected intake packages, release-zone
provenance, block-population evidence, calibration inputs, holdout evidence,
and source-frequency records. The scale-control layer now fails closed on full
grid CSV, full conditional-curve output, missing reduced-output flags,
excessive sidecars, missing rebuildability artifacts, or submit-package
contract mismatches; validation-output summaries separate replay-critical
families from diagnostic/debug fanout; preserved Balfrin run roots can be
audited read-only against output/reducer budgets; and the scale readiness
matrix gives workers one compact evidence dashboard. It now also carries an
operational-readiness check across scientific validation, reproducibility,
GIS/package QA, provenance, monitoring, versioning, and support status; the
current classification remains diagnostic-only, not operational-candidate
ready. After the 24-zone
diagnostic push, the current hazard-planning boundary remains 10 zones while
the diagnostic reducer-pressure boundary is measured and repeated at 24 zones
on single-node `postproc`. The next scale action is a larger bounded diagnostic
only if queue policy remains favorable; regional and Swiss-wide execution
remain deferred phase changes. The main local reducer-pressure helpers
can now regenerate deterministic scratch roots under a caller-supplied `/tmp`
path and report manifest paths plus byte/file counts, but Balfrin access and
remote checkout alignment still must be verified before any trusted submission
package is used. Older local hazard-layer stress-test notes
are preserved through `docs/archive/README.md`; current scale interpretation
should use this snapshot, the scale readiness matrix, and the output-profile
contract instead of dated archived reviews. The Balfrin/Tschamut conditional demonstration track now has
a frozen minimal
demonstration contract, deterministic case and command planning, a working
single-node SLURM submission path, a measured Balfrin run root, a canonical
evidence bundle, a replay smoke helper, a live interruption/resume proof, a
post-run scientific interpretation layer, GIS/COG scope classification,
runtime/scaling frontier helpers, AOI/release/scenario dry-run automation, and
a second-site acquisition trigger matrix. The follow-up target-area probe path
has also moved from packaged handoff to one explicitly authorized measured
Balfrin run. The measured Balfrin single-release-zone run is:

- run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3`;
- SLURM job: `4326021`;
- node: `nid001226`;
- exit status: completed successfully with exit code `0`.

The authorized target-area probe is:

- run root:
  `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`;
- SLURM job: `4329024`;
- exit status: completed successfully with exit code `0`;
- measured evidence: 58 output files, `192350243` output bytes, and `729600`
  conditional-curve rows.

The current target-area review state is now also wrapped into a deterministic
target-area evidence bundle, metrics report, GIS/COG scope audit, scaling
envelope, management package, evidence-gated closure package, metrics
completion rerun package, metrics-completion authorization preflight, remote
Balfrin access preflight, post-run collector rehearsal, and physical-evidence
acquisition pack. Those reports now preserve a metrics-completion source label
that distinguishes `recovered_existing_run_root`, `new_metrics_completion_rerun`,
and `blocked_missing_metrics` without implying a stronger claim. TB-264's
metrics-completion postproc attempt failed closed before submission because the
remote Balfrin checkout was dirty; TB-265 integrated that result as
`incomplete`, not measured. The evidence bundle and decision surfaces now also
carry `blocked_pre_submit` as a distinct metrics state, so dirty or otherwise
blocked pre-submit attempts are not collapsed into recovered or missing metric
labels. The Balfrin access preflight now includes a read-only remote checkout
hygiene gate that fails closed on dirty pre-submit state, records remote HEAD,
and reports safe operator cleanup commands without deleting remote files. The
multi-zone follow-up path now has a
reviewed-package/authorization submission gate, smallest-probe authorization
preflight, scalable command-plan output-profile enforcement, reducer
manifest/file-family budget regression coverage, handoff-derived output budget
projection, a fixture-backed throughput profile, and a local scaling ladder.
TB-267's smallest
multi-zone probe also failed closed before submission because the preflight
remained `blocked_reducer_budget` at `manifest_size_bytes` and the
authorization record was missing; TB-268 integrated that branch as
`blocked_incomplete`, not measured. The later TB-286/TB-287 refresh fixed the
two-zone reducer/output-budget branch but exposed `blocked_dirty_remote_checkout`
as the remaining pre-submit blocker. After TB-303, the user granted standing
clearance for GPT-5.5 workers to submit and actively monitor Balfrin `postproc`
jobs, including multiple concurrent jobs and filling the partition. A GPT-5.5
worker then created a reviewed/authorized audit record for the two-zone package,
but submission still stopped before `sbatch` because the Balfrin access
preflight remained `blocked_dirty_remote_checkout`. TB-304 preserved the
untracked checkout clutter in
`/users/olifu/work/tb304_remote_checkout_cleanup_20260519T185745Z.tgz`,
removed only those stale generated checkout files, and reran the access
preflight to `ready_for_read_only_collection`. No measured multi-zone result has
been promoted. TB-305 then measured the exact bounded synthetic postproc
microbenchmark on Balfrin `postproc` as job `4339870`; TB-306 classifies it in
the scale dashboard as `measured_on_balfrin_postproc_microbenchmark`, an
efficiency-only label that does not count as measured hazard execution or
multi-zone scale capability. The runner-side measurement was `0.6338623960000405`
wall seconds, `0.048968283` CPU seconds, `32624` kbytes peak RSS, `154` files
touched, and `89802` bytes touched. TB-307 then completed that target-area
metrics-completion rerun
on `postproc` as job `4339889` with exit `0:0`, elapsed `00:00:29`,
`memory_peak_mb=5.4375`, `130` validation files / `34565498` validation bytes,
and `99` hazard files / `273194249` hazard bytes preserved at
`/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v1`.
TB-308 integrates those measured values across the evidence bundle, closure
package, decision gate, and scale-readiness dashboard, so another target-area
metrics-completion rerun is no longer the ranked current action. TB-309 then
failed closed before `sbatch` because the reviewed two-zone submit command used
the target-area wrapper manifest instead of the executable
`public_real_site_conditional_pilot_run_v1` contract. TB-320 repaired that
manifest mismatch, but TB-321 failed closed before `sbatch` on newer
pre-submit gates: the regenerated handoff classified the live package against
the four-zone review-only profile (`next_larger_four_zone_review_only_probe`,
`release_zone_count=4`) instead of `smallest_live_two_zone_probe`, and its
reviewed commands targeted `/scratch/rust_rockfall/...`, which is not writable
on Balfrin for this account. TB-312 later measured the exact compact
four-zone post-processing/reducer package on Balfrin `postproc` as efficiency
evidence only, and TB-314 confirmed the local scratch ladder still first
blocks at 8 zones on `accumulation_seconds`. TB-362 then reran the explicit
two-zone hazard path after the remote checkout was cleaned and fast-forwarded,
but failed closed before `sbatch`: authorization, reducer-budget,
submit-contract, and output-budget acceptance were ready/accepted, while the
remote output-profile gate returned `blocked_output_profile` with a four-zone
review-package reason. TB-407 then completed the smallest bounded multi-zone
probe on Balfrin `postproc` and preserved measured run-root evidence, so the
smallest multi-zone branch is now measured rather than merely blocked. The
older TB-362 two-zone branch remains failed-closed/blocked rather than measured
multi-zone hazard evidence. TB-428 then attempted the next regional split
live-probe gate, but correctly failed closed before scheduler submission: the
regional split/merge contract was ready with 12 splits, while the reviewed
package exceeded the `next_larger_four_zone_review_only_probe` manifest-size
budget (`14550` bytes measured versus `14000` allowed). TB-431 compacted that
package path enough for the reviewed package gate to pass in fixture-backed
preflight. TB-432 then reran the live gate and failed closed before `sbatch`
because the Balfrin remote checkout hygiene/access preflight reported three
stale generated `command_plan.json` files under
`validation/private/tb407_repaired_handoff_remote/...`. TB-447 later executed
one bounded regional split `postproc` job and TB-448 collected the preserved
run-root metrics for that same run root, so the regional split branch is now
measured and TB-432 is historical failed-closed/no-submit evidence. The next
blocker category is comparison work rather than evidence collection: thread the
measured regional split pressure into the scenario-cardinality and output-tier
projection surfaces before any further live recommendation.
TB-315 through TB-318 then moved
the AOI path from scattered dry-run commands to a guided, fixture-backed
bounds-to-review-map workflow with map packaging and a polished static QA
surface. The
physical-evidence path now has an
explicit release/scenario physical-meaning firewall, an observed
runout/deposition acquisition blocker matrix, a template-only operator
acquisition package, fixture-backed intake acceptance smoke tests, a
release-zone provenance intake bridge, and a triage split where release-zone
provenance and block-population evidence remain acquisition candidates while
source-frequency records are deferred until a later phase change. Those reports
keep measured, unavailable, blocked, dry-run, unauthorized, historical,
template, fixture-backed, candidate, accepted, rejected, and deferred
provenance separate. The target-area metrics-completion source label now
distinguishes recovered existing run-root metrics, the measured TB-307 rerun,
blocked pre-submit attempts, failed-closed attempts, and missing-metrics
branches. The TB-243 read-only spatial-artifact inventory recovered
the run-root-referenced hazard manifest plus standard and pilot GIS package
manifests from the preserved Balfrin root, but the target-area cellwise
spatial layers and derived spatial uncertainty products remain explicit
`unavailable_from_preserved_root` deferrals. Those spatial deferrals are not
execution-metrics blockers and are not physical validation evidence.
TB-244 then refreshed the closure synthesis so the demonstration package can
distinguish `metrics_complete`, `metrics_unrecoverable_deferred`, and
`blocked_no_new_measured_evidence` while keeping the TB-243 spatial-artifact
classification separate from the execution-metrics result and preserving the
post-metrics next-action ranking.

These are the first real Balfrin demonstration evidence records in the
repository. They are still bounded, non-operational conditional diagnostic
demonstrations. They do not establish physical credibility, annual frequency,
risk, exposure, vulnerability, regulatory usability, or Swiss-wide scale-up.
TB-338/TB-445 now package the measured evidence, the projection-only Swiss-scale
feasibility classification, the failed-closed submit branches, and the
deferred next authorized step into one management-facing surface without
upgrading any claim. TB-461 moved the downstream decision surface toward a
reducer-pressure-first ranking, but the current review found that some
scale-readiness and next-live-run helper paths still depend on regenerated
scratch reducer artifacts and therefore are not clean-checkout robust. That
remains separate from claim promotion: the regional split branch is measured at
the bounded-probe level, but the next decisive evidence gap is larger measured
multi-zone Balfrin hazard execution after clean-checkout helper robustness,
remote checkout alignment, and measured regional-split comparison are current.
The largest near-term gaps have moved from "can the Balfrin demo execute?" and
"can an AOI dry run be composed?" to "can real arbitrary-AOI public geodata be
acquired and preprocessed reproducibly?", "can release-zone and scenario
generation remain deterministic and defensible on real terrain?", and "can a
small measured multi-zone Balfrin hazard run complete with acceptable reducer,
manifest, GIS, and output pressure?" Standing `postproc` clearance does not
relax access, readiness, authorization-record/audit, output-budget,
preservation, or post-run evidence gates, and it does not authorize
non-postproc partitions, distributed execution, scale-up claims, or
scientific/operational claim upgrades.

Post-TB-319, the AOI-to-map and scale-status front doors are stronger but
still bounded. The
workflow now has an AOI hazard-map packager that emits a compact review package
with raster inventory, checksums, release/scenario overlays, COG-ready or
`cog_blocked` classification, and explicit claim boundaries. It also has a
static AOI map QA review surface that exposes terrain, release-zone, scenario,
hazard-layer, context, COG, fixture-backed, conditional-only, observed-overlay,
first-blocker, next-command, and non-operational warnings. A fixture-backed
end-to-end regression now exercises explicit AOI bounds, staged input
verification, guided workflow status, prepared-pilot local execution, map
packaging, and QA review under `/tmp`. Optional observed
runout/deposition and field-supported release-zone provenance overlays can be
attached to AOI map packages, but only through accepted real-input-ready
evidence; fixture-only or ambiguous-role evidence is blocked and cannot appear
as accepted physical validation. This is a usability and evidence-separation
improvement, not a physical-credibility or operational upgrade.

Post-TB-430, the user-facing AOI/QGIS path is easier to find and less
scattered: `docs/aoi_user_manual.md` is the compact command-level entry point,
and the QGIS Processing bridge is a manifest-only prototype validated against
the existing AOI front-door commands and tracked QGIS style assets. This
improves review usability and future GUI integration readiness without adding a
plugin, GUI, new execution framework, or operational map claim.

Post-TB-387, the active execution queue stayed centered on the adjacent-
candidate review path: TB-404 regenerated scenario tables from the accepted
adjacent candidate, TB-405 threaded that table through the prepared-pilot
compiler, and TB-411 extended the candidate-expansion ladder so the current
first executable management-AOI work is to keep that adjacent-candidate bundle
flowing rather than re-open the old source-zone-overlap repair. The same queue
also now includes complexity-reduction work: compact multi-zone
manifest-pressure measurement, prepared-pilot state consolidation, extraction
of a small hazard-layer packaging primitive from the giant builder, clean
checkout dependency cleanup, and user-facing AOI front-door/documentation
consolidation. The current adjacent-candidate bottleneck is scenario
cardinality and reducer pressure, not the stale source-zone-overlap repair.
This backlog intentionally favors executable capability, measured pressure
reduction, and script-surface simplification over additional blocked/deferred
reports.

Post-TB-393, the management-AOI Balfrin execution state still failed closed
before `sbatch`, but the current candidate/scenario path is now the adjacent-
candidate review bundle and generated scenario table rather than the old
zero-candidate 4x4 crop. Balfrin SSH, remote checkout hygiene, run-root
visibility, and scheduler query were all reachable, and the remaining unblock
action is to keep the adjacent-candidate scenario-table path threaded through
prepared-pilot compilation; the next ranked bottlenecks are scenario
cardinality, reducer pressure, hazard throughput, GIS packaging, and Balfrin
access. This is not measured multi-zone Balfrin hazard execution.

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
verification contract, one real-staged swissALTI3D AOI terrain crop for the
Chant Sura / Fluelapass candidate, deterministic release-zone candidate
sensitivity reporting, a measured real-terrain
candidate sweep with runtime/output measurements and multi-zone readiness
reporting, a measured real-terrain candidate stability report with zero
candidate cells, empty stable/unstable/heuristic-sensitive masks across the
bounded slope, resolution, smoothing, and AOI-boundary perturbations, and a
clear not-ready recommendation for scenario generation, deterministic candidate
stability ranking with bounded 2/4/8-zone probe selection, generic
candidate-source-zone scenario generation, a site-level
AOI-to-prepared-pilot dry-run composition, an optional ignored-root
case-skeleton bundle with scenario-generation and GIS scope summaries, and
explicit blocked/deferred boundaries for missing public-context products.

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
   AOI and Balfrin command plans now share an output-profile validator, so
   scalable plans explicitly block full grid CSV, full conditional curves,
   missing reduced-output controls, excessive sidecars, and missing
   rebuildability artifacts outside tiny fixture-smoke contexts. The bounded
   validation summary and multi-zone reducer-pressure reports now carry
   validation-output inventories that separate replay-critical output families
   from diagnostic/debug fanout. This improves budget evidence and replay
   auditability; it does not convert a blocked scale tier into measured
   execution.
   TB-161 freezes the next target-area demonstration contract at
   `validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`,
   including the Tschamut selected domain, the target-gate reproduction
   record, the conditional-only scenario-family basis, the scalable
   conditional output mode, and the single-job Balfrin boundary with a
   read-only command-plan hook. The tracked target-area public
   geodata/source/scenario inputs for that contract are present and the public
   real-site manifest validates; this readiness is separate from the Chant
   Sura / Fluelapass second-site public-context track, which remains blocked or
   deferred until real second-site inputs are staged.
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
   sensitivity report that compares threshold, smoothing, terrain-resolution,
   and AOI-boundary perturbations. That report separates stable, unstable,
   and heuristic-sensitive candidate regions, adds a sensitivity matrix and
   persistence metrics, and the measured real-terrain sweep wrapper now adds
   component-area distributions, slope/topography thresholds, scratch-root
   output counts, runtime measurements, and an explicit multi-zone stress-test
   readiness signal. None of that validates any release-zone output. The
   scenario-table helper can reproduce the committed Tschamut summary table and
   now also accepts generic candidate source-zone metadata plus a policy
   template, emitting provenance-aware manifests with stable ids and explicit
   conditional-only weighting semantics. These helpers do not generate
   production release zones, tune thresholds, fit block populations, or claim
   field evidence. The remaining automation gap is moving from fixture-backed
   dry-run contracts to a measured, public-context-backed second-site run only
   after real swisstopo context is staged. The current management-AOI branch is
   now anchored on the adjacent-candidate review bundle and its generated
   scenario table, so the current first unblock action is to keep that bundle
   threaded through prepared-pilot compilation instead of revisiting the stale
   zero-candidate 4x4 crop repair. This is an AOI/candidate-state and
   prepared-pilot bookkeeping blocker, not a Balfrin or COG packaging blocker.
6. Swiss-wide portability has a concrete Chant Sura / Fluelapass candidate, a
   multisite source/scenario contract audit, a reusable public-geodata workflow
   contract, deterministic acquisition planning, a public-geodata cache
   verifier, a real-staged Chant Sura swissALTI3D terrain crop, a tiny
   synthetic core-input staging path for the still-fixture-backed
   source/scenario records, a real-context readiness gate, a product readiness
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
   ensemble-frontier, and Swiss-wide envelope helpers. TB-407 then added the
   measured smallest multi-zone probe, which remains bounded diagnostic
   evidence rather than scale-up authorization. The Balfrin metrics
   report now separates mandatory, ancillary, measured, unavailable, and
   blocked fields, so memory peak and split-output provenance are explicit
   rather than implied: the live run-root collector can recover split-output
   write kinds when the output summary is still present, while the canonical
   bundle marks those fields unavailable when the preserved summary does not
   retain the run-root scaling tree. The Swiss-wide envelope helper records the
   measured Balfrin demo run root
   `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3`,
   and now surfaces explicit `no_go`, `defer`, and `allowed_next_probe`
   labels for planning cases. It also emits a canonical 10-zone / 100-zone /
   regional / Swiss-wide planning table so manifest, reducer, memory, and
   scheduler bottlenecks are explicit before larger runs are attempted. The
   bounded next-ensemble probe evaluates the
   complete optional-metadata contract and still fails closed when optional
   metadata is absent. One bounded target-area probe has now been explicitly
   authorized and measured on Balfrin; future generated submission packages are
   operator handoffs, not execution approval. Labels such as `allowed_next_probe`
   or `ready_for_authorization_review` are planning states only; they do not
   authorize `sbatch` without a later user instruction for the exact run and
   GPT-5.5 Balfrin-worker routing through the live-run protocol. A
   metrics-remediation contract
   records missing mandatory, unavailable ancillary, and next-run-required
   fields. TB-170 now wraps the frozen target-area handoff report, the
   preserved probe-metrics report, and the measured canonical bundle into one
   deterministic target-area evidence bundle so the current demonstration
   state is auditable without collapsing unavailable or blocked evidence into
   the measured sections. TB-312 added the measured four-zone Balfrin postproc
   result as separate evidence, TB-313 rejected the accumulator micro-
   optimization, TB-314 refreshed the local 1/2/4/8/12-zone ladder so the
   scratch-local frontier still first blocks at 8 zones on
   `accumulation_seconds`, and TB-407 added the measured smallest multi-zone
   probe so the canonical surfaces now distinguish measured, failed-closed,
   fixture-backed, projection-only, and deferred branches more clearly. TB-302
   adds a read-only Balfrin run-root output-budget auditor for future preserved
   roots, and TB-303 adds the
   worker-facing scale dashboard that labels tiers as `measured_on_balfrin`,
   `fixture_backed`, `scratch_local`, `projection_only`, or
   `blocked_pre_submit`. None of this authorizes Swiss-wide execution or a new
   live Balfrin submission.
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
    composition, blocked case-skeleton handoff bundles with scenario-generation
    and GIS scope summaries, and the release-candidate physical-meaning
    firewall that labels `workflow_generated`, `field_supported`,
    `mixed_provenance`, or `blocked_missing_provenance` candidate rows while
    keeping sampling weights conditional-only, the Balfrin pilot
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
    benchmark data and objective-function evaluation remain absent. TB-178
    extends that into `docs/target_area_physical_evidence_acquisition_pack.md`,
    which keeps observed benchmark intake, release-zone provenance,
    block-population evidence, calibration separation, and source-frequency
    evidence in distinct acquisition buckets instead of one implied validation
    claim.
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
    generalized candidate-source-zone scenario generation; TB-152 emitted
    an ignored AOI case-skeleton/command handoff bundle that remains blocked
    from execution; TB-153 added the optional probabilistic and hazard
    probability metadata needed by the reduced bounded-probe fixture while
    retaining fail-closed missing-metadata behavior; TB-154 threaded the
    `deferred_pending_authorization` recommendation through Balfrin and
    Swiss-wide frontier helpers; TB-155 added the Balfrin submission-package
    handoff and a follow-up fix kept `--generate-only` fast; TB-156 added the
    Balfrin metrics remediation checklist; TB-157 connected AOI case skeletons
    to generic scenario generation; TB-158 added product-by-product Chant Sura
    real-context staging guidance; TB-159 mapped AOI automation outputs to
    physical-credibility boundaries; TB-160 added the AOI GIS scope review
    summary; TB-161 through TB-167 froze and prepared the target-area
    demonstration path; TB-168 executed the authorized target-area Balfrin
    probe; TB-169 through TB-179 turned that run into metrics, evidence,
    GIS/COG, diagnostic, restartability, scaling, management, second-site, and
    physical-evidence review artifacts, then left the backlog empty for the
    next gap-analysis pass.
13. Second-site realism remains deliberately deferred. TB-114 added
    `docs/chant_sura_fluelapass_real_context_acquisition_decision.md` and
    recorded a defer recommendation for real Chant Sura / Fluelapass public
    context. The decision pack lists the required products, cache/output roots,
    readiness impact, reproduction commands, and product-by-product stage/defer
    matrix, but no public context was downloaded and no second-site ensemble or
    hazard build was run. The current repo-root cache verifier now reports the
    Chant Sura swissALTI3D terrain crop as `ready` / `real_staged`; the
    real-context gate remains `blocked_partial_real_inputs` because the AOI
    tile catalog, source-zone metadata, scenario table, and source-scenario
    policy are still fixture-backed, and public-context products remain
    deferred. TB-249 through TB-251 tightened this boundary: the
    real-context readiness gate now reports fixture-backed, partial-real,
    metadata-mismatch, missing-row, and missing-file cases separately; the
    no-download acquisition handoff gives a concrete next action such as
    `stage_local_existing_input`, `request_download_authorization`,
    `defer_second_site`, or `ready_no_handoff_needed`; and the Chant Sura
    prepared-pilot dry-run report emits `blocked_missing_real_core_inputs`
    rather than treating fixture scaffolding as real workflow evidence.
14. Backlog and worker-context hygiene have improved materially. TB-181 through
    TB-383 completed the post-TB-179 execution queues: deterministic
    release-candidate stress evidence, multi-zone reducer pressure,
    second-site dry-run realism, shared validator helpers, dependency
    guidance, calibration failure diagnostics, runtime-facing panic-path
    reduction, clean-checkout Python test stabilization, ignored-artifact
    dependency auditing, CI portability guardrails, Balfrin next-action
    decision support, scalable output-profile enforcement, reducer
    file-family regression coverage, hazard-accumulation hotspot isolation,
    workflow-shell coupling inventory, physical-meaning firewalling for
    release/scenario automation, observed runout/deposition acquisition
    blocker classification, Balfrin remote-access and worker-routing
    preflights, target-area metrics and smallest multi-zone authorization
    preflights, post-run collector rehearsal, handoff-derived output-budget
    projection, real-input Chant Sura gates, observed-intake acceptance smoke,
    release-zone provenance intake, block-population/source-frequency blocker
    mapping, workflow-shell helper extraction, command-plan manifest
    consolidation, read-only Balfrin recovery/authorization handoffs, stricter
    Chant Sura real-core dry-run gating, observed benchmark candidate triage,
    deterministic real-input intake acceptance/rejection, physical-evidence
    triage for release-zone provenance, block-population evidence, and
    source-frequency records, blocked live-run integration without claim
    promotion, a fixture-backed AOI-to-map review path with optional
    real-evidence overlays, measured target-area metrics completion, measured
    four-zone postproc/reducer evidence, rejected accumulator optimization
    evidence, refreshed local scaling-ladder status, integrated the blocked
    four-zone hazard branch into the dashboard and next-run surface, real-staged
    Chant Sura terrain preprocessing, honest zero-candidate propagation through
    scenario pressure, prepared-pilot, Balfrin handoff, and no-submit execution
    state helpers, and a GIS/COG stress check showing the largest committed real
    output is demonstration-readable. The active backlog should now focus on
    completing local candidate/scenario/output-default hardening, making the
    Balfrin decision helpers clean-checkout safe, regenerating reducer-pressure
    scratch evidence deterministically, aligning the Balfrin remote checkout,
    and only then resuming bounded `postproc` execution tasks.

## Backlog Quality Assessment

The current backlog should be judged by whether it creates new measurements,
analysis capabilities, reproducibility, or execution capacity. The strongest
tasks are those that turn the existing Tschamut/Balfrin artifacts into
actionable scientific evidence or remove a measured execution blocker.
Synthesis, closure semantics, and additional blocked-state vocabulary should
follow evidence changes, not substitute for them.

Over-procedural areas to avoid:

- repeated reclassification of the same `inconclusive` evidence without a new
  analysis or run;
- additional YAML records, validators, gates, or intake reports that do not
  enable execution, measurement, reproducibility, real-evidence acquisition, or
  consolidation of duplicated logic;
- roadmap/status maintenance that does not change what a worker can run or
  learn;
- management-style closure or evidence packaging that duplicates an existing
  canonical summary without replacing stale surfaces;
- chains of blocked/deferred reports where the next action is still another
  classification step rather than staging input, recovering evidence,
  measuring runtime/output pressure, or explicitly deferring the path;
- secondary GIS/QGIS bookkeeping when the main conditional hazard-map evidence
  remains unresolved.

Current high-value work after TB-319:

- keep the active queue focused on the measured and blocked evidence that
  already exists, using the capability filter to reject tasks that mainly add
  wrappers around known blocked states;
- defer larger hazard work until the four-zone hazard branch is measured; the
  TB-332 branch failed closed before `sbatch`, so it does not support an
  eight-zone probe, while the older TB-309 two-zone submit-contract repair
  remains a lower-ranked live blocker;
- use the standing Balfrin `postproc` clearance only when GPT-5.5 worker
  routing, active monitoring, access, remote-cleanliness, output-budget,
  authorization-record/audit, preservation, and post-run evidence gates pass;
  the clearance does not itself promote any failed-closed branch into measured
  evidence;
- keep using the Balfrin remote-access preflight, worker-routing metadata,
  smallest multi-zone preflight, run-root output-budget auditor, and post-run
  collector rehearsal before treating any future run as evidence;
- advance the user-defined AOI path from fixtures to real staged public
  geodata through the explicit dry-run/local-copy/download-gated acquisition
  driver, then rerun the guided bounds-to-review-map workflow without
  committing generated outputs;
- treat the rejected accumulator optimization as evidence against broad
  performance churn and require a new measured hypothesis before touching the
  hazard accumulator again;
- advance Chant Sura only from real staged inputs named by the frozen
  acquisition package and prepared-pilot gate, not from fixtures; use the
  acquisition/staging driver and TB-250 handoff recommendation before
  attempting a real-input dry run;
- use the observed runout/deposition operator package, candidate-acquisition
  report, and real-input intake acceptance/rejection logic as
  acquisition/schema machinery only, not physical validation;
- use the AOI map packager and static QA review surface as diagnostic review
  tools only; optional observed-evidence overlays must remain accepted real
  evidence attachments, not calibration or physical-probability evidence;
- keep release-zone provenance, block-population evidence, and source-frequency
  evidence separated from conditional scenario weights; release-zone
  provenance and block-population evidence are acquisition candidates, while
  source-frequency records remain deferred until a later phase explicitly
  authorizes frequency semantics;
- continue workflow-shell consolidation only where it removes concrete
  coupling without changing public CLI schemas or status vocabulary;
- use existing canonical evidence summaries for management-facing
  demonstration evidence, while keeping the closure status inconclusive and
  non-operational; add another summary only if it replaces stale summaries or is
  needed to support a bounded authorization/recovery decision;
- close or explicitly defer remaining ancillary measured-metrics gaps while
  keeping fixture-backed regression evidence distinct from live measurements;
- treat the AOI case-skeleton, scenario-generation handoff, and GIS scope
  summary as reproducible operator handoff artifacts, not as authorization to
  execute a second-site ensemble or as generated hazard/GIS evidence;
- use the scale readiness matrix before proposing larger Balfrin work, and
  keep `measured_on_balfrin`, `fixture_backed`, `scratch_local`,
  `projection_only`, and `blocked_pre_submit` tiers separate;
- use the run-root output-budget auditor only on preserved roots and only as
  read-only evidence; it does not authorize new runs or mutate remote data;
- keep the Chant Sura / Fluelapass real-context decision tied to the trigger
  matrix and measured evidence, not synthetic fixtures;
- keep physical credibility work tied to independent observed
  runout/deposition, release-zone, block-population, calibration, and holdout
  evidence rather than treating successful execution as validation.
