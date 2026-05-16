# Current Maturity Snapshot

This snapshot preserves the detailed project objective, capability-gap analysis,
and backlog-quality assessment that previously lived in `docs/task_backlog.md`.
Keep `docs/task_backlog.md` compact and executable; update this snapshot during
orchestrator/backlog-refill work when the maturity framing changes materially.

---
## Project Objective

The repository is trying to become an automated, reproducible rockfall
hazard-map workflow for Switzerland's Alpine terrain using public geodata,
primarily swisstopo. The first concrete milestone is a valley-scale Tschamut
pilot that produces conditional grid-cell intensity-exceedance hazard-map
products with documented uncertainty, provenance, performance, and
non-operational interpretation limits.

Medium-term objectives are to make the conditional pilot scientifically
interpretable, reproducible on Balfrin/CSCS-style infrastructure, and scalable
toward larger release-zone ensembles. True physical or annual
intensity-frequency products remain deferred until source occurrence rates,
block-population frequencies, uncertainty propagation, and validation or
calibration evidence exist.

The selected Tschamut target-scale evidence remains `inconclusive`. The
same-scale artifact chain is reproducible and measured, and the repository now
has multi-seed uncertainty, spatial uncertainty interpretation, closure
criteria, GIS/package, command-plan, COG proof-of-concept, and bounded
runtime/output evidence. Larger selected-domain runs remain blocked until the
dominant uncertainty and output-profile gaps below are reduced with measured
evidence. Second-site pilots remain non-executed, but Chant Sura / Flüelapass
now has a concrete candidate manifest, a concrete acquisition manifest, a tiny
synthetic core-input staging helper, and an explicit
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
   uncertainty is localized rather than diffuse, but `max_kinetic_energy` and
   `max_jump_height` remain support/nodata sensitive enough that the closure
   matrix treats both dominant layers as closure-limiting.
3. Output volume is measured and now has a native rebuildable reduced
   execution mode.
   Target validation output remains the dominant measured pressure at
   `2716` files / `764598283` bytes and `272.573375917` seconds in the
   same-scale set. Target-side `summary_only` output reduced substantially but
   remains non-rebuildable. The native `rebuildable_reduced_output` mode now
   writes the builder-facing trajectory, deposition, impact-event, diagnostics,
   trajectory-metadata, and stop-state artifacts directly and is exposed in the
   same-scale command plan. The remaining workflow gap is making downstream
   synthesis and tests consistently distinguish the old non-rebuildable
   `summary_only` profile from the valid native reduced mode.
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
   multisite source/scenario contract audit, and a tiny synthetic core-input
   staging path. The candidate now has the ignored terrain, source-zone,
   scenario, processed-input, validation-root, and hazard-root inputs needed to
   separate core readiness from `deferred_public_context_inputs`. No second-site
   ensemble or hazard build is authorized, and the synthetic inputs must not be
   represented as real swisstopo evidence.
7. Scaling direction is measured for the current same-scale set. The
   single-job Balfrin path remains sufficient for the next same-scale step,
   distributed execution stays deferred, and the dominant bottleneck is
   validation output size rather than hazard-reducer parallelism.
8. GIS package manifests are complete and declared GeoTIFF outputs are present
   for the same-scale artifacts. COG readiness is blocked for the committed
   standard roots by the current strip-organized raster layout, missing
   overviews, and `cloud_optimized: false` metadata, not by missing package
   manifests. The first-class `--export-cog` path now writes an ignored
   `gate_v1_cog_export` package that audits as COG-ready, proving the
   package-level export path without changing the committed roots. The
   remaining GIS workflow gaps are now reduced to report wording and any
   future export-scope changes, because the audit exposes both the standard
   root layer inventory and the converted-package layer inventory, including
   the intentionally omitted 0.5 m jump-height layers.
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
    control; native rebuildable reduced output; default COG-ready GIS export;
    a site-level orchestrator that chains those steps; and, most importantly,
    physical frequency semantics from source occurrence rates, block-population
    frequencies, uncertainty propagation, and validation/calibration evidence.
    The near-term achievable product remains an automated conditional
    diagnostic hazard-map workflow; true intensity-frequency curves remain
    deferred until the physical-probability layer exists.

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

Underrepresented high-value work:

- fixing post-TB-057 engineering drift that can mislead workers before the next
  scientific task, especially live-artifact-dependent command-plan tests, stale
  COG documentation, and ambiguous converted-package COG readiness summaries;
- decomposing the support/nodata component of the closure-limiting
  `max_kinetic_energy` and `max_jump_height` uncertainty instead of only
  reporting that it exists;
- translating spatial uncertainty masks into closure-gap deltas that identify
  what evidence would move the pilot toward deferred, no-go, or accepted
  diagnostic status;
- turning the rebuildable reduced-output proof into a normal generation/output
  mode before any larger validation-output run is attempted;
- moving Chant Sura / Flüelapass from synthetic core staging toward a concrete
  public-context acquisition decision without pretending that context products
  are already real validation evidence;
- keeping the package-level COG export path reproducible on regenerated
  packages while keeping manual QGIS acceptance deferred;
- mapping the missing physical-credibility evidence into concrete field or
  reference data requirements rather than broad calibration language.
