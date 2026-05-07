# Onboarding and Local Setup

Status: developer onboarding and reproducibility setup notes. These notes do
not change simulator physics, validation semantics, benchmark filters, or
calibration policy.

This document is the generic setup guide for working on the repository from a
fresh checkout. Keep platform- or site-specific details out of committed docs
unless they describe a reusable class of environment issue.

## Prerequisites

Required for normal development:

- Rust toolchain with `cargo`, `rustc`, `rustfmt`, and `clippy`.
- Python `>= 3.9`.
- PyYAML for repository consistency checks and benchmark/data scripts.
- Git.

Optional tools depend on the workflow:

- public dataset preparation may require network access and extra Python
  packages documented by the relevant dataset script or benchmark document;
- visualization workflows may require plotting dependencies;
- large benchmark runs need sufficient local storage and should write only to
  ignored result/cache paths.

## Fresh Checkout

Start by checking the repository state:

```bash
git status -sb
```

If the branch has local commits, untracked files, or generated ignored outputs,
inspect them before pulling, staging, or deleting anything. Generated outputs
under `target/`, `verification/results/`, `validation/results/`,
`hazard/results/`, `data/raw/`, and public benchmark result directories should
normally remain ignored and unstaged.

## Rust Toolchain

If Cargo is unavailable, install Rust with the official user-local `rustup`
installer for your operating system. On Unix-like systems, the standard install
path is:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup-init.sh
sh /tmp/rustup-init.sh -y --profile minimal
. "$HOME/.cargo/env"
rustup component add rustfmt clippy
```

For persistent shell setup, add Cargo's environment loader to the end of your
shell startup file if the installer did not already do so. For Bash:

```bash
printf '\n. "$HOME/.cargo/env"\n' >> "$HOME/.bashrc"
```

Check first if the line may already exist:

```bash
tail -n 20 "$HOME/.bashrc"
```

Verify the installed tools:

```bash
cargo --version
rustc --version
cargo fmt --version
cargo clippy --version
```

## Python and PyYAML

Repository scripts should be run with Python `>= 3.9`. If your default
`python3` is older, use a newer interpreter explicitly or set
`RUST_ROCKFALL_PYTHON` for the repository git hooks:

```bash
export RUST_ROCKFALL_PYTHON=/path/to/python3.11
```

Install PyYAML for the interpreter you use:

```bash
python3 -m pip install --user PyYAML
```

If you use a non-default interpreter, install PyYAML through that interpreter:

```bash
/path/to/python3.11 -m pip install --user PyYAML
```

Avoid relying on machine-local package paths in committed workflows. If an
environment needs a temporary `PYTHONPATH` workaround, keep it local and record
the stable requirement as "Python >= 3.9 with PyYAML".

## Local Git Hooks

Install the local hook templates after cloning or when `.git/hooks` is missing:

```bash
scripts/install_git_hooks.sh
```

The hooks select Python `>= 3.9`, preferring `RUST_ROCKFALL_PYTHON`, and run the
Rust/Python checks through the same path used by local commits and pushes.

Run the hook chain directly before handoff:

```bash
scripts/git-hooks/pre-commit
scripts/git-hooks/pre-push
```

## Basic Onboarding Checks

After Rust and Python are available, run:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
cargo run -- verify --all
cargo run -- validate --all
python3 scripts/check_repo_consistency.py
scripts/git-hooks/pre-commit
```

Before pushing, run:

```bash
scripts/git-hooks/pre-push
```

`cargo run -- verify --all` and `cargo run -- validate --all` write ignored
diagnostic outputs. Do not stage those generated files unless a tiny fixture is
being intentionally added and documented.

## Optional Public Benchmark Data

The larger public benchmark preparation commands download or create ignored
benchmark packages. They are useful for local diagnostic reproduction, but they
are not part of the default onboarding check and do not imply operational
hazard-map validity.

Use them only when the benchmark data are intentionally needed:

```bash
python3 scripts/prepare_tschamut_public_benchmark.py --force
python3 scripts/prepare_chant_sura_public_benchmark.py
python3 scripts/prepare_chant_sura_eota221_benchmark.py
python3 scripts/prepare_mel_de_la_niva_benchmark.py
```

The Mel de la Niva runnable smoke package is opt-in and writes under an ignored
results path:

```bash
python3 scripts/prepare_mel_de_la_niva_benchmark.py \
  --download-runnable-archives \
  --make-runnable \
  --output-root validation/results/public_benchmarks/mel_de_la_niva_runnable
```

Optional smoke validations for the generated Mel package:

```bash
cargo run -- validate \
  --case validation/results/public_benchmarks/mel_de_la_niva_runnable/cases/mel_de_la_niva_baseline.yaml

cargo run -- validate \
  --case validation/results/public_benchmarks/mel_de_la_niva_runnable/cases/mel_de_la_niva_rotational.yaml
```

Mel de la Niva remains an opt-in smoke/generalization scaffold, not calibrated
field validation. Public Tschamut remains diagnostic-only for model selection
while registration sensitivity is unresolved.

## Handoff Hygiene

Before committing or handing off:

```bash
git status -sb --ignored
git diff --check
```

Confirm that generated outputs remain ignored and unstaged. If local data or
benchmark archives were downloaded, keep them under the documented ignored
paths and record only small intentional fixtures or metadata in git.
