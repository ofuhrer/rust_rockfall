use approx::assert_abs_diff_eq;
use rust_rockfall::{
    geodata::{ReleaseZoneMetadata, TerrainClassMap, TerrainClassMetadata, TerrainSourceMetadata},
    geometry::SphereBlock,
    io,
    manifest::RunManifest,
    shape::{
        box_principal_moments_kg_m2, ellipsoid_principal_moments_kg_m2, select_box_support_point,
        shape_contact_v0_energy_diagnostic, sphere_principal_moments_kg_m2, BlockShapeMetadata,
        BlockShapeType, ShapeContactV0Scaffold,
    },
    simulation::{SimulationConfig, SimulationError, TerrainConfig},
    state::{BodyState, ContactState},
    stochastic::{ReleasePerturbation, RoughnessModel},
    terrain::{
        ChannelizedGully, ClampedDemGrid, DemGrid, GaussianBump, Paraboloid, Plane,
        SinusoidalRoughSlope, StepTerrain, TerracedSlope, Terrain, TerrainError, VShapedValley,
    },
    validation::{load_case, run_case_file, CaseStatus, ScientificStatus},
    ContactModel, ContactParameterProvider, ContactParameters, ScarringSettings,
    SoilInteractionModel, Vec3,
};

#[test]
fn run_manifest_without_performance_section_remains_backward_compatible() {
    let text = r#"{
      "schema_version": "run_manifest_v1",
      "created_unix_s": 1,
      "case_id": "legacy_manifest",
      "model_version": "0.5.0",
      "git_hash": null,
      "config_fingerprint": null,
      "completion_status": "passed",
      "seed_policy": {
        "global_seed": null,
        "ensemble_size": 1,
        "derivation": "legacy"
      },
      "terrain": {
        "terrain_type": "plane",
        "path": null,
        "metadata_path": null,
        "crs": null,
        "epsg": null,
        "vertical_datum": null,
        "resolution_m": null,
        "extent": null,
        "nodata": null,
        "source_dataset": null,
        "source_product": null,
        "source_url": null,
        "source_filename": null,
        "license": null,
        "download_status": null,
        "preprocessing_status": null,
        "raw_sha256": null,
        "processed_sha256": null,
        "provenance_notes": []
      },
      "release_zone": null,
      "terrain_classes": null,
      "outputs": [],
      "warnings": []
    }"#;
    let manifest: RunManifest = serde_json::from_str(text).unwrap();
    assert_eq!(manifest.case_id, "legacy_manifest");
    assert!(manifest.trajectory_metadata.is_none());
    assert!(manifest.shape_metadata.is_none());
    assert!(manifest.performance.is_none());
    assert!(manifest.stop_state.is_none());
    assert!(manifest.stop_state_summary.is_none());

    let text_with_legacy_metadata = text.replace(
        "\"terrain_classes\": null,\n      \"outputs\": []",
        "\"terrain_classes\": null,\n      \"trajectory_metadata\": {\n        \"schema_version\": \"trajectory_metadata_table_v1\",\n        \"path\": \"metadata.csv\",\n        \"row_count\": 2,\n        \"total_sampling_weight\": 2.0\n      },\n      \"outputs\": []",
    );
    let manifest: RunManifest = serde_json::from_str(&text_with_legacy_metadata).unwrap();
    let metadata = manifest.trajectory_metadata.unwrap();
    assert_eq!(metadata.probability_model, "unweighted");
    assert_eq!(metadata.probability_semantics, "sampling_weight_only");
}

#[test]
fn shape_metadata_parses_and_computes_mass_properties() {
    let path = temp_path("shape_metadata.yaml");
    fs::write(
        &path,
        r#"schema_version: shape_metadata_v1
shape_id: ellipsoid_test
shape_type: ellipsoid
shape_class: elongated
dimensions_m:
  semi_axes_m: [0.5, 0.25, 0.125]
  equivalent_radius_m: 0.5
mass_properties:
  mass_kg: 10.0
  density_kgpm3: 100.0
orientation:
  representation: quaternion_wxyz
  initialization_mode: fixed_quaternion
  initial_quaternion_wxyz: [0.0, 1.0, 0.0, 0.0]
provenance:
  source_dataset: synthetic_shape_fixture
  license: MIT
  notes: ["test fixture"]
"#,
    )
    .unwrap();

    let metadata = BlockShapeMetadata::from_yaml_file(&path).unwrap();
    assert_eq!(metadata.shape_id, "ellipsoid_test");
    assert_eq!(metadata.shape_class_or_default(), "elongated");
    let moments = metadata.computed_principal_moments_kg_m2().unwrap();
    let expected = ellipsoid_principal_moments_kg_m2(10.0, [0.5, 0.25, 0.125]);
    assert_abs_diff_eq!(moments[0], expected[0], epsilon = 1.0e-12);
    assert_abs_diff_eq!(
        sphere_principal_moments_kg_m2(10.0, 0.5)[0],
        1.0,
        epsilon = 1.0e-12
    );
    assert_abs_diff_eq!(
        box_principal_moments_kg_m2(12.0, [1.0, 2.0, 3.0])[0],
        13.0,
        epsilon = 1.0e-12
    );
    fs::remove_file(path).unwrap();
}

#[test]
fn shape_metadata_rejects_invalid_dimensions_inertia_and_quaternion() {
    let invalid_dimension = serde_yaml::from_str::<BlockShapeMetadata>(
        r#"schema_version: shape_metadata_v1
shape_id: bad_dimension
shape_type: box
dimensions_m:
  side_lengths_m: [1.0, 0.0, 2.0]
mass_properties:
  mass_kg: 10.0
"#,
    )
    .unwrap();
    assert!(invalid_dimension.validate().is_err());

    let invalid_quaternion = serde_yaml::from_str::<BlockShapeMetadata>(
        r#"schema_version: shape_metadata_v1
shape_id: bad_quaternion
shape_type: sphere
dimensions_m:
  radius_m: 0.5
mass_properties:
  mass_kg: 10.0
orientation:
  representation: quaternion_wxyz
  initialization_mode: fixed_quaternion
  initial_quaternion_wxyz: [1.0, 1.0, 0.0, 0.0]
"#,
    )
    .unwrap();
    assert!(invalid_quaternion.validate().is_err());

    let invalid_inertia = serde_yaml::from_str::<BlockShapeMetadata>(
        r#"schema_version: shape_metadata_v1
shape_id: bad_inertia
shape_type: custom_principal_moments
dimensions_m:
  equivalent_radius_m: 0.5
mass_properties:
  mass_kg: 10.0
  principal_moments_kg_m2: [1.0, -1.0, 2.0]
"#,
    )
    .unwrap();
    assert!(invalid_inertia.validate().is_err());
}

#[test]
fn tschamut_public_shape_sidecars_validate_against_block_metadata() {
    let cases = [
        (
            "data/processed/tschamut2014/shape_metadata/block_1_st_leonard.yaml",
            "tschamut2014_block_1_st_leonard",
            69.0,
            0.176667,
            [0.37, 0.32, 0.37],
        ),
        (
            "data/processed/tschamut2014/shape_metadata/block_2_most_heavy.yaml",
            "tschamut2014_block_2_most_heavy",
            79.0,
            0.198333,
            [0.5, 0.3, 0.39],
        ),
        (
            "data/processed/tschamut2014/shape_metadata/block_4_plate.yaml",
            "tschamut2014_block_4_plate",
            40.0,
            0.16,
            [0.46, 0.3, 0.2],
        ),
    ];

    for (path, shape_id, mass_kg, radius_m, lengths_m) in cases {
        let metadata = BlockShapeMetadata::from_yaml_file(path).unwrap();
        assert_eq!(metadata.shape_id, shape_id);
        assert_eq!(metadata.shape_type, BlockShapeType::PrincipalDimensions);
        assert_eq!(
            metadata.shape_class.as_deref(),
            Some("principal_dimensions_from_overview")
        );
        assert_abs_diff_eq!(metadata.mass_properties.mass_kg, mass_kg, epsilon = 1.0e-12);
        assert_abs_diff_eq!(
            metadata.dimensions_m.equivalent_radius_m.unwrap(),
            radius_m,
            epsilon = 1.0e-12
        );
        assert_eq!(
            metadata.orientation.initial_quaternion_wxyz,
            [1.0, 0.0, 0.0, 0.0]
        );
        let principal_lengths_m = metadata.dimensions_m.principal_lengths_m.unwrap();
        for (actual, expected) in principal_lengths_m.iter().zip(lengths_m) {
            assert_abs_diff_eq!(*actual, expected, epsilon = 1.0e-12);
        }
        let moments = metadata.computed_principal_moments_kg_m2().unwrap();
        let expected_moments = box_principal_moments_kg_m2(mass_kg, lengths_m);
        for (actual, expected) in moments.iter().zip(expected_moments) {
            assert_abs_diff_eq!(*actual, expected, epsilon = 1.0e-12);
            assert!(*actual > 0.0);
        }
        metadata
            .validate_against_block(&SphereBlock { radius_m, mass_kg })
            .unwrap();
        assert!(metadata
            .provenance
            .notes
            .iter()
            .any(|note| note.contains("passive")));
    }
}

#[test]
fn shape_contact_v0_scaffold_accepts_principal_dimensions_box_metadata() {
    let metadata = BlockShapeMetadata::from_yaml_file(
        "data/processed/tschamut2014/shape_metadata/block_1_st_leonard.yaml",
    )
    .unwrap();
    let scaffold = ShapeContactV0Scaffold::from_metadata(&metadata).unwrap();

    assert_eq!(scaffold.active_contact_model, "shape_contact_v0");
    assert_eq!(scaffold.active_shape_type, "principal_dimensions_box_v0");
    assert_eq!(scaffold.principal_dimensions_m, [0.37, 0.32, 0.37]);
    assert_eq!(scaffold.orientation_wxyz, [1.0, 0.0, 0.0, 0.0]);
    let expected = box_principal_moments_kg_m2(69.0, [0.37, 0.32, 0.37]);
    for (actual, expected) in scaffold.principal_moments_kg_m2.iter().zip(expected) {
        assert_abs_diff_eq!(*actual, expected, epsilon = 1.0e-12);
    }
}

#[test]
fn shape_contact_v0_scaffold_rejects_invalid_mass_dimensions_and_orientation() {
    let invalid_mass = serde_yaml::from_str::<BlockShapeMetadata>(
        r#"schema_version: shape_metadata_v1
shape_id: bad_mass
shape_type: principal_dimensions
dimensions_m:
  principal_lengths_m: [1.0, 2.0, 3.0]
  equivalent_radius_m: 1.0
mass_properties:
  mass_kg: -1.0
  mass_property_model: box_principal_dimensions
"#,
    )
    .unwrap();
    assert!(ShapeContactV0Scaffold::from_metadata(&invalid_mass).is_err());

    let invalid_dimensions = serde_yaml::from_str::<BlockShapeMetadata>(
        r#"schema_version: shape_metadata_v1
shape_id: bad_dimensions
shape_type: principal_dimensions
dimensions_m:
  principal_lengths_m: [1.0, 0.0, 3.0]
  equivalent_radius_m: 1.0
mass_properties:
  mass_kg: 10.0
  mass_property_model: box_principal_dimensions
"#,
    )
    .unwrap();
    assert!(ShapeContactV0Scaffold::from_metadata(&invalid_dimensions).is_err());

    let fixed_orientation = serde_yaml::from_str::<BlockShapeMetadata>(
        r#"schema_version: shape_metadata_v1
shape_id: fixed_orientation
shape_type: principal_dimensions
dimensions_m:
  principal_lengths_m: [1.0, 2.0, 3.0]
  equivalent_radius_m: 1.0
mass_properties:
  mass_kg: 10.0
  mass_property_model: box_principal_dimensions
orientation:
  representation: quaternion_wxyz
  initialization_mode: fixed_quaternion
  initial_quaternion_wxyz: [1.0, 0.0, 0.0, 0.0]
"#,
    )
    .unwrap();
    let error = ShapeContactV0Scaffold::from_metadata(&fixed_orientation)
        .unwrap_err()
        .to_string();
    assert!(error.contains("identity orientation only"));
}

