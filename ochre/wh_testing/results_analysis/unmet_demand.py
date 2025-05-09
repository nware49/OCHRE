import os
import pandas as pd

def count_usage_events(water_tank_df):
    # Initialize event count
    usage_events = []
    event_start = None
    for i, row in water_tank_df.iterrows():
        # Ignore 'Leak' events
        if row['UsageType'] == 'Leak' or row['UsageVolume'] == 0:
            if event_start is not None:
                # We ended an event, so add it
                usage_events.append((event_start, row['Timestamp'] - water_tank_df.loc[event_start, 'Timestamp']))
            event_start = None
        else:
            # Start or continue an event
            if event_start is None:
                event_start = i
    # Finalize last event
    if event_start is not None:
        usage_events.append((event_start, water_tank_df.loc[i, 'Timestamp'] - water_tank_df.loc[event_start, 'Timestamp']))
    return len(usage_events)

def count_unmet_demand_events(unmet_demand_df):
    # Initialize unmet demand events
    unmet_events = []
    threshold = unmet_demand_df['Hot Water Unmet Demand (kW)'].max() * 0.1
    event_start = None
    for i, row in unmet_demand_df.iterrows():
        if row['Hot Water Unmet Demand (kW)'] >= threshold:
            if event_start is None:
                event_start = i
        else:
            if event_start is not None and (row['Time'] - unmet_demand_df.loc[event_start, 'Time']).total_seconds() > 1:
                unmet_events.append((event_start, i))
            event_start = None
    if event_start is not None:
        unmet_events.append((event_start, i))
    return len(unmet_events)

def process_files(hot_water_traces_dir, results_dir):
    result = []
    
    # Iterate over each file in the hot_water_traces directory
    for filename in os.listdir(hot_water_traces_dir):
        if filename.endswith(".csv"):
            # Read the water usage trace
            water_tank_df = pd.read_csv(os.path.join(hot_water_traces_dir, filename))
            water_tank_df['Timestamp'] = pd.to_datetime(water_tank_df['Timestamp'])

            # Find the corresponding results directory and unmet demand files
            results_subdir = os.path.join(results_dir, filename[:-4])  # Remove .csv extension
            if not os.path.isdir(results_subdir):
                continue  # Skip if the corresponding directory doesn't exist

            unmet_demand_files = [f for f in os.listdir(results_subdir) if f.startswith("Water Tank_") and f.endswith(".csv")]
            
            # Iterate over all unmet demand files in the results subdirectory
            for unmet_filename in unmet_demand_files:
                # Extract the water heater architecture name
                architecture_name = unmet_filename.replace("Water Tank_", "").replace(".csv", "")
                print("Parsing", architecture_name, "on", filename)

                # Load unmet demand data
                unmet_demand_df = pd.read_csv(os.path.join(results_subdir, unmet_filename))
                unmet_demand_df['Time'] = pd.to_datetime(unmet_demand_df['Time'])

                # Ensure 'Date' column is created for grouping
                water_tank_df['Date'] = water_tank_df['Timestamp'].dt.date
                unmet_demand_df['Date'] = unmet_demand_df['Time'].dt.date

                # Calculate daily usage and unmet demand events
                daily_usage_events = water_tank_df.groupby('Date').apply(count_usage_events)
                daily_unmet_events = unmet_demand_df.groupby('Date').apply(count_unmet_demand_events)

                # Align indices to avoid mismatches
                daily_usage_events, daily_unmet_events = daily_usage_events.align(daily_unmet_events, fill_value=0)

                # Create a DataFrame to store results
                combined_df = pd.DataFrame({
                    'Date': daily_usage_events.index,
                    'Number_of_Usage_Events': daily_usage_events.values,
                    'Number_of_Unmet_Demand_Events': daily_unmet_events.values
                })

                # Calculate the unmet-to-usage ratio safely
                combined_df['Unmet_to_Usage_Ratio'] = combined_df['Number_of_Unmet_Demand_Events'] / combined_df['Number_of_Usage_Events']
                combined_df['Unmet_to_Usage_Ratio'] = combined_df['Unmet_to_Usage_Ratio'].fillna(0)  # Avoid NaNs

                # Add the architecture name column
                combined_df['Architecture'] = architecture_name

                # Append to results list
                result.append(combined_df[['Date', 'Architecture', 'Unmet_to_Usage_Ratio']])

    # Combine all architectures into a single DataFrame
    final_df = pd.concat(result, ignore_index=True)

    final_df.to_csv(os.path.join(os.getcwd(), "ochre\\wh_tests\\results_analysis", "usage_ratios2.csv"))

    # Pivot the table so that each architecture is a column and dates are the index
    pivot_df = final_df.pivot(index='Date', columns='Architecture', values='Unmet_to_Usage_Ratio')

    # Save to CSV
    pivot_df.to_csv(os.path.join(os.getcwd(), "ochre\\wh_tests\\results_analysis", "unmet_to_usage_ratios_pivoted2.csv"))

    return pivot_df

# Specify the directories where your files are stored
hot_water_traces_dir = os.path.join(os.getcwd(), "ochre\\wh_tests\\hot_water_traces")
results_dir = os.path.join(os.getcwd(), "ochre\\wh_tests\\results")

# Process the files and generate the result
final_result_df = process_files(hot_water_traces_dir, results_dir)

