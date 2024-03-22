import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.interpolate import interp1d

from accumulated_impingement import calculate_impingement
from src.turbines import TURBINES

# calculate_impingement(TURBINES["IEA 3.4 130"], "e2", 0.02)
slidervalues = np.linspace(1.001, 100, 20)
turbine = TURBINES["IEA 3.4 130"]


final_Eyield = []
final_Eyield_without_erosion = []

for slidervalue in slidervalues:
    impingement_raw, impingement_testdata, r_acc_limit, lossvector = calculate_impingement(
        TURBINES["IEA 3.4 130"], "nordsen iii vest", slidervalue
    )
    pv_wind = np.array(turbine["power_curve"]["wind_speed"])
    pv_power = np.array(turbine["power_curve"]["power"])  # MW
    pv_rotorspeed = np.array(turbine["power_curve"]["rotor_speed"])

    Pi = interp1d(pv_wind, pv_power, fill_value="extrapolate")(np.array(impingement_raw["wsp_150.0"]))
    omega_max = slidervalue / turbine["radius"] * 30 / np.pi
    if omega_max == 0:
        omega_max = omega_max + 1e-4
    mask = (pv_wind > turbine["cut_in_wind_speed"]) & (pv_wind < turbine["cut_out_wind_speed"])
    Pi_max = interp1d(pv_rotorspeed[mask], pv_power[mask], kind="linear", fill_value="extrapolate")(np.array(omega_max))

    Pi_capped = Pi
    Pi_capped[(impingement_raw["qrain_150.0"] > 0)] = np.clip(
        Pi_capped[(impingement_raw["qrain_150.0"] > 0)], None, Pi_max
    )

    Ey_noloss = Pi_capped.cumsum()  # MWh
    Ey = np.array(Pi_capped * lossvector / 100).cumsum()  # MWh
    print(f"Vtipmax={slidervalue}")
    print(f"{Ey_noloss[-1]}")
    print(f"{Ey[-1]}")
    final_Eyield.append(Ey[-1])  # we need windspeed & powercurve & lossvector
    final_Eyield_without_erosion.append(Ey_noloss[-1])

plt.figure()
plt.plot(slidervalues, final_Eyield)
plt.plot(slidervalues, final_Eyield_without_erosion)

########
impingement_raw, impingement_testdata, r_acc_limit, lossvector = calculate_impingement(
    TURBINES["IEA 3.4 130"], "nordsen iii vest", 150
)
pv_wind = np.array(turbine["power_curve"]["wind_speed"])
pv_power = np.array(turbine["power_curve"]["power"])  # MW
pv_rotorspeed = np.array(turbine["power_curve"]["rotor_speed"])
mask = (pv_wind > turbine["cut_in_wind_speed"]) & (pv_wind < turbine["cut_out_wind_speed"])
Pi = interp1d(pv_wind[mask], pv_power[mask], fill_value="extrapolate")(np.array(impingement_raw["wsp_150.0"]))

Ey_noloss = Pi.cumsum()  # MWh
Ey = np.array(Pi * lossvector / 100).cumsum()  # MWh
print("now vtipmax = 150\n")
print(f"{Ey_noloss[-1]}")
print(f"{Ey[-1]}")
final_Eyield.append(Ey[-1])  # we need windspeed & powercurve & lossvector


final_eff = []
final_Eyield = []
final_income = []

# plt.figure()

for slidervalue in slidervalues:
    impingement_raw, impingement_testdata, r_acc_limit, lossvector = calculate_impingement(
        TURBINES["IEA 3.4 130"], "nordsen iii vest", slidervalue
    )
    final_eff.append(lossvector.to_numpy()[-1])

    pv_wind = np.array(turbine["power_curve"]["wind_speed"])
    pv_power = np.array(turbine["power_curve"]["power"]) / 1000
    pv_rotorspeed = np.array(turbine["power_curve"]["rotor_speed"])

    Pi = interp1d(pv_wind, pv_power, fill_value="extrapolate")(np.array(impingement_raw["wsp_150.0"]))

    # calculate omega capped
    omega_max = slidervalue / turbine["radius"] * 30 / np.pi
    if omega_max == 0:
        omega_max = omega_max + 1e-4
    mask = (np.array(turbine["power_curve"]["wind_speed"]) > turbine["cut_in_wind_speed"]) & (
        np.array(turbine["power_curve"]["wind_speed"]) < turbine["cut_out_wind_speed"]
    )
    Pi_max = interp1d(pv_rotorspeed[mask], pv_power[mask], fill_value="extrapolate")(omega_max)
    Pi_max[Pi_max < 0] = 0
    Pi_max = Pi_max * 1e6
    # Create the 'omega_capped' column
    Pi_capped = np.where(
        (impingement_raw["qrain_150.0"] > 0) & (Pi > Pi_max),
        Pi_max,
        Pi,
    )

    Ey = Pi_capped * lossvector.cumsum()
    # plt.plot(impingement_raw["timestamp"], Pi_capped)
    # income = Ey *

    final_Eyield.append(Ey.to_numpy()[-1])  # we need windspeed & powercurve & lossvector
    # final_income.income(             )
# plt.show()

# create some plots

# plot 1 Peff for different Vtip,max
plt.figure()
plt.scatter(slidervalues, final_eff)
plt.title("Power efficiency after 9 years")
plt.xlabel("V_tip,max (during rain) [m/s]")
plt.show()


# plot 2 Eyield for different Vtip,max
plt.figure()
plt.scatter(slidervalues, final_Eyield)
plt.title("Accumulated energy yield after 9 years [Gwh]")
plt.xlabel("V_tip,max (during rain) [m/s]")
plt.show()

# plot 3 total income for different Vtip,max
# plt.figure()
# plt.scatter(slidervalues, final_income)
# # plt.show()
# plt.title("Accumulated total income after 9 years [Eur]")
# plt.xlabel("V_tip,max (during rain) [m/s]")
