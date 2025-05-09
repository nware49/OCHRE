import os
import pandas as pd
import matplotlib.pyplot as plt

g2l = 3.78541  # gallons to liters
c_water = 4.186  # Specific heat capacity of water in kJ/kg°C
density_water = 1  # kg/L (approximate)

filename = "hot_water_traces/traces_1min/continuous_12S1003_trace_1min.csv"


def fahrenheit_to_celsius(f_temp):
    return (f_temp - 32) * 5/9


def get_hw_trace(filename, inlet_temp_f=50, outlet_temp_f=122, uef=1.0):
    df = pd.read_csv(filename)

    # Convert time columns to datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')

    # Calculate simulation duration
    start_time = df["Timestamp"].iloc[0]
    end_time = df["Timestamp"].iloc[-1]
    duration = end_time - start_time
    num_days = duration.total_seconds() / 86400  # Convert duration to days

    # Calculate time resolution
    time_diffs = df["Timestamp"].diff().dropna()
    unique_diffs = time_diffs.unique()
    if len(unique_diffs) > 1:
        raise ValueError(f"Inconsistent time intervals detected: {unique_diffs}")
    time_res = time_diffs.iloc[0]

    # Convert hot water draws from gallons to liters
    df["UsageVolume_L"] = df["UsageVolume"] * g2l
    
    # Print the 5 highest demand minutes
    top_5_usage = df.nlargest(5, "UsageVolume")
    #print("Top 5 highest demand minutes:")
    #print(top_5_usage)
    
    # Convert temperatures from Fahrenheit to Celsius
    inlet_temp = fahrenheit_to_celsius(inlet_temp_f)
    outlet_temp = fahrenheit_to_celsius(outlet_temp_f)
    
    # Calculate thermal energy required (Q = m * c * ΔT)
    df["ThermalEnergy_kJ"] = df["UsageVolume_L"] * density_water * c_water * (outlet_temp - inlet_temp)
    
    total_energy_kJ = df["ThermalEnergy_kJ"].sum()
    total_energy_kWh = total_energy_kJ / 3600  # Convert kJ to kWh
    
    # Calculate required energy in kWh based on UEF
    required_energy_kWh = total_energy_kWh / uef if uef > 0 else float('inf')
    
    # Calculate total gallons of hot water used
    total_gallons_used = df["UsageVolume"].sum()
    avg_gallons_per_day = total_gallons_used / num_days if num_days > 0 else float('inf')
    
    #print(f"Total gallons of hot water used: {total_gallons_used:.2f} gallons")
    #print(f"Average gallons per day: {avg_gallons_per_day:.2f} gallons/day")
    
    return {
        "Filename": filename,
        "Total Energy (kJ)": total_energy_kJ,
        "Total Energy (kWh)": total_energy_kWh,
        "Required Energy (kWh)": required_energy_kWh,
        "Total Gallons Used": total_gallons_used,
        "Average Gallons Per Day": avg_gallons_per_day
    }

def analyze_directory(directory, output_csv="results.csv", inlet_temp_f=50, outlet_temp_f=122, uef=1.0):
    results = []
    for file in os.listdir(directory):
        if file.endswith(".csv"):
            filepath = os.path.join(directory, file)
            try:
                result = get_hw_trace(filepath, inlet_temp_f, outlet_temp_f, uef)
                results.append(result)
            except Exception as e:
                print(f"Error processing {file}: {e}")
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")

    return results_df


def plot_results(results_df):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    ax1.boxplot([results_df["Total Energy (kWh)"], results_df["Required Energy (kWh)"], results_df["Average Gallons Per Day"]],
                labels=["Total Energy (kWh)", "Required Energy (kWh)", "Average Gallons Per Day"])
    ax1.set_ylabel("Energy (kWh) & Gallons Per Day")
    ax1.set_title("Distribution of Water Heating Metrics for Household Hot Water Traces")
    
    ax2 = ax1.twinx()
    ax2.boxplot([results_df["Total Gallons Used"]], positions=[4], labels=["Total Gallons Used"], boxprops=dict(color='blue'))
    ax2.set_ylabel("Total Gallons Used")
    
    plt.show()



filedir = "hot_water_traces/traces_1min/"
results = analyze_directory(filedir, "trace_summary analysis.csv", inlet_temp_f=50, outlet_temp_f=122, uef=1)

plot_results(results)
# tot_E_kJ, tot_E_kWh, req_E, dataframe = get_hw_trace(filename)

# print("kJ:", tot_E_kJ, "kWH:", tot_E_kWh)