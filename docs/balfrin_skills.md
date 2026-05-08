# Balfrin Skills

Status: practical cluster-discovery notes for running application and workflow
work on Balfrin. This covers SLURM, hardware, filesystems, and executable
workflows. It is an operational guide, not an application design document.

Snapshot date: 2026-05-08.

Sources:

- local discovery via `ssh balfrin` as user `olifu`;
- exported Confluence page
  `/Users/fuhrer/Downloads/SLURM+partitions+on+Balfrin-+Rules+and+Guidelines.doc`.

Balfrin is the MeteoSwiss failover and R&D system. It is shared with
production-adjacent resources, including home and store filesystems. Do not run
compute-heavy work on login nodes, do not run jobs from the home directory, and
avoid large parallel I/O unless coordinated. `balfrin-ln001` is reserved for
operations.

There is no accounting requirement on Balfrin, so `--account` / `-A` can be
omitted.

## Connect and Inspect

Connect:

```bash
ssh balfrin
```

Useful first checks:

```bash
hostname
whoami
id
sinfo --version
sinfo -o "%P|%D|%t|%c|%m|%G|%l|%N"
scontrol show partition
squeue -u olifu -o "%.18i %.14P %.18j %.10u %.2t %.12M %.6D %R"
```

Observed on 2026-05-08:

- login landed on `balfrin-ln003`;
- SLURM version was `23.02.7`;
- cluster name was `balfrinm`;
- user was `olifu`;
- home was `/users/olifu`;
- scratch was `/scratch/mch/olifu`;
- default partition was `postproc`.

Use scratch or another appropriate work filesystem for build/run directories:

```bash
mkdir -p "$SCRATCH/app"
cd "$SCRATCH/app"
```

## Partition Summary

Balfrin has GPU partitions and CPU post-processing partitions. The number of
GPU nodes is adjusted depending on demand; the exported policy page says this
can range from 30 to 48 GPU nodes. Operational NWP partitions are intentionally
excluded from this guide; do not use them for application or development work.

GPU nodes observed by `sinfo` have:

- `GRES=gpu:4`;
- `CPUS=128`;
- about `456704 MB` memory per node.

CPU post-processing nodes observed by `sinfo` have:

- no GPU GRES;
- `CPUS=256`;
- about `456704 MB` memory per node.

## Operational NWP Queues

UNDER NO CIRCUMSTANCES should queues with only `s83opr` access be used for
application, research, development, test, or exploratory work. These are
MeteoSwiss operational NWP production queues. Do not submit jobs to them, do
not use them for quick tests, and do not include them in automated queue
selection logic.

Operational NWP queues are intentionally omitted from the partition tables
below. If `sinfo` or `scontrol show partition` shows additional partitions with
`AllowGroups=s83opr` only, treat them as out of bounds. More generally, avoid
all production-only partitions unless an authorized operational procedure
explicitly instructs otherwise.

## Hardware Snapshot

This section describes representative nodes sampled through SLURM allocations
on 2026-05-08. Treat it as a live snapshot, not a permanent hardware contract:
Balfrin's GPU-node count and partition membership are operationally adjusted.

Probe method:

- CPU node sample:
  `srun --partition=pp-short --time=00:03:00 --nodes=1 --ntasks=1 --cpus-per-task=1 ...`
- GPU node samples:
  `srun --partition=debug --time=00:03:00 --nodes=1 --ntasks=1 --cpus-per-task=1 --gres=gpu:1 ...`
- Commands used inside the allocation included `hostname`, `uname -a`,
  `/etc/os-release`, `lscpu`, `free -b`, `numactl --hardware`, selected
  `/proc/cpuinfo` fields, and `nvidia-smi` when available.

### CPU Nodes

Representative sampled node: `nid001236` from `pp-short`.

| Property | Observed value |
| --- | --- |
| Operating system | SUSE Linux Enterprise Server 15 SP5 (`sles`, `VERSION_ID=15.5`) |
| Kernel | `5.14.21-150500.55.97_13.0.78-cray_shasta_c` |
| Architecture | `x86_64` |
| CPU model | AMD EPYC 7713 64-Core Processor |
| Sockets | 2 |
| Cores per socket | 64 |
| Threads per core | 2 |
| Logical CPUs | 256 |
| NUMA domains | 8 |
| L1d / L1i cache | 4 MiB each across 128 instances |
| L2 cache | 64 MiB across 128 instances |
| L3 cache | 512 MiB across 16 instances |
| Visible memory from `free -b` | `540177072128` bytes, about 503 GiB |
| Swap | none |
| GPU availability | no GPU GRES in SLURM; `nvidia-smi` did not communicate with an NVIDIA driver on the sampled CPU node |

