# Mel de la Niva Public Benchmark

Role: external high-energy/generalization benchmark using public 2015 event
data from Zenodo DOI `10.5281/zenodo.7257979`.

Preparation scaffold:

```bash
python3 scripts/prepare_mel_de_la_niva_benchmark.py
```

The scaffold records expected public archives and local ignored raw-data paths.
It does not download the roughly gigabyte-scale dataset by default.

First runnable no-tuning package:

```bash
python3 scripts/prepare_mel_de_la_niva_benchmark.py \
  --download-runnable-archives \
  --make-runnable \
  --output-root validation/results/public_benchmarks/mel_de_la_niva_runnable

cargo run -- validate \
  --case validation/results/public_benchmarks/mel_de_la_niva_runnable/cases/mel_de_la_niva_baseline.yaml
cargo run -- validate \
  --case validation/results/public_benchmarks/mel_de_la_niva_runnable/cases/mel_de_la_niva_rotational.yaml
```

This generates an ignored path-endpoint/deposition smoke benchmark using the
public LAS trajectories, 2015 deposited-block GIS points, and SfM DSM crop in
EPSG:21781/LV03. It is runnable and provenance-rich, but not calibrated
high-energy field validation: the public LAS files do not carry observation
timestamps, so the first package uses path endpoints and a documented
non-calibrated initial-speed policy. `observed_runout_m` is horizontal
release-to-matched-deposited-block endpoint displacement. The generated
deposition CSV and manifest record nearest-neighbor match distances and use no
hard match threshold in this first smoke package, so matches are QA evidence,
not strong field-validation evidence. The active block masses use a documented
2670 kg/m3 density assumption, not measured Mel de la Niva block density.
