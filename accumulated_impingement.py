import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.interpolate import interp1d
from turbine_definition import TURBINES


def calculate_impingement(turbine, windfarm, slider):
    windfarm_files = {
        'e2': 'Climate_Data/latvia_edata.csv',
        'nordsen iii vest': 'Climate_Data/denmark_edata.csv'
    }
    # # Check if the selected country is in the dictionary

    if windfarm in windfarm_files:
        # Read the corresponding CSV file
        impingement_raw = pd.read_csv(windfarm_files[windfarm], sep=",", decimal=".")
    else:
        print('Invalid country selected.')

    # Parameters
    n_max = turbine['n_max']  # Rpm
    radius = turbine['radius']  # m
    # Load the CSV file for the specified windfarm
    impingement_raw = pd.read_csv(windfarm_files[windfarm], sep=",", decimal=".")
    impingement_raw["timestamp"] = pd.to_datetime(impingement_raw["timestamp"])

    # Interpolate n.star
    impingement_raw["n_star"] = interp1d(turbine["power_curve"]["wind_speed"], turbine["power_curve"]["rotor_speed"], fill_value="extrapolate")(impingement_raw['wsp_150.0'])

    # Calculate omega
    impingement_raw["omega"] = (((2 * np.pi) / 60)) * impingement_raw["n_star"]

    #calculate omega capped
    omega_max = slider* 30 /np.pi
    # Create the 'omega_capped' column
    impingement_raw["omega_capped"] = np.where(
        (impingement_raw["qrain_150.0"] > 0.01) & (impingement_raw["omega"] > omega_max),
        omega_max,
        impingement_raw["omega"]
    )

    # Calculate v.max
    impingement_raw["v_max"] = np.sqrt(impingement_raw["wsp_150.0"] ** 2 + (impingement_raw["omega_capped"] * radius) ** 2)

    # Calculate r.impg
    impingement_raw["r_impg"] = (impingement_raw["qrain_150.0"] * impingement_raw["v_max"] * 3600 * (1.225 / 1000))

    # Accumulate r.impg
    impingement_raw["r_impg_acc_sum"] = impingement_raw["r_impg"].cumsum()

    # First Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(impingement_raw["timestamp"], impingement_raw["r_impg_acc_sum"])
    plt.xlabel("Timestamp")
    plt.ylabel("Accumulated Impingement [m]")
    plt.title("Accumulated Impingement Over Time")
    # plt.show()

    # Load impingement test data and sort
    impingement_testdata = pd.read_csv("data/erosion/wpd_datasets_clean.csv", sep=",", decimal=".", header=0)
    p = pl.read_csv("data/erosion/wpd_datasets_clean.csv").sort("3L_X")

    coating = "GS"
    curve = p.select([f"{coating}_X", f"{coating}_Y"]).drop_nulls().to_numpy()

    rotor_speed = n_max * np.pi / 30 * radius

    # find location on plot
    r_acc_limit = interp1d(curve[:, 1], curve[:, 0])(rotor_speed)

    plt.figure(figsize=(10, 6))
    # plt.semilogx(curve[:, 0], curve[:, 1], color="blue", label="3L")
    plt.semilogx(
        impingement_testdata["3L_X"],
        impingement_testdata["3L_Y"],
        color="black",
        label="3L",
        alpha=0.3,
    )
    plt.semilogx(
        impingement_testdata["GCG20_X"],
        impingement_testdata["GCG20_Y"],
        color="green",
        label="GCG20",
        alpha=0.3,
    )
    plt.semilogx(
        impingement_testdata["GAG20_X"],
        impingement_testdata["GAG20_Y"],
        color="red",
        label="GAG20",
        alpha=0.3,
    )
    plt.semilogx(
        impingement_testdata["GS_X"],
        impingement_testdata["GS_Y"],
        color="magenta",
        label="GS",
    )

    plt.axhline(rotor_speed)
    # plt.axvline(r_acc_limit)
    plt.axvline(impingement_raw["r_impg_acc_sum"].to_numpy()[-1])
    plt.legend()


    plt.xlabel("Racc")
    plt.ylabel("rot speed")
    # plt.show()

    # Calculate turbine efficiency loss over time
    power_loss = 0.02  # Assuming slider value is used here
    lossvector = (1 - impingement_raw["r_impg_acc_sum"] / r_acc_limit * power_loss) * 100

    # Plot turbine efficiency over time
    plt.figure(figsize=(10, 6))
    plt.plot(impingement_raw["timestamp"], lossvector)
    plt.xlabel("Timestamp")
    plt.ylabel("Turbine Efficiency [%]")
    plt.title("Turbine Efficiency Over Time")
    plt.show()

    return impingement_raw, impingement_testdata, r_acc_limit, lossvector