The CPU-node NUMA layout exposed 8 NUMA nodes. Each NUMA node had 16 physical
cores plus the corresponding SMT siblings, for example node 0 had CPUs
`0-15,128-143`. Reported NUMA memory per domain was about 63-65 GiB.

CPU nodes are the right target for CPU-only application, preprocessing, and
post-processing work. Prefer `pp-short` for short checks, `postproc` for
ordinary CPU work, `pp-serial` for serial/low-core work, and `pp-long` for
longer CPU work.

### GPU Nodes

Representative sampled nodes: `nid001009` for full CPU/OS data and `nid001005`
for focused GPU identity/topology data, both from `debug`.

| Property | Observed value |
| --- | --- |
| Operating system | SUSE Linux Enterprise Server 15 SP5 (`sles`, `VERSION_ID=15.5`) |
| Kernel | `5.14.21-150500.55.97_13.0.78-cray_shasta_c` |
| Architecture | `x86_64` |
| CPU model | AMD EPYC 7713 64-Core Processor |
| Sockets | 1 |
| Cores per socket | 64 |
| Threads per core | 2 |
| Logical CPUs | 128 |
| NUMA domains | 4 |
| L1d / L1i cache | 2 MiB each across 64 instances |
| L2 cache | 32 MiB across 64 instances |
| L3 cache | 256 MiB across 8 instances |
| Visible memory from `free -b` | `540257071104` bytes, about 503 GiB |
| Swap | none |
| SLURM GPU GRES | `gpu:4` |
| GPU model reported by `nvidia-smi` | `NVIDIA PG506-232` |
| GPUs per node | 4 |
| Memory per GPU | `98304 MiB` |
| NVIDIA driver | `550.54.15` |
| CUDA version reported by NVIDIA-SMI | `12.4` |
| Persistence mode | enabled |
| MIG mode | disabled |

Focused `nvidia-smi -L` output on `nid001005` listed four GPUs:

```text
GPU 0: NVIDIA PG506-232
GPU 1: NVIDIA PG506-232
GPU 2: NVIDIA PG506-232
GPU 3: NVIDIA PG506-232
```

The sampled GPU node reported PCI bus IDs:

```text
GPU 0: 00000000:03:00.0
GPU 1: 00000000:41:00.0
GPU 2: 00000000:82:00.0
GPU 3: 00000000:C1:00.0
```

`nvidia-smi topo -m` reported `NV4` connectivity between every GPU pair in the
sampled node. NUMA affinity was reported as NUMA domain 3 for GPU 0, domain 2
for GPU 1, domain 1 for GPU 2, and domain 0 for GPU 3. The topology output
also showed CPU affinity for GPU 3 as `0,64`; CPU affinity for GPUs 0-2 was not
printed by that command on the sampled node.

Request only the GPU count needed with `--gres=gpu:N`, especially on
shared-capable partitions. Even when `--gres=gpu:1` was requested for the probe,
`nvidia-smi` listed the node's four physical GPUs, so do not rely on
`nvidia-smi` visibility alone as proof of allocation size; use SLURM variables
and the scheduler request as the allocation contract.

## Filesystems and I/O

Filesystem snapshot from `balfrin-ln003` on 2026-05-08:

| Path | Environment variable | Type | Observed capacity | Intended use |
| --- | --- | --- | ---: | --- |
| `/users/olifu` | `$HOME` | Lustre mounted under `/users` | `80G` total, `77G` used, `3.6G` available by `df -hT` | Shell configuration, credentials, small source checkouts, small scripts, and lightweight logs. Do not run compute-heavy or I/O-heavy jobs here. |
| `/scratch/mch/olifu` | `$SCRATCH` | Lustre mounted under `/scratch/mch` | `800T` total, `718T` used, `83T` available by `df -hT` | Shared login/compute work area for builds, job working directories, generated outputs, caches, and large temporary files. |

Both filesystems are visible on login and compute nodes, but `$SCRATCH` is the
right location for scheduled work. Keep `$HOME` small and quiet: it is shared
infrastructure, was 96% full in the 2026-05-08 probe, and should not be used
for heavy builds, bulk output, or large intermediate files.

Use this pattern for Balfrin runs:

```bash
export APP_WORK="$SCRATCH/app"
mkdir -p "$APP_WORK"
cd "$APP_WORK"
```

