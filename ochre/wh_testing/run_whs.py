import os
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from ochre import HeatPumpWaterHeater, ElectricResistanceWaterHeater, \
    GasWaterHeater, TanklessWaterHeater, GasTanklessWaterHeater, WaterHeater, \
    ESEHeatPumpWaterHeater, ESEElectricResistanceWaterHeater, LPHeatPumpWaterHeater

import itertools

import logging
import time
import random  # For generating random data for the example


from datetime import datetime

# Generate log file name with the current date and time
log_filename = datetime.now().strftime("script_log_%Y-%m-%d_%H-%M-%S.txt")
# Set up logging
logging.basicConfig(
    filename=log_filename,  # Log file name
    level=logging.INFO,         # Log level
    format="%(asctime)s - %(message)s",  # Log format
)

# local imports
from wh_configs import configurations
from traces import get_hw_trace

from pathlib import Path

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
RESULTS_DIR = Path(__file__).parent / f'results_{timestamp}'


def save_results(df, wh_name, trace_name):
    """Save results DataFrame to a CSV file in the results directory."""
    filename = f"{wh_name}.csv"
    filepath = RESULTS_DIR / trace_name / filename
    df.to_csv(filepath, index=False)
    print(f"Saved results: {filepath}")
    return filepath

def plot_water_heating_power(filepath):
    """Plot 'Water Heating Electric Power (kW)' from all saved results."""
    fig, ax = plt.subplots(figsize=(10, 6))
    filedir = filepath.parent

    for csv_file in filedir.glob("*.csv"):
        df = pd.read_csv(csv_file)
        if "Water Heating Electric Power (kW)" in df.columns:
            ax.plot(df["Water Heating Electric Power (kW)"], label=csv_file.stem)

    ax.set_xlabel("Time Step")
    ax.set_ylabel("Power (kW)")
    ax.set_title("Water Heating Electric Power (kW) for Each Configuration")
    ax.legend()
    plt.show()


def run_water_heater(wh_type, **params):
    """Run a single water heater configuration with given trace and parameters."""
    wh = wh_type(**params)
    df = wh.simulate()
    return df

def run_all_configurations(trace_dir):
    """Run all water heater types with all traces in the directory."""
    # Get all trace files
    trace_dir = Path(__file__).parent / trace_dir
    trace_files = list(Path(trace_dir).glob('*.csv'))
    print("found ", len(trace_files), " traces")

    # Store results
    results = []
    
    once_flag = False
    # Run each configuration with each trace
    for trace_file in trace_files:
        if once_flag == True:
            continue
        #once_flag = True # comment / uncomment if necessary
        print("running trace: ", trace_file.name)
        hw_trace, start_time, duration, time_res = get_hw_trace(trace_file)  # Adjust based on your trace loading method
        # create example water draw schedule and add to equipment args
        times = pd.date_range(start_time, start_time + duration, freq=time_res)
        hot_water_draws = np.where(hw_trace["UsageVolume"] > 0, hw_trace["UsageVolume"], 0)

        schedule = pd.DataFrame(
            {
                "Water Heating (L/min)": hot_water_draws,
                "Water Fixtures (L/min)": np.where(~hw_trace["UsageType"].isin(["Shower", "Clotheswasher", "Dishwasher"]), hw_trace["UsageVolume"], 0),
                "Showers (L/min)": np.where(hw_trace["UsageType"] == "Shower", hw_trace["UsageVolume"], 0),
                "Clothes Washer (L/min)": np.where(hw_trace["UsageType"] == "Clotheswasher", hw_trace["UsageVolume"], 0),
                "Dishwasher (L/min)": np.where(hw_trace["UsageType"] == "Dishwasher", hw_trace["UsageVolume"], 0),
                "Zone Temperature (C)": 20,
                "Mains Temperature (C)": 7,
                "Zone Wet Bulb Temperature (C)": 22,
            },
            index=times,
        )

        for wh_name, config in configurations.items():
            logging.info(f"Architecture: {wh_name} trace name: {trace_file}")
            if config['class'] != ElectricResistanceWaterHeater:
                #continue
                pass
            print(f"Running {wh_name} with trace {trace_file.name}")

            wh_params = config['params']
            wh_params['start_time'] = start_time
            wh_params['duration'] = duration
            wh_params['time_res'] = time_res
            print('time res:', time_res)
            wh_params['schedule'] = schedule
            wh_params['verbosity'] = 6
            wh_params['output_path'] = str(RESULTS_DIR / trace_file.name.split('.')[0])
            wh_params['save_results'] = True
            
            wh = config['class'](**wh_params)

            #filename = save_results(df, wh_name, trace_file.name)

            df = wh.simulate()
            water_results = wh.model.generate_results()
            if config['class'] == ESEHeatPumpWaterHeater:
                # Collect results
                results.append({
                    'water_heater_type': wh.name,
                    'trace_file': trace_file.name,
                    'total_delivered_wh': df['Water Heating Delivered (W)'].sum()/60,
                    'total_electric_power_kwh': df['Water Heating Electric Power (kW)'].sum()/(60*2.6),
                    'total_sensible_heat_wh': df['Water Heating Total Sensible Heat Gain (W)'].sum()/60,
                    # 'alt_electric_power_kwh': water_results['Hot Water Heat Loss (W)'],
                    #'energy_input': df.energy_input,
                    #'energy_output': df.energy_output,
                    #'average_tank_temp': np.mean(df.tank_temperatures) if hasattr(df, 'tank_temperatures') else None,
                    # Add more metrics as needed
                })
            else:
                # Collect results
                results.append({
                    'water_heater_type': wh.name,
                    'trace_file': trace_file.name,
                    'total_delivered_wh': df['Water Heating Delivered (W)'].sum()/60,
                    'total_electric_power_kwh': df['Water Heating Electric Power (kW)'].sum()/60,
                    'total_sensible_heat_wh': df['Water Heating Total Sensible Heat Gain (W)'].sum()/60,
                    # 'alt_electric_power_kwh': water_results['Hot Water Heat Loss (W)'],
                    #'energy_input': df.energy_input,
                    #'energy_output': df.energy_output,
                    #'average_tank_temp': np.mean(df.tank_temperatures) if hasattr(df, 'tank_temperatures') else None,
                    # Add more metrics as needed
                })
                #print("ElectricPower:", df['Hot Water Heat Loss (W)'].sum()/60)
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results
    #results_df.to_csv('water_heater_results.csv', index=False)
    return results_df

