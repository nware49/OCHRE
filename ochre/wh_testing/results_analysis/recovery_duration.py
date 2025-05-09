import os
import pandas as pd

# Paths
results_dir = "../results"
results_dir = "ochre/wh_tests/results_20250407135003"
output_file = "ochre/wh_tests/results_analysis/recovery_durations.csv"

# Dictionary to hold durations for each configuration
recovery_data = {}


# Iterate through all subdirectories (one per configuration)
for subdir in os.listdir(results_dir):
    config_path = os.path.join(results_dir, subdir)
    #print(config_path)
    if not os.path.isdir(config_path):
        #print("not dir", config_path)
        continue

    # Find the correct data file in this configuration directory
    for file in os.listdir(config_path):
        if file.startswith("Water Tank_") and file.endswith(".csv"):
            print("Parsing file:", file)
            architecture_name = file.replace("Water Tank_", "").replace(".csv", "")
            filepath = os.path.join(config_path, file)
            df = pd.read_csv(filepath)
            if "Time" not in df.columns or "Hot Water Heat Injected (W)" not in df.columns:
                continue

            df['Time'] = pd.to_datetime(df['Time'])
            df = df.sort_values('Time')

            # Track recovery event durations
            durations = []
            heating = False
            start_time = None

            for i, row in df.iterrows():
                flow = row["Hot Water Heat Injected (W)"]
                if not heating and flow > 0:
                    # Start of recovery
                    start_time = row["Time"]
                    heating = True
                elif heating and flow == 0:
                    # End of recovery
                    end_time = row["Time"]
                    duration = (end_time - start_time).total_seconds()
                    durations.append(duration)
                    heating = False
                    start_time = None

            recovery_data[architecture_name] = durations
            #break  # Only process one file per configuration

# Create a DataFrame with durations (different lengths will be filled with NaN)
recovery_df = pd.DataFrame(recovery_data)

# Save to CSV
recovery_df.to_csv(output_file, index=False)

print(f"Recovery durations saved to {output_file}")