#[test]
fn shape_contact_v0_support_point_selection_is_deterministic() {
    let support = select_box_support_point(
        Vec3::new(10.0, 20.0, 30.0),
        Vec3::new(0.0, 0.0, 1.0),
        [2.0, 4.0, 6.0],
        [1.0, 0.0, 0.0, 0.0],
    )
    .unwrap();

    assert_eq!(support.active_contact_model, "shape_contact_v0");
    assert_eq!(support.active_shape_type, "principal_dimensions_box_v0");
    assert_eq!(support.support_corner_signs, [1, 1, -1]);
    assert_abs_diff_eq!(support.support_point_m[0], 11.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(support.support_point_m[1], 22.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(support.support_point_m[2], 27.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(support.orientation_norm_error, 0.0, epsilon = 1.0e-12);
}

#[test]
fn shape_contact_v0_support_tie_break_flat_upward_normal_uses_positive_zero_signs() {
    let support = select_box_support_point(
        Vec3::new(0.0, 0.0, 0.0),
        Vec3::new(0.0, 0.0, 1.0),
        [2.0, 4.0, 6.0],
        [1.0, 0.0, 0.0, 0.0],
    )
    .unwrap();

    assert_eq!(support.support_corner_signs, [1, 1, -1]);
}

#[test]
fn shape_contact_v0_support_tie_break_inclined_normal_with_zero_component() {
    let support = select_box_support_point(
        Vec3::new(0.0, 0.0, 0.0),
        Vec3::new(0.0, 1.0, 1.0),
        [2.0, 4.0, 6.0],
        [1.0, 0.0, 0.0, 0.0],
    )
    .unwrap();

    assert_eq!(support.support_corner_signs, [1, -1, -1]);
}

#[test]
fn shape_contact_v0_support_tie_break_near_zero_components_use_raw_sign() {
    let positive_near_zero = select_box_support_point(
        Vec3::new(0.0, 0.0, 0.0),
        Vec3::new(-1.0e-15, 0.0, 1.0),
        [2.0, 4.0, 6.0],
        [1.0, 0.0, 0.0, 0.0],
    )
    .unwrap();
    let negative_near_zero = select_box_support_point(
        Vec3::new(0.0, 0.0, 0.0),
        Vec3::new(1.0e-15, 0.0, 1.0),
        [2.0, 4.0, 6.0],
        [1.0, 0.0, 0.0, 0.0],
    )
    .unwrap();

    assert_eq!(positive_near_zero.support_corner_signs, [1, 1, -1]);
    assert_eq!(negative_near_zero.support_corner_signs, [-1, 1, -1]);
}

#[test]
fn shape_contact_v0_energy_diagnostic_is_accounting_only() {
    let mut pre = BodyState::new(Vec3::new(0.0, 0.0, 10.0), Vec3::new(1.0, 0.0, 0.0));
    pre.angular_velocity_radps = Vec3::new(0.0, 2.0, 0.0);
    let post = pre;
    let diagnostic =
        shape_contact_v0_energy_diagnostic(&pre, &post, 10.0, [1.0, 2.0, 3.0], 9.81).unwrap();

    assert_abs_diff_eq!(
        diagnostic.pre_total_mechanical_energy_j,
        diagnostic.post_total_mechanical_energy_j,
        epsilon = 1.0e-12
    );
    assert_abs_diff_eq!(diagnostic.contact_energy_delta_j, 0.0, epsilon = 1.0e-12);
}

use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};

#[test]
fn plane_height_normal_and_sphere_distance_are_consistent() {
    let terrain = Plane {
        z0_m: 2.0,
        slope_x: 0.5,
        slope_y: -0.25,
    };

    assert_abs_diff_eq!(terrain.height(4.0, 2.0), 3.5, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.normal(4.0, 2.0).norm(), 1.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(
        terrain.signed_distance_sphere(Vec3::new(0.0, 0.0, 3.0), 0.5),
        (Vec3::new(0.0, 0.0, 1.0).dot(&terrain.normal(0.0, 0.0))) - 0.5,
        epsilon = 1.0e-12
    );
}

#[test]
fn paraboloid_height_and_normal_use_quadratic_gradient() {
    let terrain = Paraboloid {
        z0_m: 1.0,
        ax: 0.25,
        ay: 0.5,
    };

    assert_abs_diff_eq!(terrain.height(2.0, 3.0), 6.5, epsilon = 1.0e-12);
    let expected = Vec3::new(-1.0, -3.0, 1.0).normalize();
    assert_abs_diff_eq!(terrain.normal(2.0, 3.0).x, expected.x, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.normal(2.0, 3.0).y, expected.y, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.normal(2.0, 3.0).z, expected.z, epsilon = 1.0e-12);
}

#[test]
fn step_terrain_switches_height_at_step_location() {
    let terrain = StepTerrain {
        step_x_m: 10.0,
        high_z_m: 5.0,
        low_z_m: 1.0,
    };

    assert_abs_diff_eq!(terrain.height(9.99, 0.0), 5.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.height(10.0, 0.0), 1.0, epsilon = 1.0e-12);
    assert_eq!(terrain.normal(10.0, 0.0), Vec3::new(0.0, 0.0, 1.0));
}

#[test]
fn procedural_terrain_variants_have_expected_heights_and_unit_normals() {
    let valley = VShapedValley {
        z0_m: 0.0,
        slope_x: -0.2,
        side_slope_abs_y: 0.5,
    };
    assert_abs_diff_eq!(valley.height(1.0, -2.0), 0.8, epsilon = 1.0e-12);
    assert_abs_diff_eq!(valley.normal(1.0, -2.0).norm(), 1.0, epsilon = 1.0e-12);

    let terrace = TerracedSlope {
        z0_m: 0.0,
        slope_x: -0.1,
        terrace_width_m: 2.0,
        terrace_height_m: -0.5,
    };
    assert_abs_diff_eq!(terrace.height(4.5, 0.0), -1.45, epsilon = 1.0e-12);

    let rough = SinusoidalRoughSlope {
        z0_m: 0.0,
        slope_x: -0.1,
        amplitude_m: 1.0,
        wavelength_m: 4.0,
    };
    assert_abs_diff_eq!(rough.height(1.0, 0.0), 0.9, epsilon = 1.0e-12);

    let bump = GaussianBump {
        z0_m: 0.0,
        slope_x: 0.0,
        center_x_m: 0.0,
        center_y_m: 0.0,
        height_m: 2.0,
        sigma_m: 1.0,
    };
    assert_abs_diff_eq!(bump.height(0.0, 0.0), 2.0, epsilon = 1.0e-12);

    let gully = ChannelizedGully {
        z0_m: 0.0,
        slope_x: -0.1,
        depth_m: 2.0,
        width_m: 1.0,
    };
    assert_abs_diff_eq!(gully.height(0.0, 0.0), -2.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(gully.normal(2.0, 0.5).norm(), 1.0, epsilon = 1.0e-12);
}

#[test]
fn dem_parser_reports_header_value_count_and_bounds_errors() {
    assert!(matches!(
        DemGrid::from_ascii_grid_str("ncols nope\n"),
        Err(TerrainError::Header("ncols"))
    ));

    assert!(matches!(
        DemGrid::from_ascii_grid_str(
            "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1 2 3\n"
        ),
        Err(TerrainError::ValueCount {
            expected: 4,
            actual: 3
        })
    ));

    let dem = DemGrid::from_ascii_grid_str(
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n2 4\n0 2\n",
    )
    .unwrap();
    assert!(matches!(
        dem.try_height(-0.1, 0.0),
        Err(TerrainError::OutOfBounds { .. })
    ));
    assert!(matches!(
        dem.try_height(0.0, 0.0),
        Err(TerrainError::OutOfBounds { .. })
    ));
    assert_abs_diff_eq!(dem.try_height(1.5, 1.5).unwrap(), 4.0, epsilon = 1.0e-12);

    let dem_with_nodata = DemGrid::from_ascii_grid_str(
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1 -9999\n0 2\n",
    )
    .unwrap();
    assert!(matches!(
        dem_with_nodata.try_height(0.5, 0.5),
        Err(TerrainError::NoData {
            col: 1,
            row_from_bottom: 1,
            ..
        })
    ));
}

#[test]
fn clamped_dem_keeps_boundary_queries_finite_without_changing_strict_dem() {
    let dem = DemGrid::from_ascii_grid_str(
        "ncols 3\nnrows 3\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n4 5 6\n2 3 4\n0 1 2\n",
    )
    .unwrap();
    assert!(matches!(
        dem.try_height(-0.5, 0.5),
        Err(TerrainError::OutOfBounds { .. })
    ));

    let clamped = ClampedDemGrid::from_grid(dem);
    assert_abs_diff_eq!(clamped.height(-0.5, 0.5), 0.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(clamped.height(3.5, 1.5), 4.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(clamped.normal(-0.5, 0.5).norm(), 1.0, epsilon = 1.0e-12);
}

#[test]
fn clamped_dem_normal_matches_planar_dem_interior_and_edge() {
    let dem = DemGrid::from_ascii_grid_str(
        "ncols 3\nnrows 3\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n4 5 6\n2 3 4\n0 1 2\n",
    )
    .unwrap();
    let strict_edge = dem.normal(0.5, 1.5);
    let clamped = ClampedDemGrid::from_grid(dem);
    let expected = Vec3::new(-1.0, -2.0, 1.0).normalize();
    let interior = clamped.normal(1.5, 1.5);
    let edge = clamped.normal(-0.5, 1.5);

    assert_abs_diff_eq!(strict_edge.x, expected.x, epsilon = 1.0e-12);
    assert_abs_diff_eq!(strict_edge.y, expected.y, epsilon = 1.0e-12);
    assert_abs_diff_eq!(strict_edge.z, expected.z, epsilon = 1.0e-12);
    assert_abs_diff_eq!(interior.x, expected.x, epsilon = 1.0e-12);
    assert_abs_diff_eq!(interior.y, expected.y, epsilon = 1.0e-12);
    assert_abs_diff_eq!(interior.z, expected.z, epsilon = 1.0e-12);
    assert_abs_diff_eq!(edge.x, expected.x, epsilon = 1.0e-12);
    assert_abs_diff_eq!(edge.y, expected.y, epsilon = 1.0e-12);
    assert_abs_diff_eq!(edge.z, expected.z, epsilon = 1.0e-12);
}

#[test]
fn terrain_config_builds_each_supported_variant() {
    assert_abs_diff_eq!(
        TerrainConfig::Plane {
            z0_m: 1.0,
            slope_x: 0.0,
            slope_y: 0.0
        }
        .build()
        .unwrap()
        .height(0.0, 0.0),
        1.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::Paraboloid {
            z0_m: 0.0,
            ax: 1.0,
            ay: 0.0
        }
        .build()
        .unwrap()
        .height(2.0, 0.0),
        4.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::Step {
            step_x_m: 1.0,
            high_z_m: 3.0,
            low_z_m: -1.0
        }
        .build()
        .unwrap()
        .height(2.0, 0.0),
        -1.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::VShapedValley {
            z0_m: 0.0,
            slope_x: 0.0,
            side_slope_abs_y: 0.5
        }
        .build()
        .unwrap()
        .height(0.0, 2.0),
        1.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::TerracedSlope {
            z0_m: 0.0,
            slope_x: 0.0,
            terrace_width_m: 2.0,
            terrace_height_m: -1.0
        }
        .build()
        .unwrap()
        .height(5.0, 0.0),
        -2.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::GaussianBump {
            z0_m: 0.0,
            slope_x: 0.0,
            center_x_m: 0.0,
            center_y_m: 0.0,
            height_m: 1.0,
            sigma_m: 1.0
        }
        .build()
        .unwrap()
        .height(0.0, 0.0),
        1.0,
        epsilon = 1.0e-12
    );
}

#[test]
fn esri_ascii_grid_config_reads_from_file() {
    let path = temp_path("terrain_config.asc");
    fs::write(
        &path,
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n2 4\n0 2\n",
    )
    .unwrap();

    let terrain = TerrainConfig::EsriAsciiGrid {
        path: path.to_string_lossy().to_string(),
    }
    .build()
    .unwrap();

    assert_abs_diff_eq!(terrain.height(0.5, 0.5), 0.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.height(1.0, 1.0), 2.0, epsilon = 1.0e-12);
    fs::remove_file(path).unwrap();
}

#[test]
fn clamped_esri_ascii_grid_config_reads_from_file() {
    let path = temp_path("terrain_config_clamped.asc");
    fs::write(
        &path,
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n2 4\n0 2\n",
    )
    .unwrap();

    let terrain = TerrainConfig::EsriAsciiGridClamped {
        path: path.to_string_lossy().to_string(),
    }
    .build()
    .unwrap();

    assert_abs_diff_eq!(terrain.height(-1.0, 0.5), 0.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.height(0.5, 0.5), 0.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.height(1.0, 1.0), 2.0, epsilon = 1.0e-12);
    fs::remove_file(path).unwrap();
}

#[test]
fn swiss_terrain_metadata_parses_and_validates_against_dem() {
    let metadata = TerrainSourceMetadata::from_yaml_file(
        "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml",
    )
    .unwrap();
    let dem = DemGrid::from_ascii_grid(
        "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_crop.asc",
    )
    .unwrap();

    assert_eq!(metadata.coordinate_reference_system.epsg, 2056);
    assert_eq!(metadata.coordinate_reference_system.vertical_datum, "LN02");
    assert_abs_diff_eq!(metadata.raster.resolution_m, 2.0, epsilon = 1.0e-12);
    assert_eq!(metadata.raster.nodata, Some(-9999.0));
    metadata.validate_against_dem(&dem).unwrap();
}

#[test]
fn swiss_terrain_metadata_rejects_bad_crs_and_extent() {
    let bad_crs = r#"
schema_version: 1
tile_id: bad
source_dataset: swisstopo_swissalti3d
source_product: swissALTI3D
source_filename: bad.asc
source_file_present: false
download_status: processed_fixture
license: synthetic
coordinate_reference_system:
  epsg: 4326
  horizontal_name: WGS84
  vertical_datum: LN02
  coordinate_unit: m
  height_unit: m
raster: { format: ESRI ASCII GRID, resolution_m: 2.0, width_px: 2, height_px: 2, nodata: -9999.0 }
extent_lv95_m: { xmin: 0.0, ymin: 0.0, xmax: 4.0, ymax: 4.0 }
preprocessing: { status: converted_to_internal_dem, crop_extent_lv95_m: null, resampling_method: none, raw_sha256: null, processed_sha256: null, tool: null, processed_utc: null }
provenance: { intended_use: test, notes: [] }
"#;
    assert!(TerrainSourceMetadata::from_yaml_str(bad_crs).is_err());

    let bad_extent = bad_crs
        .replace("epsg: 4326", "epsg: 2056")
        .replace("xmax: 4.0", "xmax: 5.0");
    assert!(TerrainSourceMetadata::from_yaml_str(&bad_extent).is_err());
}

#[test]
fn simulation_config_json_defaults_and_seeded_initial_state_are_deterministic() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 2.0],
        "initial_velocity_mps": [1.0, 0.0, 0.0],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 1.0,
        "random_seed": 7,
        "release_perturbation": { "position_uniform_m": 0.1, "velocity_uniform_mps": 0.2 }
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_abs_diff_eq!(config.gravity_mps2, 9.81, epsilon = 1.0e-12);
    assert_abs_diff_eq!(config.normal_restitution, 0.25, epsilon = 1.0e-12);
    assert_eq!(config.contact_model, ContactModel::TranslationalV0);
    assert_eq!(config.soil_interaction_model, SoilInteractionModel::None);
    assert_eq!(config.roughness_model, RoughnessModel::None);
    assert_eq!(config.initial_state(), config.initial_state());
}

#[test]
fn simulation_config_json_accepts_rotational_contact_model() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 0.5],
        "initial_velocity_mps": [1.0, 0.0, 0.0],
        "initial_angular_velocity_radps": [0.0, 2.0, 0.0],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 0.02,
        "contact_model": "sphere_rotational_v1",
        "rolling_resistance_coefficient": 0.1
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_eq!(config.contact_model, ContactModel::SphereRotationalV1);
    assert_abs_diff_eq!(
        config.rolling_resistance_coefficient,
        0.1,
        epsilon = 1.0e-12
    );
    assert!(!config.run().unwrap().samples.is_empty());
}

#[test]
fn simulation_config_json_accepts_stochastic_contact_roughness() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 2.0],
        "initial_velocity_mps": [1.0, 0.0, -0.5],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 1.0,
        "random_seed": 11,
        "roughness_model": "stochastic_contact_v1",
        "roughness_std_normal": 0.05,
        "roughness_std_tangent": 0.04,
        "roughness_std_angle": 0.03
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_eq!(config.roughness_model, RoughnessModel::StochasticContactV1);
    assert_abs_diff_eq!(config.roughness_std_angle, 0.03, epsilon = 1.0e-12);
    assert_eq!(config.run().unwrap().samples, config.run().unwrap().samples);
}

