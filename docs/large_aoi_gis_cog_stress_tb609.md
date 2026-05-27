# Large AOI GIS/COG Stress TB-609

Date: 2026-05-26; refreshed for TB-631 on 2026-05-27

Status: measured local larger-output package and COG conversion stress test.

Artifact root:
`hazard/results/tschamut_public_pilot/target_gate_v1`

Scratch roots:

- TB-609 standard package: `/tmp/tb609_large_aoi_gis_cog/package`
- TB-609 converted package: `/tmp/tb609_large_aoi_gis_cog/converted`
- TB-631 standard package: `/tmp/tb631_large_aoi_gis_cog/package`
- TB-631 converted package: `/tmp/tb631_large_aoi_gis_cog/converted`

Report artifacts:

- `/tmp/tb609_large_aoi_gis_cog/report.json`
- `/tmp/tb609_large_aoi_gis_cog/report.md`
- `/tmp/tb631_large_aoi_gis_cog/report.json`
- `/tmp/tb631_large_aoi_gis_cog/report.md`

## Result

The TB-631 refresh confirmed `hazard/results/tschamut_public_pilot/target_gate_v1`
is the largest currently available package-capable hazard output root and
reported `stress_test_status: ready`.

| Measure | Value |
| --- | ---: |
| Package generation seconds | `10.16826254199259` |
| Package file count | `39` |
| Package byte count | `401,265` |
| Raster count | `22` |
| Vector count | `2` |
| Manifest file count | `3` |
| Manifest size bytes | `333,291` |
| QA review HTML size bytes | `52,408` |
| QA review manifest size bytes | `38,620` |
| COG conversion seconds | `19.775688750029076` |
| Converted package file count | `39` |
| Converted package byte count | `403,419` |
| Converted raster count | `22` |
| Converted manifest size bytes | `333,888` |

Readiness and parity:

- standard package readiness: `gis_package_ready`
- converted package readiness: `cog_package_ready`
- converted package status: `cog_package_ready`
- layer parity: `parity_match`
- missing layer count: `0`
- extra layer count: `0`
- first GIS packaging bottleneck: `no_blocker`

Recorded source manifest runtime carried by the package:

- package runtime seconds: `41.61543712497223`
- core output write seconds: `7.48151166702155`
- output files: `53`
- output bytes: `22,061,720`

## Swiss-Scale Tie-In

This closes the current local output/COG packaging pressure question for the
largest checked-in real output root. The result is small relative to national
input byte estimates, but it proves the current package and conversion path can
produce a COG-ready review bundle with layer parity for this bounded artifact.

## Boundary

This is local packaging and COG conversion evidence only. It does not download
or stage national public geodata, run a larger simulation, authorize Swiss-wide
execution, or create operational hazard, annual-probability, risk, exposure, or
vulnerability claims.