For repository work, either clone into `$SCRATCH` or keep a small source tree
in `$HOME` and copy/sync the run tree to `$SCRATCH` before submitting jobs. For
Rust builds on Balfrin, prefer a target directory on `$SCRATCH` so incremental
build artifacts do not fill home:

```bash
export CARGO_TARGET_DIR="$SCRATCH/app/target"
```

For Python or tool caches, point cache directories at `$SCRATCH` when they may
grow:

```bash
export UV_CACHE_DIR="$SCRATCH/.cache/uv"
export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"
```

### Lustre Behavior

`lfs` is available at `/usr/bin/lfs`. The `$SCRATCH` mount observed by
`findmnt` was:

```text
/scratch/mch lustre 172.28.1.2@tcp,172.28.1.3@tcp:172.28.1.4@tcp,172.28.1.5@tcp:/capstor/scratch/mch
```

`lfs getstripe "$SCRATCH"` reported the default user-directory stripe as:

```text
stripe_count:  1
stripe_size:   1048576
stripe_offset: -1
```

That default is reasonable for many ordinary files, but Lustre generally
performs best when jobs write fewer large files rather than many small files.
This matters because debug logs, per-task artifacts, and fine-grained CSV or
JSON output can otherwise create many small files or high metadata pressure.

Practical guidance:

- Write job outputs under a per-run directory in `$SCRATCH`, for example
  `$SCRATCH/app/runs/<run_id>`.
- Prefer manifest-backed chunk files, Parquet/Arrow-style columnar files,
  tarballs, or other batched outputs over one tiny file per work item.
- Keep SLURM stdout/stderr concise; write detailed machine-readable outputs to
  chunked data files rather than printing large logs.
- Avoid many ranks or array tasks appending to the same file. Give each task a
  separate chunk path, then merge with a reducer job.
- Avoid repeated directory scans over very large output trees from many jobs at
  once.
- Stage final small reports, selected figures, and commit-worthy fixtures back
  to the repository after the run; leave bulky raw outputs on `$SCRATCH` or move
  them to the appropriate long-term storage outside git.
- Clean obsolete run directories when they are no longer needed.

For large single-file outputs, set striping before creating the file or
directory. Confirm local policy before choosing aggressive values, but a modest
stripe count is often appropriate for files that will grow to many GiB:

```bash
mkdir -p "$SCRATCH/app/runs/<run_id>"
lfs setstripe -c 4 -S 16M "$SCRATCH/app/runs/<run_id>/large_outputs"
```

Stripe settings apply to files created after the setting is applied. Inspect
the result with:

```bash
lfs getstripe "$SCRATCH/app/runs/<run_id>/large_outputs"
```

For small files, metadata, source code, scripts, manifests, and logs, keep the
default striping. Over-striping small files can waste resources and increase
load.

Useful filesystem inspection commands:

```bash
df -hT "$HOME" "$SCRATCH"
findmnt -T "$HOME" -o TARGET,SOURCE,FSTYPE,OPTIONS
findmnt -T "$SCRATCH" -o TARGET,SOURCE,FSTYPE,OPTIONS
lfs df -h "$SCRATCH"
lfs getstripe "$SCRATCH"
lfs quota -h -u "$USER" "$SCRATCH"
stat -f -c "%n type=%T block_size=%S total_blocks=%b free_blocks=%f avail_blocks=%a files=%c free_files=%d" "$HOME" "$SCRATCH"
```

### Node-Local Temporary Storage

A `pp-short` compute-node probe on `nid001236` showed:

```text
TMPDIR=/tmp
SLURM_TMPDIR=
/tmp     tmpfs  428G
/dev/shm tmpfs  428G
```

Use `/tmp` or `/dev/shm` only for per-job temporary files that can be deleted at
job end. They are not shared campaign storage, may disappear when the job ends
or the node changes, and should not be used for outputs that reducers or later
jobs need. A safe pattern is:

```bash
JOB_TMP="/tmp/${USER}/${SLURM_JOB_ID}"
mkdir -p "$JOB_TMP"
cleanup() {
  rm -rf "$JOB_TMP"
}
trap cleanup EXIT
```

If a job stages data through `/tmp`, copy final results back to `$SCRATCH`
before the command exits.

## Generic Workflow Patterns

Balfrin has the standard SLURM command set plus useful campaign tools:

```text
sbatch, srun, squeue, sacct, scontrol, sinfo, sprio, sstat, seff
lfs, rsync, tar, zstd, pigz, python3, uv, jq, yq, git, tmux, uenv
```

The environment module system is present, but the visible module tree was
minimal in the 2026-05-08 probe. `uenv` is available (`uenv 5.2.0-dev`) and is
the likely path for packaged user environments when a workflow needs one:

