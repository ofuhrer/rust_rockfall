use super::*;

pub(super) fn run_case_file(path: impl AsRef<Path>) -> Result<CaseReport, ValidationError> {
    let case = load_case(path)?;
    run_case(&case)
}

pub(super) fn run_case(case: &BenchmarkCase) -> Result<CaseReport, ValidationError> {
    let total_started = Instant::now();
    let mut timing = RuntimeTiming::default();
    let mut warnings = Vec::new();
    let mut output_entries = Vec::new();
    let mut stop_state_summary = None;
    let mut terrain_material_exposure_summary = None;
    let load_started = Instant::now();
    let terrain_source = load_terrain_source_metadata(case)?;
    let release_zone_source = load_release_zone_metadata(case, terrain_source.as_ref())?;
    let terrain_class_map = load_terrain_class_map(case, terrain_source.as_ref())?;
    let shape_metadata = load_block_shape_metadata(case)?;
    let probabilistic_metadata =
        load_probabilistic_metadata_context(case, release_zone_source.as_ref())?;
    let mut trajectory_metadata =
        TrajectoryMetadataCollector::with_probabilistic_metadata(probabilistic_metadata.clone());
    let mut ensemble_execution = None;
    timing.terrain_load_seconds += load_started.elapsed().as_secs_f64();
    let mut release_zone_manifest = release_zone_source
        .as_ref()
        .map(|source| release_zone_manifest(case.release_zone.as_ref(), source, 0));
    let terrain_class_manifest = terrain_class_map
        .as_ref()
        .map(|class_map| terrain_class_manifest(case.terrain_classes.as_ref(), class_map))
        .transpose()?;
    let observations = match load_observations(case, &mut warnings)? {
        ObservationLoad::Loaded(data) => data,
        ObservationLoad::MissingRequired(path) => {
            let report = skipped_report(
                case,
                format!(
                    "observation file is not available: {}; run scripts/download_datasets.py and scripts/preprocess_datasets.py for public data cases",
                    path.display()
                ),
            )?;
            if let Some(path) = &case.outputs.diagnostics_json {
                let output_started = Instant::now();
                write_report(path, &report)?;
                timing.output_write_seconds += output_started.elapsed().as_secs_f64();
                output_entries.push(file_output_manifest(
                    path,
                    "diagnostics",
                    "json",
                    Some(report.metrics.len()),
                    None,
                )?);
            }
            if let Some(path) = &case.outputs.manifest_json {
                timing.total_wall_seconds = total_started.elapsed().as_secs_f64();
                let performance = timing.to_manifest(&output_entries);
                write_run_manifest(
                    path,
                    RunManifestContext {
                        case,
                        report: &report,
                        outputs: output_entries,
                        terrain_source: terrain_source.as_ref(),
                        release_zone: release_zone_manifest.as_ref(),
                        terrain_classes: terrain_class_manifest.as_ref(),
                        shape_metadata: shape_metadata.as_ref(),
                        trajectory_metadata: None,
                        ensemble_execution: None,
                        performance,
                        stop_state_summary: None,
                        terrain_material_exposure_summary: None,
                    },
                )?;
            }
            return Ok(report);
        }
    };
    if case.validation_scope.is_some() && lacks_acceptance_thresholds(&case.expected) {
        warnings.push(
            "real-world validation case has no pass/fail acceptance thresholds; passed means the workflow completed and reported metrics".to_string(),
        );
    }
    if shape_metadata.is_some() {
        warnings.push(PASSIVE_SHAPE_WARNING.to_string());
    }

    let config = build_simulation_config(case)?;
    let terrain_started = Instant::now();
    let terrain = config.terrain.build()?;
    timing.terrain_load_seconds += terrain_started.elapsed().as_secs_f64();
    let class_provider = terrain_class_map
        .as_ref()
        .map(|class_map| class_map as &dyn ContactParameterProvider);
    let simulation_started = Instant::now();
    let mut result =
        config.run_with_terrain_and_contact_parameters(terrain.as_ref(), class_provider)?;
    annotate_result_terrain_material_context(&mut result, terrain_class_map.as_ref());
    timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
    timing.trajectory_count += 1;
    timing.impact_event_count += result.impact_events.len();
    trajectory_metadata.insert_single_result(case, &result, &config.block, shape_metadata.as_ref());
    if validation_output_mode_writes_builder_facing_outputs(case) {
        if let Some(path) = &case.outputs.trajectory_csv {
            let output_started = Instant::now();
            write_trajectory_csv_with_id(path, default_single_trajectory_id(), &result.samples)?;
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
            output_entries.push(file_output_manifest(
                path,
                "trajectory",
                "csv",
                Some(result.samples.len()),
                None,
            )?);
        }
        if let Some(path) = &case.outputs.impact_events_csv {
            let output_started = Instant::now();
            write_impact_events_csv_with_id(
                path,
                default_single_trajectory_id(),
                &result.impact_events,
            )?;
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
            let impact_events_kind = if validation_output_mode_is_rebuildable_reduced_output(case) {
                "impact_events_csv"
            } else {
                "impact_events"
            };
            output_entries.push(file_output_manifest(
                path,
                impact_events_kind,
                "csv",
                Some(result.impact_events.len()),
                None,
            )?);
        }
        if validation_output_mode_writes_debug_outputs(case) {
            if let Some(path) = &case.outputs.impact_events_json {
                let output_started = Instant::now();
                io::write_impact_events_json(path, &result.impact_events)?;
                timing.output_write_seconds += output_started.elapsed().as_secs_f64();
                output_entries.push(file_output_manifest(
                    path,
                    "impact_events",
                    "json",
                    Some(result.impact_events.len()),
                    None,
                )?);
            }
        }
    }

    let samples = &result.samples;
    let first = samples
        .first()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;
    let last = samples
        .last()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;

    let mut metrics = compute_metrics(MetricContext {
        samples,
        impact_events: &result.impact_events,
        first,
        last,
        terrain: terrain.as_ref(),
        block: &config.block,
        observations: &observations.deposition_points,
        expected: &case.expected,
    });
    compute_ensemble_metrics(EnsembleMetricContext {
        case,
        contact_parameters: class_provider,
        terrain_class_map: terrain_class_map.as_ref(),
        metrics: &mut metrics,
        warnings: &mut warnings,
        output_entries: &mut output_entries,
        timing: &mut timing,
        trajectory_metadata: &mut trajectory_metadata,
        shape_metadata: shape_metadata.as_ref(),
        stop_state_summary: &mut stop_state_summary,
        terrain_material_exposure_summary: &mut terrain_material_exposure_summary,
        ensemble_execution: &mut ensemble_execution,
    })?;
    compute_validation_ensemble_metrics(ValidationEnsembleContext {
        case,
        base_config: &config,
        contact_parameters: class_provider,
        terrain_class_map: terrain_class_map.as_ref(),
        observations: &observations,
        metrics: &mut metrics,
        warnings: &mut warnings,
        output_entries: &mut output_entries,
        timing: &mut timing,
        trajectory_metadata: &mut trajectory_metadata,
        shape_metadata: shape_metadata.as_ref(),
        stop_state_summary: &mut stop_state_summary,
        terrain_material_exposure_summary: &mut terrain_material_exposure_summary,
    })?;
    if let Some(source) = release_zone_source.as_ref() {
        release_zone_manifest = compute_release_zone_metrics(ReleaseZoneMetricContext {
            case,
            base_config: &config,
            contact_parameters: class_provider,
            terrain_class_map: terrain_class_map.as_ref(),
            release_zone: source,
            observations: &observations,
            metrics: &mut metrics,
            warnings: &mut warnings,
            output_entries: &mut output_entries,
            timing: &mut timing,
            trajectory_metadata: &mut trajectory_metadata,
            shape_metadata: shape_metadata.as_ref(),
            stop_state_summary: &mut stop_state_summary,
            terrain_material_exposure_summary: &mut terrain_material_exposure_summary,
        })?;
    }
    compute_observed_trajectory_metrics(
        case,
        &config,
        class_provider,
        &observations,
        &mut metrics,
    )?;
    compute_observed_contact_metrics(case, &config, class_provider, &observations, &mut metrics)?;
    compute_roughness_comparison_metrics(case, &config, samples, &mut metrics)?;
    compute_scarring_comparison_metrics(case, &config, samples, &mut metrics)?;

    let requested_metrics = requested_metrics(case);
    if !requested_metrics.is_empty() {
        metrics.retain(|name, _| requested_metrics.iter().any(|requested| requested == name));
    }

    let failures = evaluate_failures(last, &metrics, &case.expected);
    let status = if failures.is_empty() {
        CaseStatus::Passed
    } else {
        CaseStatus::Failed
    };
    let execution_status = execution_status_for_case_status(status);
    let scientific_status = scientific_status_for_case(case, status);

    let report = CaseReport {
        case_id: case.case_id.clone(),
        status,
        execution_status,
        scientific_status,
        timestamp_unix_s: now_unix_s(),
        model_version: env!("CARGO_PKG_VERSION").to_string(),
        git_hash: git_hash(),
        metrics,
        tolerances: case.expected.tolerances.clone(),
        failures,
        warnings,
        parameters: config,
        stop_state: result.stop_state.clone(),
    };

    let trajectory_metadata_manifest = if let Some(path) = &case.outputs.trajectory_metadata_csv {
        let rows = trajectory_metadata.rows();
        let output_started = Instant::now();
        write_trajectory_metadata_csv(path, &rows)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "trajectory_metadata",
            "csv",
            Some(rows.len()),
            None,
        )?);
        Some(TrajectoryMetadataManifest {
            schema_version: TRAJECTORY_METADATA_SCHEMA_VERSION.to_string(),
            path: path.to_string_lossy().to_string(),
            row_count: rows.len(),
            probability_model: probabilistic_metadata
                .as_ref()
                .map(|metadata| legacy_probability_model(metadata.probability_mode).to_string())
                .unwrap_or_else(|| default_probability_model().to_string()),
            probability_semantics: probabilistic_metadata
                .as_ref()
                .map(|_| "scenario_table_v1".to_string())
                .unwrap_or_else(|| "sampling_weight_only".to_string()),
            normalization_convention: probabilistic_metadata
                .as_ref()
                .map(|metadata| normalization_scope_text(metadata.normalization_scope).to_string())
                .unwrap_or_else(|| "unweighted_current_outputs".to_string()),
            total_sampling_weight: rows.iter().map(|row| row.sampling_weight).sum(),
            map_product_id: probabilistic_metadata
                .as_ref()
                .map(|metadata| metadata.map_product_id.clone()),
            source_zone_id: probabilistic_metadata
                .as_ref()
                .map(|metadata| metadata.source_zone_id.clone()),
            source_zone_metadata_path: probabilistic_metadata.as_ref().map(|metadata| {
                metadata
                    .source_zone_metadata_path
                    .to_string_lossy()
                    .to_string()
            }),
            scenario_table_path: probabilistic_metadata
                .as_ref()
                .map(|metadata| metadata.scenario_table_path.to_string_lossy().to_string()),
            scenario_id: probabilistic_metadata
                .as_ref()
                .map(|metadata| metadata.scenario.scenario_id.clone()),
            probability_mode: probabilistic_metadata
                .as_ref()
                .map(|metadata| probability_mode_text(metadata.probability_mode).to_string()),
            normalization_scope: probabilistic_metadata
                .as_ref()
                .map(|metadata| normalization_scope_text(metadata.normalization_scope).to_string()),
        })
    } else {
        None
    };

    if let Some(path) = &case.outputs.diagnostics_json {
        let output_started = Instant::now();
        write_report(path, &report)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "diagnostics",
            "json",
            Some(report.metrics.len()),
            None,
        )?);
    }

    if let Some(path) = &case.outputs.manifest_json {
        timing.total_wall_seconds = total_started.elapsed().as_secs_f64();
        let performance = timing.to_manifest(&output_entries);
        write_run_manifest(
            path,
            RunManifestContext {
                case,
                report: &report,
                outputs: output_entries,
                terrain_source: terrain_source.as_ref(),
                release_zone: release_zone_manifest.as_ref(),
                terrain_classes: terrain_class_manifest.as_ref(),
                shape_metadata: shape_metadata.as_ref(),
                trajectory_metadata: trajectory_metadata_manifest,
                ensemble_execution,
                performance,
                stop_state_summary,
                terrain_material_exposure_summary,
            },
        )?;
    }

    Ok(report)
}

