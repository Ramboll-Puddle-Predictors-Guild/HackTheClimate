import csv
from typing import Sequence
import numpy as np

def read_power_curve(path: str) -> dict[str, Sequence[float]]:
    """Read a wind speed-power-turbine speed curve from CSV.

    CSV is expected to contain records of ..code-block::

        {
            "wind_speed": float,
            "power": float,
            "rotor_speed": float
        }
    """
    curve = {"wind_speed": [], "power": [], "rotor_speed": []}
    with open(path) as buffer:
        reader = csv.DictReader(buffer, lineterminator="\n")
        for record in reader:
            curve["wind_speed"].append(float(record["wind_speed"]))
            curve["power"].append(float(record["power"]) * 1e-3)
            curve["rotor_speed"].append(float(record["rotor_speed"]))
    return curve


def get_power_at_wind_velocity(
    wind_speed: float, curve: dict[str, Sequence[float]]
) -> float:
    """Get the power output at a given wind speed."""
    wind_speeds = [float(speed) for speed in curve['wind_speed']]
    powers = curve['power']

    return np.interp(wind_speed, wind_speeds, powers)
