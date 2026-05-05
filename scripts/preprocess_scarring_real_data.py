#!/usr/bin/env python3
"""Build a small real impact-level scarring calibration dataset.

The source data are the open table downloads from Caviezel et al. (2019),
Earth Surface Dynamics. Table 1 provides scar dimensions and Table 2 provides
the reconstructed jump-wise impact and lift-off energies for the Chant Sura
RF16/RF18 EOTA221 runs. The output is a compact calibration CSV for the
existing single-impact scarring workflow.
"""

from __future__ import annotations

import csv
import math
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "chant_sura_2020"
OUT_DIR = ROOT / "calibration" / "data" / "scarring_single_impact"
OUT_CSV = OUT_DIR / "chant_sura_esurf_2019_impacts.csv"
OUT_METADATA = OUT_DIR / "chant_sura_esurf_2019_metadata.yaml"

TABLES = {
    "scar_dimensions": {
        "url": "https://esurf.copernicus.org/articles/7/199/2019/esurf-7-199-2019-t01.xlsx",
        "raw_file": "esurf-7-199-2019-t01.xlsx",
    },
    "trajectory_sections": {
        "url": "https://esurf.copernicus.org/articles/7/199/2019/esurf-7-199-2019-t02.xlsx",
        "raw_file": "esurf-7-199-2019-t02.xlsx",
    },
}

# The selected rows correspond to transitions explicitly linked to scars in
# Caviezel et al. (2019), Table 2. Rows with "mse" and "scp" are alternative
# reconstruction treatments and are intentionally excluded here.
TRANSITIONS = [
    ("21", "22", "2.1"),
    ("22", "23", "2.2"),
    ("23", "24", "2.3"),
    ("41", "42", "4.1"),
    ("42", "43", "4.2"),
    ("43", "44", "4.3"),
]

EOTA221_MASS_KG = 780.0
CONCRETE_DENSITY_KGPM3 = 2400.0
GRAVITY_MPS2 = 9.81


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_paths = {key: download_table(spec) for key, spec in TABLES.items()}

    scars = read_scar_table(raw_paths["scar_dimensions"])
    jumps, ratios = read_trajectory_table(raw_paths["trajectory_sections"])
    rows = build_rows(scars, jumps, ratios)
    write_csv(rows)
    write_metadata(len(rows))
    print(f"wrote {len(rows)} impacts to {OUT_CSV.relative_to(ROOT)}")
    return 0


def download_table(spec: dict[str, str]) -> Path:
    path = RAW_DIR / spec["raw_file"]
    if not path.exists():
        urllib.request.urlretrieve(spec["url"], path)
    return path


def read_xlsx_rows(path: Path) -> list[list[str]]:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{namespace}si"):
                shared_strings.append("".join(text.text or "" for text in item.iter(f"{namespace}t")))

        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in root.findall(f".//{namespace}row"):
            values: list[str] = []
            for cell in row.findall(f"{namespace}c"):
                value = cell.find(f"{namespace}v")
                text = "" if value is None else value.text or ""
                if cell.attrib.get("t") == "s" and text:
                    text = shared_strings[int(text)]
                values.append(text)
            rows.append(values)
    return rows


def read_scar_table(path: Path) -> dict[str, dict[str, float]]:
    rows = read_xlsx_rows(path)
    header = rows[0]
    scars: dict[str, dict[str, float]] = {}
    for row in rows[1:]:
        record = dict(zip(header, row))
        scar_id = record["Scar"]
        scars[scar_id] = {
            "length_ifm_m": parse_float(record.get("sLifm")),
            "length_adm_m": parse_float(record.get("sLadm")),
            "width_ifm_m": parse_float(record.get("sWifm")),
            "width_adm_m": parse_float(record.get("sWadm")),
            "depth_ifm_m": parse_float(record.get("sDifm")),
            "depth_adm_m": parse_float(record.get("sDadm")),
        }
    return scars


def read_trajectory_table(path: Path) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    rows = read_xlsx_rows(path)
    header = rows[0]
    jumps: dict[str, dict[str, float]] = {}
    ratios: dict[str, float] = {}
    for row in rows[1:]:
        record = dict(zip(header, row))
        run_jump = record["RunJNr"]
        if "mse" in run_jump or "scp" in run_jump:
            continue
        if "→" in run_jump:
            ratios[run_jump] = parse_float(record.get("Ekinbn+1/Ekinen"))
            continue
        speed_begin, speed_end = split_pair(record["vresb/e (m\u2009s−1)"])
        energy_begin, energy_end = split_pair(record["Ekinb/e (kJ)"])
        jumps[run_jump] = {
            "jump_length_m": parse_float(record["JL (m)"]),
            "jump_height_m": parse_float(record["JH (m)"]),
            "velocity_begin_mps": speed_begin,
            "velocity_end_mps": speed_end,
            "energy_begin_j": 1000.0 * energy_begin,
            "energy_end_j": 1000.0 * energy_end,
        }
    return jumps, ratios


