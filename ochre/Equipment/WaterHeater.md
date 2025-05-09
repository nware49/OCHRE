To determine which parameters are "settable" for each water heater configuration class in the provided source code, we need to identify the attributes or inputs that can be configured or adjusted during initialization or runtime via the constructor (`__init__`) or external control methods (e.g., `update_external_control`). "Settable" parameters are typically those that can be passed as arguments to the constructor (via `kwargs`) or modified through control signals, as opposed to fixed or derived values calculated internally.

The code defines a base `WaterHeater` class and several derived classes:
- `ElectricResistanceWaterHeater`
- `HeatPumpWaterHeater`
- `LPHeatPumpWaterHeater` (Low Power Heat Pump Water Heater)
- `ESEElectricResistanceWaterHeater` (Energy Storage Enhanced)
- `ESEHeatPumpWaterHeater` (Energy Storage Enhanced)
- `GasWaterHeater`
- `TanklessWaterHeater`
- `GasTanklessWaterHeater`

Each class inherits properties from its parent and may add or override specific parameters. We'll analyze the `__init__` method and `update_external_control` method of each class to deduce the settable parameters, focusing on:
1. Parameters explicitly set in `__init__` via `kwargs` or defaults.
2. Parameters that can be updated via external control signals.

---

### General Approach
- **Base Class (`WaterHeater`)**: Provides common parameters inherited by all subclasses.
- **Derived Classes**: May override defaults, add new parameters, or extend functionality.
- **Settable Parameters**: Include those passed via `kwargs`, set with defaults in `__init__`, or adjustable via `update_external_control`.

---

### 1. `WaterHeater` (Base Class)
The base class defines the core functionality and parameters for all water heaters.

#### Settable Parameters from `__init__`:
- **`use_ideal_capacity`**: Optional argument, defaults to `None` (determined by time resolution if not provided).
- **`model_class`**: Optional, defaults to `None` (set based on `water_nodes` if not provided).
- **`water_nodes`**: Number of nodes in the water tank model (via `kwargs`), defaults to 2.
- **`name`**: Equipment name (via `kwargs`), defaults to `'Water Heater'`.
- **`Efficiency (-)`**: Unitless efficiency, defaults to 1.
- **`Capacity (W)`**: Rated capacity in watts, defaults to 4500 W.
- **`Setpoint Temperature (C)`**: Required parameter (no default, must be provided via `kwargs`).
- **`Max Tank Temperature (C)`**: Maximum tank temperature, defaults to 60°C (converted from 140°F).
- **`Max Setpoint Ramp Rate (C/min)`**: Maximum setpoint ramp rate, no default (optional).
- **`Deadband Temperature (C)`**: Deadband range in delta °C, defaults to 5.56°C.
- **`Max Power (kW)`**: Maximum power in kW, no default (optional).
- **`Water Tank`**: Dictionary of additional water tank model arguments (via `kwargs`).

#### Settable Parameters from `update_external_control`:
- **`Setpoint`**: Updates `setpoint_temp` or `Water Heating Setpoint (C)` in the schedule (in °C).
- **`Deadband`**: Updates `deadband_temp` or `Water Heating Deadband (C)` in the schedule (in °C).
- **`Max Power`**: Updates `max_power` or `Water Heating Max Power (kW)` in the schedule (in kW).
- **`Load Fraction`**: Forces the water heater off (0) or allows normal operation (1).
- **`Duty Cycle`**: Fraction of time on (0 to 1), as a single value or list.

#### Notes:
- The `optional_inputs` list suggests additional schedule-based inputs: `"Water Heating Setpoint (C)"`, `"Water Heating Deadband (C)"`, `"Water Heating Max Power (kW)"`, and `"Zone Temperature (C)"`.
- Parameters like `setpoint_temp`, `deadband_temp`, and `max_power` can be set either at initialization or dynamically via control signals.

---

### 2. `ElectricResistanceWaterHeater`
Inherits from `WaterHeater` with specific modes: `['Upper On', 'Lower On', 'Off']`.

#### Additional Settable Parameters:
- None explicitly added in `__init__`.

