use clap::{Parser, Subcommand};
use rust_rockfall::{io, simulation::SimulationError, validation};
use std::{
    fs,
    path::{Path, PathBuf},
};
use thiserror::Error;

#[derive(Debug, Parser)]
#[command(
    version,
    about = "Run and validate an independent research rockfall simulation"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Run one simulation from a JSON config and write trajectory CSV.
    Run {
        #[arg(short, long)]
        config: PathBuf,
        #[arg(short, long)]
        output: PathBuf,
    },
    /// Run verification cases from verification/.
    Verify {
        #[arg(long)]
        case: Option<PathBuf>,
        #[arg(long)]
        all: bool,
    },
    /// Run validation cases from validation/cases/.
    Validate {
        #[arg(long)]
        case: Option<PathBuf>,
        #[arg(long)]
        all: bool,
    },
    /// Run lightweight synthetic benchmark cases.
    Benchmark {
        #[arg(long)]
        case: Option<PathBuf>,
        #[arg(long)]
        all: bool,
    },
}

#[derive(Debug, Error)]
enum CliError {
    #[error("I/O error: {0}")]
    StdIo(#[from] std::io::Error),
    #[error("{0}")]
    Io(#[from] io::IoError),
    #[error("{0}")]
    Simulation(#[from] SimulationError),
    #[error("{0}")]
    Validation(#[from] validation::ValidationError),
    #[error("{0}")]
    Usage(String),
}

fn main() -> Result<(), CliError> {
    let cli = Cli::parse();
    match cli.command {
        Command::Run { config, output } => run_simulation(config, output),
        Command::Verify { case, all } => run_case_command(case, all, Path::new("verification")),
        Command::Validate { case, all } => {
            run_case_command(case, all, Path::new("validation/cases"))
        }
        Command::Benchmark { case, all } => {
            run_case_command(case, all, Path::new("verification/synthetic/benchmarks"))
        }
    }
}

fn run_simulation(config: PathBuf, output: PathBuf) -> Result<(), CliError> {
    let config = io::read_config(config)?;
    let result = config.run()?;
    io::write_trajectory_csv(&output, &result.samples)?;
    eprintln!(
        "wrote {} trajectory samples to {}",
        result.samples.len(),
        output.display()
    );
    Ok(())
}

fn run_case_command(case: Option<PathBuf>, all: bool, root: &Path) -> Result<(), CliError> {
    let case_paths = if all {
        collect_yaml_cases(root)?
    } else if let Some(case) = case {
        vec![case]
    } else {
        return Err(CliError::Usage(
            "provide --case <path> or --all for this command".to_string(),
        ));
    };

    let mut failed = 0usize;
    let mut skipped = 0usize;
    for path in case_paths {
        let report = validation::run_case_file(&path)?;
        println!(
            "{}\t{:?}\t{}",
            path.display(),
            report.status,
            serde_json::to_string(&report.metrics).unwrap_or_else(|_| "{}".to_string())
        );
        match report.status {
            validation::CaseStatus::Failed => failed += 1,
            validation::CaseStatus::Skipped => skipped += 1,
            validation::CaseStatus::Passed => {}
        }
    }

    if failed > 0 {
        return Err(CliError::Usage(format!("{failed} case(s) failed")));
    }
    if skipped > 0 {
        eprintln!("{skipped} case(s) skipped because optional data were unavailable");
    }
    Ok(())
}

fn collect_yaml_cases(root: &Path) -> Result<Vec<PathBuf>, CliError> {
    let mut cases = Vec::new();
    collect_yaml_cases_recursive(root, &mut cases)?;
    cases.sort();
    Ok(cases)
}

fn collect_yaml_cases_recursive(root: &Path, cases: &mut Vec<PathBuf>) -> Result<(), CliError> {
    if !root.exists() {
        return Ok(());
    }
    for entry in fs::read_dir(root)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            collect_yaml_cases_recursive(&path, cases)?;
        } else if matches!(
            path.extension().and_then(|extension| extension.to_str()),
            Some("yaml") | Some("yml")
        ) {
            cases.push(path);
        }
    }
    Ok(())
}
