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
pub fn write_trajectory_samples_parquet(
    path: impl AsRef<Path>,
    trajectory_ids_and_seeds: &[(&str, Option<u64>)],
    all_samples: &[&[TrajectorySample]],
) -> Result<(), IoError> {
    assert_eq!(
        trajectory_ids_and_seeds.len(),
        all_samples.len(),
        "trajectory_ids_and_seeds and all_samples must have the same length"
    );
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let row_count: usize = all_samples.iter().map(|s| s.len()).sum();

    let mut col_trajectory_id: Vec<String> = Vec::with_capacity(row_count);
    let mut col_seed: Vec<Option<u64>> = Vec::with_capacity(row_count);
    let mut col_time_s: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_x_m: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_y_m: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_z_m: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_vx_mps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_vy_mps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_vz_mps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_speed_mps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_kinetic_j: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_rotational_j: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_potential_j: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_total_energy_j: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_contact_state: Vec<String> = Vec::with_capacity(row_count);
    let mut col_omega_x_radps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_omega_y_radps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_omega_z_radps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_contact_tangent_speed_mps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_rolling_residual_mps: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_scarring_depth_m: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_scarring_drag_force_n: Vec<f64> = Vec::with_capacity(row_count);
    let mut col_scarring_energy_loss_j: Vec<f64> = Vec::with_capacity(row_count);

    for ((id, seed), samples) in trajectory_ids_and_seeds.iter().zip(all_samples.iter()) {
        for sample in *samples {
            col_trajectory_id.push((*id).to_string());
            col_seed.push(*seed);
            col_time_s.push(sample.time_s);
            col_x_m.push(sample.x_m);
            col_y_m.push(sample.y_m);
            col_z_m.push(sample.z_m);
            col_vx_mps.push(sample.vx_mps);
            col_vy_mps.push(sample.vy_mps);
            col_vz_mps.push(sample.vz_mps);
            col_speed_mps.push(sample.speed_mps);
            col_kinetic_j.push(sample.kinetic_j);
            col_rotational_j.push(sample.rotational_j);
            col_potential_j.push(sample.potential_j);
            col_total_energy_j.push(sample.total_energy_j);
            col_contact_state.push(contact_state_str(sample.contact_state).to_string());
            col_omega_x_radps.push(sample.omega_x_radps);
            col_omega_y_radps.push(sample.omega_y_radps);
            col_omega_z_radps.push(sample.omega_z_radps);
            col_contact_tangent_speed_mps.push(sample.contact_tangent_speed_mps);
            col_rolling_residual_mps.push(sample.rolling_residual_mps);
            col_scarring_depth_m.push(sample.scarring_depth_m);
            col_scarring_drag_force_n.push(sample.scarring_drag_force_n);
            col_scarring_energy_loss_j.push(sample.scarring_energy_loss_j);
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
    let properties = WriterProperties::builder()
        .set_compression(Compression::ZSTD(Default::default()))
        .build();
    let file = File::create(path)?;
    let mut writer = ArrowWriter::try_new(file, schema, Some(properties))?;
    writer.write(&batch)?;
    writer.close()?;
    Ok(())
}