pub(super) fn write_report(
    path: impl AsRef<Path>,
    report: &CaseReport,
) -> Result<(), ValidationError> {
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, serde_json::to_string_pretty(report)?)?;
    Ok(())
}

pub(super) fn write_run_manifest(
    path: impl AsRef<Path>,
    context: RunManifestContext<'_>,
) -> Result<(), ValidationError> {
    let manifest = build_run_manifest(context);
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, serde_json::to_string_pretty(&manifest)?)?;
    Ok(())
}

pub(super) fn build_run_manifest(context: RunManifestContext<'_>) -> RunManifest {
    let RunManifestContext {
        case,
        report,
        outputs,
        terrain_source,
        release_zone,
        terrain_classes,
        shape_metadata,
        trajectory_metadata,
        ensemble_execution,
        performance,
        stop_state_summary,
        terrain_material_exposure_summary,
    } = context;
    RunManifest {
        schema_version: RUN_MANIFEST_SCHEMA_VERSION.to_string(),
        created_unix_s: report.timestamp_unix_s,
        case_id: case.case_id.clone(),
        model_version: report.model_version.clone(),
        git_hash: report.git_hash.clone(),
        config_fingerprint: report.parameters.config_fingerprint().ok(),
        completion_status: case_status_text(report.status).to_string(),
        execution_status: execution_status_text(report.execution_status).to_string(),
        scientific_status: scientific_status_text(report.scientific_status).to_string(),
        seed_policy: SeedPolicyManifest {
            global_seed: case.random.seed,
            ensemble_size: case.random.ensemble_size.max(1),
            derivation:
                "single trajectories use random.seed directly; ensembles derive trajectory seeds from global seed, case ID, and trajectory ID"
                    .to_string(),
        },
        terrain: terrain_manifest(&case.terrain, terrain_source),
        release_zone: release_zone.cloned(),
        terrain_classes: terrain_classes.cloned(),
        shape_metadata: shape_metadata.map(|metadata| shape_metadata_manifest(case, metadata)),
        trajectory_metadata,
        ensemble_execution,
        outputs,
        performance: Some(performance),
        stop_state: report.stop_state.clone(),
        stop_state_summary,
        terrain_material_exposure_summary,
        validation_output_mode: case.outputs.validation_output_mode,
        warnings: report.warnings.clone(),
    }
}

