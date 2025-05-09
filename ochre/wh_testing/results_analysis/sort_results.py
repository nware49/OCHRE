import pandas as pd

# Load the CSV file
df = pd.read_csv("ochre/wh_tests/results_analysis/usage_ratios2.csv", header=None, names=["Index", "Date", "Architecture", "Unmet_to_Usage_Ratio"])

# Replace 'inf' values with 0
df.replace([float('inf'), 'inf'], 0, inplace=True)

# Pivot the data to have WH Architecture as columns and Ratio values below
sorted_df = df.pivot_table(index="Date", columns="Architecture", values="Unmet_to_Usage_Ratio", aggfunc='first')

# Save the new CSV
sorted_df.to_csv("sorted_water_heaters.csv")

print("CSV successfully processed and saved!")
