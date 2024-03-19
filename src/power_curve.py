"""Module for computing power output."""

import csv
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

COEFFICIENT_OF_PERFORMANCE = 0.25

ROTOR_DIAMETER = 236.0
AREA = np.pi * (ROTOR_DIAMETER / 2) ** 2
AIR_DENSITY = 1.225

CUT_IN_WIND_SPEED = 3.0
RATED_WIND_SPEED = 13.0
CUT_OUT_WIND_SPEED = 31.0


# def get_power_at_wind_velocity(wind_velocity: float) -> float:
#     """Get wind turbine power output at a given wind velocity."""

#     return COEFFICIENT_OF_PERFORMANCE * 0.5 * AIR_DENSITY * AREA * wind_velocity**3


def read_power_curve(path: str) -> dict[str, Sequence[float]]:
    curve = {"wind_speed": [], "power": [], "rotor_speed": []}
    with open(path) as buffer:
        reader = csv.DictReader(buffer, lineterminator="\n")
        for record in reader:
            curve["wind_speed"].append(float(record["wind_speed"]))
            curve["power"].append(float(record["power"]) * 1e-3)
            curve["rotor_speed"].append(float(record["rotor_speed"]))
    return curve


def get_power_at_wind_velocity(wind_velocity: float) -> float:
    if wind_velocity < CUT_IN_WIND_SPEED:
        power = 0.0
    elif CUT_IN_WIND_SPEED <= wind_velocity <= RATED_WIND_SPEED:
        power = COEFFICIENT_OF_PERFORMANCE * 0.5 * AIR_DENSITY * AREA * wind_velocity**3
    elif RATED_WIND_SPEED < wind_velocity <= CUT_OUT_WIND_SPEED:
        power = (
            COEFFICIENT_OF_PERFORMANCE * 0.5 * AIR_DENSITY * AREA * RATED_WIND_SPEED**3
        )
    else:
        power = 0.0

    return power


def get_power_curve(wind_velocities: Sequence[float]) -> Sequence[float]:
    """Get wind turbine power output at a sequence of wind velocities."""
    powers = []
    for velocity in wind_velocities:
        if velocity < CUT_IN_WIND_SPEED:
            powers.append(0.0)
        elif CUT_IN_WIND_SPEED <= velocity <= RATED_WIND_SPEED:
            powers.append(get_power_at_wind_velocity(velocity))
        elif RATED_WIND_SPEED < velocity <= CUT_OUT_WIND_SPEED:
            powers.append(get_power_at_wind_velocity(RATED_WIND_SPEED))
        else:
            powers.append(0.0)

    return powers


def show_power_curve():
    velocities = np.linspace(2, 40, 1000)
    powers = get_power_curve(velocities)
    powers = [power / 1e6 for power in powers]

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(velocities, powers)
    ax.set_xlabel("Wind Velocity (m/s)")
    ax.set_ylabel("Power (MW)")
    plt.show()