#[test]
fn simulation_config_json_accepts_scarring_contact_model() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 2.0],
        "initial_velocity_mps": [0.0, 0.0, -1.0],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 1.0,
        "soil_interaction_model": "scarring_contact_v1",
        "soil_strength_pa": 100000.0,
        "scarring_drag_coefficient": 1.0,
        "scarring_layer_density_kgpm3": 1600.0,
        "scarring_max_depth_m": 0.05
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_eq!(
        config.soil_interaction_model,
        SoilInteractionModel::ScarringContactV1
    );
    let result = config.run().unwrap();
    assert!(result
        .samples
        .iter()
        .any(|sample| sample.scarring_energy_loss_j > 0.0));
}

#[test]
fn validation_yaml_rejects_unknown_contact_model() {
    let path = temp_path("bad_contact_model.yaml");
    fs::write(
        &path,
        r#"
case_id: bad_contact_model
terrain: { type: plane, parameters: { z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 } }
block: { mass: 1.0, radius: 0.5 }
parameters:
  contact_model: hidden_magic
"#,
    )
    .unwrap();

    assert!(load_case(&path).is_err());
    fs::remove_file(path).unwrap();
}

#[test]
fn shape_contact_v0_requires_shape_metadata_before_simulation() {
    let path = temp_path("shape_contact_missing_metadata.yaml");
    fs::write(
        &path,
        r#"case_id: shape_contact_missing_metadata
terrain:
  type: plane
block:
  mass: 10.0
  radius: 0.5
parameters:
  contact_model: shape_contact_v0
simulation:
  dt: 0.01
  t_max: 0.01
"#,
    )
    .unwrap();

    let error = run_case_file(&path).unwrap_err().to_string();

    assert!(error.contains("shape_contact_v0 requires block_shape.metadata_path"));
    fs::remove_file(path).unwrap();
}

#[test]
fn shape_contact_v0_with_metadata_stops_before_unimplemented_dynamics() {
    let path = temp_path("shape_contact_with_metadata.yaml");
    fs::write(
        &path,
        r#"case_id: shape_contact_with_metadata
terrain:
  type: plane
block:
  mass: 69.0
  radius: 0.176667
block_shape:
  metadata_path: data/processed/tschamut2014/shape_metadata/block_1_st_leonard.yaml
parameters:
  contact_model: shape_contact_v0
simulation:
  dt: 0.01
  t_max: 0.01
"#,
    )
    .unwrap();

    let error = run_case_file(&path).unwrap_err().to_string();

    assert!(error.contains("shape_contact_v0 is a verification scaffold"));
    fs::remove_file(path).unwrap();
}

#[test]
fn validation_yaml_rejects_unknown_roughness_model() {
    let path = temp_path("bad_roughness_model.yaml");
    fs::write(
        &path,
        r#"
case_id: bad_roughness_model
terrain: { type: plane, parameters: { z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 } }
block: { mass: 1.0, radius: 0.5 }
parameters:
  roughness_model: hidden_magic
"#,
    )
    .unwrap();

    assert!(load_case(&path).is_err());
    fs::remove_file(path).unwrap();
}

#[test]
fn validation_yaml_rejects_unknown_soil_interaction_model() {
    let path = temp_path("bad_soil_interaction_model.yaml");
    fs::write(
        &path,
        r#"
case_id: bad_soil_interaction_model
terrain: { type: plane, parameters: { z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 } }
block: { mass: 1.0, radius: 0.5 }
parameters:
  soil_interaction_model: hidden_magic
"#,
    )
    .unwrap();

    assert!(load_case(&path).is_err());
    fs::remove_file(path).unwrap();
}

#[test]
fn simulation_validation_rejects_non_positive_inputs() {
    let mut config = minimal_config();
    config.block = SphereBlock::new(0.0, 1.0);
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("block.radius_m"))
    ));

    let mut config = minimal_config();
    config.block = SphereBlock::new(1.0, 0.0);
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("block.mass_kg"))
    ));

    let mut config = minimal_config();
    config.dt_s = 0.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("dt_s"))
    ));

    let mut config = minimal_config();
    config.max_time_s = 0.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("max_time_s"))
    ));

    let mut config = minimal_config();
    config.gravity_mps2 = 0.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("gravity_mps2"))
    ));

    let mut config = minimal_config();
    config.normal_restitution = -0.1;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("normal_restitution"))
    ));

    let mut config = minimal_config();
    config.tangential_restitution = f64::NAN;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("tangential_restitution"))
    ));

    let mut config = minimal_config();
    config.normal_restitution = 1.0;
    config.tangential_restitution = 1.0;
    assert!(config.run().is_ok());

    let mut config = minimal_config();
    config.normal_restitution = 1.01;
    assert!(matches!(
        config.run(),
        Err(SimulationError::OutOfRange {
            field: "normal_restitution",
            min: 0.0,
            max: 1.0,
        })
    ));

    let mut config = minimal_config();
    config.tangential_restitution = 1.01;
    assert!(matches!(
        config.run(),
        Err(SimulationError::OutOfRange {
            field: "tangential_restitution",
            min: 0.0,
            max: 1.0,
        })
    ));

    let mut config = minimal_config();
    config.friction_coefficient = -0.1;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("friction_coefficient"))
    ));

    let mut config = minimal_config();
    config.rolling_resistance_coefficient = -0.1;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive(
            "rolling_resistance_coefficient"
        ))
    ));

    let mut config = minimal_config();
    config.stop_speed_mps = -0.1;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("stop_speed_mps"))
    ));

    let mut config = minimal_config();
    config.release_perturbation = ReleasePerturbation {
        position_uniform_m: -0.1,
        velocity_uniform_mps: 0.0,
    };
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive(
            "release_perturbation.position_uniform_m"
        ))
    ));

    let mut config = minimal_config();
    config.release_perturbation = ReleasePerturbation {
        position_uniform_m: 0.0,
        velocity_uniform_mps: f64::NAN,
    };
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive(
            "release_perturbation.velocity_uniform_mps"
        ))
    ));

    let mut config = minimal_config();
    config.roughness_std_angle = -0.1;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("roughness_std_angle"))
    ));

    let mut config = minimal_config();
    config.soil_strength_pa = -1.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("soil_strength_pa"))
    ));

    let mut config = minimal_config();
    config.scarring_max_depth_m = Some(-0.1);
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("scarring_max_depth_m"))
    ));
}

#[test]
fn read_config_reports_json_errors_and_write_csv_round_trips_samples() {
    let bad_config_path = temp_path("bad_config.json");
    fs::write(&bad_config_path, "{not json").unwrap();
    assert!(io::read_config(&bad_config_path).is_err());
    fs::remove_file(bad_config_path).unwrap();

    let result = minimal_config().run().unwrap();
    let csv_path = temp_path("trajectory.csv");
    io::write_trajectory_csv(&csv_path, &result.samples).unwrap();
    let csv_text = fs::read_to_string(&csv_path).unwrap();

    assert!(csv_text.contains("time_s"));
    assert!(csv_text.contains("contact_state"));
    assert!(
        csv_text.contains(match result.samples.last().unwrap().contact_state {
            ContactState::Airborne => "airborne",
            ContactState::Sliding => "sliding",
            ContactState::Impact => "impact",
            ContactState::Rolling => "rolling",
            ContactState::Stopped => "stopped",
        })
    );
    assert!(csv_text.contains("omega_x_radps"));
    assert!(csv_text.contains("rolling_residual_mps"));
    assert!(csv_text.contains("scarring_depth_m"));
    assert!(csv_text.contains("scarring_energy_loss_j"));
    fs::remove_file(csv_path).unwrap();

    let mut impact_config = minimal_config();
    impact_config.initial_position_m = [0.0, 0.0, 1.0];
    impact_config.initial_velocity_mps = [0.0, 0.0, -1.0];
    impact_config.max_time_s = 0.4;
    let impact_result = impact_config.run().unwrap();
    assert_eq!(impact_result.impact_events.len(), 1);

    let impact_csv_path = temp_path("impact_events.csv");
    io::write_impact_events_csv(&impact_csv_path, &impact_result.impact_events).unwrap();
    let impact_csv = fs::read_to_string(&impact_csv_path).unwrap();
    assert!(impact_csv.contains("impact_index"));
    assert!(impact_csv.contains("post_scarring_vz_mps"));
    fs::remove_file(impact_csv_path).unwrap();

    let impact_json_path = temp_path("impact_events.json");
    io::write_impact_events_json(&impact_json_path, &impact_result.impact_events).unwrap();
    let impact_json = fs::read_to_string(&impact_json_path).unwrap();
    assert!(impact_json.contains("\"impact_index\""));
    assert!(impact_json.contains("\"scarring_capped_energy_loss_j\""));
    fs::remove_file(impact_json_path).unwrap();
}

