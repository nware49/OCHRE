import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set plotting style
plt.rcParams.update({
    'font.size': 20,
    'axes.titlesize': 24,
    'axes.labelsize': 20,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'legend.fontsize': 18,
})

# Load cost data
cost_df = pd.read_csv('annual_costs.csv')

# Compute mean and std deviation
summary_df = cost_df.groupby('water_heater_type').agg({
    'annual_cost_MA': ['mean', 'std'],
    'annual_cost_NY': ['mean', 'std'],
    'annual_cost_CA': ['mean', 'std'],
}).reset_index()

# Flatten columns
summary_df.columns = ['water_heater_type',
                      'MA_mean', 'MA_std',
                      'NY_mean', 'NY_std',
                      'CA_mean', 'CA_std']

# Order and relabel
ordered_labels = [
    "Low Power Heat Pump Water Heater",
    "ESE Heat Pump Water Heater",
    "Heat Pump Water Heater",
    "Electric Resistance Water Heater",
    "Gas Water Heater",
    "ESE PCM Heat Pump Water Heater",
    "Tankless Water Heater",
    "Gas Tankless Water Heater"
]

label_mapping = {
    "Low Power Heat Pump Water Heater": "HP (Rheem 120V)",
    "ESE Heat Pump Water Heater": "HP (120V) + Water Tank + Battery",
    "Heat Pump Water Heater": "HP (240V) + Resistive",
    "Electric Resistance Water Heater": "Electric Resistive (240V)",
    "Gas Water Heater": "Gas Water Heater",
    "ESE PCM Heat Pump Water Heater": "HP (120V) + PCM Tank + Battery",
    "Tankless Water Heater": "Tankless Electric (240V)",
    "Gas Tankless Water Heater": "Tankless Gas"
}

y_labels = [
    "120V Heat Pump Water Heater",
    "120V Heat Pump + Water Tank + Li-Ion",
    "240V Heat Pump Water Heater",
    "240V Electric Resistive",
    "Gas Water Heater",
    "120V Heat Pump + PCM + Li-Ion",
    "240V Tankless Electric",
    "Tankless Gas"
]

# Select the row to copy
row_to_copy = summary_df[summary_df['water_heater_type'] == 'ESE Heat Pump Water Heater'].copy()

# Change the water heater type
row_to_copy.loc[:, 'water_heater_type'] = 'ESE PCM Heat Pump Water Heater'

# Append it to the original dataframe
summary_df = pd.concat([summary_df, row_to_copy], ignore_index=True)

summary_df = summary_df.set_index("water_heater_type").loc[ordered_labels].reset_index()
display_labels = [label_mapping[name] for name in ordered_labels]

print(summary_df)
summary_df.to_csv("annual_costs_summary.csv")

# Plot
labels = summary_df['water_heater_type']
y = np.arange(len(labels))
height = 0.25

fig, ax = plt.subplots(figsize=(12, 8))

oracle_efficiency = [0, 129, 0, 0, 0, 129, 0, 0]

bar1 = ax.barh(y - height, summary_df['MA_mean'], height, label='MA',
               color='royalblue', xerr=summary_df['MA_std'], capsize=5)
bar2 = ax.barh(y, summary_df['NY_mean'], height, label='NY',
               color='seagreen', xerr=summary_df['NY_std'], capsize=5)
bar3 = ax.barh(y + height, summary_df['CA_mean'], height, label='CA',
               color='orange', xerr=summary_df['CA_std'], capsize=5)
bar4 = ax.barh(y, oracle_efficiency, height*3, label='Predictive\n"Oracle"\nEfficiency',
               color='firebrick')

ax.set_xlabel('Annual Cost ($)')
ax.set_yticks(y)
ax.set_yticklabels(y_labels)
ax.invert_yaxis()
ax.legend()
ax.grid(True, axis='x', linestyle='--', alpha=0.7)
#ax.set_xscale('log')


plt.tight_layout()
plt.show()
