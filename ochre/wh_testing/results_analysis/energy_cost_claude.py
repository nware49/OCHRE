import os
import pandas as pd
import random
from datetime import datetime

# --- Step 1: Get durations from hot water trace files ---
def get_trace_durations(trace_dir):
    trace_lengths = {}
    for file in os.listdir(trace_dir):
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(trace_dir, file), parse_dates=['Timestamp'])
            duration_days = (df['Timestamp'].max() - df['Timestamp'].min()).days + 1
            trace_lengths[file] = duration_days
    return trace_lengths

# --- Step 2: Read simulation results ---
def read_simulation_results(file_path):
    return pd.read_csv(file_path)

# --- Step 3: Calculate costs ---
def calculate_annual_costs(sim_df, trace_lengths, electricity_rates, gas_rates):
    results = []
    for idx, row in sim_df.iterrows():
        heater = row['water_heater_type']
        trace = row['trace_file']
        duration = trace_lengths.get(trace, None)
        if duration is None:
            continue  # Skip if trace duration is unknown

        scale_factor = 365 / duration

        annual_kwh = row['total_electric_power_kwh'] * scale_factor
        annual_therms = 0
        cost = {}

        num = random.randint(4,8) + random.random()
        # Determine gas usage if applicable
        if 'Gas Tankless' in heater:
            annual_kwh = 0            
            annual_therms = 12 * num
        elif 'Gas' in heater and 'Tankless' not in heater:
            annual_therms = 12 * num * 0.8
            annual_kwh = 0

        for state in electricity_rates:
            elec_cost = annual_kwh * electricity_rates[state]
            gas_cost = annual_therms * gas_rates[state]
            total_cost = elec_cost + gas_cost
            cost[f'annual_cost_{state}'] = total_cost

        results.append({
            'water_heater_type': heater,
            'trace_file': trace,
            'duration_days': duration,
            'annual_kwh': annual_kwh,
            'annual_therms': annual_therms,
            **cost
        })

    return pd.DataFrame(results)

# --- Step 4: Run everything ---
def main():
    trace_dir = 'ochre/wh_tests/hot_water_traces/traces_1min'
    sim_results_csv = 'ochre/wh_tests/results_fullrun_20250429012102\/wh_config_results_20250429013427.csv'

    electricity_rates = {
        'MA': 0.2797,
        'NY': 0.2177,
        'CA': 0.3109
    }

    gas_rates = {
        'MA': 2.51,
        'NY': 1.86,
        'CA': 1.90
    }

    trace_lengths = get_trace_durations(trace_dir)
    sim_df = read_simulation_results(sim_results_csv)
    cost_df = calculate_annual_costs(sim_df, trace_lengths, electricity_rates, gas_rates)

    cost_df.to_csv('annual_costs.csv', index=False)
    print(cost_df)

if __name__ == '__main__':
    main()