#[test]
fn write_csv_reports_path_errors() {
    let result = minimal_config().run().unwrap();
    let directory_path = temp_path("csv_directory");
    fs::create_dir(&directory_path).unwrap();

    assert!(io::write_trajectory_csv(&directory_path, &result.samples).is_err());
    fs::remove_dir(directory_path).unwrap();
}

#[test]
fn read_config_successfully_loads_example_shape() {
    let path = temp_path("valid_config.json");
    fs::write(
        &path,
        r#"{
            "block": { "radius_m": 0.5, "mass_kg": 10.0 },
            "initial_position_m": [0.0, 0.0, 2.0],
            "initial_velocity_mps": [1.0, 0.0, 0.0],
            "terrain": { "kind": "step", "step_x_m": 1.0, "high_z_m": 0.0, "low_z_m": -1.0 },
            "dt_s": 0.01,
            "max_time_s": 1.0
        }"#,
    )
    .unwrap();

    let config = io::read_config(&path).unwrap();
    assert!(matches!(config.terrain, TerrainConfig::Step { .. }));
    fs::remove_file(path).unwrap();
}

#[test]
fn validation_case_runner_writes_metrics_for_synthetic_fixture() {
    let output = PathBuf::from("validation/results/synthetic_plane_basic_metrics.json");
    let _ = fs::remove_file(&output);

    let report = run_case_file("validation/cases/synthetic_plane_basic.yaml").unwrap();

    assert!(matches!(
        report.status,
        CaseStatus::Passed | CaseStatus::Failed
    ));
    assert!(report.metrics.contains_key("deposition_point_error_m"));
    assert!(output.exists());
    fs::remove_file(output).unwrap();
}

#[test]
fn validation_reports_raw_and_significant_impact_counts_separately() {
    let case_path = temp_path("impact_count_semantics.yaml");
    let diagnostics = temp_path("impact_count_semantics.json");
    let trajectory = temp_path("impact_count_semantics.csv");
    let impacts = temp_path("impact_count_semantics_impacts.csv");
    fs::write(
        &case_path,
        format!(
            r#"case_id: impact_count_semantics
title: Impact count semantics
level: 1
description: Temporary scarring case with low-energy contact chatter.
terrain:
  type: plane
  parameters: {{ z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }}
block: {{ mass: 50.0, radius: 0.5 }}
release:
  position: [0.0, 0.0, 1.0]
  velocity: [1.0, 0.0, -0.2]
parameters:
  gravity: 9.81
  normal_restitution: 0.4
  tangential_restitution: 0.85
  friction_coefficient: 0.4
  soil_interaction_model: scarring_contact_v1
  soil_strength_pa: 500000.0
  scarring_drag_coefficient: 0.01
  scarring_layer_density_kgpm3: 1600.0
simulation: {{ dt: 0.005, t_max: 1.0, stop_velocity: 0.05 }}
random: {{ seed: 777, ensemble_size: 1 }}
expected:
  metrics: [impact_event_count, significant_impact_count, significant_impact_min_normal_speed_mps]
outputs:
  diagnostics_json: {}
  trajectory_csv: {}
  impact_events_csv: {}
"#,
            diagnostics.display(),
            trajectory.display(),
            impacts.display()
        ),
    )
    .unwrap();

    let report = run_case_file(&case_path).unwrap();

    assert!(report.metrics["impact_event_count"] > report.metrics["significant_impact_count"]);
    assert!(report.metrics["significant_impact_count"] > 0.0);
    assert_abs_diff_eq!(
        report.metrics["significant_impact_min_normal_speed_mps"],
        0.05,
        epsilon = 1.0e-12
    );
    fs::remove_file(case_path).unwrap();
    fs::remove_file(diagnostics).unwrap();
    fs::remove_file(trajectory).unwrap();
    fs::remove_file(impacts).unwrap();
}

#[test]
fn validation_compares_observed_trajectory_shape_and_energy() {
    let case_path = temp_path("observed_trajectory_case.yaml");
    let observations = temp_path("observed_trajectory.csv");
    let releases = temp_path("observed_trajectory_releases.csv");
    let diagnostics = temp_path("observed_trajectory_metrics.json");
    let trajectory = temp_path("observed_trajectory_output.csv");

    fs::write(
        &observations,
        "trajectory_id,experiment_id,time_s,x_m,y_m,z_m,vx_mps,vy_mps,vz_mps,speed_mps,kinetic_j\n\
         obs_001,synthetic,0.0,0.0,0.0,2.0,1.0,0.0,0.0,1.0,5.0\n\
         obs_001,synthetic,0.1,0.1,0.0,1.95095,1.0,0.0,-0.981,1.4008429605062802,9.811805\n",
    )
    .unwrap();
    fs::write(
        &releases,
        "trajectory_id,experiment_id,x_m,y_m,z_m,vx_mps,vy_mps,vz_mps,mass_kg,radius_m\n\
         obs_001,synthetic,0.0,0.0,2.0,1.0,0.0,0.0,10.0,0.5\n",
    )
    .unwrap();
    fs::write(
        &case_path,
        format!(
            r#"case_id: observed_trajectory_case
terrain:
  type: plane
  parameters: {{ z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }}
block: {{ mass: 10.0, radius: 0.5 }}
release:
  position: [0.0, 0.0, 2.0]
  velocity: [1.0, 0.0, 0.0]
simulation: {{ dt: 0.05, t_max: 0.1, stop_velocity: 0.01 }}
observations:
  release_points_csv: {}
  trajectory_csv: {}
expected:
  metrics:
    - validation_trajectory_count
    - observed_trajectory_sample_count
    - trajectory_shape_mean_error_m
    - trajectory_energy_mean_relative_error
outputs:
  diagnostics_json: {}
  trajectory_csv: {}
"#,
            releases.display(),
            observations.display(),
            diagnostics.display(),
            trajectory.display()
        ),
    )
    .unwrap();

    let report = run_case_file(&case_path).unwrap();

    assert_eq!(report.status, CaseStatus::Passed);
    assert_abs_diff_eq!(
        report.metrics["validation_trajectory_count"],
        1.0,
        epsilon = 1.0e-12
    );
    assert_abs_diff_eq!(
        report.metrics["observed_trajectory_sample_count"],
        2.0,
        epsilon = 1.0e-12
    );
    assert!(report.metrics["trajectory_shape_mean_error_m"] < 1.0e-12);
    assert!(report.metrics["trajectory_energy_mean_relative_error"] < 1.0e-12);

    fs::remove_file(case_path).unwrap();
    fs::remove_file(observations).unwrap();
    fs::remove_file(releases).unwrap();
    fs::remove_file(diagnostics).unwrap();
    fs::remove_file(trajectory).unwrap();
}

#[test]
fn validation_compares_observed_contact_events() {
    let case_path = temp_path("observed_contact_case.yaml");
    let observations = temp_path("observed_contact_trajectory.csv");
    let contacts = temp_path("observed_contact_events.csv");
    let releases = temp_path("observed_contact_releases.csv");
    let diagnostics = temp_path("observed_contact_metrics.json");
    let trajectory = temp_path("observed_contact_output.csv");

    fs::write(
        &observations,
        "trajectory_id,experiment_id,time_s,x_m,y_m,z_m,vx_mps,vy_mps,vz_mps,speed_mps,kinetic_j\n\
         seg00,synthetic_contact,0.0,0.0,0.0,2.0,0.0,0.0,-1.0,1.0,5.0\n\
         seg00,synthetic_contact,0.46,0.0,0.0,0.5,0.0,0.0,-5.5,5.5,151.25\n",
    )
    .unwrap();
    fs::write(
        &releases,
        "trajectory_id,experiment_id,x_m,y_m,z_m,vx_mps,vy_mps,vz_mps,mass_kg,radius_m\n\
         seg00,synthetic_contact,0.0,0.0,2.0,0.0,0.0,-1.0,10.0,0.5\n",
    )
    .unwrap();
    fs::write(
        &contacts,
        "event_id,trajectory_id,experiment_id,source_segment_id,next_segment_id,impact_index,impact_time_s,x_m,y_m,z_m,incoming_vx_mps,incoming_vy_mps,incoming_vz_mps,outgoing_vx_mps,outgoing_vy_mps,outgoing_vz_mps,pre_impact_kinetic_j,post_impact_kinetic_j,mass_kg,radius_m\n\
         impact00,seg00,synthetic_contact,seg00,seg01,0,0.46,0.0,0.0,0.5,0.0,0.0,-5.5,0.0,0.0,2.75,151.25,37.8125,10.0,0.5\n",
    )
    .unwrap();
    fs::write(
        &case_path,
        format!(
            r#"case_id: observed_contact_case
terrain:
  type: plane
  parameters: {{ z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }}
block: {{ mass: 10.0, radius: 0.5 }}
release:
  position: [0.0, 0.0, 2.0]
  velocity: [0.0, 0.0, -1.0]
parameters:
  normal_restitution: 0.5
  tangential_restitution: 1.0
  friction_coefficient: 0.0
simulation: {{ dt: 0.01, t_max: 0.5, stop_velocity: 0.01 }}
observations:
  release_points_csv: {}
  trajectory_csv: {}
  contact_events_csv: {}
expected:
  metrics:
    - observed_contact_event_count
    - contact_event_compared_count
    - impact_timing_mean_error_s
    - rebound_velocity_mean_error_mps
outputs:
  diagnostics_json: {}
  trajectory_csv: {}
"#,
            releases.display(),
            observations.display(),
            contacts.display(),
            diagnostics.display(),
            trajectory.display()
        ),
    )
    .unwrap();

    let report = run_case_file(&case_path).unwrap();

    assert_eq!(report.status, CaseStatus::Passed);
    assert_abs_diff_eq!(
        report.metrics["observed_contact_event_count"],
        1.0,
        epsilon = 1.0e-12
    );
    assert_abs_diff_eq!(
        report.metrics["contact_event_compared_count"],
        1.0,
        epsilon = 1.0e-12
    );
    assert!(report.metrics["impact_timing_mean_error_s"] <= 0.02);
    assert!(report.metrics["rebound_velocity_mean_error_mps"] <= 0.2);

    fs::remove_file(case_path).unwrap();
    fs::remove_file(observations).unwrap();
    fs::remove_file(contacts).unwrap();
    fs::remove_file(releases).unwrap();
    fs::remove_file(diagnostics).unwrap();
    fs::remove_file(trajectory).unwrap();
}

#[test]
fn tschamut_validation_fixture_runs_reproducibly() {
    let output = PathBuf::from("validation/results/tschamut_basic_metrics.json");
    let trajectory = PathBuf::from("validation/results/tschamut_basic_trajectory.csv");
    let ensemble = PathBuf::from("validation/results/tschamut_basic_ensemble_deposition.csv");
    let _ = fs::remove_file(&output);
    let _ = fs::remove_file(&trajectory);
    let _ = fs::remove_file(&ensemble);

    let first = run_case_file("validation/cases/tschamut_basic.yaml").unwrap();
    let second = run_case_file("validation/cases/tschamut_basic.yaml").unwrap();

    assert_eq!(first.status, CaseStatus::Passed);
    assert_eq!(
        first.scientific_status,
        ScientificStatus::ReportedWithoutAcceptanceThresholds
    );
    assert_eq!(first.metrics, second.metrics);
    assert!(first.metrics.contains_key("deposition_centroid_error_m"));
    assert!(first.metrics.contains_key("runout_distance_error_m"));
    assert!(output.exists());
    assert!(trajectory.exists());
    assert!(ensemble.exists());
    fs::remove_file(output).unwrap();
    fs::remove_file(trajectory).unwrap();
    fs::remove_file(ensemble).unwrap();
}

