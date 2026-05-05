# Hazard Layer Outputs

This directory is reserved for generated probabilistic hazard-layer products.
Generated files under `hazard/results/` are local artifacts and are not committed,
except for `.gitkeep`.

The first workflow is implemented in `scripts/build_hazard_layers.py`. It
consumes existing trajectory, deposition, and optional impact-event CSV outputs
and writes diagnostic research layers such as reach probability, deposition
density, maximum kinetic energy, maximum jump height, and significant impact
density. It also writes JSON metadata and a `run_manifest_v1` sidecar so output
files, row counts, warnings, and grid provenance can be audited separately from
the human-readable report.

These are hazard layers only. They do not include exposure, vulnerability, or
risk modelling, and they are not operational Swiss hazard maps.
