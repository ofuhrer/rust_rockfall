use super::*;

pub(super) fn compute_deposition_cloud_metrics(
    runs: &[TrajectoryRun],
    observations: &ObservationData,
    observed_deposition_configured: bool,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
) {
    let simulated_points = runs
        .iter()
        .map(|run| {
            (
                run.summary.final_position_m[0],
                run.summary.final_position_m[1],
            )
        })
        .collect::<Vec<_>>();
    let observed_points = observations
        .deposition_points
        .iter()
        .map(|point| (point.x_m, point.y_m))
        .collect::<Vec<_>>();
    if simulated_points.is_empty() || observed_points.is_empty() {
        if observed_deposition_configured {
            warnings.push(
                "deposition cloud metrics were omitted because simulated or observed deposition points were unavailable"
                    .to_string(),
            );
        }
        return;
    }

    let simulated_runouts = runs
        .iter()
        .map(|run| run.summary.runout_m)
        .collect::<Vec<_>>();
    let observed_runouts = observations
        .deposition_points
        .iter()
        .filter_map(observed_runout)
        .collect::<Vec<_>>();

    if observed_runouts.is_empty() {
        warnings.push(
            "observed deposition points do not include release coordinates; runout error is omitted"
                .to_string(),
        );
    } else {
        metrics.insert(
            "observed_mean_runout_m".to_string(),
            mean(&observed_runouts),
        );
        metrics.insert(
            "simulated_mean_runout_m".to_string(),
            mean(&simulated_runouts),
        );
        metrics.insert(
            "runout_distance_error_m".to_string(),
            (mean(&simulated_runouts) - mean(&observed_runouts)).abs(),
        );
    }

    let simulated_centroid = centroid2(&simulated_points);
    let observed_centroid = centroid2(&observed_points);
    metrics.insert(
        "deposition_centroid_error_m".to_string(),
        distance2(simulated_centroid, observed_centroid),
    );
    metrics.insert(
        "deposition_cloud_mean_nearest_error_m".to_string(),
        symmetric_mean_nearest_distance(&simulated_points, &observed_points),
    );
    metrics.insert(
        "lateral_spread_error_m".to_string(),
        (stddev_axis_y(&simulated_points) - stddev_axis_y(&observed_points)).abs(),
    );
    metrics.insert(
        "deposition_cloud_overlap_fraction".to_string(),
        cloud_overlap_fraction(&simulated_points, &observed_points, 15.0),
    );
}

pub(super) fn compute_roughness_comparison_metrics(
    case: &BenchmarkCase,
    config: &SimulationConfig,
    samples: &[TrajectorySample],
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    if case.parameters.roughness_model != RoughnessModel::StochasticContactV1 {
        return Ok(());
    }
    if case.parameters.roughness_std_normal != 0.0
        || case.parameters.roughness_std_tangent != 0.0
        || case.parameters.roughness_std_angle != 0.0
    {
        return Ok(());
    }

    let mut baseline = config.clone();
    baseline.roughness_model = RoughnessModel::None;
    baseline.roughness_std_normal = 0.0;
    baseline.roughness_std_tangent = 0.0;
    baseline.roughness_std_angle = 0.0;
    let baseline_result = baseline.run()?;
    metrics.insert(
        "roughness_zero_baseline_max_position_delta_m".to_string(),
        max_position_delta(samples, &baseline_result.samples),
    );
    Ok(())
}

pub(super) fn compute_scarring_comparison_metrics(
    case: &BenchmarkCase,
    config: &SimulationConfig,
    samples: &[TrajectorySample],
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    if case.parameters.soil_interaction_model != SoilInteractionModel::ScarringContactV1 {
        return Ok(());
    }
    if case.parameters.soil_strength_pa != 0.0
        || case.parameters.scarring_drag_coefficient != 0.0
        || case.parameters.scarring_layer_density_kgpm3 != 0.0
        || case.parameters.scarring_max_depth_m.unwrap_or(0.0) != 0.0
    {
        return Ok(());
    }

    let mut baseline = config.clone();
    baseline.soil_interaction_model = SoilInteractionModel::None;
    baseline.soil_strength_pa = 0.0;
    baseline.scarring_drag_coefficient = 0.0;
    baseline.scarring_layer_density_kgpm3 = 0.0;
    baseline.scarring_max_depth_m = None;
    let baseline_result = baseline.run()?;
    metrics.insert(
        "scarring_zero_baseline_max_position_delta_m".to_string(),
        max_position_delta(samples, &baseline_result.samples),
    );
    Ok(())
}

pub(super) fn evaluate_failures(
    last: &TrajectorySample,
    metrics: &BTreeMap<String, f64>,
    expected: &ExpectedConfig,
) -> Vec<String> {
    let mut failures = Vec::new();
    for (metric, tolerance) in &expected.tolerances {
        if let Some(value) = metrics.get(metric) {
            if value > tolerance {
                failures.push(format!("{metric}={value} exceeds tolerance {tolerance}"));
            }
        }
    }

    for (metric, target) in &expected.values {
        if let Some(value) = metrics.get(metric) {
            let tolerance = expected.tolerances.get(metric).copied().unwrap_or(0.0);
            if (value - target).abs() > tolerance {
                failures.push(format!(
                    "{metric}={value} differs from target {target} by more than tolerance {tolerance}"
                ));
            }
        }
    }

    for (metric, minimum) in &expected.minimums {
        if metrics.get(metric).copied().unwrap_or_default() < *minimum {
            failures.push(format!("{metric} below minimum {minimum}"));
        }
    }

    for (metric, maximum) in &expected.maximums {
        if metrics.get(metric).copied().unwrap_or(f64::INFINITY) > *maximum {
            failures.push(format!("{metric} above maximum {maximum}"));
        }
    }

    if let Some(contact_state) = expected.contact_state {
        if last.contact_state != contact_state {
            failures.push(format!(
                "final contact_state={:?}, expected {:?}",
                last.contact_state, contact_state
            ));
        }
    }
    if let Some(min_runout) = expected.min_runout_m {
        if metrics.get("runout_m").copied().unwrap_or_default() < min_runout {
            failures.push(format!("runout_m below minimum {min_runout}"));
        }
    }
    if let Some(max_runout) = expected.max_runout_m {
        if metrics.get("runout_m").copied().unwrap_or_default() > max_runout {
            failures.push(format!("runout_m above maximum {max_runout}"));
        }
    }
    if let Some(min_impacts) = expected.min_impact_count {
        if metrics.get("impact_count").copied().unwrap_or_default() < min_impacts as f64 {
            failures.push(format!("impact_count below minimum {min_impacts}"));
        }
    }
    if let Some(max_impacts) = expected.max_impact_count {
        if metrics.get("impact_count").copied().unwrap_or_default() > max_impacts as f64 {
            failures.push(format!("impact_count above maximum {max_impacts}"));
        }
    }

    failures
}
