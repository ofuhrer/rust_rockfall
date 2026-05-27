# TB-682 Balfrin Hazard-Output Pressure Ladder

Date: 2026-05-27

TB-682 measured larger single-node hazard-output pressure on Balfrin
`postproc` under the current reduced-output profile: summary-only conditional
curves, no grid CSV fanout, and isolated `$SCRATCH` run roots.

## Runs

| release zones | job id | state | profile wall s | time elapsed | peak RSS MB | hazard files | hazard bytes | manifest bytes | output-byte budget |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| 96 | `4379367` | `COMPLETED` | `0.396282` | `0:02.93` | `44.5156` | 29 | 1,261,335 | 134,632 | pass |
| 192 | `4379388` | `COMPLETED` | `0.441348` | `0:02.33` | `48.4766` | 29 | 1,353,399 | 198,522 | pass |
| 384 | `4379371` | `COMPLETED` | `0.587962` | `0:04.04` | `49.4141` | 29 | 1,536,400 | 325,518 | fail |

Run roots:

- 96 zones:
  `/scratch/mch/olifu/rust_rockfall/probes/tb682_96_zone_hazard_output_pressure_20260527_153323`
- 192 zones:
  `/scratch/mch/olifu/rust_rockfall/probes/tb682_192_zone_hazard_output_pressure_20260527_153459`
- 384 zones:
  `/scratch/mch/olifu/rust_rockfall/probes/tb682_384_zone_hazard_output_pressure_20260527_153407`

## Result

- Largest measured size still under the current reduced-output byte budget:
  `192` release zones.
- First measured output-byte blocker: `384` release zones
  (`1,536,400` > `1,500,000` hazard output bytes).
- Manifest-byte budget is already blocked at all three larger sizes:
  `134,632`, `198,522`, and `325,518` bytes versus the `60,000` byte budget.
- Runtime and memory remain comfortably below the six-hour single-node boundary
  for this synthetic hazard-output shape.

## Next Safe Size

Use `192` release zones as the current measured output-byte-safe size under the
existing reduced-output profile. Do not attempt more than `192` zones as a
replay-ready support point until manifest bytes and hazard output bytes are
reduced. A larger diagnostic run can still be submitted if it is explicitly
classified as output-byte-blocker evidence.

## Boundary

This is single-node `postproc` hazard-output pressure evidence. It is not
physical-probability evidence, annual-frequency evidence, operational evidence,
risk/exposure/vulnerability evidence, distributed execution evidence,
Swiss-wide execution, or non-`postproc` evidence.
