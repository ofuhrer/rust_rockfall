use crate::{
    simulation::SimulationConfig,
    state::{ImpactEvent, TrajectorySample},
};
use std::{fs::File, io::BufReader, path::Path};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum IoError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("CSV error: {0}")]
    Csv(#[from] csv::Error),
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
