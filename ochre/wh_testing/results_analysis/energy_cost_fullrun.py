import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.size': 20,
    'axes.titlesize': 24,
    'axes.labelsize': 20,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'legend.fontsize': 18,
})

# Load CSV data for multiple instances
df = pd.read_csv("ochre/wh_tests/results_fullrun_20250429012102/wh_config_results_20250429013427.csv")  # Change to your file path

# Compute mean and std deviation for each heater type
grouped = df.groupby('water_heater_type')
mean_df = grouped.mean().reset_index()
std_df = grouped.std().reset_index()
summary_df = pd.merge(mean_df, std_df, on='water_heater_type')

# Electricity rates ($/kWh)
electricity_rates = {
    'MA': 0.2797,
    'NY': 0.2177,
    'CA': 0.3109
}

# Gas rates ($/therm)
gas_rates = {
    'MA': 2.51,
    'NY': 1.86,
    'CA': 1.90
}

# Estimated gas usage for 12 days (therms)
estimated_12_day_gas_therms = {
    'Gas Water Heater': 150 * (12 / 365),
    'Gas Tankless Water Heater': 120 * (12 / 365)
}

# Function to calculate daily and annual usage/costs
def calculate_costs(row):
    daily_kwh = row['total_electric_power_kwh'] / 12
    annual_kwh = daily_kwh * 365

    if row['water_heater_type'] in estimated_12_day_gas_therms:
        daily_gas_therms = estimated_12_day_gas_therms[row['water_heater_type']] / 12
    else:
        daily_gas_therms = 0

    costs = {
        'daily_kwh': daily_kwh,
        'annual_kwh': annual_kwh,
        'daily_gas_therms': daily_gas_therms
    }

    for state in electricity_rates:
        daily_electric_cost = daily_kwh * electricity_rates[state]
        annual_electric_cost = daily_electric_cost * 365
        annual_gas_cost = daily_gas_therms * 365 * gas_rates[state]
        total_annual_cost = annual_electric_cost + annual_gas_cost
        costs[f'{state}_annual_cost'] = total_annual_cost

    return pd.Series(costs)

cost_df = summary_df.join(summary_df.apply(calculate_costs, axis=1))

# Desired order and label mapping
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

# Apply label ordering and mapping
cost_df = cost_df.set_index("water_heater_type").loc[ordered_labels].reset_index()
display_labels = [label_mapping[name] for name in ordered_labels]

# Plotting with error bars
fig, ax = plt.subplots(figsize=(10, 7))
y = np.arange(len(cost_df))
height = 0.25

# Convert std_dev of 12d_kwh into annual cost std_dev per state
def std_to_cost(std_kwh, state_rate):
    return (std_kwh / 12) * 365 * state_rate

for i, (state, color) in enumerate(zip(['MA', 'NY', 'CA'], ['royalblue', 'seagreen', 'orange'])):
    offset = (i - 1) * height
    values = cost_df[f'{state}_annual_cost']
    errors = cost_df['total_electric_power_kwh'].apply(lambda std: std_to_cost(std, electricity_rates[state]))
    ax.barh(y + offset, values, height, label=state, color=color, xerr=errors, capsize=5)

ax.set_xlabel('Annual Cost ($)')
ax.set_yticks(y)
ax.set_yticklabels(display_labels)
ax.invert_yaxis()
ax.legend()
ax.grid(True, axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
