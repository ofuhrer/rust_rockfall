use super::*;

pub(super) fn load_observations(
    case: &BenchmarkCase,
    warnings: &mut Vec<String>,
) -> Result<ObservationLoad, ValidationError> {
    let Some(observations) = &case.observations else {
        return Ok(ObservationLoad::Loaded(ObservationData::default()));
    };

    let mut data = ObservationData::default();
    if let Some(path) = &observations.release_points_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.release_points = read_release_points(path)?;
    }

    if let Some(path) = &observations.deposition_points_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.deposition_points = read_deposition_points(path)?;
    }
    if let Some(path) = &observations.trajectory_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.trajectory_samples = read_observed_trajectory_samples(path)?;
    }
    if let Some(path) = &observations.contact_events_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.contact_events = read_observed_contact_events(path)?;
    }
    if data.deposition_points.len() > 1 && data.release_points.is_empty() {
        warnings.push(format!(
            "case {} has {} observed deposition points; current metrics use the first point",
            case.case_id,
            data.deposition_points.len()
        ));
    }
    Ok(ObservationLoad::Loaded(data))
}

pub(super) fn read_deposition_points(path: &Path) -> Result<Vec<DepositionPoint>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut points = Vec::new();
    for record in reader.deserialize() {
        points.push(record?);
    }
    Ok(points)
}

pub(super) fn read_release_points(path: &Path) -> Result<Vec<ReleasePoint>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut points = Vec::new();
    for record in reader.deserialize() {
        points.push(record?);
    }
    Ok(points)
}

pub(super) fn read_observed_trajectory_samples(
    path: &Path,
) -> Result<Vec<ObservedTrajectorySample>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut samples = Vec::new();
    for record in reader.deserialize() {
        samples.push(record?);
    }
    Ok(samples)
}

pub(super) fn read_observed_contact_events(
    path: &Path,
) -> Result<Vec<ObservedContactEvent>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut events = Vec::new();
    for record in reader.deserialize() {
        events.push(record?);
    }
    Ok(events)
}
