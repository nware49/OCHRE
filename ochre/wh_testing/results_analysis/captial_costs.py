import matplotlib.pyplot as plt
import pandas as pd

# Data
data = {
    'Architecture': [
        'HP + PCM + Battery (Hypo 1)',
        'HP + PCM + Battery (Hypo 2)',
        'HP + Water Tank + Battery',
        'Tankless Electric (240)',
        'Tankless Gas',
        'Electric Resistive (240)',
        'Electric Resistive + HP (240)',
        'Electric HP (State 120)',
        'Electric HP (Rheem 120)',
        'Gas Water Heater'
    ],
    # 'Capital Cost': [5135.68, 4485.12, 3599.00, 749.92, 1375.44, 729.00, 1699.00, 3045.00, 1599.00, 1339.59],
    # 'Install Cost': [0, 0, 0, 2000, 1500, 1500, 1500, 0, 0, 900],
    # 'Rebate': [900, 900, 900, 0, 600, 0, 2750, 2750, 2750, 0],
    'Total Cost': [6206.45, 5385.12, 3499, 2749.92, 2875.44, 2229, 3199, 3945, 2499, 2239.59],
    'Consumer Cost': [2673.66, 2271.21, 1347, 2749.92, 2875.44, 2229, 1200.01, 1565.55, 857.01, 2239.59],
    'Rebate Amount': [3532.79, 3113.91, 2152, 0.0, 0.0, 0.0, 1999, 2379, 1642, 0.0]
}

df = pd.DataFrame(data)

# Calculate total cost before rebate and consumer out-of-pocket cost
# df['Total Cost'] = df['Capital Cost'] + df['Install Cost']
# df['Consumer Cost'] = df['Total Cost'] - df['Rebate']
# df['Rebate Amount'] = df['Rebate'].where(df['Rebate'] <= df['Total Cost'], df['Total Cost'])

palette = ['steelblue', 'firebrick', 'steelblue', 'steelblue', 'steelblue', 'firebrick', 'steelblue', 'steelblue']


# Plotting
plt.figure(figsize=(14, 7))
bars1 = plt.barh(df['Architecture'], df['Consumer Cost'], color=palette, label='Out-of-pocket Cost')
bars2 = plt.barh(df['Architecture'], df['Rebate Amount'], left=df['Consumer Cost'], color='lightgreen', label='Rebate')

# Add text labels
for bar, cost in zip(bars1, df['Total Cost']):
    consumer_cost = bar.get_width()
    plt.text(consumer_cost + 50, bar.get_y() + bar.get_height()/2, f'Total: ${consumer_cost:,.0f}', va='center')
    pre_rebate = cost
    plt.text(max(pre_rebate + 50, consumer_cost + 1000), bar.get_y() + bar.get_height()/2, f'Before Rebate: ${pre_rebate:,.0f}', va='center')

# Labels and formatting
plt.xlabel('Cost ($)')
plt.title('Total Cost Breakdown by Water Heater Architecture')
plt.legend()
plt.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.gca().invert_yaxis()
plt.subplots(figsize=(14, 8))

plt.show()