#[test]
fn ensemble_trajectory_dir_is_opt_in_and_deterministic() {
    let case_path = temp_path("ensemble_trajectories.yaml");
    let diagnostics = temp_path("ensemble_trajectories.json");
    let manifest = temp_path("ensemble_trajectories_manifest.json");
    let trajectory = temp_path("ensemble_trajectories_representative.csv");
    let metadata = temp_path("ensemble_trajectory_metadata.csv");
    let ensemble_dir = temp_path("ensemble_trajectories_dir");
    let ensemble_impacts_dir = temp_path("ensemble_impacts_dir");
    let ensemble_impacts_parquet = temp_path("ensemble_impacts.parquet");
    fs::write(
        &case_path,
        format!(
            r#"case_id: ensemble_trajectory_output
title: Ensemble trajectory output
level: 3
description: Temporary case that writes one full trajectory CSV per ensemble member.
terrain:
  type: plane
  parameters: {{ z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }}
block: {{ mass: 10.0, radius: 0.5 }}
release:
  position: [0.0, 0.0, 1.0]
  velocity: [1.0, 0.0, -0.2]
  perturbation: {{ position_uniform_m: 0.01, velocity_uniform_mps: 0.01 }}
parameters:
  gravity: 9.81
  normal_restitution: 0.3
  tangential_restitution: 0.8
  friction_coefficient: 0.4
simulation: {{ dt: 0.005, t_max: 0.5, stop_velocity: 0.01 }}
random: {{ seed: 123, ensemble_size: 3 }}
expected:
  metrics: [ensemble_mean_runout_m]
outputs:
  diagnostics_json: {}
  manifest_json: {}
  trajectory_csv: {}
  trajectory_metadata_csv: {}
  ensemble_trajectories_dir: {}
  ensemble_impact_events_dir: {}
  ensemble_impact_events_parquet: {}
"#,
            diagnostics.display(),
            manifest.display(),
            trajectory.display(),
            metadata.display(),
            ensemble_dir.display(),
            ensemble_impacts_dir.display(),
            ensemble_impacts_parquet.display()
        ),
    )
    .unwrap();

    let first = run_case_file(&case_path).unwrap();
    let first_file = ensemble_dir.join("trajectory_000000.csv");
    let second_file = ensemble_dir.join("trajectory_000001.csv");
    let third_file = ensemble_dir.join("trajectory_000002.csv");
    let stale_trajectory = ensemble_dir.join("stale_trajectory.csv");
    let stale_impact = ensemble_impacts_dir.join("stale_impact.csv");
    let first_impacts = ensemble_impacts_dir.join("trajectory_000000.csv");
    assert_eq!(first.status, CaseStatus::Passed);
    assert!(trajectory.exists());
    assert!(metadata.exists());
    assert!(first_file.exists());
    assert!(second_file.exists());
    assert!(third_file.exists());
    assert!(first_impacts.exists());
    assert!(ensemble_impacts_parquet.exists());
    assert!(manifest.exists());
    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(manifest_json["schema_version"], "run_manifest_v1");
    assert_eq!(manifest_json["case_id"], "ensemble_trajectory_output");
    assert_eq!(manifest_json["completion_status"], "passed");
    assert_eq!(manifest_json["execution_status"], "completed");
    assert_eq!(manifest_json["scientific_status"], "not_evaluated");
    assert_eq!(manifest_json["seed_policy"]["global_seed"], 123);
    assert_eq!(manifest_json["outputs"].as_array().unwrap().len(), 6);
    assert_eq!(
        manifest_json["trajectory_metadata"]["schema_version"],
        "trajectory_metadata_table_v1"
    );
    assert_eq!(manifest_json["trajectory_metadata"]["row_count"], 3);
    assert_eq!(
        manifest_json["trajectory_metadata"]["total_sampling_weight"],
        3.0
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["probability_model"],
        "unweighted"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["normalization_convention"],
        "unweighted_current_outputs"
    );
    assert!(
        manifest_json["performance"]["total_wall_seconds"]
            .as_f64()
            .unwrap()
            >= 0.0
    );
    assert!(
        manifest_json["performance"]["simulation_seconds"]
            .as_f64()
            .unwrap()
            >= 0.0
    );
    assert!(
        manifest_json["performance"]["output_write_seconds"]
            .as_f64()
            .unwrap()
            >= 0.0
    );
    assert!(
        manifest_json["performance"]["trajectory_count"]
            .as_u64()
            .unwrap()
            >= 1
    );
    assert!(
        manifest_json["performance"]["output_file_count"]
            .as_u64()
            .unwrap()
            >= 4
    );
    let trajectory_dir_manifest = manifest_json["outputs"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entry| entry["kind"] == "ensemble_trajectories")
        .expect("ensemble trajectory directory output manifest");
    assert_eq!(trajectory_dir_manifest["file_count"], 3);
    assert!(trajectory_dir_manifest["row_count"].as_u64().unwrap() > 0);
    assert_eq!(trajectory_dir_manifest["format"], "csv_directory");
    assert_eq!(
        trajectory_dir_manifest["sha256"].as_str().unwrap().len(),
        64
    );
    let csv_impact_row_count: usize = fs::read_dir(&ensemble_impacts_dir)
        .unwrap()
        .map(|entry| {
            let path = entry.unwrap().path();
            csv::Reader::from_path(path).unwrap().records().count()
        })
        .sum();
    let csv_impact_manifest = manifest_json["outputs"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entry| {
            entry["kind"] == "ensemble_impact_events" && entry["format"] == "csv_directory"
        })
        .expect("ensemble impact-event csv directory output manifest");
    assert_eq!(
        csv_impact_manifest["row_count"].as_u64().unwrap(),
        csv_impact_row_count as u64
    );
    assert_eq!(csv_impact_manifest["sha256"].as_str().unwrap().len(), 64);
    let parquet_manifest = manifest_json["outputs"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entry| entry["kind"] == "ensemble_impact_events" && entry["format"] == "parquet")
        .expect("ensemble impact-event parquet output manifest");
    assert_eq!(parquet_manifest["schema_version"], "impact_events_table_v1");
    assert_eq!(
        parquet_manifest["row_count"].as_u64().unwrap(),
        csv_impact_row_count as u64
    );
    assert_eq!(parquet_manifest["file_count"], 1);
    assert_eq!(parquet_manifest["compression"], "uncompressed");
    assert!(parquet_manifest["sha256"].as_str().unwrap().len() == 64);
    let first_contents = fs::read_to_string(&first_file).unwrap();
    assert!(first_contents.starts_with("trajectory_id,time_s"));
    assert!(first_contents.contains("trajectory_000000"));
    let impact_contents = fs::read_to_string(&first_impacts).unwrap();
    assert!(impact_contents.starts_with("trajectory_id,impact_index"));
    assert!(impact_contents.contains("trajectory_000000"));
    let metadata_contents = fs::read_to_string(&metadata).unwrap();
    assert!(metadata_contents.starts_with("trajectory_id,release_id,source_zone_id"));
    assert!(metadata_contents.contains("trajectory_000000,trajectory_000000,manual_release"));
    assert!(metadata_contents.contains("release_probability"));
    assert!(metadata_contents.contains("block_density_kgpm3"));
    assert!(metadata_contents.contains("probability_model"));
    assert!(metadata_contents.contains("unweighted"));
    assert_eq!(metadata_contents.lines().count(), 4);

    fs::write(
        &stale_trajectory,
        "trajectory_id,time_s,x_m,y_m,z_m\nstale,0,0,0,0\n",
    )
    .unwrap();
    fs::write(
        &stale_impact,
        "trajectory_id,impact_index,time_s,x_m,y_m,z_m\nstale,1,0,0,0,0\n",
    )
    .unwrap();
    let second = run_case_file(&case_path).unwrap();
    assert_eq!(first.metrics, second.metrics);
    assert_eq!(first_contents, fs::read_to_string(&first_file).unwrap());
    assert_eq!(metadata_contents, fs::read_to_string(&metadata).unwrap());
    assert!(!stale_trajectory.exists());
    assert!(!stale_impact.exists());

    fs::remove_file(case_path).unwrap();
    fs::remove_file(diagnostics).unwrap();
    fs::remove_file(manifest).unwrap();
    fs::remove_file(trajectory).unwrap();
    fs::remove_file(metadata).unwrap();
    fs::remove_file(ensemble_impacts_parquet).unwrap();
    fs::remove_file(first_file).unwrap();
    fs::remove_file(second_file).unwrap();
    fs::remove_file(third_file).unwrap();
    for entry in fs::read_dir(&ensemble_impacts_dir).unwrap() {
        fs::remove_file(entry.unwrap().path()).unwrap();
    }
    fs::remove_dir(ensemble_dir).unwrap();
    fs::remove_dir(ensemble_impacts_dir).unwrap();
}

#[test]
fn passive_shape_metadata_is_manifested_and_does_not_change_runout() {
    let shape_path = temp_path("passive_shape.yaml");
    let shaped_case_path = temp_path("passive_shape_case.yaml");
    let baseline_case_path = temp_path("passive_shape_baseline.yaml");
    let diagnostics = temp_path("passive_shape_metrics.json");
    let manifest = temp_path("passive_shape_manifest.json");
    let metadata = temp_path("passive_shape_trajectory_metadata.csv");
    fs::write(
        &shape_path,
        r#"schema_version: shape_metadata_v1
shape_id: synthetic_box_block
shape_type: principal_dimensions
shape_class: blocky
dimensions_m:
  equivalent_radius_m: 0.5
  principal_lengths_m: [1.0, 0.8, 0.6]
mass_properties:
  mass_kg: 10.0
  density_kgpm3: 20.0
  mass_property_model: box_principal_dimensions
orientation:
  representation: quaternion_wxyz
  initialization_mode: identity
  initial_quaternion_wxyz: [1.0, 0.0, 0.0, 0.0]
provenance:
  source_dataset: synthetic_shape_fixture
  source_record_id: synthetic_box_block
  license: MIT
  notes: ["passive metadata test"]
"#,
    )
    .unwrap();
    let base_yaml = r#"case_id: passive_shape_scaffold
title: Passive shape scaffold
terrain:
  type: plane
  parameters: { z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }
block: { mass: 10.0, radius: 0.5 }
release:
  position: [0.0, 0.0, 1.0]
  velocity: [1.0, 0.0, -0.2]
parameters:
  gravity: 9.81
  normal_restitution: 0.3
  tangential_restitution: 0.8
  friction_coefficient: 0.4
simulation: { dt: 0.005, t_max: 0.5, stop_velocity: 0.01 }
random: { seed: 456, ensemble_size: 1 }
"#;
    fs::write(&baseline_case_path, base_yaml).unwrap();
    fs::write(
        &shaped_case_path,
        format!(
            r#"{base_yaml}block_shape:
  metadata_path: {}
outputs:
  diagnostics_json: {}
  manifest_json: {}
  trajectory_metadata_csv: {}
"#,
            shape_path.display(),
            diagnostics.display(),
            manifest.display(),
            metadata.display()
        ),
    )
    .unwrap();

    let baseline = run_case_file(&baseline_case_path).unwrap();
    let shaped = run_case_file(&shaped_case_path).unwrap();
    assert_eq!(shaped.status, CaseStatus::Passed);
    assert_abs_diff_eq!(
        shaped.metrics["runout_m"],
        baseline.metrics["runout_m"],
        epsilon = 1.0e-12
    );
    assert!(shaped
        .warnings
        .iter()
        .any(|warning| warning.contains("passive")));
    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(
        manifest_json["shape_metadata"]["schema_version"],
        "shape_metadata_v1"
    );
    assert_eq!(
        manifest_json["shape_metadata"]["active_contact_shape"],
        "sphere"
    );
    assert_eq!(
        manifest_json["shape_metadata"]["shape_id"],
        "synthetic_box_block"
    );
    assert_eq!(
        manifest_json["shape_metadata"]["principal_moments_kg_m2"][0],
        10.0 * (0.8_f64.powi(2) + 0.6_f64.powi(2)) / 12.0
    );
    assert!(manifest_json["shape_metadata"]["warnings"][0]
        .as_str()
        .unwrap()
        .contains("passive"));
    let metadata_contents = fs::read_to_string(&metadata).unwrap();
    assert!(metadata_contents.contains("shape_id"));
    assert!(metadata_contents.contains("synthetic_box_block"));
    assert!(metadata_contents.contains("principal_length_m"));
    assert!(metadata_contents.contains("0.8"));

    fs::remove_file(shape_path).unwrap();
    fs::remove_file(shaped_case_path).unwrap();
    fs::remove_file(baseline_case_path).unwrap();
    fs::remove_file(diagnostics).unwrap();
    fs::remove_file(manifest).unwrap();
    fs::remove_file(metadata).unwrap();
}