fn case_status_text(status: CaseStatus) -> &'static str {
    match status {
        CaseStatus::Passed => "passed",
        CaseStatus::Failed => "failed",
        CaseStatus::Skipped => "skipped",
    }
}

pub(super) fn execution_status_for_case_status(status: CaseStatus) -> ExecutionStatus {
    match status {
        CaseStatus::Passed => ExecutionStatus::Completed,
        CaseStatus::Failed => ExecutionStatus::Failed,
        CaseStatus::Skipped => ExecutionStatus::Skipped,
    }
}

pub(super) fn scientific_status_for_case(
    case: &BenchmarkCase,
    status: CaseStatus,
) -> ScientificStatus {
    if status == CaseStatus::Skipped {
        return ScientificStatus::NotEvaluated;
    }
    if status == CaseStatus::Failed {
        return ScientificStatus::FailsAcceptanceThresholds;
    }
    if case.validation_scope.is_some() && lacks_acceptance_thresholds(&case.expected) {
        return ScientificStatus::ReportedWithoutAcceptanceThresholds;
    }
    if has_acceptance_thresholds(&case.expected) {
        ScientificStatus::MeetsAcceptanceThresholds
    } else {
        ScientificStatus::NotEvaluated
    }
}

fn execution_status_text(status: ExecutionStatus) -> &'static str {
    match status {
        ExecutionStatus::Completed => "completed",
        ExecutionStatus::Failed => "failed",
        ExecutionStatus::Skipped => "skipped",
    }
}

fn scientific_status_text(status: ScientificStatus) -> &'static str {
    match status {
        ScientificStatus::MeetsAcceptanceThresholds => "meets_acceptance_thresholds",
        ScientificStatus::FailsAcceptanceThresholds => "fails_acceptance_thresholds",
        ScientificStatus::ReportedWithoutAcceptanceThresholds => {
            "reported_without_acceptance_thresholds"
        }
        ScientificStatus::NotEvaluated => "not_evaluated",
    }
}
