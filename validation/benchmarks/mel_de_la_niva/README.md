# Mel de la Niva Public Benchmark

Role: external high-energy/generalization benchmark using public 2015 event
data from Zenodo DOI `10.5281/zenodo.7257979`.

Preparation scaffold:

```bash
python3 scripts/prepare_mel_de_la_niva_benchmark.py
```

The scaffold records expected public archives and local ignored raw-data paths.
It does not download the roughly gigabyte-scale dataset or create runnable cases
until a CRS-consistent processed package is deliberately prepared.
