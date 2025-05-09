import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.size': 15,            # Base font size
    'axes.titlesize': 18,       # Title
    'axes.labelsize': 15,       # Axis labels
    'xtick.labelsize': 15,      # X tick labels
    'ytick.labelsize': 15,      # Y tick labels
    'legend.fontsize': 18,      # Legend text
})

# Your data
data = {
    "Architecture": [
        "HP (120V) + PCM Tank + Battery",
        # "HP + PCM + Battery (H2)",
        "HP (120V) + Water Tank + Battery",
        "Tankless Electric (240V)",
        "Tankless Gas",
        "Electric Resistive (240V)",
        "HP (240V) + Resistive",
        #"HP (State 120V)",
        "HP (Rheem 120V)",
        "Gas Water Heater"
    ],
    #"Installation Cost": [900, 900, 900, 2000, 1500, 1500, 1500, 900, 900, 900],
    #"Capital Cost": [5306.45, 4485.12, 2599, 749.92, 1375.44, 729, 1699, 3045, 1599, 1339.59],
    #"Total Cost": [6206.45, 5385.12, 3499, 2749.92, 2875.44, 2229, 3199, 3945, 2499, 2239.59],
    #"Cost After Rebate": [2673.66, 2271.21, 1347, 2749.92, 2875.44, 2229, 1200.01, 1565.55, 857.01, 2239.59],
    #"Total Discount Amount": [-3532.79, -3113.91, -2152, 0.0, 0.0, 0.0, -1999, -2379, -1642, 0.0]
    "Installation Cost": [900, 900, 2000, 1500, 1500, 1500, 900, 900],
    "Capital Cost": [5306.45, 2599, 749.92, 1375.44, 729, 1699, 1599, 1339.59],
    "Total Cost": [6206.45, 3499, 2749.92, 2875.44, 2229, 3199, 2499, 2239.59],
    "Cost After Rebate": [2673.66, 1347, 2749.92, 2875.44, 2229, 1714.30, 1224.30, 2239.59],
    "Total Discount Amount": [-3532.79, -2152, 0.0, 0.0, 0.0, -1485, -1275, 0.0]
}

df = pd.DataFrame(data)
df = df.sort_values(by='Cost After Rebate')
df = df[::-1]

# For bar positions
y = np.arange(len(df))
height = 0.35

# Colors
colors = {
    'out_of_pocket': 'steelblue',
    'rebate': 'lightgreen',
    'capital': 'indianred',
    'install': 'indigo'
}

# Plot
fig, ax = plt.subplots(figsize=(12, 7))

palette1 = ['steelblue', 'firebrick', 'steelblue', 'steelblue', 'steelblue', 'firebrick', 'steelblue', 'steelblue'][::-1]
palette2 = ['lightgreen', 'lightgreen', 'lightgreen', 'lightgreen', 'lightgreen', 'lightgreen', 'lightgreen', 'lightgreen']

# First bar: Total Cost (Cost After Rebate + Discount)
bar1 = ax.barh(y - height/2, df['Cost After Rebate'], height, label='Out-of-pocket Cost', color=palette1)
bar1b = ax.barh(y - height/2, -df['Total Discount Amount'], height,
                left=df['Cost After Rebate'], label='Rebate + Tax Credit', color=palette2)

# Second bar: Capital + Installation Cost
height = height / 4
bar2 = ax.barh(y + height/2, df['Capital Cost'], height, label='Capital Cost', color=colors['capital'])
bar2b = ax.barh(y + height/2, df['Installation Cost'], height,
                left=df['Capital Cost'], label='Installation Cost', color=colors['install'])

x_labels = [
    "120V Heat Pump Water Heater",
    "120V Heat Pump + Water Tank + Li-Ion",
    "240V Heat Pump Water Heater",
    "240V Electric Resistive",
    "Gas Water Heater",
    "120V Heat Pump + PCM + Li-Ion",
    "240V Tankless Electric",
    "Tankless Gas"
][::-1]

# Aesthetics
ax.set_xlabel('Cost ($)')
#ax.set_title('Cost of Installing Water Heater Architectures in Massachusetts')
ax.set_yticks(y)
ax.set_yticklabels(x_labels)
ax.legend()
ax.grid(axis='x', linestyle='--', alpha=0.5)
ax.set_xlim(0,8300)

# Add text labels
for bar, cost in zip(bar1, df['Total Cost']):
    consumer_cost = bar.get_width()
    plt.text(consumer_cost + 50, bar.get_y() + bar.get_height()/2, f'Total: ${consumer_cost:,.0f}', va='center')
    pre_rebate = cost
    if consumer_cost != pre_rebate:
        plt.text(max(pre_rebate + 50, consumer_cost + 1000), bar.get_y() + bar.get_height()/2, f'Before Rebate: ${pre_rebate:,.0f}', va='center')

plt.tight_layout()
plt.show()