#[test]
fn swissalti3d_pilot_case_writes_terrain_provenance_manifest() {
    let diagnostics = PathBuf::from("validation/results/swissalti3d_pilot_metrics.json");
    let trajectory = PathBuf::from("validation/results/swissalti3d_pilot_trajectory.csv");
    let manifest = PathBuf::from("validation/results/swissalti3d_pilot_manifest.json");
    let _ = fs::remove_file(&diagnostics);
    let _ = fs::remove_file(&trajectory);
    let _ = fs::remove_file(&manifest);

    let report = run_case_file("validation/cases/swissalti3d_pilot.yaml").unwrap();

    assert_eq!(report.status, CaseStatus::Passed);
    assert!(manifest.exists());
    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(manifest_json["terrain"]["epsg"], 2056);
    assert_eq!(manifest_json["terrain"]["vertical_datum"], "LN02");
    assert_eq!(
        manifest_json["terrain"]["source_dataset"],
        "swisstopo_swissalti3d"
    );
    assert_eq!(
        manifest_json["terrain"]["metadata_path"],
        "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml"
    );
    assert_eq!(manifest_json["terrain"]["extent"]["xmin"], 2600000.0);
    assert!(
        manifest_json["performance"]["terrain_load_seconds"]
            .as_f64()
            .unwrap()
            >= 0.0
    );

    fs::remove_file(diagnostics).unwrap();
    fs::remove_file(trajectory).unwrap();
    fs::remove_file(manifest).unwrap();
}

#[test]
fn release_zone_metadata_parses_and_samples_deterministically() {
    let release_zone = ReleaseZoneMetadata::from_yaml_file(
        "validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml",
    )
    .unwrap();

    assert_eq!(release_zone.zone_id, "swissalti3d_pilot_source_area");
    assert_eq!(release_zone.coordinate_reference_system.epsg, 2056);
    assert_abs_diff_eq!(release_zone.area_m2(), 16.0, epsilon = 1.0e-12);

    let first = release_zone.sample_points().unwrap();
    let second = release_zone.sample_points().unwrap();
    assert_eq!(first, second);
    assert_eq!(first.len(), 4);
    assert!(first.iter().all(|point| point.x_m >= 2600001.0
        && point.x_m <= 2600005.0
        && point.y_m >= 1200001.0
        && point.y_m <= 1200005.0));
}

#[test]
fn release_zone_rejects_invalid_polygon_and_unsupported_crs() {
    let invalid_polygon = r#"
schema_version: 1
zone_id: invalid
source_dataset: synthetic
license: fixture
coordinate_reference_system:
  epsg: 2056
  horizontal_name: CH1903+ / LV95
  vertical_datum: LN02
  coordinate_unit: m
  height_unit: m
geometry:
  type: polygon
  coordinates:
    - [2600001.0, 1200001.0]
    - [2600002.0, 1200001.0]
sampling:
  mode: deterministic_grid
  count: 1
  seed: 1
provenance:
  intended_use: test
"#;
    assert!(ReleaseZoneMetadata::from_yaml_str(invalid_polygon).is_err());

    let unsupported_crs = invalid_polygon
        .replace(
            "- [2600002.0, 1200001.0]",
            "- [2600002.0, 1200001.0]\n    - [2600001.0, 1200002.0]",
        )
        .replace("epsg: 2056", "epsg: 4326");
    assert!(ReleaseZoneMetadata::from_yaml_str(&unsupported_crs).is_err());
}

#[test]
fn release_zone_crs_and_extent_match_swissalti3d_terrain_metadata() {
    let terrain = TerrainSourceMetadata::from_yaml_file(
        "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml",
    )
    .unwrap();
    let release_zone = ReleaseZoneMetadata::from_yaml_file(
        "validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml",
    )
    .unwrap();

    release_zone
        .validate_against_terrain_source(&terrain)
        .unwrap();

    let outside = serde_yaml::to_string(&release_zone)
        .unwrap()
        .replace("2600005.0", "2600015.0");
    let outside = ReleaseZoneMetadata::from_yaml_str(&outside).unwrap();
    assert!(outside.validate_against_terrain_source(&terrain).is_err());
}

#[test]
fn swissalti3d_release_zone_pilot_writes_release_manifest_and_points() {
    let diagnostics =
        PathBuf::from("validation/results/swissalti3d_release_zone_pilot_metrics.json");
    let manifest = PathBuf::from("validation/results/swissalti3d_release_zone_pilot_manifest.json");
    let releases = PathBuf::from("validation/results/swissalti3d_release_zone_points.csv");
    let deposition = PathBuf::from("validation/results/swissalti3d_release_zone_deposition.csv");
    let stop_state =
        PathBuf::from("validation/results/swissalti3d_release_zone_deposition_stop_state.csv");
    for path in [&diagnostics, &manifest, &releases, &deposition, &stop_state] {
        let _ = fs::remove_file(path);
    }

    let report = run_case_file("validation/cases/swissalti3d_release_zone_pilot.yaml").unwrap();

    assert_eq!(report.status, CaseStatus::Passed);
    assert_eq!(report.metrics["release_zone_point_count"], 4.0);
    assert!(manifest.exists());
    assert!(releases.exists());
    assert!(deposition.exists());
    assert!(stop_state.exists());
    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(
        manifest_json["release_zone"]["zone_id"],
        "swissalti3d_pilot_source_area"
    );
    assert_eq!(manifest_json["release_zone"]["epsg"], 2056);
    assert_eq!(manifest_json["release_zone"]["generated_release_points"], 4);
    assert_eq!(
        manifest_json["release_zone"]["metadata_path"],
        "validation/data/processed/swisstopo_pilot/release_zone_source_area.yaml"
    );
    let release_csv = fs::read_to_string(&releases).unwrap();
    assert!(release_csv.contains("source_zone_id"));
    assert!(release_csv.contains("swissalti3d_pilot_source_area"));
    let stop_state_csv = fs::read_to_string(&stop_state).unwrap();
    assert!(stop_state_csv.starts_with("release_id,trajectory_id,seed,stop_reason"));
    assert!(stop_state_csv.contains("final_contact_state"));
    assert!(stop_state_csv.contains("terrain_slope_abs"));
    assert!(stop_state_csv.contains("terrain_material_context_available"));
    assert_eq!(stop_state_csv.lines().count(), 5);
    let stop_state_row = read_first_csv_row(&stop_state);
    assert_eq!(
        stop_state_row["terrain_material_context_available"],
        "false"
    );
    assert!(stop_state_row["terrain_material_instrumentation_gaps"]
        .contains("terrain_classes metadata is not configured"));
    assert_eq!(
        manifest_json["stop_state_summary"]["schema_version"],
        "stop_state_summary_v3"
    );
    assert_eq!(manifest_json["stop_state_summary"]["trajectory_count"], 4);
    assert_eq!(
        manifest_json["stop_state_summary"]["explicit_stop_state_count"],
        4
    );
    assert_eq!(
        manifest_json["stop_state_summary"]["path"],
        "validation/results/swissalti3d_release_zone_deposition_stop_state.csv"
    );
    assert!(manifest_json["outputs"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| {
            entry["kind"] == "ensemble_stop_state"
                && entry["schema_version"] == "stop_state_table_v3"
                && entry["row_count"] == 4
        }));

    for path in [&diagnostics, &manifest, &releases, &deposition, &stop_state] {
        fs::remove_file(path).unwrap();
    }
}

#[test]
fn legacy_stop_state_csv_rows_default_missing_terrain_material_fields() {
    let csv = r#"release_id,trajectory_id,seed,stop_reason,final_contact_state,final_speed_mps,final_kinetic_j,termination_low_velocity,termination_max_steps,termination_t_max,termination_domain_exit,termination_terrain_error,last_significant_impact_time_s,last_significant_impact_x_m,last_significant_impact_y_m,last_significant_impact_z_m,distance_last_significant_impact_to_final_m,low_energy_contact_count,terrain_normal_x,terrain_normal_y,terrain_normal_z,terrain_slope_abs,runout_m
r1,t1,1,explicit_stopped_state,stopped,0.0,0.0,true,false,false,false,false,,,,,,1,0.0,0.0,1.0,0.0,2.0
"#;
    let mut reader = csv::Reader::from_reader(csv.as_bytes());
    let row: rust_rockfall::validation::EnsembleStopStateRow =
        reader.deserialize().next().unwrap().unwrap();

    assert!(!row.terrain_material_context_available);
    assert!(row.final_terrain_class_id.is_none());
    assert!(row.final_terrain_class_name.is_none());
    assert!(row.final_terrain_class_source.is_none());
    assert!(row.last_significant_impact_terrain_class_id.is_none());
    assert!(row.significant_impact_count.is_none());
    assert!(row.significant_impact_terrain_class_counts.is_empty());
    assert!(row
        .significant_impact_terrain_class_sequence_head
        .is_empty());
    assert!(row
        .significant_impact_terrain_class_sequence_tail
        .is_empty());
    assert!(!row.significant_impact_terrain_class_sequence_truncated);
    assert_eq!(row.significant_impact_terrain_class_unavailable_count, 0);
    assert!(row.terrain_material_instrumentation_gaps.is_empty());
}

#[test]
fn terrain_class_metadata_parses_and_matches_swissalti3d_dem() {
    let terrain = TerrainSourceMetadata::from_yaml_file(
        "validation/data/processed/swisstopo_pilot/swissalti3d_pilot_metadata.yaml",
    )
    .unwrap();
    let class_map = TerrainClassMap::from_metadata_file(
        "validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml",
    )
    .unwrap();

    class_map.validate_against_terrain_source(&terrain).unwrap();
    assert_eq!(
        class_map.metadata.layer_id,
        "swissalti3d_pilot_material_classes"
    );
    assert_eq!(class_map.coverage().len(), 2);
    assert_eq!(class_map.class_id_at(2600001.0, 1200001.0), Some(1));
    assert_eq!(
        class_map.class_id_at(2600007.999999, 1200007.999999),
        Some(1)
    );
    assert_eq!(class_map.class_id_at(2600008.0, 1200008.0), None);
}

#[test]
fn terrain_class_metadata_rejects_bad_crs_and_unknown_class_id() {
    let text = fs::read_to_string(
        "validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml",
    )
    .unwrap();
    let bad_crs = text.replace("epsg: 2056", "epsg: 4326");
    assert!(TerrainClassMetadata::from_yaml_str(&bad_crs).is_err());

    let metadata = TerrainClassMetadata::from_yaml_str(&text).unwrap();
    let unknown_grid = r#"
ncols 4
nrows 4
xllcorner 2600000
yllcorner 1200000
cellsize 2
NODATA_value -9999
2 2 1 1
2 9 1 1
1 1 2 2
1 1 2 2
"#;
    let grid =
        rust_rockfall::geodata::TerrainClassGrid::from_ascii_grid_str(unknown_grid.trim()).unwrap();
    assert!(TerrainClassMap::from_metadata_and_grid(metadata, grid).is_err());
}

#[test]
fn terrain_class_lookup_overrides_only_configured_parameters() {
    let class_map = TerrainClassMap::from_metadata_file(
        "validation/data/processed/swisstopo_pilot/terrain_classes_metadata.yaml",
    )
    .unwrap();
    let base = ContactParameters {
        normal_restitution: 0.2,
        tangential_restitution: 0.8,
        friction_coefficient: 0.45,
        rolling_resistance_coefficient: 0.0,
        scarring: ScarringSettings::default(),
    };

    let bedrock = class_map.parameters_at(2600001.0, 1200001.0, base);
    assert_abs_diff_eq!(bedrock.normal_restitution, 0.32);
    assert_abs_diff_eq!(bedrock.tangential_restitution, 0.90);
    assert_abs_diff_eq!(bedrock.friction_coefficient, 0.35);
    assert_eq!(bedrock.scarring, base.scarring);

    let talus = class_map.parameters_at(2600005.0, 1200003.0, base);
    assert_abs_diff_eq!(talus.normal_restitution, 0.18);
    assert_abs_diff_eq!(talus.friction_coefficient, 0.55);
    assert_abs_diff_eq!(talus.scarring.soil_strength_pa, 60000.0);

    let outside = class_map.parameters_at(2599990.0, 1199990.0, base);
    assert_eq!(outside, base);
}

