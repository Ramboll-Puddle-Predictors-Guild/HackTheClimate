from pathlib import Path

from src.power_curve import read_power_curve

_DATA_DIR = Path(__file__).parents[1] / "data" / "wind_turbines"

TURBINES = {
    "IEA 3.4 130": {
        "power_curve": read_power_curve(_DATA_DIR / "IEA_3p4_powercurve.csv"),
        "cut_in_wind_speed": 4.0,
        "cut_out_wind_speed": 25.0,
        "rated_wind_speed": 9.8,
        "n_min": 3.8,
        "n_max": 12.9,
        "radius": 65,
    },
    "IEA 15 240": {
        "power_curve": read_power_curve(_DATA_DIR / "IEA_15_powercurve.csv"),
        "cut_in_wind_speed": 3.0,
        "cut_out_wind_speed": 25.0,
        "rated_wind_speed": 10.66,
        "n_min": 5,
        "n_max": 7.56,
        "radius": 120,
    },
}