def build_rows(
    scars: dict[str, dict[str, float]],
    jumps: dict[str, dict[str, float]],
    ratios: dict[str, float],
) -> list[dict[str, object]]:
    radius_m = equivalent_sphere_radius_m(EOTA221_MASS_KG, CONCRETE_DENSITY_KGPM3)
    rows: list[dict[str, object]] = []
    for from_jump, to_jump, scar_id in TRANSITIONS:
        incoming = jumps[from_jump]
        outgoing = jumps[to_jump]
        incoming_speed = incoming["velocity_end_mps"]
        normal_speed = min(incoming_speed, math.sqrt(2.0 * GRAVITY_MPS2 * incoming["jump_height_m"]))
        tangent_speed = math.sqrt(max(incoming_speed * incoming_speed - normal_speed * normal_speed, 0.0))
        angle_deg = math.degrees(math.atan2(normal_speed, tangent_speed)) if tangent_speed > 0.0 else 90.0
        pre_energy_j = incoming["energy_end_j"]
        post_energy_j = outgoing["energy_begin_j"]
        total_loss_j = max(pre_energy_j - post_energy_j, 0.0)
        scar = scars[scar_id]
        rows.append(
            {
                "impact_id": f"chant_sura_{scar_id.replace('.', '_')}",
                "source_dataset_id": "chant_sura_2020",
                "source_publication": "Caviezel et al. 2019, Earth Surface Dynamics, doi:10.5194/esurf-7-199-2019",
                "source_transition": f"{from_jump}->{to_jump}",
                "scar_id": scar_id,
                "mass_kg": EOTA221_MASS_KG,
                "radius_m": radius_m,
                "incoming_total_speed_mps": incoming_speed,
                "incoming_normal_speed_mps": normal_speed,
                "incoming_tangent_speed_mps": tangent_speed,
                "impact_angle_deg": angle_deg,
                "observed_scarring_depth_m": scar["depth_adm_m"],
                "observed_scarring_depth_ifm_m": scar["depth_ifm_m"],
                "observed_scarring_depth_source": "adm_max_depth_from_uas_altitude_difference_map",
                "observed_pre_impact_translational_j": pre_energy_j,
                "observed_post_rebound_translational_j": post_energy_j,
                "observed_total_translational_energy_loss_j": total_loss_j,
                "observed_scarring_energy_loss_j": "",
                "published_energy_transition_ratio": ratios.get(f"{from_jump}→{to_jump}", ""),
                "notes": (
                    "Real reconstructed impact/scar row. Normal/tangent split is an effective "
                    "flat-plane proxy derived from published jump height; energy loss includes all "
                    "translational contact losses and is not purely scarring."
                ),
            }
        )
    return rows


def write_csv(rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys())
    with OUT_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_metadata(row_count: int) -> None:
    OUT_METADATA.write_text(
        f"""dataset_id: chant_sura_esurf_2019_impacts
source_dataset_id: chant_sura_2020
source_dataset_doi: https://doi.org/10.16904/envidat.174
source_publication_doi: https://doi.org/10.5194/esurf-7-199-2019
license: Copernicus open-access article tables; underlying EnviDat dataset under WSL Data Policy
generated_by: scripts/preprocess_scarring_real_data.py
row_count: {row_count}
raw_inputs:
  - data/raw/chant_sura_2020/esurf-7-199-2019-t01.xlsx
  - data/raw/chant_sura_2020/esurf-7-199-2019-t02.xlsx
output:
  path: calibration/data/scarring_single_impact/chant_sura_esurf_2019_impacts.csv
  units: SI
assumptions:
  - EOTA221 mass is treated as 780 kg.
  - Spherical radius is an equivalent-volume proxy using concrete density 2400 kg/m3.
  - Effective normal impact speed is derived from jump height as sqrt(2*g*JH).
  - Observed post-rebound energy is the beginning energy of the next published jump.
  - Observed total translational energy loss includes restitution, terrain interaction, and scarring; it is not a pure scarring measurement.
  - ADM scar depth is used as the calibration depth target because it is extracted from UAS altitude-difference mapping.
limitations:
  - Impact normal and tangent components are inferred, not directly measured.
  - Rock shape is EOTA221, but the simulator uses an equivalent sphere.
  - The rows are suitable for exploratory calibration only, not validation or operational parameter selection.
""",
        encoding="utf-8",
    )


def equivalent_sphere_radius_m(mass_kg: float, density_kgpm3: float) -> float:
    return (3.0 * mass_kg / (4.0 * math.pi * density_kgpm3)) ** (1.0 / 3.0)


def split_pair(value: str) -> tuple[float, float]:
    left, right = value.split("/")
    return parse_float(left), parse_float(right)


def parse_float(value: object) -> float:
    text = str(value or "").strip()
    if text in {"", "–", "-"}:
        return float("nan")
    return float(text)


if __name__ == "__main__":
    raise SystemExit(main())
