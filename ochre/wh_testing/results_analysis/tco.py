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


# Placeholder data
data = {
    "Architecture": [
        "HP + PCM + Battery (H1)", "HP + Water Tank + Battery",
        "Tankless Electric (240)", "Tankless Gas", "Electric Resistive (240)",
        "Resistive + HP (240)", "HP (Rheem 120)", "Gas Water Heater"
    ],
    "Capital Cost": [5306.45, 2099, 749.92, 1375.44, 729, 1699, 1599, 1339.59],
    "Installation Cost": [900, 900, 2000, 1500, 1500, 1500, 900, 900],
    "Rebate": [3532.79, 2152, 0, 0, 0, 1999, 1642, 0],
    "Cost After Rebate": [2673.66, 1347, 2749.92, 2875.44, 2229, 1714.30, 1224.30, 2239.59],
    "Annual Cost": [
    744.5,  # HP + PCM + Battery (H1)
    #1620.784,  # HP + PCM + Battery (H2) — same as above (ESE HPWH)
    744.5,  # HP + Water Tank + Battery — similar to Tankless Electric
    1439.757,  # Tankless Electric (240) — Tankless Water Heater
    566.196,   # Tankless Gas — Gas Tankless Water Heater
    1815.019,  # Electric Resistive (240)
    635.797,   # Resistive + HP (240) — Heat Pump Water Heater
    #598.110,   # HP (State 120) — Low Power HPWH
    598.110,   # HP (Rheem 120) — Low Power HPWH
    376.500    # Gas Water Heater
],
    "Lifespan": [12, 12, 20, 20, 12, 12, 12, 10]
}

df = pd.DataFrame(data)
df = df.sort_values('Cost After Rebate')
df = df[::-1]

# Constants
years = 60
discount_rate = 0.03

# Function to compute TCO
def compute_tco(row):
    init_cost = row['Capital Cost'] + row['Installation Cost'] - row['Rebate']
    lifespan = row['Lifespan']
    annual = row['Annual Cost']

    total_cost = 0

    # Initial cost
    total_cost += init_cost  # at year 0

    # Replacement costs
    for year in range(lifespan, years, lifespan):
        total_cost += init_cost / ((1 + discount_rate) ** year)

    # Annual usage cost
    for year in range(1, years + 1):
        total_cost += annual / ((1 + discount_rate) ** year)

    return total_cost

df['TCO'] = df.apply(compute_tco, axis=1)
df['Annualized Cost'] = df['TCO'] / years

# Sort for plotting
df_sorted = df

# Plot
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(df_sorted['Architecture'], df_sorted['Annualized Cost'], height=0.25, color='mediumseagreen')
ax.set_xlabel('Annualized Total Cost of Ownership ($/year)')
#ax.set_title('Total Cost of Ownership Over 50 Years')
ax.grid(axis='x', linestyle='--', alpha=0.5)
ax.set_xlim(0,1200)

# Annotate
for bar in bars:
    width = bar.get_width()
    ax.text(width + 20, bar.get_y() + bar.get_height() / 2, f"${width:.2f}", va='center')

plt.tight_layout()
plt.show()
