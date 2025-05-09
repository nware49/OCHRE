import math
import pandas as pd
import matplotlib.pyplot as plt

# AO Smith dimensions (in inches), converted to ft³ (1 ft³ = 1728 in³)
ao_smith_in3 = {
    'Electric Resistive': 66.0 * math.pi * (22 / 2) ** 2,
    '120V HPWH': 66.0 * math.pi * (22 / 2) ** 2,
    'Gas Tankless': 41.8 * 16.53 * 20.25,
    'Gas w/ Tank': 57 * math.pi * (22 / 2) ** 2,
    'Electric Tankless': 18.13 * 17 * 10,
    '240V HPWH': 63.0 * math.pi * (22 / 2) ** 2,
}

# Convert AO Smith volumes to ft³
ao_smith_ft3 = {k: v / 1728 for k, v in ao_smith_in3.items()}

# Rheem volumes in ft³
rheem_ft3 = {
    'Electric Resistive': 13.95,
    'ESE HPWH': 6.49,
    '240V HPWH': 10.88,
    '120V HPWH': 14.90,
    'Gas w/ Tank': 14.09,
    'Gas Tankless': 3.91,
    'Electric Tankless': 0.77
}

# Combine into DataFrame
combined_df = pd.DataFrame({
    'Type': list(rheem_ft3.keys()),
    'Rheem (ft³)': [rheem_ft3.get(k, None) for k in rheem_ft3.keys()],
    'AO Smith (ft³)': [ao_smith_ft3.get(k, None) for k in rheem_ft3.keys()]
})

# Plot
fig, ax = plt.subplots(figsize=(12, 6))
x = range(len(combined_df))
width = 0.35

ax.bar([i - width/2 for i in x], combined_df['Rheem (ft³)'], width=width, label='Rheem', color='skyblue')
ax.bar([i + width/2 for i in x], combined_df['AO Smith (ft³)'], width=width, label='AO Smith', color='orange')

ax.set_xticks(x)
ax.set_xticklabels(combined_df['Type'], rotation=25, ha='right')
ax.set_ylabel('Volume (ft³)')
ax.set_title('Water Heater Volume Comparison: Rheem vs. AO Smith')
ax.legend()
plt.tight_layout()
plt.show()