```bash
uenv image find
uenv start <image>
uenv run <image> -- <command>
uenv status
uenv stop
```

Record any loaded `uenv` image, view, or custom environment setup in the run
manifest. For plain shell jobs, make the environment explicit in the batch
script instead of relying on an interactive shell:

```bash
set -euo pipefail
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
```

Use `tmux` on the login node for long monitoring sessions, not for compute
work. Keep the actual computation inside SLURM jobs.

### Campaign Directory Layout

Use a stable layout under `$SCRATCH` so array tasks, reducers, and recovery
commands can find each other without scanning huge trees:

```text
$SCRATCH/<campaign>/
  manifests/
    campaign.json
    chunks.tsv
    inputs.sha256
  configs/
    chunk_000000.yaml
    chunk_000001.yaml
  logs/
    build-%j.out
    array-%A_%a.out
    reduce-%j.out
  chunks/
    chunk_000000/
      manifest.json
      outputs...
    chunk_000001/
      manifest.json
      outputs...
  reduce/
    region_*.parquet
    national_manifest.json
```

The important properties are:

- every chunk has a deterministic ID;
- every job writes to one chunk directory;
- each chunk writes a small manifest with command, host, job ID, start/end time,
  input paths, output paths, row counts, and checksums where practical;
- reducers read chunk manifests rather than guessing from directory contents;
- partial outputs are written to temporary names and atomically renamed when
  complete.

Atomic completion marker pattern:

```bash
out="$RUN_ROOT/result.parquet"
tmp="${out}.tmp.${SLURM_JOB_ID}"
your_command --output "$tmp"
sync "$tmp" 2>/dev/null || true
mv "$tmp" "$out"
printf '{"status":"complete","job_id":"%s"}\n' "$SLURM_JOB_ID" > "$RUN_ROOT/manifest.json"
```

### Arrays and Dependencies

Live SLURM config reported `MaxArraySize=1001`. Use arrays for batches up to
that size, and split larger campaigns into multiple arrays or submit waves.
Always throttle arrays with `%N` so the campaign respects Balfrin's shared-use
rules and avoids filesystem pressure:

```bash
#SBATCH --array=0-999%20
#SBATCH --output=logs/array-%A_%a.out
#SBATCH --error=logs/array-%A_%a.err
```

Use `--parsable` to capture job IDs for dependencies:

```bash
build_id=$(sbatch --parsable build.sbatch)
array_id=$(sbatch --parsable --dependency=afterok:${build_id} chunks.sbatch)
reduce_id=$(sbatch --parsable --dependency=afterok:${array_id} reduce.sbatch)
echo "build=$build_id array=$array_id reduce=$reduce_id"
```

Common dependency types:

| Dependency | Use |
| --- | --- |
| `afterok:<job_id>` | Run only if the dependency succeeds. Use for build -> array -> reducer pipelines. |
| `afterany:<job_id>` | Run after completion regardless of success. Use for cleanup or diagnostics. |
| `afternotok:<job_id>` | Run only after failure. Use for failure-report jobs. |
| `singleton` | Allow only one running job with the same name and user. Useful for reducers or monitors that must not overlap. |

Adjust an already submitted array throttle when Balfrin is busy or empty:

```bash
scontrol update ArrayTaskThrottle=<count> JobId=<array_job_id>
```

Show one array task per line:

```bash
squeue -r -j <array_job_id> -o "%.18i %.8T %.10M %.6D %R"
```

Cancel selected tasks:

```bash
scancel <array_job_id>_<task_id>
scancel <array_job_id>_[10-50]
```

### Preemption, Time Limits, and Cleanup

Live config reported:

- `PreemptType=preempt/partition_prio`;
- `PreemptMode=REQUEUE`;
- `KillWait=30 sec`;
- `ProctrackType=proctrack/cgroup`;
- `TaskPlugin=task/cgroup,task/affinity`.

The `preemptible` partition also reported a 60 second grace period in the
partition settings. For jobs that need cleanup or checkpointing, request a
warning signal before time limit and trap termination:

```bash
#SBATCH --signal=B:TERM@120
#SBATCH --requeue

terminate() {
  echo "termination signal at $(date -Is)"
  # checkpoint, close manifests, or mark partial output here
  exit 143
}
trap terminate TERM
```

Design jobs to be idempotent: if a chunk manifest says complete and all
expected output checks pass, a rerun should skip that chunk or write a new
attempt directory. This is safer than trying to repair partially written files.

### Monitoring and Accounting

Useful live commands:

