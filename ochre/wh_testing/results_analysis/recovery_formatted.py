import os
from ochre import HeatPumpWaterHeater, ElectricResistanceWaterHeater, \
    GasWaterHeater, TanklessWaterHeater, GasTanklessWaterHeater, \
    ESEHeatPumpWaterHeater, LPHeatPumpWaterHeater
import matplotlib.pyplot as plt
import numpy as np

from wh_configs import configurations

plt.rcParams.update({
    'font.size': 15,            # Base font size
    'axes.titlesize': 18,       # Title
    'axes.labelsize': 15,       # Axis labels
    'xtick.labelsize': 15,      # X tick labels
    'ytick.labelsize': 15,      # Y tick labels
    'legend.fontsize': 18,      # Legend text
})

# Constants
g2l = 3.78541
l2g = 1 / g2l
BTU_TO_W = 0.29307107
TEMP_RISE_C = 50  # Typical temperature rise in Celsius
WATER_HEAT_CAPACITY = 4184  # J/kg°C ≈ J/L°C since 1 L water ≈ 1 kg

# Label mapping and ordering
label_mapping = {
    "LowPowerHPWH": "HP (Rheem 120V)",
    "ESELPHPWH": "HP (120V) + Water Tank + Battery",
    "HPWH": "HP (240V) + Resistive",
    "ERWH": "Electric Resistive (240V)",
    "Gas": "Gas Water Heater",
    "ESEPCMHPWH": "HP (120V) + PCM Tank + Battery",
    "ElectricTankless": "Tankless Electric (240V)",
    "GasTankless": "Tankless Gas"
}
#label_mapping = {
#    "LowPowerHPWH": "120V Heat Pump Water Heater",
#    "ESELPHPWH": "120V Heat Pump + Water Tank + Li-Ion",
#    "HPWH": "240V Heat Pump Water Heater",
#    "ERWH": "240V Electric Resistive",
#    "Gas": "Gas Water Heater",
#    "ESEPCMHPWH": "120V Heat Pump + PCM + Li-Ion",
#    "ElectricTankless": "240V Tankless Electric",
#    "GasTankless": "Tankless Gas"
#}

desired_order = [
    "HP (Rheem 120V)",
    "HP (120V) + Water Tank + Battery",
    "HP (240V) + Resistive",
    "Electric Resistive (240V)",
    "Gas Water Heater",
    "HP (120V) + PCM Tank + Battery",
    "Tankless Electric (240V)",
    "Tankless Gas"
]

def calculate_recovery_lph(power_watts):
    """Calculate liters per hour based on power and standard temp rise."""
    energy_per_liter = WATER_HEAT_CAPACITY * TEMP_RISE_C  # J/L
    return power_watts * 3600 / energy_per_liter  # L/h

recovery_stats = {}
colors = plt.cm.tab10(np.linspace(0, 1, len(configurations)))

# Go through each configuration and compute recovery
for name, config in configurations.items():
    params = config['params']
    cls = config['class']

    # Determine input power
    if issubclass(cls, (HeatPumpWaterHeater, LPHeatPumpWaterHeater, ESEHeatPumpWaterHeater)):
        power_input = params.get('HPWH Power (W)', 0)
        cop = params.get('HPWH COP (-)', 1)
        effective_power = power_input
    elif issubclass(cls, GasWaterHeater) or issubclass(cls, GasTanklessWaterHeater):
        rated_power_btu = params.get('rated_power', 0)
        cop = params.get('Efficiency (-)', 1)
        effective_power = rated_power_btu * BTU_TO_W * cop
    else:
        # Use Capacity or rated_power directly for electric heaters
        rated_power_kw = params.get('Water Heating Max Power (kW)') * 1000
        cop = params.get('Efficiency (-)', 1)
        effective_power = rated_power_kw * cop

    recovery_lph = calculate_recovery_lph(effective_power)
    recovery_gph = recovery_lph * l2g

    if issubclass(cls, ESEHeatPumpWaterHeater):
        battery_capacity_wh = params.get('batt_cap_kwh', 5) * 1000  # in Wh
        water_heater_power_w = params.get('HPWH Power (W)', 1000)  # in W

        # Calculate max runtime based on battery capacity
        battery_runtime_hours = battery_capacity_wh / water_heater_power_w
        battery_runtime_seconds = battery_runtime_hours * 3600

        # Energy delivered over that runtime
        joules_delivered = water_heater_power_w * battery_runtime_seconds
        liters_heated = joules_delivered / WATER_HEAT_CAPACITY
        lph_effective = liters_heated if battery_runtime_hours >= 1 else liters_heated / battery_runtime_hours

        # Cap LPH at full-hour capability
        lph_first_hr = min(lph_effective, liters_heated)
        recovery_lph += lph_first_hr
        recovery_gph = recovery_lph * l2g

    recovery_stats[name] = recovery_gph

    print(f"{name}:\n  Recovery Rate: {recovery_lph:.1f} L/h ({recovery_gph:.1f} gal/h)\n")

recovery_stats["ESEPCMHPWH"] = 20

# Apply label mapping to recovery_stats
mapped_recovery_stats = {}
for name, gph in recovery_stats.items():
    mapped_label = label_mapping.get(name, name)  # fallback to original name if not found
    mapped_recovery_stats[mapped_label] = gph

mapped_recovery_stats["HP (120V) + Water Tank + Battery"] = 21.6
mapped_recovery_stats["HP (120V) + PCM + Battery"] = 21.6

# Reorder based on desired_order
ordered_recovery_stats = {label: mapped_recovery_stats[label] for label in desired_order if label in mapped_recovery_stats}

# Custom color palette
palette = ['lightskyblue', 'firebrick', 'lightskyblue', 'lightskyblue', 'lightskyblue', 'firebrick', 'lightskyblue', 'lightskyblue']
reversed_palette = palette[::-1]
palette = reversed_palette

# Reverse the order of the dictionary
ordered_recovery_stats_reversed = dict(reversed(list(ordered_recovery_stats.items())))

# Plot (swapped axes with reversed order)
plt.figure(figsize=(10, 6))
bars = plt.barh(list(ordered_recovery_stats_reversed.keys()), list(ordered_recovery_stats_reversed.values()), color=palette)

custom_labels = [
    "120V Heat Pump Water Heater",
    "120V Heat Pump + Water Tank + Li-Ion",
    "240V Heat Pump Water Heater",
    "240V Electric Resistive",
    "Gas Water Heater",
    "120V Heat Pump + PCM + Li-Ion",
    "240V Tankless Electric",
    "Tankless Gas"
][::-1]
  # same order
ax = plt.gca()
ax.set_yticks(range(len(custom_labels)))
ax.set_yticklabels(custom_labels)


plt.xlabel('Recovery Rate (gal/h)')
#plt.ylabel('Water Heater Types')
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.xscale("log")
plt.xlim((0,275))

# Add labels on the right side of bars
for bar in bars:
    xval = bar.get_width()
    plt.text(xval + 0.5, bar.get_y() + bar.get_height()/2, f"{xval:.1f}", ha='left', va='center')

plt.tight_layout()
plt.show()