#### Settable Parameters from `update_external_control`:
- Inherits all from `WaterHeater`.
- Duty cycles can be split between upper and lower elements if provided as a list.

#### Notes:
- Uses the base class parameters without adding new ones in `__init__`.

---

### 3. `HeatPumpWaterHeater`
Inherits from `ElectricResistanceWaterHeater` with modes: `['Heat Pump On', 'Lower On', 'Upper On', 'Off']`.

#### Additional Settable Parameters from `__init__`:
- **`hp_only_mode`**: Boolean, defaults to `False`.
- **`water_nodes`**: Defaults to 12 (overrides base class default of 2).
- **`HPWH Minimum On Time (min)`**: Minimum heat pump on time, defaults to 10 minutes.
- **`HPWH Minimum Off Time (min)`**: Minimum off time, defaults to 0 minutes.
- **`Deadband Temperature (C)`**: Defaults to 8.17°C (overrides base class default of 5.56°C).
- **`Low Power HPWH`**: Boolean, defaults to `False`.
- **`HPWH COP (-)`**: Nominal COP, required (no default).
- **`HPWH Capacity (W)`**: Heat pump capacity in watts, optional (if not provided, derived from `HPWH Power (W)`).
- **`HPWH Power (W)`**: Heat pump power in watts, defaults to 500 W (used if `HPWH Capacity (W)` not provided).
- **`HPWH Parasitics (W)`**: Parasitic power in watts, defaults to 1 W.
- **`HPWH Fan Power (W)`**: Fan power in watts, defaults to 35 W.
- **`HPWH SHR (-)`**: Sensible heat ratio, defaults to 0.88.
- **`HPWH Interaction Factor (-)`**: Interaction factor, defaults to 0.75 if indoors, 1 otherwise.
- **`HPWH Wall Interaction Factor (-)`**: Wall interaction factor, defaults to 0.5.

#### Settable Parameters from `update_external_control`:
- Inherits from `ElectricResistanceWaterHeater`.
- **`HP Duty Cycle`**: Duty cycle for heat pump mode (0 to 1).
- **`ER Duty Cycle`**: Duty cycle for electric resistance mode (0 to 1).

#### Notes:
- Adds heat pump-specific parameters and overrides some defaults (e.g., `water_nodes`, `deadband_temp`).

---

### 4. `LPHeatPumpWaterHeater` (Low Power Heat Pump Water Heater)
Inherits from `HeatPumpWaterHeater`.

#### Additional Settable Parameters:
- **`Low Power HPWH`**: Defaults to `True` (overrides `HeatPumpWaterHeater` default of `False`).

#### Notes:
- Identical to `HeatPumpWaterHeater` except for the default value of `Low Power HPWH`, which affects capacity and COP coefficients.

---

### 5. `ESEElectricResistanceWaterHeater` (Energy Storage Enhanced)
Inherits from `ElectricResistanceWaterHeater` with modes: `['Upper On', 'Lower On', 'Off', 'Charging Battery', 'Discharging Battery']`.

#### Additional Settable Parameters:
- None added in `__init__`.

#### Notes:
- Extends modes to include battery charging/discharging, but no additional settable parameters are defined in the provided code.

---

### 6. `ESEHeatPumpWaterHeater` (Energy Storage Enhanced)
Inherits from `ElectricResistanceWaterHeater` with modes: `['Heat Pump On', 'Lower On', 'Upper On', 'Both On', 'Off']` and `battery_mode`: `['Charging Battery', 'Discharging Battery', 'Off']`.

#### Additional Settable Parameters from `__init__`:
- Inherits all from `HeatPumpWaterHeater`.
- **`Battery State of Charge (%)`**: Battery SOC, defaults to 0%.
- **`Thermal Tank State of Charge (%)`**: Tank SOC, defaults to 0%.
- **`Demand Rate (%)`**: Demand rate, defaults to 0%.

#### Notes:
- Adds battery and tank SOC parameters for energy storage logic in `run_thermostat_control`.

---

### 7. `GasWaterHeater`
Inherits from `WaterHeater`.

