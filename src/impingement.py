from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.interpolate import interp1d

from src.turbines import TURBINES

_DATA_DIR = Path(__file__).parents[1] / "Climate_Data"
WINDFARM_FILES = {"e2": _DATA_DIR / "latvia_edata.csv", "nordsen iii vest": _DATA_DIR / "denmark_edata.csv"}


def calculate_impingement(turbine: dict, windfarm: Literal["e2", "nordsen iii vest"], slider):

    if windfarm in WINDFARM_FILES:
        # Read the corresponding CSV file
        impingement_raw = pd.read_csv(WINDFARM_FILES[windfarm], sep=",", decimal=".")
    else:
        raise FileNotFoundError("Invalid country selected.")

    # Parameters
    n_max = turbine["n_max"]  # Rpm
    radius = turbine["radius"]  # m
    # Load the CSV file for the specified windfarm
    impingement_raw = pd.read_csv(WINDFARM_FILES[windfarm], sep=",", decimal=".")
    impingement_raw["timestamp"] = pd.to_datetime(impingement_raw["timestamp"])

    # Interpolate n.star
    impingement_raw["n_star"] = interp1d(
        turbine["power_curve"]["wind_speed"], turbine["power_curve"]["rotor_speed"], fill_value="extrapolate"
    )(impingement_raw["wsp_150.0"])

    # Calculate omega
    impingement_raw["omega"] = (((2 * np.pi) / 60)) * impingement_raw["n_star"]

    # calculate omega capped
    omega_max = slider / turbine["radius"]
    # Create the 'omega_capped' column
    impingement_raw["omega_capped"] = np.where(
        (impingement_raw["qrain_150.0"] > 0) & (impingement_raw["omega"] > omega_max),
        omega_max,
        impingement_raw["omega"],
    )

    # Calculate v.max
    impingement_raw["v_max"] = np.sqrt(
        impingement_raw["wsp_150.0"] ** 2 + (impingement_raw["omega_capped"] * radius) ** 2
    )

    # Calculate r.impg
    impingement_raw["r_impg"] = impingement_raw["qrain_150.0"] * impingement_raw["v_max"] * 3600 * (1.225 / 1000)

    # Accumulate r.impg
    impingement_raw["r_impg_acc_sum"] = impingement_raw["r_impg"].cumsum()

    # Load impingement test data and sort
    impingement_testdata = pd.read_csv("data/erosion/wpd_datasets_clean.csv", sep=",", decimal=".", header=0)
    p = pl.read_csv("data/erosion/wpd_datasets_clean.csv").sort("3L_X")

    coating = "GS"
    curve = p.select([f"{coating}_X", f"{coating}_Y"]).drop_nulls().to_numpy()

    rotor_speed = n_max * np.pi / 30 * radius

    # find location on plot
    r_acc_limit = interp1d(curve[:, 1], curve[:, 0])(rotor_speed)

    # Calculate turbine efficiency loss over time
    power_loss = 0.02  # Assuming slider value is used here
    lossvector = (1 - impingement_raw["r_impg_acc_sum"] / r_acc_limit * power_loss) * 100

    return impingement_raw, impingement_testdata, r_acc_limit, lossvector
