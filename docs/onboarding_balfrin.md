# Balfrin Onboarding Notes

Status: local development and reproducibility setup notes for CSCS Balfrin-style
user environments. These notes do not change simulator physics, validation
semantics, benchmark filters, or calibration policy.

The repository can be used on Balfrin from a user-local toolchain. The setup
below keeps Rust, Cargo, Python packages, generated validation outputs, and
public benchmark downloads outside tracked source files unless a fixture is
explicitly intended for git.

## Environment Baseline

Start from the repository checkout:

```bash
ssh balfrin.cscs.ch
cd /users/olifu/work/rust_rockfall
git status -sb
```

If the branch has local commits or generated ignored outputs, inspect them
before pulling or staging. Generated outputs under `target/`,
`verification/results/`, `validation/results/`, `hazard/results/`,
`data/raw/`, and public benchmark result directories should normally remain
ignored and unstaged.

## Rust Toolchain

If Cargo is not available, install Rust with the official user-local `rustup`
installer:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup-init.sh
sh /tmp/rustup-init.sh -y --profile minimal
. "$HOME/.cargo/env"
rustup component add rustfmt clippy
```

To avoid sourcing Cargo manually in every shell, append the Cargo environment
loader to the end of `~/.bashrc` if it is not already present:

```bash
printf '\n. "$HOME/.cargo/env"\n' >> "$HOME/.bashrc"
```

Check before appending if the file may already contain that line:

```bash
tail -n 20 "$HOME/.bashrc"
```

Expected tools for normal development:

```bash
cargo --version
rustc --version
cargo fmt --version
cargo clippy --version
```

## Python and PyYAML

Some repository scripts require Python syntax newer than Python 3.6. On Balfrin,
plain `python3` may be too old even when a newer interpreter such as
`/usr/bin/python3.11` is available.

Prefer setting the repository hook interpreter explicitly:

```bash
export RUST_ROCKFALL_PYTHON=/usr/bin/python3.11
```

Install PyYAML for the interpreter used by the repository when possible:

```bash
python3 -m pip install --user PyYAML
```

If the default Python is old but already has a compatible site-package cache,
the repository git hooks try a local fallback for PyYAML. For manual commands,
the equivalent explicit form is:

```bash
PYTHONPATH=/usr/lib64/python3.6/site-packages /usr/bin/python3.11 scripts/check_repo_consistency.py
```

Use this only as an environment workaround. It should not become a repository
runtime dependency or a validation assumption.

## Local Hooks

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
scripts/git-hooks/pre-commit
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
