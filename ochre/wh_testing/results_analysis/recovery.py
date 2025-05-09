import os
from ochre import HeatPumpWaterHeater, ElectricResistanceWaterHeater, \
    GasWaterHeater, TanklessWaterHeater, GasTanklessWaterHeater, \
    ESEHeatPumpWaterHeater, LPHeatPumpWaterHeater
import matplotlib.pyplot as plt
import numpy as np

from wh_configs import configurations

# Constants
g2l = 3.78541
l2g = 1 / g2l
BTU_TO_W = 0.29307107
TEMP_RISE_C = 50  # Typical temperature rise in Celsius
WATER_HEAT_CAPACITY = 4184  # J/kg°C ≈ J/L°C since 1 L water ≈ 1 kg

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

    if issubclass(cls, (ESEHeatPumpWaterHeater)):
        battery_capacity_wh = params.get('batt_cap_kwh', 5)  # battery energy capacity in watt-hours
        water_heater_power_w = params.get('HPWH Power (W)', 1000)  # power draw of resistive heater in watts

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


# Plot
plt.figure(figsize=(10, 6))
bars = plt.bar(recovery_stats.keys(), recovery_stats.values())
plt.ylabel('Recovery Rate (gal/h)')
plt.title('Water Heater Recovery Rates by Architecture')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)
#plt.xscale("log")

# Add labels on top of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{yval:.1f}", ha='center', va='bottom')

plt.tight_layout()
plt.show()