import pandas as pd

g2l = 3.78541  # gallons to liters
l2g = 1 / g2l  # liters to gallons

def get_hw_trace(filename):
    df = pd.read_csv(filename)

    # Convert time columns to datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')

    # Calculate simulation duration
    start_time = df["Timestamp"].iloc[0]
    end_time = df["Timestamp"].iloc[-1]
    duration = end_time - start_time

    # Calculate time resolution
    time_diffs = df["Timestamp"].diff().dropna()
    unique_diffs = time_diffs.unique()
    if len(unique_diffs) > 1:
        raise ValueError(f"Inconsistent time intervals detected: {unique_diffs}")
    time_res = time_diffs.iloc[0]

    # Convert hot water draws from gallons to liters
    df["UsageVolume"] = df["UsageVolume"] * g2l  # Gallons to Liters, 6 * 10 second intervals for GPM
    hot_water_draws = df

    return hot_water_draws, start_time, duration, time_res

