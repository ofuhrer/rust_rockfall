# Management AOI Scenario Pressure TB-610

Date: 2026-05-26

Status: measured local adjacent-candidate scenario-table and storage pressure.

Inputs:

- candidate review manifest:
  `validation/private/source_zone_review/candidate_source_zone_review_manifest.json`
- scenario-pressure report:
  `/tmp/tb610_management_aoi_scenario_pressure.json`
- storage-tier report:
  `/tmp/tb610_scenario_storage_pressure.json`

Scratch outputs:

- scenario pressure root: `/tmp/tb610_management_aoi_scenario_pressure`
- scenario table root: `/tmp/tb610_management_aoi_scenario_table`

No generated scratch outputs are committed.

## Active Candidate Result

The management-AOI scenario-pressure helper reported
`scenario_pressure_status: ready`.

| Measure | Value |
| --- | ---: |
| Accepted adjacent candidate count | `1` |
| Candidate area square meters | `105,344` |
| Candidate cell count | `1` |
| Scenario rows | `3` |
| Scenario table CSV bytes | `2,282` |
| Scenario table manifest bytes | `4,626` |
| Scenario table file count | `5` |
| Scenario table total bytes | `14,996` |
| Scenario table runtime seconds | `0.01698` |

Scenario-family cardinality:

- `reviewed_block_family_large`: `1` row
- `reviewed_block_family_medium`: `1` row
- `reviewed_block_family_small`: `1` row

Release-zone cardinality:

- `tschamut_adjacent_prau_mulins_candidate_v1`: `3` rows

The candidate bundle manifest is `17,786` bytes and the candidate bundle total
is `17,352,606` bytes.

## Batching And Storage Pressure

The storage-output-tier helper reported `measurement_status: ready` for the
same real AOI path and measured the active table as `3` rows, `5` files, and
`15,162` total bytes including its own manifest accounting.

Measured expanded candidate-set pressure:

| Candidate repeat count | Candidate records | Scenario rows | Manifest bytes | Total bytes |
| ---: | ---: | ---: | ---: | ---: |
| `1` | `10` | `100` | `71,919` | `193,657` |
| `3` | `30` | `300` | `211,277` | `595,867` |
| `8` | `80` | `800` | `549,564` | `1,569,339` |

The recommended next package batching cap is the `3-repeat / 30-candidate /
300-row` batch. The compact batch regression guard passed with this cap.

Measured replay tiers:

| Tier | Files | Bytes | Replay suitability |
| --- | ---: | ---: | --- |
| `minimal` | `5` | `15,162` | `insufficient_missing_trajectory_outputs` |
| `rebuildable_reduced` | `17` | `3,953,602` | `sufficient` |
| `gis` | `56` | `79,160,991` | `sufficient_for_review_not_minimal_replay` |
| `research_full` | `2,716` | `764,598,283` | `sufficient_but_not_smallest` |

For the next Balfrin diagnostic package, the measured recommendation is
`rebuildable_reduced`: it is the smallest tier that preserves builder-facing
replay inputs, while GIS and research-full outputs should stay optional unless
review or trajectory inspection requires them.

## Next Bottleneck

The next measured storage bottleneck is `gis_and_research_full_output_growth`.
The active scenario table itself is small; the scaling pressure comes from
manifest growth in expanded candidate batches and from optional GIS/research
output families.

## TB-649 Refresh

Date: 2026-05-27

The adjacent-candidate scenario inputs were regenerated into scratch roots:

- scenario pressure report: `/tmp/tb649_management_aoi_scenario_pressure.json`
- storage-tier report: `/tmp/tb649_scenario_storage_pressure.json`
- scenario pressure root: `/tmp/tb649_management_aoi_scenario_pressure`
- scenario table root: `/tmp/tb649_management_aoi_scenario_table`

The current accepted candidate remains
`tschamut_adjacent_prau_mulins_candidate_v1`. The regenerated prepared-pilot
handoff is `ready` with `3` scenario rows, `1` accepted candidate, `5`
scenario-table files, `2,282` scenario-table CSV bytes, `4,626` manifest bytes,
and `14,996` total scenario-table bytes. The next AOI action is still to
inspect or consume the generated scenario table through the prepared-pilot /
AOI front-door path.

The storage-tier refresh remains `ready`: the active real-AOI table is `3`
rows and the compact batch cap remains `3` repeats / `30` candidate records /
`300` scenario rows with `211,277` manifest bytes and `595,867` total bytes.
The replay recommendation remains `rebuildable_reduced`; the first storage
bottleneck remains GIS and research-full output growth rather than the active
scenario table.

## Boundary

This is local scenario-table and storage-pressure evidence only. It does not
submit a Balfrin job, authorize Swiss-wide execution, demonstrate distributed
execution, or create operational hazard, annual-frequency, physical-probability,
risk, exposure, or vulnerability claims.
