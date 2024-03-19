import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.interpolate import interp1d

# Define a dictionary mapping country names to CSV file paths
country_files = {
    'e2': 'Climate_Data/latvia_edata.csv',
    'nordsen iii vest': 'Climate_Data/denmark_edata.csv'
}

# Parameters
n_min = 5  # Rpm
n_max = 7.56  # Rpm
v_rated = 10.66  # m/s
v_min = 7  # m/s
radius = 120  # m


# Ask the user to select a country
country = input('Please select a wind farm: ').lower()

# Check if the selected country is in the dictionary
if country in country_files:
    # Read the corresponding CSV file
    impingement_raw = pd.read_csv(country_files[country], sep=",", decimal=".")
else:
    print('Invalid country selected.')

# TODO: calculate impingement here

# Convert timestamp from string to datetime
impingement_raw["timestamp"] = pd.to_datetime(
    impingement_raw["timestamp"], dayfirst=True
)


# Calculate n.star
impingement_raw["n_star"] = ((n_max - n_min) / (v_rated - v_min)) * (
    impingement_raw["wsp_150.0"] - v_min
) + n_min

# Check if n.star is within the limits
impingement_raw.loc[impingement_raw["wsp_150.0"] > v_rated, "n_star"] = n_max
impingement_raw.loc[
    (impingement_raw["wsp_150.0"] > 3) & (impingement_raw["wsp_150.0"] < 7), "n_star"
] = 5
impingement_raw.loc[impingement_raw["wsp_150.0"] < 3, "n_star"] = 0

# Calculate omega
impingement_raw["omega"] = (((2 * np.pi) / 60)) * impingement_raw["n_star"]

# Calculate v.max
impingement_raw["v_max"] = np.sqrt(
    impingement_raw["wsp_150.0"] ** 2 + (impingement_raw["omega"] * radius) ** 2
)

# Calculate r.impg
impingement_raw["r_impg"] = (
    impingement_raw["qrain_150.0"] * impingement_raw["v_max"] * 3600 * (1.225 / 1000)
)

# Calculate r.impg.acc.sum
impingement_raw["r_impg_acc_sum"] = impingement_raw["r_impg"].cumsum()

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(impingement_raw["timestamp"], impingement_raw["r_impg_acc_sum"])
plt.xlabel("Timestamp")
plt.ylabel("accumulated impingement [m]")
plt.show()

# lookup accumulated impingement at which the coating fails (from wpd dataset)

impingement_testdata = pd.read_csv(
    "data/wpd_datasets_clean.csv", sep=",", decimal=".", header=0
)
p = pl.read_csv("data/wpd_datasets_clean.csv").sort(by="3L_X")

coating = "GS"
curve = p.select([f"{coating}_X", f"{coating}_Y"]).drop_nulls().to_numpy()

rotor_speed = n_max * np.pi / 30 * radius

# find location on plot
r_acc_limit = interp1d(curve[:, 1], curve[:, 0])(rotor_speed)


print(r_acc_limit)


# impingement_testdata = impingement_testdata.dropna()


# df = impingement_testdata

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
plt.show()


# now calculate power loss timevector
power_loss = 0.02  # assuming 2% loss at r_acc_limit
# lossvector = pl.from_pandas(impingement_raw['r_impg_acc_sum'])
lossvector = (1 - impingement_raw["r_impg_acc_sum"] / r_acc_limit * power_loss) * 100

# specially for martin, have fun with it
lossvector_polar = pl.from_pandas(lossvector)


# another plot of turbine efficiency
plt.figure(figsize=(10, 6))
plt.scatter(impingement_raw["timestamp"], lossvector)
plt.ylabel("turbine efficiency [%]")
plt.show()
