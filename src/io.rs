use crate::{
    simulation::SimulationConfig,
    state::{ContactState, ImpactEvent, TrajectorySample},
};
use arrow_array::{ArrayRef, Float64Array, RecordBatch, StringArray, UInt64Array};
use arrow_schema::{DataType, Field, Schema};
use parquet::{arrow::ArrowWriter, basic::Compression, file::properties::WriterProperties};
use std::{fs::File, io::BufReader, path::Path, sync::Arc};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum IoError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("CSV error: {0}")]
    Csv(#[from] csv::Error),
    #[error("Arrow error: {0}")]
    Arrow(#[from] arrow_schema::ArrowError),
    #[error("Parquet error: {0}")]
    Parquet(#[from] parquet::errors::ParquetError),
    #[error("invalid input: {0}")]
    InvalidInput(String),
}

pub fn read_config(path: impl AsRef<Path>) -> Result<SimulationConfig, IoError> {
    let file = File::open(path)?;
    Ok(serde_json::from_reader(BufReader::new(file))?)
}

pub fn write_trajectory_csv(
    path: impl AsRef<Path>,
    samples: &[TrajectorySample],
) -> Result<(), IoError> {
    let mut writer = csv::Writer::from_path(path)?;
    for sample in samples {
        writer.serialize(sample)?;
    }
    writer.flush()?;
    Ok(())
}

pub fn write_impact_events_csv(
    path: impl AsRef<Path>,
    events: &[ImpactEvent],
) -> Result<(), IoError> {
    let mut writer = csv::Writer::from_path(path)?;
    for event in events {
        writer.serialize(event)?;
    }
    writer.flush()?;
    Ok(())
}

pub fn write_impact_events_json(
    path: impl AsRef<Path>,
    events: &[ImpactEvent],
) -> Result<(), IoError> {
    let file = File::create(path)?;
    serde_json::to_writer_pretty(file, events)?;
    Ok(())
}

fn contact_state_str(state: ContactState) -> &'static str {
    match state {
        ContactState::Airborne => "airborne",
        ContactState::Sliding => "sliding",
        ContactState::Impact => "impact",
        ContactState::Rolling => "rolling",
        ContactState::Stopped => "stopped",
    }
}

/// Write trajectory samples from multiple trajectories into a single Parquet file.
///
/// Each row records one time-step sample. The `trajectory_id` and optional `seed`
/// columns identify which trajectory a sample belongs to, making this the preferred
/// format for large ensemble outputs where per-trajectory CSV files would be
/// impractical.
///
/// Column schema matches the field names of [`TrajectorySample`], plus a leading
/// `trajectory_id` (UTF-8) and nullable `seed` (UInt64) column.
///
/// Data is written as one [`RecordBatch`] per trajectory, so memory usage scales
/// with the largest single trajectory rather than the full ensemble.
pub fn write_trajectory_samples_parquet(
    path: impl AsRef<Path>,
    trajectory_ids_and_seeds: &[(&str, Option<u64>)],
    all_samples: &[&[TrajectorySample]],
) -> Result<(), IoError> {
    if trajectory_ids_and_seeds.len() != all_samples.len() {
        return Err(IoError::InvalidInput(format!(
            "trajectory_ids_and_seeds length ({}) must equal all_samples length ({})",
            trajectory_ids_and_seeds.len(),
            all_samples.len(),
        )));
    }

    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }

    let schema = Arc::new(Schema::new(vec![
        Field::new("trajectory_id", DataType::Utf8, false),
        Field::new("seed", DataType::UInt64, true),
        Field::new("time_s", DataType::Float64, false),
        Field::new("x_m", DataType::Float64, false),
        Field::new("y_m", DataType::Float64, false),
        Field::new("z_m", DataType::Float64, false),
        Field::new("vx_mps", DataType::Float64, false),
        Field::new("vy_mps", DataType::Float64, false),
        Field::new("vz_mps", DataType::Float64, false),
        Field::new("speed_mps", DataType::Float64, false),
        Field::new("kinetic_j", DataType::Float64, false),
        Field::new("rotational_j", DataType::Float64, false),
        Field::new("potential_j", DataType::Float64, false),
        Field::new("total_energy_j", DataType::Float64, false),
        Field::new("contact_state", DataType::Utf8, false),
        Field::new("omega_x_radps", DataType::Float64, false),
        Field::new("omega_y_radps", DataType::Float64, false),
        Field::new("omega_z_radps", DataType::Float64, false),
        Field::new("contact_tangent_speed_mps", DataType::Float64, false),
        Field::new("rolling_residual_mps", DataType::Float64, false),
        Field::new("scarring_depth_m", DataType::Float64, false),
        Field::new("scarring_drag_force_n", DataType::Float64, false),
        Field::new("scarring_energy_loss_j", DataType::Float64, false),
    ]));

    let properties = WriterProperties::builder()
        .set_compression(Compression::ZSTD(Default::default()))
        .build();
    let file = File::create(path)?;
    let mut writer = ArrowWriter::try_new(file, schema.clone(), Some(properties))?;

    // Write one RecordBatch per trajectory to keep peak memory proportional to
    // the largest single trajectory rather than the full ensemble.
    for ((id, seed), samples) in trajectory_ids_and_seeds.iter().zip(all_samples.iter()) {
        let n = samples.len();
        if n == 0 {
            continue;
        }

        let col_trajectory_id: Vec<String> = vec![(*id).to_string(); n];
        let col_seed: Vec<Option<u64>> = vec![*seed; n];
        let col_time_s: Vec<f64> = samples.iter().map(|s| s.time_s).collect();
        let col_x_m: Vec<f64> = samples.iter().map(|s| s.x_m).collect();
        let col_y_m: Vec<f64> = samples.iter().map(|s| s.y_m).collect();
        let col_z_m: Vec<f64> = samples.iter().map(|s| s.z_m).collect();
        let col_vx_mps: Vec<f64> = samples.iter().map(|s| s.vx_mps).collect();
        let col_vy_mps: Vec<f64> = samples.iter().map(|s| s.vy_mps).collect();
        let col_vz_mps: Vec<f64> = samples.iter().map(|s| s.vz_mps).collect();
        let col_speed_mps: Vec<f64> = samples.iter().map(|s| s.speed_mps).collect();
        let col_kinetic_j: Vec<f64> = samples.iter().map(|s| s.kinetic_j).collect();
        let col_rotational_j: Vec<f64> = samples.iter().map(|s| s.rotational_j).collect();
        let col_potential_j: Vec<f64> = samples.iter().map(|s| s.potential_j).collect();
        let col_total_energy_j: Vec<f64> = samples.iter().map(|s| s.total_energy_j).collect();
        let col_contact_state: Vec<String> = samples
            .iter()
            .map(|s| contact_state_str(s.contact_state).to_string())
            .collect();
        let col_omega_x_radps: Vec<f64> = samples.iter().map(|s| s.omega_x_radps).collect();
        let col_omega_y_radps: Vec<f64> = samples.iter().map(|s| s.omega_y_radps).collect();
        let col_omega_z_radps: Vec<f64> = samples.iter().map(|s| s.omega_z_radps).collect();
        let col_contact_tangent_speed_mps: Vec<f64> = samples
            .iter()
            .map(|s| s.contact_tangent_speed_mps)
            .collect();
        let col_rolling_residual_mps: Vec<f64> =
            samples.iter().map(|s| s.rolling_residual_mps).collect();
        let col_scarring_depth_m: Vec<f64> = samples.iter().map(|s| s.scarring_depth_m).collect();
        let col_scarring_drag_force_n: Vec<f64> =
            samples.iter().map(|s| s.scarring_drag_force_n).collect();
        let col_scarring_energy_loss_j: Vec<f64> =
            samples.iter().map(|s| s.scarring_energy_loss_j).collect();

        let columns: Vec<ArrayRef> = vec![
            Arc::new(StringArray::from(col_trajectory_id)),
            Arc::new(UInt64Array::from(col_seed)),
            Arc::new(Float64Array::from(col_time_s)),
            Arc::new(Float64Array::from(col_x_m)),
            Arc::new(Float64Array::from(col_y_m)),
            Arc::new(Float64Array::from(col_z_m)),
            Arc::new(Float64Array::from(col_vx_mps)),
            Arc::new(Float64Array::from(col_vy_mps)),
            Arc::new(Float64Array::from(col_vz_mps)),
            Arc::new(Float64Array::from(col_speed_mps)),
            Arc::new(Float64Array::from(col_kinetic_j)),
            Arc::new(Float64Array::from(col_rotational_j)),
            Arc::new(Float64Array::from(col_potential_j)),
            Arc::new(Float64Array::from(col_total_energy_j)),
            Arc::new(StringArray::from(col_contact_state)),
            Arc::new(Float64Array::from(col_omega_x_radps)),
            Arc::new(Float64Array::from(col_omega_y_radps)),
            Arc::new(Float64Array::from(col_omega_z_radps)),
            Arc::new(Float64Array::from(col_contact_tangent_speed_mps)),
            Arc::new(Float64Array::from(col_rolling_residual_mps)),
            Arc::new(Float64Array::from(col_scarring_depth_m)),
            Arc::new(Float64Array::from(col_scarring_drag_force_n)),
            Arc::new(Float64Array::from(col_scarring_energy_loss_j)),
        ];

        let batch = RecordBatch::try_new(schema.clone(), columns)?;
        writer.write(&batch)?;
    }

    writer.close()?;
    Ok(())
}
