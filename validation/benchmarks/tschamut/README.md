# Tschamut 2014 Public Benchmark

Role: deposition/runout validation and grouped failure-mode analysis.

Primary preparation script:

```bash
python3 scripts/prepare_tschamut_public_benchmark.py --force
```

The generated package is written under ignored `validation/results/` paths.
The public EnviDat observations and public swissALTI3D tile are downloaded into
ignored raw-data paths. No model parameters are tuned by the preparation script.
