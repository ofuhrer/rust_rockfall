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
- `uv` for a project-local Python runtime and virtual environment.
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

Use `uv` so repository Python tools do not depend on system Python packages or
the system default Python version.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install -r requirements-tools.txt
```

The `.venv/` directory is ignored by git. The repository hooks prefer
`.venv/bin/python` when it exists, so activating the environment is not required
for hook execution.

For interactive Python commands, either activate the environment:

```bash
. .venv/bin/activate
python scripts/check_repo_consistency.py
```

or call it directly:

```bash
.venv/bin/python scripts/check_repo_consistency.py
```

When `.venv/` has not been created yet, use `uv run` rather than relying on a
possibly old system `python3`:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py
```

Set `RUST_ROCKFALL_PYTHON` only when intentionally overriding the local
environment:

```bash
export RUST_ROCKFALL_PYTHON="$PWD/.venv/bin/python"
```

## Local Git Hooks

Install the local hook templates after cloning or when `.git/hooks` is missing:

```bash
scripts/install_git_hooks.sh
```

The hooks select Python `>= 3.9`, preferring `RUST_ROCKFALL_PYTHON` and then
`.venv/bin/python`, and run the Rust/Python checks through the same path used by
local commits and pushes.

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
.venv/bin/python scripts/check_repo_consistency.py
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
.venv/bin/python scripts/prepare_tschamut_public_benchmark.py --force
.venv/bin/python scripts/prepare_chant_sura_public_benchmark.py
.venv/bin/python scripts/prepare_chant_sura_eota221_benchmark.py
.venv/bin/python scripts/prepare_mel_de_la_niva_benchmark.py
```

The Mel de la Niva runnable smoke package is opt-in and writes under an ignored
results path:

```bash
.venv/bin/python scripts/prepare_mel_de_la_niva_benchmark.py \
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