#[test]
fn swissalti3d_terrain_class_pilot_writes_class_manifest() {
    let diagnostics = PathBuf::from(
        "validation/results/swissalti3d_release_zone_terrain_classes_pilot_metrics.json",
    );
    let manifest = PathBuf::from(
        "validation/results/swissalti3d_release_zone_terrain_classes_pilot_manifest.json",
    );
    let releases = PathBuf::from("validation/results/swissalti3d_terrain_class_release_points.csv");
    let deposition = PathBuf::from("validation/results/swissalti3d_terrain_class_deposition.csv");
    let stop_state =
        PathBuf::from("validation/results/swissalti3d_terrain_class_deposition_stop_state.csv");
    let exposure = PathBuf::from(
        "validation/results/swissalti3d_terrain_class_deposition_terrain_material_exposure.csv",
    );
    for path in [
        &diagnostics,
        &manifest,
        &releases,
        &deposition,
        &stop_state,
        &exposure,
    ] {
        let _ = fs::remove_file(path);
    }

    let report =
        run_case_file("validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml")
            .unwrap();

    assert_eq!(report.status, CaseStatus::Passed);
    assert_eq!(report.metrics["release_zone_point_count"], 4.0);
    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(
        manifest_json["terrain_classes"]["layer_id"],
        "swissalti3d_pilot_material_classes"
    );
    assert_eq!(
        manifest_json["terrain_classes"]["schema_version"],
        "terrain_class_manifest_v1"
    );
    assert_eq!(
        manifest_json["terrain_classes"]["metadata_schema_version"],
        1
    );
    assert!(
        manifest_json["terrain_classes"]["metadata_sha256"]
            .as_str()
            .unwrap()
            .len()
            >= 64
    );
    assert!(
        manifest_json["terrain_classes"]["class_grid_sha256"]
            .as_str()
            .unwrap()
            .len()
            >= 64
    );
    assert_eq!(manifest_json["terrain_classes"]["epsg"], 2056);
    assert_eq!(
        manifest_json["terrain_classes"]["class_coverage"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    let bedrock_coverage = manifest_json["terrain_classes"]["class_coverage"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entry| entry["class_id"] == 1)
        .unwrap();
    assert_eq!(bedrock_coverage["active_parameter_override_count"], 4);
    assert_eq!(
        bedrock_coverage["active_parameter_override_fields"]
            .as_array()
            .unwrap()
            .iter()
            .map(|value| value.as_str().unwrap())
            .collect::<Vec<_>>(),
        vec![
            "restitution_n",
            "restitution_t",
            "friction_mu",
            "rolling_resistance"
        ]
    );
    assert!(releases.exists());
    assert!(deposition.exists());
    assert!(stop_state.exists());
    assert!(exposure.exists());
    let stop_state_row = read_first_csv_row(&stop_state);
    assert_eq!(stop_state_row["terrain_material_context_available"], "true");
    assert_eq!(
        stop_state_row["final_terrain_class_source"],
        "swissalti3d_pilot_material_classes"
    );
    assert!(matches!(
        stop_state_row["final_terrain_class_name"].as_str(),
        "synthetic_bedrock" | "synthetic_talus"
    ));
    assert!(
        manifest_json["stop_state_summary"]["terrain_material_context_available_count"]
            .as_u64()
            .unwrap()
            > 0
    );
    assert!(
        !manifest_json["stop_state_summary"]["final_terrain_class_counts"]
            .as_object()
            .unwrap()
            .is_empty()
    );
    assert!(
        !manifest_json["stop_state_summary"]["significant_impact_terrain_class_counts"]
            .as_object()
            .unwrap()
            .is_empty()
    );
    assert_ne!(
        stop_state_row["significant_impact_terrain_class_counts"],
        "{}"
    );
    let exposure_row = read_first_csv_row(&exposure);
    assert_eq!(
        exposure_row["terrain_class_source"],
        "swissalti3d_pilot_material_classes"
    );
    assert_eq!(
        exposure_row["terrain_material_context_status"],
        "classified"
    );
    assert!(
        manifest_json["terrain_material_exposure_summary"]["classified_sample_count"]
            .as_u64()
            .unwrap()
            > 0
    );
    assert!(manifest_json["outputs"]
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| {
            entry["kind"] == "release_zone_terrain_material_exposure"
                && entry["schema_version"] == "terrain_material_exposure_table_v1"
        }));

    for path in [
        &diagnostics,
        &manifest,
        &releases,
        &deposition,
        &stop_state,
        &exposure,
    ] {
        fs::remove_file(path).unwrap();
    }
}

#[test]
fn terrain_class_stop_state_reports_out_of_grid_gap() {
    let case_path = temp_path("terrain_class_out_of_grid_case.yaml");
    let metadata_path = temp_path("terrain_class_out_of_grid_metadata.yaml");
    let grid_path = metadata_path.with_file_name("terrain_class_out_of_grid.asc");
    let diagnostics = temp_path("terrain_class_out_of_grid_diagnostics.json");
    let manifest = temp_path("terrain_class_out_of_grid_manifest.json");

    fs::write(
        &grid_path,
        r#"ncols 1
nrows 1
xllcorner 100
yllcorner 100
cellsize 1
NODATA_value -9999
1
"#,
    )
    .unwrap();
    fs::write(
        &metadata_path,
        format!(
            r#"schema_version: 1
layer_id: out_of_grid_material_fixture
source_dataset: synthetic_fixture
source_url: null
license: synthetic fixture
coordinate_reference_system:
  epsg: 2056
  horizontal_name: CH1903+ / LV95
  vertical_datum: LN02
  coordinate_unit: m
  height_unit: m
raster:
  format: ESRI ASCII GRID
  resolution_m: 1.0
  width_px: 1
  height_px: 1
  nodata: -9999.0
extent_lv95_m:
  xmin: 100.0
  ymin: 100.0
  xmax: 101.0
  ymax: 101.0
class_grid_path: {}
classes:
  - id: 1
    name: synthetic_class
    parameter_overrides: {{}}
provenance:
  intended_use: stop_state_out_of_grid_test
  notes: ["Synthetic test fixture."]
"#,
            grid_path.file_name().unwrap().to_string_lossy()
        ),
    )
    .unwrap();
    fs::write(
        &case_path,
        format!(
            r#"case_id: terrain_class_out_of_grid_case
terrain: {{ type: plane, parameters: {{ z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }} }}
terrain_classes:
  metadata_path: {}
block: {{ mass: 10.0, radius: 0.5 }}
release: {{ position: [0.0, 0.0, 0.5], velocity: [1.0, 0.0, 0.0] }}
parameters:
  gravity: 9.81
  normal_restitution: 0.0
  tangential_restitution: 1.0
  friction_coefficient: 0.5
simulation: {{ dt: 0.01, t_max: 5.0, max_steps: 500, stop_velocity: 0.05 }}
outputs:
  diagnostics_json: {}
  manifest_json: {}
"#,
            metadata_path.display(),
            diagnostics.display(),
            manifest.display()
        ),
    )
    .unwrap();

    let report = run_case_file(&case_path).unwrap();
    let stop_state = report.stop_state.unwrap();

    assert!(!stop_state.terrain_material_context_available);
    assert!(stop_state.final_terrain_class_id.is_none());
    assert!(stop_state
        .terrain_material_instrumentation_gaps
        .iter()
        .any(|gap| gap.contains("final position has no terrain/material class")));
    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(
        manifest_json["stop_state"]["terrain_material_context_available"],
        false
    );

    for path in [
        &case_path,
        &metadata_path,
        &grid_path,
        &diagnostics,
        &manifest,
    ] {
        fs::remove_file(path).unwrap();
    }
}

#[test]
fn probabilistic_scenario_metadata_propagates_to_trajectory_metadata() {
    let case_path = temp_path("probabilistic_metadata_case.yaml");
    let no_prob_case_path = temp_path("probabilistic_metadata_baseline_case.yaml");
    let metadata = temp_path("probabilistic_trajectory_metadata.csv");
    let diagnostics = temp_path("probabilistic_metadata_diagnostics.json");
    let manifest = temp_path("probabilistic_metadata_manifest.json");
    let baseline_diagnostics = temp_path("probabilistic_metadata_baseline.json");
    fs::write(
        &case_path,
        probabilistic_metadata_case_yaml(ProbabilisticMetadataCaseYamlInput {
            case_id: "probabilistic_metadata_case",
            source_zone_metadata_path: Some(
                "tests/fixtures/probabilistic_phase1/source_zone_valid.yaml",
            ),
            scenario_table_path: Some("tests/fixtures/probabilistic_phase1/scenario_level1.csv"),
            map_product_id: Some("phase1_test_map"),
            probability_mode: Some("sampling_weighted_conditional"),
            normalization_scope: Some("conditioned_on_scenario"),
            scenario_id: None,
            metadata: &metadata,
            diagnostics: &diagnostics,
            manifest: Some(&manifest),
        }),
    )
    .unwrap();
    fs::write(
        &no_prob_case_path,
        format!(
            r#"case_id: probabilistic_metadata_case
terrain: {{ type: plane, parameters: {{ z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }} }}
block: {{ mass: 50.0, radius: 0.25 }}
release: {{ position: [0.0, 0.0, 1.0], velocity: [1.0, 0.0, 0.0] }}
simulation: {{ dt: 0.02, t_max: 0.1, max_steps: 5, stop_velocity: 0.1 }}
outputs:
  diagnostics_json: {}
"#,
            baseline_diagnostics.display()
        ),
    )
    .unwrap();

    let report = run_case_file(&case_path).unwrap();
    let baseline = run_case_file(&no_prob_case_path).unwrap();
    assert_eq!(report.metrics, baseline.metrics);
    let row = read_first_csv_row(&metadata);
    assert_eq!(row["trajectory_id"], "trajectory_000000");
    assert_eq!(row["map_product_id"], "phase1_test_map");
    assert_eq!(row["source_zone_id"], "zone_a");
    assert_eq!(row["release_cell_id"], "trajectory_000000");
    assert_eq!(row["scenario_id"], "scenario_a");
    assert_eq!(row["block_scenario_id"], "block_a");
    assert_eq!(row["block_size_class"], "equivalent_radius_small");
    assert_eq!(row["block_shape_class"], "sphere");
    assert_eq!(
        row["terrain_material_assumption_id"],
        "uniform_global_parameters"
    );
    assert_eq!(row["model_configuration_id"], "translational_v0");
    assert_eq!(row["sampling_weight"], "1.0");
    assert_eq!(row["probability_model"], "sampling_weighted");
    assert_eq!(row["probability_mode"], "sampling_weighted_conditional");
    assert_eq!(row["normalization_scope"], "conditioned_on_scenario");
    assert_eq!(row["annual_frequency_per_year"], "");

    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(
        manifest_json["trajectory_metadata"]["map_product_id"],
        "phase1_test_map"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["probability_mode"],
        "sampling_weighted_conditional"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["normalization_scope"],
        "conditioned_on_scenario"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["scenario_id"],
        "scenario_a"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["total_sampling_weight"],
        1.0
    );

    for path in [
        case_path,
        no_prob_case_path,
        metadata,
        diagnostics,
        manifest,
        baseline_diagnostics,
    ] {
        fs::remove_file(path).unwrap();
    }
}

#[test]
fn probabilistic_phase1_smoke_case_propagates_scenario_metadata() {
    let diagnostics = PathBuf::from("validation/results/probabilistic_phase1_smoke_metrics.json");
    let manifest = PathBuf::from("validation/results/probabilistic_phase1_smoke_manifest.json");
    let metadata =
        PathBuf::from("validation/results/probabilistic_phase1_smoke_trajectory_metadata.csv");
    let trajectory = PathBuf::from("validation/results/probabilistic_phase1_smoke_trajectory.csv");
    let releases =
        PathBuf::from("validation/results/probabilistic_phase1_smoke_release_points.csv");
    let deposition = PathBuf::from("validation/results/probabilistic_phase1_smoke_deposition.csv");
    let trajectories = PathBuf::from("validation/results/probabilistic_phase1_smoke_trajectories");
    for path in [
        &diagnostics,
        &manifest,
        &metadata,
        &trajectory,
        &releases,
        &deposition,
    ] {
        let _ = fs::remove_file(path);
    }
    let _ = fs::remove_dir_all(&trajectories);

    let report = run_case_file("validation/cases/probabilistic_phase1_smoke.yaml").unwrap();
    assert_eq!(report.status, CaseStatus::Passed);
    assert!(manifest.exists());
    assert!(metadata.exists());
    assert!(trajectory.exists());
    assert_eq!(fs::read_dir(&trajectories).unwrap().count(), 4);

    let row = read_first_csv_row(&metadata);
    assert_eq!(row["map_product_id"], "phase1_smoke_map");
    assert_eq!(row["source_zone_id"], "swissalti3d_pilot_source_area");
    assert_eq!(row["scenario_id"], "phase1_smoke_scenario");
    assert_eq!(row["release_cell_id"], row["release_id"]);
    assert_eq!(row["block_scenario_id"], "phase1_smoke_block");
    assert_eq!(
        row["terrain_material_assumption_id"],
        "uniform_global_parameters"
    );
    assert_eq!(row["model_configuration_id"], "translational_v0");
    assert_eq!(row["sampling_weight"], "1.0");
    assert_eq!(row["probability_mode"], "sampling_weighted_conditional");
    assert_eq!(row["normalization_scope"], "conditioned_on_scenario");
    assert_eq!(row["annual_frequency_per_year"], "");

    let manifest_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&manifest).unwrap()).unwrap();
    assert_eq!(
        manifest_json["trajectory_metadata"]["map_product_id"],
        "phase1_smoke_map"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["source_zone_id"],
        "swissalti3d_pilot_source_area"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["scenario_id"],
        "phase1_smoke_scenario"
    );
    assert_eq!(
        manifest_json["trajectory_metadata"]["probability_mode"],
        "sampling_weighted_conditional"
    );

    for path in [
        &diagnostics,
        &manifest,
        &metadata,
        &trajectory,
        &releases,
        &deposition,
    ] {
        let _ = fs::remove_file(path);
    }
    let _ = fs::remove_dir_all(&trajectories);
}