```bash
squeue -u olifu -o "%.18i %.14P %.24j %.8T %.12M %.6D %R"
squeue --start -u olifu
scontrol show job <job_id>
sstat -j <job_id>.batch --format=AveCPU,AveRSS,MaxRSS,MaxDiskRead,MaxDiskWrite
sacct -j <job_id> --format=JobID,JobName,Partition,State,ExitCode,Elapsed,AllocCPUS,MaxRSS,MaxDiskRead,MaxDiskWrite,WorkDir
seff <job_id>
sprio -u olifu
```

`sacct` is backed by `accounting_storage/slurmdbd`; recent probes returned
completed jobs with `State`, `ExitCode`, `Elapsed`, `AllocCPUS`, `MaxRSS`,
disk-read/write fields, and `WorkDir`. SLURM's `MinJobAge` was 300 seconds, so
very recent completed jobs may disappear from `squeue` before all accounting
details are useful.

For campaign status, prefer manifest-based monitoring plus SLURM state:

```bash
find "$SCRATCH/<campaign>/chunks" -name manifest.json -print | wc -l
squeue -u olifu -j <array_job_id>
sacct -j <array_job_id> --format=JobID,State,ExitCode,Elapsed,MaxRSS
```

### Notifications

SLURM mail support is configured with `MailProg=/bin/mail`. If email delivery
is configured for the account, jobs can request notifications:

```bash
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<address>
```

For very large arrays, avoid mail on every array task. Prefer a final reducer or
summary job that sends one notification.

### Data Transfer and Packaging

`rsync`, `tar`, `zstd`, and `pigz` are available. Use `rsync` for source trees
and manifests, and package many small review artifacts before transferring them
off Balfrin:

```bash
rsync -a --info=progress2 local_dir/ balfrin:$SCRATCH/<campaign>/input/

tar -I "zstd -T0" -cf review_artifacts.tar.zst review_artifacts/
rsync -a balfrin:$SCRATCH/<campaign>/review_artifacts.tar.zst .
```

Do not package or transfer large raw datasets or full campaign outputs unless
there is a clear retention target. Prefer compact manifests, summaries, and
selected QA artifacts for review.

## Rust Executables via SLURM

Balfrin had a user-local Rust toolchain on the login node and compute nodes on
2026-05-08:

```text
rustc 1.95.0 (59807616e 2026-04-14)
cargo 1.95.0 (f2d3ce0bd 2026-03-21)
```

The tools were found under `/users/olifu/.cargo/bin`. A scheduled `pp-short`
smoke job compiled and ran a tiny Rust executable on `nid001236`, confirming
that Rust executables can be built and launched from SLURM jobs when
`$HOME/.cargo/bin` is on `PATH`.

For examples below, replace `app` with the real Cargo binary name. Check the
available command-line surface before writing batch scripts:

```bash
app --help
app --version
app <subcommand> --help
```

Prefer this workflow:

1. Put the working tree and build artifacts on `$SCRATCH`.
2. Build the release executable once in a CPU SLURM job.
3. Reuse the compiled `target/release/app` executable from subsequent
   run, analysis, or post-processing jobs.
4. Write generated outputs to run-specific directories under `$SCRATCH`.

Avoid `cargo run` for production-scale jobs. `cargo run` mixes compilation and
execution, can repeat dependency/build work, and can create Cargo lock
contention when many jobs start at once. Use `cargo build --release --locked`
first, then call the executable directly.

### Stage or Clone the Repository

If the repository is available from a remote Git service, clone directly on
Balfrin into `$SCRATCH`. If not, sync a local checkout to Balfrin while
excluding generated outputs and local build products:

```bash
rsync -a --delete \
  --exclude target \
  --exclude .venv \
  --exclude results \
  --exclude output \
  --exclude tmp \
  --exclude data/raw \
  /path/to/app/ \
  balfrin:$SCRATCH/app/src/
```

On Balfrin:

```bash
cd "$SCRATCH/app/src"
git status -sb
git rev-parse --short HEAD
```

For uncommitted local experiments, record `git diff --stat` and enough patch or
branch information in the run notes to reproduce the executable later.

### Build Job

Use a CPU partition for builds. This keeps compilation off login nodes and away
from GPU nodes:

