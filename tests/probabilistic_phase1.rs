use rust_rockfall::probabilistic::{
    MapPackageManifest, NormalizationScope, ProbabilityMode, ScenarioTable, SourceZoneMetadata,
};
use std::path::Path;

const FIXTURE_ROOT: &str = "tests/fixtures/probabilistic_phase1";

#[test]
fn source_zone_metadata_v1_parses_and_validates() {
    let metadata =
        SourceZoneMetadata::from_yaml_file(Path::new(FIXTURE_ROOT).join("source_zone_valid.yaml"))
            .unwrap();
    assert_eq!(metadata.schema_version, "source_zone_metadata_v1");
    assert_eq!(metadata.source_zone_id, "zone_a");
    assert_eq!(metadata.crs_epsg, 2056);
    assert_eq!(metadata.vertical_datum, "LN02");
    assert_eq!(metadata.geometry.vertices.len(), 4);
    assert_eq!(metadata.release_sampling_policy.release_count, Some(4));
    assert!(metadata.annual_release_frequency_per_year.is_none());
}

#[test]
fn scenario_table_v1_parses_level1_and_level2_rows() {
    let level1 =
        ScenarioTable::from_csv_file(Path::new(FIXTURE_ROOT).join("scenario_level1.csv")).unwrap();
    assert_eq!(level1.schema_version, "scenario_table_v1");
    assert_eq!(level1.rows.len(), 1);
    assert_eq!(level1.rows[0].scenario_id, "scenario_a");
    assert_eq!(level1.total_sampling_weight(), 1.0);

    let level2 =
        ScenarioTable::from_csv_file(Path::new(FIXTURE_ROOT).join("scenario_level2_weighted.csv"))
            .unwrap();
    assert_eq!(level2.rows.len(), 2);
    assert_eq!(level2.total_sampling_weight(), 1.0);
    assert_eq!(
        level2.rows[1].model_configuration_id,
        "sphere_rotational_v1"
    );
}

#[test]
fn map_package_manifest_validates_against_source_zone_and_scenario_table() {
    let source =
        SourceZoneMetadata::from_yaml_file(Path::new(FIXTURE_ROOT).join("source_zone_valid.yaml"))
            .unwrap();
    let scenario =
        ScenarioTable::from_csv_file(Path::new(FIXTURE_ROOT).join("scenario_level2_weighted.csv"))
            .unwrap();
    let package = MapPackageManifest::from_file(
        Path::new(FIXTURE_ROOT).join("map_package_level2_valid.json"),
    )
    .unwrap();

    assert_eq!(
        package.probability_mode,
        ProbabilityMode::SamplingWeightedConditional
    );
    assert_eq!(
        package.normalization_scope,
        Some(NormalizationScope::ConditionedOnFilter)
    );
    package
        .validate_with_metadata(&source, Some(&scenario))
        .unwrap();
}

#[test]
fn level1_conditional_package_accepts_equal_sampling_weights() {
    let source =
        SourceZoneMetadata::from_yaml_file(Path::new(FIXTURE_ROOT).join("source_zone_valid.yaml"))
            .unwrap();
    let scenario =
        ScenarioTable::from_csv_file(Path::new(FIXTURE_ROOT).join("scenario_level1.csv")).unwrap();
    let package = MapPackageManifest::from_file(
        Path::new(FIXTURE_ROOT).join("map_package_level1_valid.json"),
    )
    .unwrap();

    assert_eq!(
        package.normalization_scope,
        Some(NormalizationScope::ConditionedOnScenario)
    );
    package
        .validate_with_metadata(&source, Some(&scenario))
        .unwrap();
}

#[test]
fn annual_frequency_mode_is_rejected_in_phase1() {
    let source =
        SourceZoneMetadata::from_yaml_file(Path::new(FIXTURE_ROOT).join("source_zone_valid.yaml"))
            .unwrap();
    let scenario =
        ScenarioTable::from_csv_file(Path::new(FIXTURE_ROOT).join("scenario_level1.csv")).unwrap();
    let package = MapPackageManifest::from_file(
        Path::new(FIXTURE_ROOT).join("map_package_annual_invalid.json"),
    )
    .unwrap();

    let error = package
        .validate_with_metadata(&source, Some(&scenario))
        .unwrap_err()
        .to_string();
    assert!(error.contains("Level 3"));
}

#[test]
fn negative_sampling_weight_is_rejected() {
    let error = ScenarioTable::from_csv_file(
        Path::new(FIXTURE_ROOT).join("scenario_negative_weight_invalid.csv"),
    )
    .unwrap_err()
    .to_string();
    assert!(error.contains("sampling_weight"));
}

#[test]
fn source_zone_mismatch_between_sidecar_scenario_and_package_is_rejected() {
    let source =
        SourceZoneMetadata::from_yaml_file(Path::new(FIXTURE_ROOT).join("source_zone_valid.yaml"))
            .unwrap();
    let scenario = ScenarioTable::from_csv_file(
        Path::new(FIXTURE_ROOT).join("scenario_source_zone_mismatch_invalid.csv"),
    )
    .unwrap();
    let package = MapPackageManifest::from_file(
        Path::new(FIXTURE_ROOT).join("map_package_level2_valid.json"),
    )
    .unwrap();

    let error = package
        .validate_with_metadata(&source, Some(&scenario))
        .unwrap_err()
        .to_string();
    assert!(error.contains("source_zone_id"));
}

#[test]
fn physical_probability_requires_explicit_probability_columns() {
    let source =
        SourceZoneMetadata::from_yaml_file(Path::new(FIXTURE_ROOT).join("source_zone_valid.yaml"))
            .unwrap();
    let scenario =
        ScenarioTable::from_csv_file(Path::new(FIXTURE_ROOT).join("scenario_level1.csv")).unwrap();
    let package = MapPackageManifest::from_file(
        Path::new(FIXTURE_ROOT).join("map_package_physical_invalid.json"),
    )
    .unwrap();

    let error = package
        .validate_with_metadata(&source, Some(&scenario))
        .unwrap_err()
        .to_string();
    assert!(error.contains("release_probability") || error.contains("scenario_probability"));
}

#[test]
fn existing_diagnostic_hazard_layer_names_are_not_relabelled_probabilistic() {
    let package = MapPackageManifest::from_yaml_str(
        r#"schema_version: map_package_manifest_v1
map_product_id: diagnostic_fixture
probability_mode: unweighted_diagnostic
source_zone_id: zone_a
source_zone_metadata_path: tests/fixtures/probabilistic_phase1/source_zone_valid.yaml
layer_semantics:
  - layer_name: reach_probability
    units: fraction_of_trajectories
    conditioned_on: []
    is_annualized: false
"#,
    )
    .unwrap();
    assert_eq!(
        package.probability_mode,
        ProbabilityMode::UnweightedDiagnostic
    );

    let bad = MapPackageManifest::from_yaml_str(
        r#"schema_version: map_package_manifest_v1
map_product_id: bad_diagnostic_fixture
probability_mode: unweighted_diagnostic
source_zone_id: zone_a
source_zone_metadata_path: tests/fixtures/probabilistic_phase1/source_zone_valid.yaml
layer_semantics:
  - layer_name: annual_reach_frequency
    units: 1/year
    conditioned_on: []
    is_annualized: true
"#,
    )
    .unwrap_err()
    .to_string();
    assert!(bad.contains("annual"));
}
