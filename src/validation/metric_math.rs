pub(super) fn mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        0.0
    } else {
        values.iter().sum::<f64>() / values.len() as f64
    }
}

pub(super) fn nonempty_mean(values: &[f64]) -> Option<f64> {
    (!values.is_empty()).then(|| mean(values))
}

pub(super) fn percentile(values: &[f64], p: f64) -> f64 {
    // `values` must be sorted in ascending order before calling this function.
    // Linear interpolation between adjacent ranks; clamps `p` to [0, 1].
    if values.is_empty() {
        return 0.0;
    }
    let rank = p.clamp(0.0, 1.0) * (values.len().saturating_sub(1)) as f64;
    let lower = rank.floor() as usize;
    let upper = rank.ceil() as usize;
    if lower == upper {
        values[lower]
    } else {
        let weight = rank - lower as f64;
        values[lower] * (1.0 - weight) + values[upper] * weight
    }
}

pub(super) fn distance3(a: [f64; 3], b: [f64; 3]) -> f64 {
    ((a[0] - b[0]).powi(2) + (a[1] - b[1]).powi(2) + (a[2] - b[2]).powi(2)).sqrt()
}

pub(super) fn centroid2(points: &[(f64, f64)]) -> (f64, f64) {
    if points.is_empty() {
        return (0.0, 0.0);
    }
    let x = points.iter().map(|point| point.0).sum::<f64>() / points.len() as f64;
    let y = points.iter().map(|point| point.1).sum::<f64>() / points.len() as f64;
    (x, y)
}

pub(super) fn distance2(a: (f64, f64), b: (f64, f64)) -> f64 {
    ((a.0 - b.0).powi(2) + (a.1 - b.1).powi(2)).sqrt()
}

pub(super) fn symmetric_mean_nearest_distance(left: &[(f64, f64)], right: &[(f64, f64)]) -> f64 {
    0.5 * (mean_nearest_distance(left, right) + mean_nearest_distance(right, left))
}

fn mean_nearest_distance(from: &[(f64, f64)], to: &[(f64, f64)]) -> f64 {
    if from.is_empty() || to.is_empty() {
        return 0.0;
    }
    from.iter()
        .map(|point| {
            to.iter()
                .map(|candidate| distance2(*point, *candidate))
                .fold(f64::INFINITY, f64::min)
        })
        .sum::<f64>()
        / from.len() as f64
}

pub(super) fn stddev_axis_y(points: &[(f64, f64)]) -> f64 {
    // Returns the **population** standard deviation (divides by n, not n−1).
    if points.len() <= 1 {
        return 0.0;
    }
    let mean_y = points.iter().map(|point| point.1).sum::<f64>() / points.len() as f64;
    let variance = points
        .iter()
        .map(|point| (point.1 - mean_y).powi(2))
        .sum::<f64>()
        / points.len() as f64;
    variance.sqrt()
}

pub(super) fn cloud_overlap_fraction(
    simulated_points: &[(f64, f64)],
    observed_points: &[(f64, f64)],
    radius_m: f64,
) -> f64 {
    if simulated_points.is_empty() {
        return 0.0;
    }
    let hits = simulated_points
        .iter()
        .filter(|point| {
            observed_points
                .iter()
                .any(|observed| distance2(**point, *observed) <= radius_m)
        })
        .count();
    hits as f64 / simulated_points.len() as f64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn percentile_interpolates_and_clamps() {
        let values = [10.0, 20.0, 30.0, 40.0];

        assert_eq!(percentile(&values, -1.0), 10.0);
        assert_eq!(percentile(&values, 0.5), 25.0);
        assert_eq!(percentile(&values, 2.0), 40.0);
        assert_eq!(percentile(&[], 0.5), 0.0);
    }

    #[test]
    fn cloud_metrics_handle_empty_and_symmetric_nearest_cases() {
        let left = [(0.0, 0.0), (2.0, 0.0)];
        let right = [(1.0, 0.0), (3.0, 0.0)];

        assert_eq!(mean(&[]), 0.0);
        assert_eq!(nonempty_mean(&[]), None);
        assert_eq!(centroid2(&left), (1.0, 0.0));
        assert_eq!(distance2((0.0, 0.0), (3.0, 4.0)), 5.0);
        assert_eq!(distance3([0.0, 0.0, 0.0], [1.0, 2.0, 2.0]), 3.0);
        assert_eq!(symmetric_mean_nearest_distance(&left, &right), 1.0);
        assert_eq!(cloud_overlap_fraction(&left, &right, 1.0), 1.0);
        assert_eq!(cloud_overlap_fraction(&[], &right, 1.0), 0.0);
    }
}