```bash
cat > build_app.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=build-app
#SBATCH --partition=pp-short
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --output=slurm-build-%j.out
#SBATCH --error=slurm-build-%j.err

set -euo pipefail

export PATH="$HOME/.cargo/bin:$PATH"
export CARGO_TARGET_DIR="$SCRATCH/app/target"
export CARGO_INCREMENTAL=0

cd "$SCRATCH/app/src"
echo "host=$(hostname) job=$SLURM_JOB_ID cpus=$SLURM_CPUS_PER_TASK"
rustc --version
cargo --version

cargo build --release --locked --bin app
"$CARGO_TARGET_DIR/release/app" --version
SLURM

sbatch build_app.sbatch
```

Notes:

- If the application commits `Cargo.lock`, `--locked` is the right default for
  reproducible cluster builds.
- `CARGO_TARGET_DIR` belongs on `$SCRATCH`; release builds can be large and
  should not fill `$HOME`.
- `CARGO_INCREMENTAL=0` is appropriate for release batch builds and reduces
  incremental-cache churn.
- `-C target-cpu=native` can improve single-node CPU performance, but only use
  it intentionally. It ties the binary to the sampled Balfrin CPU generation
  and can make later portability less clear.

### Run One Application Command

This is the direct executable pattern for an application command with one input
configuration and one output directory:

```bash
cat > run_app_one.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=app-one
#SBATCH --partition=postproc
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --output=slurm-run-%j.out
#SBATCH --error=slurm-run-%j.err

set -euo pipefail

export PATH="$HOME/.cargo/bin:$PATH"
export CARGO_TARGET_DIR="$SCRATCH/app/target"

REPO="$SCRATCH/app/src"
RUN_ROOT="$SCRATCH/app/runs/${SLURM_JOB_ID}"
BIN="$CARGO_TARGET_DIR/release/app"

mkdir -p "$RUN_ROOT"
cd "$REPO"

echo "host=$(hostname) job=$SLURM_JOB_ID submit=$SLURM_SUBMIT_DIR"
"$BIN" --version

"$BIN" run \
  --config "$REPO/configs/example.yaml" \
  --output-dir "$RUN_ROOT"
SLURM

sbatch --dependency=afterok:<build_job_id> run_app_one.sbatch
```

Replace `configs/example.yaml` and the command arguments with the application's
real interface. Keep large outputs under `$SCRATCH`, then copy only selected
small reports or fixtures back into the repository.

### Run Analysis or Post-Processing Jobs

Use the executable directly:

```bash
cat > postprocess.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=app-postprocess
#SBATCH --partition=postproc
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --output=slurm-postprocess-%j.out
#SBATCH --error=slurm-postprocess-%j.err

set -euo pipefail

export CARGO_TARGET_DIR="$SCRATCH/app/target"
REPO="$SCRATCH/app/src"
BIN="$CARGO_TARGET_DIR/release/app"

cd "$REPO"
"$BIN" postprocess \
  --input "$SCRATCH/app/runs/<run_id>" \
  --output "$SCRATCH/app/reduce/<run_id>"
SLURM

sbatch --dependency=afterok:<array_job_id> postprocess.sbatch
```

For long post-processing runs, increase the time limit and choose the partition
according to expected runtime. Keep repository-relative result paths under the
scratch working tree so outputs land on the work filesystem.

### Job Arrays for Ensembles

For many independent configs or release-zone chunks, use a SLURM array with a
concurrency throttle. Keep each task's output isolated:

```bash
#SBATCH --array=0-99%8

CONFIG_LIST="$SCRATCH/app/configs/configs.txt"
CONFIG="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$CONFIG_LIST")"
RUN_ROOT="$SCRATCH/app/runs/${SLURM_ARRAY_JOB_ID}/${SLURM_ARRAY_TASK_ID}"
mkdir -p "$RUN_ROOT"

"$BIN" run \
  --config "$CONFIG" \
  --output-dir "$RUN_ROOT"
```

The array throttle, `%8` in the example, should be chosen so the run respects
Balfrin's shared-system rules and avoids excessive filesystem pressure. For
large campaigns, design chunk IDs, manifests, row counts, checksums, and
deterministic reducer jobs before scaling up.

### Runtime Hygiene

- Use CPU partitions for CPU-only application runs unless the implementation
  genuinely uses GPUs.
- Set `--cpus-per-task` to the level actually used. The current executable is
  primarily a CPU process; requesting more CPUs than it can use only reduces
  cluster availability.
- Keep `SLURM_JOB_ID`, git commit, command line, config path, binary path, and
  output directory in each run log.
- Prefer one build job per code revision, then many run jobs depending on that
  build with `--dependency=afterok:<build_job_id>`.
- Do not let many array tasks all run `cargo build` in the same target
  directory.
- Keep stdout/stderr readable; write high-volume outputs to explicit data files
  under `$SCRATCH`.

### GPU Partitions

