import pandas as pd
from pathlib import Path

def select_usage_type(group):
    non_none_leak = group.loc[~group['UsageType'].isin(['None', 'Leak'])]
    if not non_none_leak.empty:
        return non_none_leak.iloc[0]['UsageType']
    if 'Leak' in group['UsageType'].values:
        return 'Leak'
    return 'None'

def aggregate_to_minute_resolution(file_path, output_dir):
    df = pd.read_csv(file_path, parse_dates=['Timestamp'])
    df.set_index('Timestamp', inplace=True)
    
    # Separate numeric columns for resampling
    numeric_cols = ['UsageVolume']  # Explicitly defining numeric columns
    df_numeric = df[numeric_cols].resample('1T').sum()
    
    # Aggregate UsageType separately
    df_usage_type = df.groupby(pd.Grouper(freq='1T')).apply(select_usage_type)
    
    # Merge results
    df_resampled = df_numeric.copy()
    df_resampled['UsageType'] = df_usage_type.values
    df_resampled.reset_index(inplace=True)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / (file_path.stem + '_1min.csv')
    
    df_resampled.to_csv(output_file, index=False)
    print(f"Processed {file_path.name} -> {output_file}")

def process_directory(directory, output_directory):
    directory = Path(directory)
    output_directory = Path(output_directory)
    output_directory.mkdir(exist_ok=True)
    
    for file_path in directory.glob("*.csv"):
        aggregate_to_minute_resolution(file_path, output_directory)

# Example usage
process_directory("hot_water_traces", "hot_water_traces/traces_1min")