#### Additional Settable Parameters from `__init__`:
- **`Energy Factor (-)`**: Required (no default), affects `skin_loss_frac`.

#### Notes:
- Sets `is_gas = True` and adjusts `skin_loss_frac` based on `Energy Factor (-)`.

---

### 8. `TanklessWaterHeater`
Inherits from `WaterHeater`.

#### Additional Settable Parameters from `__init__`:
- **`use_ideal_capacity`**: Forced to `True`.
- **`model_class`**: Forced to `IdealWaterModel`.
- **`Capacity (W)`**: Defaults to 20000 W (overrides base class default of 4500 W).
- **`Parasitic Power (W)`**: Parasitic power in watts (not explicitly set here, but relevant for `GasTanklessWaterHeater`).

#### Notes:
- Overrides some base class defaults and fixes certain parameters.

---

### 9. `GasTanklessWaterHeater`
Inherits from `TanklessWaterHeater`.

#### Additional Settable Parameters from `__init__`:
- **`Parasitic Power (W)`**: Required (no default), converted to kW.

#### Notes:
- Sets `is_gas = True` and adds parasitic power for gas operation.

---

### Summary of Settable Parameters by Class

| **Class**                     | **Settable Parameters**                                                                                                   |
|-------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| `WaterHeater`                 | `use_ideal_capacity`, `model_class`, `water_nodes`, `name`, `Efficiency (-)`, `Capacity (W)`, `Setpoint Temperature (C)`, `Max Tank Temperature (C)`, `Max Setpoint Ramp Rate (C/min)`, `Deadband Temperature (C)`, `Max Power (kW)`, `Setpoint`, `Deadband`, `Max Power`, `Load Fraction`, `Duty Cycle` |
| `ElectricResistanceWaterHeater` | Inherits all from `WaterHeater`                                                                                          |
| `HeatPumpWaterHeater`         | Inherits all from `ElectricResistanceWaterHeater` + `hp_only_mode`, `water_nodes` (default 12), `HPWH Minimum On Time (min)`, `HPWH Minimum Off Time (min)`, `Deadband Temperature (C)` (default 8.17), `Low Power HPWH`, `HPWH COP (-)`, `HPWH Capacity (W)`, `HPWH Power (W)`, `HPWH Parasitics (W)`, `HPWH Fan Power (W)`, `HPWH SHR (-)`, `HPWH Interaction Factor (-)`, `HPWH Wall Interaction Factor (-)`, `HP Duty Cycle`, `ER Duty Cycle` |
| `LPHeatPumpWaterHeater`       | Inherits all from `HeatPumpWaterHeater` + `Low Power HPWH` (default `True`)                                               |
| `ESEElectricResistanceWaterHeater` | Inherits all from `ElectricResistanceWaterHeater`                                                                    |
| `ESEHeatPumpWaterHeater`      | Inherits all from `HeatPumpWaterHeater` + `Battery State of Charge (%)`, `Thermal Tank State of Charge (%)`, `Demand Rate (%)` |
| `GasWaterHeater`              | Inherits all from `WaterHeater` + `Energy Factor (-)`                                                                     |
| `TanklessWaterHeater`         | Inherits all from `WaterHeater` + `use_ideal_capacity` (fixed `True`), `model_class` (fixed `IdealWaterModel`), `Capacity (W)` (default 20000) |
| `GasTanklessWaterHeater`      | Inherits all from `TanklessWaterHeater` + `Parasitic Power (W)`                                                           |

---

### Conclusion
- **Common Settable Parameters**: All classes inherit the base `WaterHeater` parameters, such as `Setpoint Temperature (C)`, `Deadband Temperature (C)`, and `Max Power (kW)`.
- **Class-Specific Additions**: Heat pump classes add COP, capacity, and duty cycle options; energy storage classes add SOC parameters; gas and tankless classes adjust energy factors and parasitic power.
- **Dynamic Control**: Parameters like `Setpoint`, `Deadband`, `Max Power`, and `Duty Cycle` can be adjusted during runtime via `update_external_control`.

Let me know if you need further clarification or a deeper analysis of specific classes!