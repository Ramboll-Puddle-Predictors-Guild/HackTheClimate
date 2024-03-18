import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# # Read the CSV file
impingement_raw = pd.read_csv("Climate_Data/impingement_dat.csv", sep=';', decimal=',')

# Parameters
n_min = 5  # Rpm
n_max = 7.56  # Rpm
v_rated = 10.66  # m/s
v_min = 7  # m/s
radius = 120  # m

# Convert timestamp from string to datetime
impingement_raw['timestamp'] = pd.to_datetime(impingement_raw['timestamp'], dayfirst=True)


# Calculate n.star
impingement_raw['n_star'] = (((n_max - n_min) / (v_rated - v_min)) * (impingement_raw['wsp_150.0'] - v_min) + n_min)

# Check if n.star is within the limits
impingement_raw.loc[impingement_raw['wsp_150.0'] > v_rated, 'n_star'] = n_max
impingement_raw.loc[(impingement_raw['wsp_150.0'] > 3) & (impingement_raw['wsp_150.0'] < 7), 'n_star'] = 5
impingement_raw.loc[impingement_raw['wsp_150.0'] < 3, 'n_star'] = 0

# Calculate omega
impingement_raw['omega'] = (((2 * np.pi) / 60)) * impingement_raw['n_star']

# Calculate v.max
impingement_raw['v_max'] = np.sqrt(impingement_raw['wsp_150.0']**2 + (impingement_raw['omega'] * radius)**2)

# Calculate r.impg
impingement_raw['r_impg'] = impingement_raw['qrain_150.0'] * impingement_raw['v_max'] * 3600 * (1.225 / 1000)

# Calculate r.impg.acc.sum
impingement_raw['r_impg_acc_sum'] = impingement_raw['r_impg'].cumsum()

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(impingement_raw['timestamp'], impingement_raw['r_impg_acc_sum'])
plt.xlabel('Timestamp')
plt.ylabel('r_impg_acc_sum')
plt.show()
