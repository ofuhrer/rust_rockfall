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
        #[arg(long)]
        impact_events_csv: Option<PathBuf>,
        #[arg(long)]
        impact_events_json: Option<PathBuf>,
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
    #[error("metrics serialization error: {0}")]
    MetricsSerialize(#[from] serde_json::Error),
    #[error("{0}")]
    Usage(String),
}

fn main() -> Result<(), CliError> {
    let cli = Cli::parse();
    match cli.command {
        Command::Run {
            config,
            output,
            impact_events_csv,
            impact_events_json,
        } => run_simulation(config, output, impact_events_csv, impact_events_json),
        Command::Verify { case, all } => run_case_command(case, all, Path::new("verification")),
        Command::Validate { case, all } => {
            run_case_command(case, all, Path::new("validation/cases"))
        }
        Command::Benchmark { case, all } => {
            run_case_command(case, all, Path::new("verification/synthetic/benchmarks"))
        }
    }
}

fn run_simulation(
    config: PathBuf,
    output: PathBuf,
    impact_events_csv: Option<PathBuf>,
    impact_events_json: Option<PathBuf>,
) -> Result<(), CliError> {
    let config = io::read_config(config)?;
    let result = config.run()?;
    io::write_trajectory_csv(&output, &result.samples)?;
    if let Some(path) = impact_events_csv {
        io::write_impact_events_csv(&path, &result.impact_events)?;
        eprintln!(
            "wrote {} impact events to {}",
            result.impact_events.len(),
            path.display()
        );
    }
    if let Some(path) = impact_events_json {
        io::write_impact_events_json(&path, &result.impact_events)?;
        eprintln!(
            "wrote {} impact events to {}",
            result.impact_events.len(),
            path.display()
        );
    }
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
        let metrics_json = serde_json::to_string(&report.metrics)?;
        println!("{}\t{:?}\t{}", path.display(), report.status, metrics_json);
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
    if !root.exists() {
        return Err(CliError::Usage(format!(
            "case root does not exist: {}",
            root.display()
        )));
    }
    let mut cases = Vec::new();
    collect_yaml_cases_recursive(root, &mut cases)?;
    cases.sort_by_key(|path| case_sort_key(path));
    if cases.is_empty() {
        return Err(CliError::Usage(format!(
            "no YAML cases found under {}",
            root.display()
        )));
    }
    Ok(cases)
}

fn collect_yaml_cases_recursive(root: &Path, cases: &mut Vec<PathBuf>) -> Result<(), CliError> {
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

fn case_sort_key(path: &Path) -> (u8, u8, u16, String) {
    let case = validation::load_case(path).ok();
    let case_id = case
        .as_ref()
        .map(|case| case.case_id.as_str())
        .unwrap_or_else(|| {
            path.file_stem()
                .and_then(|stem| stem.to_str())
                .unwrap_or("")
        });
    let level = case.as_ref().and_then(|case| case.level).unwrap_or(99);
    (
        level,
        family_order(path, case_id),
        case_order(case_id),
        path.to_string_lossy().to_string(),
    )
}

fn family_order(path: &Path, case_id: &str) -> u8 {
    let path_text = path.to_string_lossy();
    if path_text.contains("/analytic/") {
        0
    } else if path_text.contains("/synthetic/") && !case_id.starts_with("regime_") {
        1
    } else if case_id.starts_with("regime_") {
        2
    } else if path_text.contains("/stochastic/") {
        3
    } else if path_text.contains("validation/cases") {
        4
    } else {
        9
    }
}

fn case_order(case_id: &str) -> u16 {
    match case_id {
        "analytic_free_fall" => 10,
        "analytic_projectile_motion" => 20,
        "analytic_energy_conservation_no_dissipation" => 30,
        "analytic_vertical_rebound" => 40,
        "analytic_repeated_bounce" => 50,
        "analytic_oblique_rebound_flat_plane" => 60,
        "analytic_inclined_slide_stop" => 70,
        "analytic_no_motion_threshold" => 80,
        "analytic_rolling_incline_solid_sphere" => 90,
        "analytic_rolling_resistance_stop" => 100,
        "analytic_rolling_energy_monotonic" => 110,
        "analytic_insufficient_static_friction_slides" => 120,
        "synthetic_flat_plane_rebound" => 210,
        "synthetic_inclined_plane_bounce_runout" => 220,
        "synthetic_paraboloid_basin_capture" => 230,
        "synthetic_step_terrain_single_drop" => 240,
        "synthetic_step_terrain_multi_bounce" => 250,
        "synthetic_ascii_dem_fixture" => 260,
        "synthetic_clamped_dem_terrain_variation" => 270,
        "synthetic_contact_roughness_energy_stability" => 280,
        "synthetic_scarring_zero_baseline" => 290,
        "synthetic_scarring_energy_dissipation" => 300,
        "synthetic_scarring_depth_velocity_scaling" => 310,
        "synthetic_scarring_depth_soil_strength_scaling" => 320,
        "regime_bounce_to_slide_transition" => 310,
        "regime_slide_to_stop_transition" => 320,
        "regime_repeated_low_energy_impacts" => 330,
        "stochastic_seeded_release_reproducibility" => 410,
        "stochastic_different_seed_spread" => 420,
        "stochastic_ensemble_runout_statistics" => 430,
        "stochastic_contact_roughness_zero_consistency" => 440,
        "stochastic_contact_roughness_reproducibility" => 450,
        "stochastic_contact_roughness_ensemble_spread" => 460,
        "validation_synthetic_plane_basic" => 510,
        "validation_swissalti3d_pilot" => 520,
        "validation_swissalti3d_release_zone_pilot" => 525,
        "validation_swissalti3d_release_zone_terrain_classes_pilot" => 530,
        "validation_swissalti3d_hazard_statistics_pilot" => 535,
        "validation_chant_sura_trajectory_subset" => 560,
        "validation_chant_sura_contact" => 565,
        "validation_chant_sura_contact_rotational" => 566,
        "validation_chant_sura_contact_roughness" => 567,
        "validation_chant_sura_contact_scarring" => 568,
        "validation_chant_sura_contact_extended" => 570,
        "validation_chant_sura_contact_extended_rotational" => 571,
        "validation_chant_sura_contact_extended_roughness" => 572,
        "validation_chant_sura_contact_extended_scarring" => 573,
        "validation_chant_sura_contact_heldout" => 575,
        "validation_chant_sura_contact_heldout_rotational" => 576,
        "validation_tschamut_proxy_plane" => 580,
        "validation_tschamut_basic" => 590,
        "validation_tschamut_baseline" => 600,
        "validation_tschamut_scarring" => 610,
        _ => 1000,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn collect_yaml_cases_reports_empty_root() {
        let root =
            std::env::temp_dir().join(format!("rust_rockfall_empty_cases_{}", std::process::id()));
        fs::create_dir_all(&root).unwrap();

        let error = collect_yaml_cases(&root).unwrap_err();
        assert!(matches!(
            error,
            CliError::Usage(message) if message.contains("no YAML cases found")
        ));

        fs::remove_dir(root).unwrap();
    }
}
