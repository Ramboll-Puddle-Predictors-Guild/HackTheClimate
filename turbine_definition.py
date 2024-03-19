# ### turbine definition
# # defines turbine parameters, and returns a dicitonary with the important parameters

import pandas as pd
import polars as pl
from src.power_curve import read_power_curve

# powercurve = pl.read_csv("data\wind_turbines\IEA_15_powercurve.csv").lazy()
IEA3p4 = pd.read_csv("data\wind_turbines\IEA_3p4_powercurve.csv", header=1)
IEA15 = pd.read_csv("data\wind_turbines\IEA_15_powercurve.csv", header=1)


TURBINES = {
    "IEA 3.4 130": {
        "power_curve": read_power_curve("data/wind_turbines/IEA_3p4_powercurve.csv"),
        "cut_in_wind_speed": 4.0,
        "cut_out_wind_speed": 25.0,
        "rated_wind_speed": 9.8,
        "n_min": 3.8,
        "n_max": 12.9,
        "radius": 65,
        # additional parameters ...
    },
    "IEA 15 240": {
        "power_curve": read_power_curve("data/wind_turbines/IEA_15_powercurve.csv"),
        "cut_in_wind_speed": 3.0,
        "cut_out_wind_speed": 25.0,
        "rated_wind_speed": 10.66,
        "n_min": 5,
        "n_max": 7.56,
        "radius": 120,
        # additional parameters ...
    },
}


# print(TURBINES["IEA 3.4 130"]["rotorspeed_curve"])

# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# # import polars as pl
# # from scipy.interpolate import interp1d

# def get_turbine(turbine_name):

# turbine=dict()

# if turbine_name = "IEA15MW":

#     n_min = 5  # Rpm
#     n_max = 7.56  # Rpm
#     v_rated = 10.66  # m/s
#     v_min = 7  # m/s
#     radius = 120  # m


# elif turbine_name = "IEA22MW":
#     n_max = 15
#     n_min = 5


# elif turbine_name = "IEA_3p4":
#     n_max
#     n_min
#     df = pd.read_csv('data.IEA_3p4_powercurve.csv')
#     df.values[:,0]
#     df.values[:,1]


# turbine['n_max']=n_max
# turbine['n_min']=n_min

# return turbine