#[test]
fn probabilistic_metadata_requires_source_zone_sidecar() {
    let case_path = temp_path("probabilistic_metadata_missing_source.yaml");
    let metadata = temp_path("probabilistic_metadata_missing_source.csv");
    let diagnostics = temp_path("probabilistic_metadata_missing_source.json");
    fs::write(
        &case_path,
        probabilistic_metadata_case_yaml(ProbabilisticMetadataCaseYamlInput {
            case_id: "probabilistic_metadata_missing_source",
            source_zone_metadata_path: None,
            scenario_table_path: Some("tests/fixtures/probabilistic_phase1/scenario_level1.csv"),
            map_product_id: Some("phase1_test_map"),
            probability_mode: Some("sampling_weighted_conditional"),
            normalization_scope: Some("conditioned_on_scenario"),
            scenario_id: None,
            metadata: &metadata,
            diagnostics: &diagnostics,
            manifest: None,
        }),
    )
    .unwrap();
    let error = run_case_file(&case_path).unwrap_err().to_string();
    assert!(error.contains("source_zone_metadata_path"));
    fs::remove_file(case_path).unwrap();
}

#[test]
fn probabilistic_metadata_rejects_invalid_scenario_tables() {
    let case_path = temp_path("probabilistic_metadata_invalid.yaml");
    let metadata = temp_path("probabilistic_metadata_invalid.csv");
    let diagnostics = temp_path("probabilistic_metadata_invalid.json");
    fs::write(
        &case_path,
        probabilistic_metadata_case_yaml(ProbabilisticMetadataCaseYamlInput {
            case_id: "probabilistic_metadata_invalid",
            source_zone_metadata_path: Some(
                "tests/fixtures/probabilistic_phase1/source_zone_valid.yaml",
            ),
            scenario_table_path: Some(
                "tests/fixtures/probabilistic_phase1/scenario_negative_weight_invalid.csv",
            ),
            map_product_id: Some("phase1_test_map"),
            probability_mode: Some("sampling_weighted_conditional"),
            normalization_scope: Some("conditioned_on_scenario"),
            scenario_id: None,
            metadata: &metadata,
            diagnostics: &diagnostics,
            manifest: None,
        }),
    )
    .unwrap();
    let error = run_case_file(&case_path).unwrap_err().to_string();
    assert!(error.contains("sampling_weight"));

    fs::write(
        &case_path,
        probabilistic_metadata_case_yaml(ProbabilisticMetadataCaseYamlInput {
            case_id: "probabilistic_metadata_mismatch",
            source_zone_metadata_path: Some(
                "tests/fixtures/probabilistic_phase1/source_zone_valid.yaml",
            ),
            scenario_table_path: Some(
                "tests/fixtures/probabilistic_phase1/scenario_source_zone_mismatch_invalid.csv",
            ),
            map_product_id: Some("phase1_test_map"),
            probability_mode: Some("sampling_weighted_conditional"),
            normalization_scope: Some("conditioned_on_scenario"),
            scenario_id: None,
            metadata: &metadata,
            diagnostics: &diagnostics,
            manifest: None,
        }),
    )
    .unwrap();
    let error = run_case_file(&case_path).unwrap_err().to_string();
    assert!(error.contains("source_zone_id"));

    fs::remove_file(case_path).unwrap();
}

#[test]
fn probabilistic_metadata_requires_explicit_mapping_for_multiple_scenarios() {
    let case_path = temp_path("probabilistic_metadata_multiscenario.yaml");
    let metadata = temp_path("probabilistic_metadata_multiscenario.csv");
    let diagnostics = temp_path("probabilistic_metadata_multiscenario.json");
    fs::write(
        &case_path,
        probabilistic_metadata_case_yaml(ProbabilisticMetadataCaseYamlInput {
            case_id: "probabilistic_metadata_multiscenario",
            source_zone_metadata_path: Some(
                "tests/fixtures/probabilistic_phase1/source_zone_valid.yaml",
            ),
            scenario_table_path: Some(
                "tests/fixtures/probabilistic_phase1/scenario_level2_weighted.csv",
            ),
            map_product_id: Some("phase1_test_map"),
            probability_mode: Some("sampling_weighted_conditional"),
            normalization_scope: Some("conditioned_on_filter"),
            scenario_id: None,
            metadata: &metadata,
            diagnostics: &diagnostics,
            manifest: None,
        }),
    )
    .unwrap();
    let error = run_case_file(&case_path).unwrap_err().to_string();
    assert!(error.contains("scenario_id is required"));

    fs::write(
        &case_path,
        probabilistic_metadata_case_yaml(ProbabilisticMetadataCaseYamlInput {
            case_id: "probabilistic_metadata_multiscenario",
            source_zone_metadata_path: Some(
                "tests/fixtures/probabilistic_phase1/source_zone_valid.yaml",
            ),
            scenario_table_path: Some(
                "tests/fixtures/probabilistic_phase1/scenario_level2_weighted.csv",
            ),
            map_product_id: Some("phase1_test_map"),
            probability_mode: Some("sampling_weighted_conditional"),
            normalization_scope: Some("conditioned_on_filter"),
            scenario_id: Some("scenario_b"),
            metadata: &metadata,
            diagnostics: &diagnostics,
            manifest: None,
        }),
    )
    .unwrap();
    let report = run_case_file(&case_path).unwrap();
    assert_eq!(report.status, CaseStatus::Passed);
    let row = read_first_csv_row(&metadata);
    assert_eq!(row["scenario_id"], "scenario_b");
    assert_eq!(row["sampling_weight"], "0.75");
    assert_eq!(row["model_configuration_id"], "sphere_rotational_v1");

    for path in [case_path, metadata, diagnostics] {
        fs::remove_file(path).unwrap();
    }
}

#[test]
fn probabilistic_metadata_keeps_annual_frequency_unsupported_in_phase1() {
    let case_path = temp_path("probabilistic_metadata_annual.yaml");
    let metadata = temp_path("probabilistic_metadata_annual.csv");
    let diagnostics = temp_path("probabilistic_metadata_annual.json");
    fs::write(
        &case_path,
        probabilistic_metadata_case_yaml(ProbabilisticMetadataCaseYamlInput {
            case_id: "probabilistic_metadata_annual",
            source_zone_metadata_path: Some(
                "tests/fixtures/probabilistic_phase1/source_zone_valid.yaml",
            ),
            scenario_table_path: Some("tests/fixtures/probabilistic_phase1/scenario_level1.csv"),
            map_product_id: Some("phase1_test_map"),
            probability_mode: Some("annual_frequency"),
            normalization_scope: Some("annual_frequency_sum"),
            scenario_id: None,
            metadata: &metadata,
            diagnostics: &diagnostics,
            manifest: None,
        }),
    )
    .unwrap();
    let error = run_case_file(&case_path).unwrap_err().to_string();
    assert!(error.contains("Level 3"));
    fs::remove_file(case_path).unwrap();
}

fn minimal_config() -> SimulationConfig {
    SimulationConfig {
        block: SphereBlock::new(0.5, 10.0),
        initial_position_m: [0.0, 0.0, 2.0],
        initial_velocity_mps: [1.0, 0.0, 0.0],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::Plane {
            z0_m: 0.0,
            slope_x: 0.0,
            slope_y: 0.0,
        },
        dt_s: 0.01,
        max_time_s: 0.05,
        gravity_mps2: 9.81,
        normal_restitution: 0.25,
        tangential_restitution: 0.85,
        friction_coefficient: 0.45,
        rolling_resistance_coefficient: 0.0,
        contact_model: ContactModel::TranslationalV0,
        soil_interaction_model: SoilInteractionModel::None,
        soil_strength_pa: 0.0,
        scarring_drag_coefficient: 0.0,
        scarring_layer_density_kgpm3: 0.0,
        scarring_max_depth_m: None,
        roughness_model: RoughnessModel::None,
        roughness_std_normal: 0.0,
        roughness_std_tangent: 0.0,
        roughness_std_angle: 0.0,
        stop_speed_mps: 0.1,
        random_seed: None,
        release_perturbation: ReleasePerturbation::default(),
    }
}

fn temp_path(name: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    std::env::temp_dir().join(format!("rust_rockfall_{nonce}_{name}"))
}

struct ProbabilisticMetadataCaseYamlInput<'a> {
    case_id: &'a str,
    source_zone_metadata_path: Option<&'a str>,
    scenario_table_path: Option<&'a str>,
    map_product_id: Option<&'a str>,
    probability_mode: Option<&'a str>,
    normalization_scope: Option<&'a str>,
    scenario_id: Option<&'a str>,
    metadata: &'a Path,
    diagnostics: &'a Path,
    manifest: Option<&'a Path>,
}

fn probabilistic_metadata_case_yaml(input: ProbabilisticMetadataCaseYamlInput<'_>) -> String {
    let ProbabilisticMetadataCaseYamlInput {
        case_id,
        source_zone_metadata_path,
        scenario_table_path,
        map_product_id,
        probability_mode,
        normalization_scope,
        scenario_id,
        metadata,
        diagnostics,
        manifest,
    } = input;
    let mut probabilistic = String::from("probabilistic_metadata:\n");
    if let Some(path) = source_zone_metadata_path {
        probabilistic.push_str(&format!("  source_zone_metadata_path: {path}\n"));
    }
    if let Some(path) = scenario_table_path {
        probabilistic.push_str(&format!("  scenario_table_path: {path}\n"));
    }
    if let Some(map_product_id) = map_product_id {
        probabilistic.push_str(&format!("  map_product_id: {map_product_id}\n"));
    }
    if let Some(probability_mode) = probability_mode {
        probabilistic.push_str(&format!("  probability_mode: {probability_mode}\n"));
    }
    if let Some(normalization_scope) = normalization_scope {
        probabilistic.push_str(&format!("  normalization_scope: {normalization_scope}\n"));
    }
    if let Some(scenario_id) = scenario_id {
        probabilistic.push_str(&format!("  scenario_id: {scenario_id}\n"));
    }
    let manifest_line = manifest
        .map(|path| format!("  manifest_json: {}\n", path.display()))
        .unwrap_or_default();
    format!(
        r#"case_id: {case_id}
terrain: {{ type: plane, parameters: {{ z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 }} }}
block: {{ mass: 50.0, radius: 0.25 }}
release: {{ position: [0.0, 0.0, 1.0], velocity: [1.0, 0.0, 0.0] }}
simulation: {{ dt: 0.02, t_max: 0.1, max_steps: 5, stop_velocity: 0.1 }}
{probabilistic}outputs:
  trajectory_metadata_csv: {}
  diagnostics_json: {}
{}"#,
        metadata.display(),
        diagnostics.display(),
        manifest_line
    )
}

fn read_first_csv_row(path: &Path) -> BTreeMap<String, String> {
    let mut reader = csv::Reader::from_path(path).unwrap();
    let headers = reader.headers().unwrap().clone();
    let record = reader.records().next().unwrap().unwrap();
    headers
        .iter()
        .zip(record.iter())
        .map(|(key, value)| (key.to_string(), value.to_string()))
        .collect()
}
