# ### turbine definition
# # defines turbine parameters, and returns a dicitonary with the important parameters

import pandas as pd
import polars as pl

# powercurve = pl.read_csv("data/IEA_15_powercurve.csv").lazy()
IEA3p4 = pd.read_csv("data/IEA_3p4_powercurve_new.csv", header=1)
IEA15 = pd.read_csv("data/IEA_15_powercurve.csv", header=1)
IEA22 = pd.read_csv("data/IEA_15_powercurve.csv", header=1)

TURBINES = {
    "IEA 3.4 130": {
        "power_curve": {
            "wind_speed": IEA3p4.to_numpy()[:, 0],
            "power": IEA3p4.to_numpy()[:, 1]
        },
        "cut_in_wind_speed": 3.0,
        "cut_out_wind_speed": 25.0,
        # additional parameters ...
    },
    "IEA 15": {
        "power_curve": {
            "wind_speed": IEA15.to_numpy()[:, 0],
            "power": IEA15.to_numpy()[:, 1]
        },
        "cut_in_wind_speed": 3.0,
        "cut_out_wind_speed": 25.0,
        # additional parameters ...
    },
    "IEA 22": {
        "power_curve": {
            "wind_speed": IEA22.to_numpy()[:, 0],
            "power": IEA22.to_numpy()[:, 1]
        },
        "cut_in_wind_speed": 3.0,
        "cut_out_wind_speed": 25.0,
        # additional parameters ...
    },
}


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
