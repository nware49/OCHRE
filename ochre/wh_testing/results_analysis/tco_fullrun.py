import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.size': 15,
    'axes.titlesize': 18,
    'axes.labelsize': 15,
    'xtick.labelsize': 15,
    'ytick.labelsize': 15,
    'legend.fontsize': 18,
})

# Placeholder capital and installation cost data
data = {
    "Architecture": [
        "HP + PCM + Battery (H1)", "HP + Water Tank + Battery",
        "Tankless Electric (240)", "Tankless Gas", "Electric Resistive (240)",
        "Resistive + HP (240)", "HP (Rheem 120)", "Gas Water Heater"
    ],
    "Capital Cost": [4806.45, 2099, 749.92, 1375.44, 729, 1699, 1599, 1339.59],
    "Installation Cost": [900, 900, 2000, 1500, 1500, 1500, 900, 900],
    "Rebate": [3532.79, 2152, 0, 0, 0, 1999, 1642, 0],
    "Cost After Rebate": [2673.66, 1347, 2749.92, 2875.44, 2229, 1714.30, 1224.30, 2239.59],
    "Lifespan": [12, 12, 20, 20, 12, 12, 12, 10]
}

df = pd.DataFrame(data)

# Load annual cost data for MA
annual_costs = pd.read_csv("annual_costs_summary.csv")  # Should contain MA_annual_cost and MA_std

# Map the external labels to internal Architecture names
label_mapping = {
    "Low Power Heat Pump Water Heater": "HP (Rheem 120)",
    "ESE Heat Pump Water Heater": "HP + Water Tank + Battery",
    "Heat Pump Water Heater": "Resistive + HP (240)",
    "Electric Resistance Water Heater": "Electric Resistive (240)",
    "Gas Water Heater": "Gas Water Heater",
    "ESE PCM Heat Pump Water Heater": "HP + PCM + Battery (H1)",
    "Tankless Water Heater": "Tankless Electric (240)",
    "Gas Tankless Water Heater": "Tankless Gas"
}

label_remapping = {
    "HP (Rheem 120)": "120V Heat Pump Water Heater",
    "HP + Water Tank + Battery": "120V Heat Pump + Water Tank + Li-Ion",
    "Resistive + HP (240)": "240V Heat Pump Water Heater",
    "Electric Resistive (240)": "240V Electric Resistive",
    "Gas Water Heater": "Gas Water Heater",
    "HP + PCM + Battery (H1)": "120V Heat Pump + PCM + Li-Ion",
    "Tankless Electric (240)": "240V Tankless Electric",
    "Tankless Gas": "Tankless Gas"
}

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

#annual_costs = annual_costs.set_index("water_heater_type").loc[ordered_labels].reset_index()
annual_costs['Architecture'] = annual_costs['water_heater_type'].map(label_mapping)
annual_ma = annual_costs[['Architecture', 'MA_mean', 'MA_std']].rename(columns={
    'MA_mean': 'Annual Cost',
    'MA_std': 'Annual Std'
})

# Merge cost data with MA annual usage cost data
df = df.merge(annual_ma, on='Architecture', how='left')

# Constants
years = 60
discount_rate = 0.03
n_simulations = 1000

# Monte Carlo TCO calculator
def compute_tco_with_uncertainty(row, n=n_simulations):
    init_cost = row['Capital Cost'] + row['Installation Cost'] - row['Rebate']
    lifespan = row['Lifespan']
    mean_annual = row['Annual Cost']
    std_annual = row['Annual Std'] if not pd.isna(row['Annual Std']) else 0

    samples = np.random.normal(mean_annual, std_annual, size=n)
    tcos = []

    for annual in samples:
        tco = init_cost
        for year in range(lifespan, years, lifespan):
            tco += init_cost / ((1 + discount_rate) ** year)
        for year in range(1, years + 1):
            tco += annual / ((1 + discount_rate) ** year)
        tcos.append(tco)

    return np.mean(tcos), np.std(tcos)

# Compute TCOs
tco_results = df.apply(lambda row: compute_tco_with_uncertainty(row), axis=1)
df['TCO'] = [mean for mean, std in tco_results]
df['TCO_std'] = [std for mean, std in tco_results]
df['Annualized Cost'] = df['TCO'] / years
df['Annualized Std'] = df['TCO_std'] / years

# Reverse the label_mapping for relabeling
reverse_mapping = {v: k for k, v in label_mapping.items()}
df['Label'] = df['Architecture'].map(reverse_mapping)

# Set label as categorical with the desired order
df['Label'] = pd.Categorical(df['Label'], categories=ordered_labels, ordered=True)

# Sort based on this new label
df_sorted = df.sort_values('Label', ascending=False)

# Identify which systems contain a battery
battery_labels = [
    "ESE Heat Pump Water Heater",       # HP + Water Tank + Battery
    "ESE PCM Heat Pump Water Heater"    # HP + PCM + Battery
]

# Generate bar colors: red if label is in battery list, else mediumseagreen
bar_colors = df_sorted['Label'].apply(
    lambda x: 'mediumseagreen' if x in battery_labels else 'mediumseagreen'
).tolist()


labels = df_sorted['Architecture']
y = np.arange(len(labels))
height = 0.25

df_sorted['Architecture'] = df_sorted['Architecture'].map(label_remapping)
# Plot
fig, ax = plt.subplots(figsize=(12, 6))
#bars = ax.barh(df_sorted['Architecture'], df_sorted['Annualized Cost'],
 #              xerr=df_sorted['Annualized Std'],
 #              height=0.25, color='mediumseagreen', capsize=5)

costs_2020 = [0, 168, 0, 0, 0, 228, 0, 0][::-1]
costs_2030 = [0, 131, 0, 0, 0, 199, 0, 0][::-1]

bar2 = ax.barh(y + height, costs_2020, height, label='2020 Li-Ion cost/kWh', color='orange')
bar1 = ax.barh(df_sorted['Architecture'], df_sorted['Annualized Cost'], xerr=df_sorted['Annualized Std'], height=0.25, color=bar_colors, capsize=5, label="2025 Li-Ion cost/kWh") 
bar3 = ax.barh(y - height, costs_2030, height, label='2030 Li-Ion cost/kWh', color='firebrick')


ax.set_xlabel('Annualized Total Cost of Ownership ($/year)')
ax.grid(axis='x', linestyle='--', alpha=0.5)
ax.set_xlim(0, df_sorted['Annualized Cost'].max() + 300)
ax.legend()

# Annotate bars
for i, bar in enumerate(bar1):
    width = bar.get_width()
    std = df_sorted.iloc[i]['Annualized Std']
    ax.text(width + std + 10, bar.get_y() + bar.get_height() / 2,
            f"${width:.0f} ± {std:.0f}", va='center')

plt.tight_layout()
plt.show()