def run_variable_config(config_name, trace_dir):
    """Run a single water heater configuration with all traces in the directory."""
    # Get all trace files
    trace_dir = Path(__file__).parent / trace_dir
    trace_files = list(Path(trace_dir).glob('*.csv'))
    print("found ", len(trace_files), " traces")

    # Store results
    results = []
    # Run each configuration with each trace
    for trace_file in trace_files:
        print("running trace: ", trace_file.name)
        hw_trace, start_time, duration, time_res = get_hw_trace(trace_file)  # Adjust based on your trace loading method
        # create example water draw schedule and add to equipment args
        times = pd.date_range(start_time, start_time + duration, freq=time_res)
        schedule = pd.DataFrame(
            {
                "Water Heating (L/min)": hw_trace,
                "Zone Temperature (C)": 20,
                "Mains Temperature (C)": 7,
                "Zone Wet Bulb Temperature (C)": 22,
            },
            index=times,
        )

        wh_params = configurations[config_name]['params']
        wh_params['start_time'] = start_time
        wh_params['duration'] = duration
        wh_params['time_res'] = time_res
        wh_params['schedule'] = schedule
        wh_params['Showers (L/min)'] = hw_trace
        wh_params['verbosity'] = 6
        wh_params['output_path'] = str(RESULTS_DIR / trace_file.name.split('.')[0])
        wh_params['save_results'] = True

        variable_params = {
            "Tank Size (L)": [100, 175, 250],
            "Capacity (W)": [3000, 4500, 5000],
        }

        # Generate all combinations
        combinations = list(itertools.product(*variable_params.values()))

        print(f"Running {config_name} with trace {trace_file.name}")
        # Iterate through each combination
        for param_values in combinations:
            
            params = dict(zip(variable_params.keys(), param_values))  # Create a dictionary of current params
            print("Running simulation with:", params)

            wh_class = configurations[config_name]['class']
            params = configurations[config_name]['params']

            # Instantiate and run the simulation
            wh = wh_class(**params)  # Assuming the class takes params as kwargs
            #if config['class'] != ElectricResistanceWaterHeater:
            #    continue
            df = wh.simulate()

            # Collect results
            results.append({
                'water_heater_type': wh.name,
                'trace_file': trace_file.name,
                'total_delivered_wh': df['Water Heating Delivered (W)'].sum()/60,
                'total_electric_power_kwh': df['Water Heating Electric Power (kW)'].sum()/60,
                'total_sensible_heat_wh': df['Water Heating Total Sensible Heat Gain (W)'].sum()/60,
                #'energy_input': df.energy_input,
                #'energy_output': df.energy_output,
                #'average_tank_temp': np.mean(df.tank_temperatures) if hasattr(df, 'tank_temperatures') else None,
                # Add more metrics as needed
            })
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results
    #results_df.to_csv('water_heater_results.csv', index=False)
    return results_df    


if __name__ == "__main__":
    logging.info("Script started.")
    trace_directory = "hot_water_traces/traces_1min"  # Replace with your traces directory
    results = run_all_configurations(trace_directory)
    
    # Print summary statistics
    print("\nSummary Statistics by Water Heater Type:")
    print(results)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    results_filepath = RESULTS_DIR / f'wh_config_results_{timestamp}.csv'
    results.to_csv(results_filepath, index=False)
    # print(results.groupby('water_heater_type').agg({
    #     'energy_input': ['mean', 'std'],
    #    'energy_output': ['mean', 'std']
    # }))
    logging.info("Script finished.")