| Partition | Typical use | Max time | Access | Priority | Sharing | Notes |
| --- | --- | ---: | --- | ---: | --- | --- |
| `debug` | debugging | 30 min | all | 100 | shared-capable | Policy says some nodes may be reserved during working hours. Use for short diagnostics. |
| `short` | CI GPU, R&D, KENDA, short development | 1 h | all | 10 | exclusive | Policy says users may submit at most 2 jobs to `short`, `short-shared`, and `pp-short`. |
| `short-shared` | CI GPU, R&D, KENDA, short development | 1 h | all | 10 | shared-capable | Use `--gres=gpu:N` when sharing a node. |
| `normal` | e-suites, ML training, regular GPU work | 24 h | all | 1 | exclusive | Use for ordinary GPU jobs, but respect the 50%-of-machine rule. |
| `normal-half` | observed live GPU subset | 24 h | all | 1 | exclusive | Present in live SLURM on 2026-05-08, not in the exported policy table. Confirm intended use before depending on it. |
| `normal-shared` | e-suites, ML training, regular GPU work | 24 h | all | 1 | shared-capable | Use `--gres=gpu:N` when sharing a node. |
| `lowprio` | lower-priority GPU work | 24 h | all | 0 | exclusive | Use for extra jobs beyond the usual shared-system limits. |
| `preemptible` | opportunistic GPU work | 24 h | group `s83` live; policy says all | 0 | exclusive | Jobs are preempted when resources are needed. Live `GraceTime=60`; install a SIGTERM handler for checkpoint/cleanup. |

The exported policy states that `debug`, `short-shared`, and `normal-shared`
allow multiple users per GPU node. The prose says `short_shared` and
`normal_shared`, but live SLURM uses hyphenated names.

For shared GPU partitions, request only the GPUs needed:

```bash
srun --partition=debug --gres=gpu:1 --ntasks=1 ./list_devices
```

If `--gres` is omitted on GPU partitions, policy says the job receives all 4
GPUs on the node and the node is not shared with other users. Never use GPU
nodes for CPU-only jobs.

### CPU Partitions

| Partition | Typical use | Max time | Access | Priority | Notes |
| --- | --- | ---: | --- | ---: | --- |
| `pp-short` | CI CPU, LETKF, pre/post-processing | 1 h | all | 10 | Policy says users may submit at most 2 jobs to `short`, `short-shared`, and `pp-short`. |
| `pp-serial` | verification / serial CPU jobs | 120 h | all | 10 policy, 1 live | Policy says max 1 physical core; live QoS showed `MaxTRESPerJob=cpu=2`. |
| `postproc` | data analysis / general CPU work | 24 h | all | 1 | Default partition on 2026-05-08. |
| `pp-long` | longer data analysis | 120 h | all | 1 | Use for long CPU post-processing when `postproc` is too short. |

The live `scontrol show partition` snapshot showed 13-14 CPU nodes in the
listed CPU partitions at that moment.

## Shared-System Rules

Use the smallest suitable partition:

- CPU-only `app` runs should use CPU partitions, usually `postproc`,
  `pp-short`, `pp-serial`, or `pp-long`.
- GPU partitions should be used only for real GPU workloads.
- `debug`, `short`, `short-shared`, and `pp-short` are for CI and short
  development tasks.
- Do not submit more than 2 jobs to `short`, `short-shared`, and `pp-short`.
- Users should generally avoid using more than 50% of the machine for more than
  15 minutes consecutively unless coordinated on the Balfrin MS Teams channel.
- Extra jobs beyond that shared-system limit should go to `lowprio`.
- The 50% rule does not apply to `preemptible`, but those jobs can be killed
  when resources are needed.
- During NWP production failover, CPU and GPU nodes may be reserved and jobs
  blocking operational work may be requeued.

For large job arrays, throttle concurrency:

```bash
#SBATCH --array=1-20%4
```

Adjust an already submitted array throttle:

```bash
scontrol update ArrayTaskThrottle=<count> JobId=<job_id>
```

Live cluster configuration on 2026-05-08 reported `MaxArraySize=1001`, so array
indices should stay below that limit unless the configuration changes.

## Submit Jobs

Submit with `sbatch` from the directory that should become
`$SLURM_SUBMIT_DIR`. Prefer a scratch/work directory rather than home.

Minimal CPU job:

```bash
cat > cpu_smoke.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=app-cpu-smoke
#SBATCH --partition=postproc
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
echo "job=$SLURM_JOB_ID host=$(hostname) cpus=$SLURM_CPUS_PER_TASK"

# Replace with the intended repository command.
cargo run --release -- --help
SLURM

sbatch cpu_smoke.sbatch
```

