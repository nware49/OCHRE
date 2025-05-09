import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.size': 20,            # Base font size
    'axes.titlesize': 24,       # Title
    'axes.labelsize': 20,       # Axis labels
    'xtick.labelsize': 18,      # X tick labels
    'ytick.labelsize': 18,      # Y tick labels
    'legend.fontsize': 18,      # Legend text
})

# Water heater energy usage data (12-day total)
data = {
    'water_heater_type': [
        'ESE Heat Pump Water Heater',
        "ESE PCM Heat Pump Water Heater",
        'Heat Pump Water Heater',
        'Electric Resistance Water Heater',
        'Gas Water Heater',
        'Tankless Water Heater',
        'Gas Tankless Water Heater',
        'Low Power Heat Pump Water Heater'
    ],
    '12d_electric_power_kwh': [
        87.511483,
        87.511483,
        74.733325,
        213.342391,
        0.0,
        169.233056,
        31.148333,
        70.303465
    ]
}

df = pd.DataFrame(data)

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
    daily_kwh = row['12d_electric_power_kwh'] / 12
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

# Apply cost calculations
cost_df = df.join(df.apply(calculate_costs, axis=1))

# Desired order of water heaters
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

# Map technical names to readable architecture labels for display
display_labels = [label_mapping[name] for name in ordered_labels]

# Reorder dataframe accordingly
cost_df = cost_df.set_index("water_heater_type").loc[ordered_labels].reset_index()

print (cost_df)
# Plotting with horizontal bars
labels = cost_df['water_heater_type']
y = np.arange(len(labels))  # y positions
height = 0.25  # bar height

fig, ax = plt.subplots(figsize=(10, 7))

bar1 = ax.barh(y - height, cost_df['MA_annual_cost'], height, label='MA', color='royalblue')
bar2 = ax.barh(y, cost_df['NY_annual_cost'], height, label='NY', color='seagreen')
bar3 = ax.barh(y + height, cost_df['CA_annual_cost'], height, label='CA', color='orange')

ax.set_xlabel('Annual Cost ($)')
#ax.set_title('Annual Operation Cost of Water Heater Types by State')
ax.set_yticks(y)
ax.set_yticklabels(display_labels)
ax.invert_yaxis()  # highest cost on top
ax.legend()
ax.grid(True, axis='x', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()
