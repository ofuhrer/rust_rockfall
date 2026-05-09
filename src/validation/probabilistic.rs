use super::*;

pub(super) fn load_probabilistic_metadata_context(
    case: &BenchmarkCase,
    release_zone: Option<&ReleaseZoneMetadata>,
) -> Result<Option<ProbabilisticMetadataContext>, ValidationError> {
    let Some(config) = &case.probabilistic_metadata else {
        return Ok(None);
    };
    let source_zone_metadata_path = required_probabilistic_path(
        config.source_zone_metadata_path.as_ref(),
        "source_zone_metadata_path",
    )?;
    let scenario_table_path =
        required_probabilistic_path(config.scenario_table_path.as_ref(), "scenario_table_path")?;
    let map_product_id =
        required_probabilistic_id(config.map_product_id.as_deref(), "map_product_id")?;
    let probability_mode = config.probability_mode.ok_or_else(|| {
        ValidationError::Case("probabilistic_metadata.probability_mode is required".to_string())
    })?;
    let normalization_scope = config.normalization_scope.ok_or_else(|| {
        ValidationError::Case("probabilistic_metadata.normalization_scope is required".to_string())
    })?;

    let source_zone = SourceZoneMetadata::from_yaml_file(&source_zone_metadata_path)?;
    if source_zone.annual_release_frequency_per_year.is_some() {
        return Err(ValidationError::Case(
            "probabilistic_metadata source-zone annual_release_frequency_per_year is Level 3 and must remain null in Phase 1".to_string(),
        ));
    }
    if let Some(release_zone) = release_zone {
        if release_zone.zone_id != source_zone.source_zone_id {
            return Err(ValidationError::Case(format!(
                "probabilistic_metadata source_zone_id '{}' does not match release-zone id '{}'",
                source_zone.source_zone_id, release_zone.zone_id
            )));
        }
    }

    let scenario_table = ScenarioTable::from_csv_file(&scenario_table_path)?;
    let package = MapPackageManifest {
        schema_version: MAP_PACKAGE_MANIFEST_SCHEMA_VERSION.to_string(),
        map_product_id: map_product_id.clone(),
        map_product_version: None,
        probability_mode,
        normalization_scope: Some(normalization_scope),
        source_zone_id: source_zone.source_zone_id.clone(),
        source_zone_metadata_path: source_zone_metadata_path.clone(),
        scenario_table_path: Some(scenario_table_path.clone()),
        hazard_manifest_paths: Vec::new(),
        raster_outputs: Vec::new(),
        layer_semantics: Vec::new(),
        validation_context: Vec::new(),
        limitations: Vec::new(),
        operational_status: None,
    };
    package.validate_with_metadata(&source_zone, Some(&scenario_table))?;
    let scenario = select_probabilistic_scenario(config.scenario_id.as_deref(), &scenario_table)?;

    Ok(Some(ProbabilisticMetadataContext {
        map_product_id,
        source_zone_metadata_path: source_zone_metadata_path.clone(),
        scenario_table_path: scenario_table_path.clone(),
        source_zone_id: source_zone.source_zone_id,
        scenario,
        probability_mode,
        normalization_scope,
    }))
}

fn required_probabilistic_path(
    value: Option<&PathBuf>,
    field: &str,
) -> Result<PathBuf, ValidationError> {
    value.cloned().ok_or_else(|| {
        ValidationError::Case(format!(
            "probabilistic_metadata.{field} is required for Phase 1 metadata propagation"
        ))
    })
}

fn required_probabilistic_id(value: Option<&str>, field: &str) -> Result<String, ValidationError> {
    let value = value.unwrap_or_default().trim();
    if value.is_empty() {
        return Err(ValidationError::Case(format!(
            "probabilistic_metadata.{field} is required for Phase 1 metadata propagation"
        )));
    }
    Ok(value.to_string())
}

fn select_probabilistic_scenario(
    scenario_id: Option<&str>,
    scenario_table: &ScenarioTable,
) -> Result<ScenarioRow, ValidationError> {
    if let Some(scenario_id) = scenario_id {
        return scenario_table
            .rows
            .iter()
            .find(|row| row.scenario_id == scenario_id)
            .cloned()
            .ok_or_else(|| {
                ValidationError::Case(format!(
                    "probabilistic_metadata.scenario_id '{scenario_id}' was not found in scenario_table_v1"
                ))
            });
    }
    if scenario_table.rows.len() == 1 {
        return Ok(scenario_table.rows[0].clone());
    }
    Err(ValidationError::Case(
        "probabilistic_metadata.scenario_id is required when scenario_table_v1 contains multiple rows".to_string(),
    ))
}