Short serial CPU job:

```bash
sbatch --partition=pp-serial --time=02:00:00 --ntasks=1 --cpus-per-task=1 cpu_smoke.sbatch
```

GPU debug job requesting one GPU on a shared-capable partition:

```bash
cat > gpu_debug.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=gpu-debug
#SBATCH --partition=debug
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
hostname
nvidia-smi
SLURM

sbatch gpu_debug.sbatch
```

Preemptible GPU job with a SIGTERM cleanup hook:

```bash
cat > preemptible_gpu.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=preemptible-gpu
#SBATCH --partition=preemptible
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --gres=gpu:4
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -euo pipefail

cleanup() {
  echo "received SIGTERM; checkpoint or cleanup here"
  exit 0
}
trap cleanup SIGTERM

cd "$SLURM_SUBMIT_DIR"
# Replace with the intended GPU command.
nvidia-smi
sleep 300
SLURM

sbatch preemptible_gpu.sbatch
```

For interactive diagnostics, use `srun` on a short/debug partition:

```bash
srun --partition=pp-short --time=00:10:00 --ntasks=1 --cpus-per-task=4 --pty bash
srun --partition=debug --time=00:10:00 --gres=gpu:1 --ntasks=1 --pty bash
```

## Monitor Jobs

Show only this user's jobs:

```bash
squeue -u olifu
squeue -u olifu -o "%.18i %.14P %.18j %.10u %.2t %.12M %.6D %R"
```

Inspect one job:

```bash
scontrol show job <job_id>
```

Follow output:

```bash
tail -f slurm-<job_id>.out
tail -f slurm-<job_id>.err
```

Check partition availability:

```bash
sinfo
sinfo -p postproc
sinfo -p normal,normal-shared,lowprio
sinfo -o "%P %D %t %G %l %N"
```

After a job leaves the queue, inspect accounting if available:

```bash
sacct -j <job_id> --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
```

The exported policy says SLURM usage per user is monitored on the CSCS Kibana
board `Slurm_accounting-Balfrin`.

## Cancel Jobs

Cancel one job:

```bash
scancel <job_id>
```

Cancel all jobs owned by `olifu`:

```bash
scancel -u olifu
```

Cancel jobs by partition or name when needed:

```bash
scancel -u olifu -p lowprio
scancel -u olifu --name app-cpu-smoke
```

Cancel selected array tasks:

```bash
scancel <job_id>_<array_index>
scancel <job_id>_[1-10]
```

## Quick Partition Discovery Commands

Use these commands when refreshing this document:

```bash
ssh balfrin 'date; hostname; whoami; sinfo --version'
ssh balfrin 'sinfo -o "%P|%D|%t|%c|%m|%G|%l|%N"'
ssh balfrin 'scontrol show partition'
ssh balfrin 'scontrol show config | egrep "^(ClusterName|SchedulerType|SelectType|SelectTypeParameters|Preempt|MaxArraySize|KillWait)"'
ssh balfrin 'sacctmgr -n -P show qos format=Name,Priority,MaxWall,MaxTRESPerJob,MaxJobsPU,MaxSubmitPU,GraceTime 2>/dev/null || true'
ssh balfrin 'sacctmgr -n -P show assoc user=olifu format=Cluster,Account,User,Partition,QOS,DefaultQOS,MaxJobs,MaxSubmit,MaxWall 2>/dev/null || true'
```

For hardware refreshes, run the probes through SLURM allocations rather than on
login nodes. A compact one-shot CPU probe:

```bash
ssh balfrin 'srun --partition=pp-short --time=00:03:00 --nodes=1 --ntasks=1 --cpus-per-task=1 bash -lc '"'"'
hostname
uname -a
cat /etc/os-release
lscpu
free -b
numactl --hardware
grep -m 8 -E "^(model name|cpu cores|siblings|cpu MHz|cache size)" /proc/cpuinfo
'"'"''
```

A compact one-shot GPU probe:

```bash
ssh balfrin 'srun --partition=debug --time=00:03:00 --nodes=1 --ntasks=1 --cpus-per-task=1 --gres=gpu:1 bash -lc '"'"'
hostname
uname -a
cat /etc/os-release
lscpu
free -b
numactl --hardware
nvidia-smi -L
nvidia-smi --query-gpu=index,gpu_name,gpu_uuid,memory.total,driver_version,pci.bus_id,persistence_mode,mig.mode.current --format=csv
nvidia-smi topo -m
'"'"''
```
