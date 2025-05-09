import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load recovery durations data
df = pd.read_csv("ochre/wh_tests/results_analysis/recovery_durations.csv")

# Convert from wide to long format for seaborn
df_long = df.melt(var_name="Configuration", value_name="Recovery Duration (s)")

# Remove NaN values
df_long.dropna(inplace=True)

# Set up the plot
plt.figure(figsize=(12, 6))
sns.boxplot(x="Configuration", y="Recovery Duration (s)", data=df_long)

# Improve formatting
plt.title("Recovery Time Distributions by Water Heater Configuration")
#plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Show or save
plt.savefig("ochre/wh_tests/results_analysis/recovery_durations_boxplot.png", dpi=300)
plt.show()
