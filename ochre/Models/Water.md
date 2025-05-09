To determine the "settable" parameters for the models `StratifiedWaterModel`, `PhaseChangeMaterialModel`, `OneNodeWaterModel`, `TwoNodeWaterModel`, and `IdealWaterModel`, I'll analyze their `__init__`, `load_rc_data`, `initialize_state`, and any control-related methods (e.g., `update_model`) to identify parameters that can be configured via constructor arguments (`kwargs`), defaults, or external inputs. "Settable" parameters are those that can be explicitly provided by the user or adjusted dynamically, as opposed to being internally calculated or fixed.

I'll present the results in the same format as the previous analysis for the water heater classes, focusing on parameters from `__init__`, `load_rc_data`, and `initialize_state`, since these models don’t have an explicit `update_external_control` method like the water heater classes. However, `update_model` accepts a `control_signal` (heat injections), which I'll include as a settable input where applicable.

---

### Analysis of Settable Parameters

#### 1. `StratifiedWaterModel`
This is the base class for stratified water tank modeling.

##### Settable Parameters from `__init__`:
- **`water_nodes`**: Number of nodes in the tank, defaults to 12.
- **`water_vol_fractions`**: Array of volume fractions per node, defaults to `None` (equal fractions if not provided).
- **`Tank Volume (L)`**: Total tank volume in liters, required (no default).
- **`Mixed Delivery Temperature (C)`**: Target temperature for tempered water draw, defaults to 40.56°C (105°F).
- **`Tempering Valve Setpoint (C)`**: Setpoint for hot water draw, defaults to 51.67°C (125°F).
- **`Setpoint Temperature (C)`**: Tank setpoint temperature, defaults to 51.67°C (125°F).

##### Settable Parameters from `load_rc_data`:
- **`Tank Height (m)`**: Height of the tank in meters, required (no default).
- **`Heat Transfer Coefficient (W/m^2/K)`**: Heat transfer coefficient, optional (alternative to `UA (W/K)`).
- **`UA (W/K)`**: Overall heat transfer coefficient, optional (alternative to `Heat Transfer Coefficient (W/m^2/K)`).

##### Settable Parameters from `initialize_state`:
- **`Initial Temperature (C)`**: Initial temperature of all nodes, optional (defaults to near setpoint minus a fraction of deadband).
- **`Setpoint Temperature (C)`**: Used for default initialization, defaults to 51.67°C (125°F).
- **`Deadband Temperature (C)`**: Deadband range, defaults to 5.56°C (10°R).

##### Settable Parameters from `update_model`:
- **`control_signal`**: Array of heat injections (W) for each node, optional (defaults to zero if not provided).

##### Notes:
- The `optional_inputs` list (`Water Fixtures (L/min)`, `Showers (L/min)`, etc.) indicates schedule-based inputs that can influence water draw but are not directly settable in the constructor.

---

#### 2. `PhaseChangeMaterialModel`
Inherits from `StratifiedWaterModel` and adds PCM-specific functionality.

##### Settable Parameters from `__init__`:
- Inherits all from `StratifiedWaterModel`:
  - **`water_nodes`**: Defaults to 12.
  - **`water_vol_fractions`**: Defaults to `None`.
  - **`Tank Volume (L)`**: Required.
  - **`Mixed Delivery Temperature (C)`**: Defaults to 40.56°C.
  - **`Tempering Valve Setpoint (C)`**: Defaults to 51.67°C.
  - **`Setpoint Temperature (C)`**: Defaults to 51.67°C.
- Additional PCM-specific parameters:
  - **`PCM Phase Change Temperature (C)`**: Temperature at which PCM changes phase, defaults to 58.0°C.
  - **`PCM Latent Heat (J/kg)`**: Latent heat of fusion, defaults to 200,000 J/kg.
  - **`PCM Specific Heat Solid (J/kg/K)`**: Specific heat of solid PCM, defaults to 2000 J/kg/K.
  - **`PCM Specific Heat Liquid (J/kg/K)`**: Specific heat of liquid PCM, defaults to 2400 J/kg/K.
  - **`PCM Density (kg/L)`**: Density of PCM, defaults to 0.88 kg/L.

##### Settable Parameters from `load_rc_data`:
- Inherits all from `StratifiedWaterModel`:
  - **`Tank Height (m)`**: Required.
  - **`Heat Transfer Coefficient (W/m^2/K)`**: Optional.
  - **`UA (W/K)`**: Optional.

##### Settable Parameters from `initialize_state`:
- Inherits all from `StratifiedWaterModel`:
  - **`Initial Temperature (C)`**: Optional.
  - **`Setpoint Temperature (C)`**: Defaults to 51.67°C.
  - **`Deadband Temperature (C)`**: Defaults to 5.56°C.
- Uses `PCM Phase Change Temperature (C)` to determine initial PCM fraction (not directly settable here but influences initialization).

##### Settable Parameters from `update_model`:
- **`control_signal`**: Array of heat injections (W) for each node, optional (defaults to zero).

##### Notes:
- PCM-specific parameters are added to model phase change behavior, while inheriting all base class settable parameters.

---

#### 3. `OneNodeWaterModel`
Inherits from `StratifiedWaterModel` with a fixed 1-node configuration.

##### Settable Parameters from `__init__`:
- Inherits all from `StratifiedWaterModel` except `water_nodes`:
  - **`water_vol_fractions`**: Defaults to `None` (but effectively ignored as it’s a 1-node model).
  - **`Tank Volume (L)`**: Required.
  - **`Mixed Delivery Temperature (C)`**: Defaults to 40.56°C.
  - **`Tempering Valve Setpoint (C)`**: Defaults to 51.67°C.
  - **`Setpoint Temperature (C)`**: Defaults to 51.67°C.
- **`water_nodes`**: Fixed to 1 (overrides any provided value).

##### Settable Parameters from `load_rc_data`:
- Inherits all from `StratifiedWaterModel`:
  - **`Tank Height (m)`**: Required.
  - **`Heat Transfer Coefficient (W/m^2/K)`**: Optional.
  - **`UA (W/K)`**: Optional.

##### Settable Parameters from `initialize_state`:
- Inherits all from `StratifiedWaterModel`:
  - **`Initial Temperature (C)`**: Optional.
  - **`Setpoint Temperature (C)`**: Defaults to 51.67°C.
  - **`Deadband Temperature (C)`**: Defaults to 5.56°C.

##### Settable Parameters from `update_model`:
- **`control_signal`**: Array of heat injections (W) for the single node, optional (defaults to zero).

##### Notes:
- Simplifies `StratifiedWaterModel` by fixing `water_nodes` to 1.

---

#### 4. `TwoNodeWaterModel`
Inherits from `StratifiedWaterModel` with a fixed 2-node configuration.

##### Settable Parameters from `__init__`:
- Inherits all from `StratifiedWaterModel` except `water_nodes` and `water_vol_fractions`:
  - **`Tank Volume (L)`**: Required.
  - **`Mixed Delivery Temperature (C)`**: Defaults to 40.56°C.
  - **`Tempering Valve Setpoint (C)`**: Defaults to 51.67°C.
  - **`Setpoint Temperature (C)`**: Defaults to 51.67°C.
- **`water_nodes`**: Fixed to 2 (overrides any provided value).
- **`water_vol_fractions`**: Fixed to `[1/3, 2/3]` (overrides any provided value).

##### Settable Parameters from `load_rc_data`:
- Inherits all from `StratifiedWaterModel`:
  - **`Tank Height (m)`**: Required.
  - **`Heat Transfer Coefficient (W/m^2/K)`**: Optional.
  - **`UA (W/K)`**: Optional.

##### Settable Parameters from `initialize_state`:
- Inherits all from `StratifiedWaterModel`:
  - **`Initial Temperature (C)`**: Optional.
  - **`Setpoint Temperature (C)`**: Defaults to 51.67°C.
  - **`Deadband Temperature (C)`**: Defaults to 5.56°C.

##### Settable Parameters from `update_model`:
- **`control_signal`**: Array of heat injections (W) for two nodes, optional (defaults to zero).

##### Notes:
- Fixes `water_nodes` to 2 and `water_vol_fractions` to `[1/3, 2/3]`.

---

#### 5. `IdealWaterModel`
Inherits from `OneNodeWaterModel` with idealized assumptions.

##### Settable Parameters from `__init__`:
- Inherits all from `OneNodeWaterModel`:
  - **`Tank Volume (L)`**: Required.
  - **`Mixed Delivery Temperature (C)`**: Defaults to 40.56°C.
  - **`Tempering Valve Setpoint (C)`**: Defaults to 51.67°C.
  - **`Setpoint Temperature (C)`**: Defaults to 51.67°C.
- **`water_nodes`**: Fixed to 1 (via `OneNodeWaterModel`).

##### Settable Parameters from `load_rc_data`:
- None explicitly settable:
  - Overrides parent method to fix `volume` to 1000 L and sets `R_WH1_AMB` to 1e6 (W/K) and `C_WH1` to `volume * water_c` internally.

##### Settable Parameters from `initialize_state`:
- **`Setpoint Temperature (C)`**: Used to set initial temperature to the setpoint, defaults to 51.67°C.
- **`Initial Temperature (C)`**: Optional (overrides default setpoint initialization).

##### Settable Parameters from `update_model`:
- **`control_signal`**: Array of heat injections (W) for the single node, optional (defaults to zero).

##### Notes:
- Overrides `load_rc_data` to enforce ideal insulation and a fixed volume, reducing settable RC parameters.

---

Below is the completed **Summary of Settable Parameters by Class** for the models `StratifiedWaterModel`, `PhaseChangeMaterialModel`, `OneNodeWaterModel`, `TwoNodeWaterModel`, and `IdealWaterModel`, based on the analysis provided in my last response. I've ensured all settable parameters identified from `__init__`, `load_rc_data`, `initialize_state`, and `update_model` are included in a concise table format, consistent with the previous water heater analysis.

---

### Summary of Settable Parameters by Class

| **Class**                  | **Settable Parameters**                                                                                          |
|----------------------------|-----------------------------------------------------------------------------------------------------------------|
| `StratifiedWaterModel`     | `water_nodes`, `water_vol_fractions`, `Tank Volume (L)`, `Mixed Delivery Temperature (C)`, `Tempering Valve Setpoint (C)`, `Setpoint Temperature (C)`, `Tank Height (m)`, `Heat Transfer Coefficient (W/m^2/K)`, `UA (W/K)`, `Initial Temperature (C)`, `Deadband Temperature (C)`, `control_signal` |
| `PhaseChangeMaterialModel` | Inherits all from `StratifiedWaterModel`: `water_nodes`, `water_vol_fractions`, `Tank Volume (L)`, `Mixed Delivery Temperature (C)`, `Tempering Valve Setpoint (C)`, `Setpoint Temperature (C)`, `Tank Height (m)`, `Heat Transfer Coefficient (W/m^2/K)`, `UA (W/K)`, `Initial Temperature (C)`, `Deadband Temperature (C)`, `control_signal` + Additional: `PCM Phase Change Temperature (C)`, `PCM Latent Heat (J/kg)`, `PCM Specific Heat Solid (J/kg/K)`, `PCM Specific Heat Liquid (J/kg/K)`, `PCM Density (kg/L)` |
| `OneNodeWaterModel`        | Inherits from `StratifiedWaterModel`: `Tank Volume (L)`, `Mixed Delivery Temperature (C)`, `Tempering Valve Setpoint (C)`, `Setpoint Temperature (C)`, `Tank Height (m)`, `Heat Transfer Coefficient (W/m^2/K)`, `UA (W/K)`, `Initial Temperature (C)`, `Deadband Temperature (C)`, `control_signal` (Note: `water_nodes` fixed to 1, `water_vol_fractions` effectively ignored) |
| `TwoNodeWaterModel`        | Inherits from `StratifiedWaterModel`: `Tank Volume (L)`, `Mixed Delivery Temperature (C)`, `Tempering Valve Setpoint (C)`, `Setpoint Temperature (C)`, `Tank Height (m)`, `Heat Transfer Coefficient (W/m^2/K)`, `UA (W/K)`, `Initial Temperature (C)`, `Deadband Temperature (C)`, `control_signal` (Note: `water_nodes` fixed to 2, `water_vol_fractions` fixed to `[1/3, 2/3]`) |
| `IdealWaterModel`          | Inherits from `OneNodeWaterModel`: `Mixed Delivery Temperature (C)`, `Tempering Valve Setpoint (C)`, `Setpoint Temperature (C)`, `Initial Temperature (C)`, `control_signal` (Note: `Tank Volume (L)` fixed to 1000 L internally, `Tank Height (m)`, `Heat Transfer Coefficient (W/m^2/K)`, `UA (W/K)` not used due to idealized RC parameters) |

---

### Explanation of Table Columns

- **`StratifiedWaterModel`**: The base class allows full flexibility in configuring the number of nodes, volume fractions, and thermal properties, with defaults for temperatures and optional RC parameters.
- **`PhaseChangeMaterialModel`**: Extends `StratifiedWaterModel` with PCM-specific parameters, maintaining all inherited settable options while adding properties critical for phase change modeling.
- **`OneNodeWaterModel`**: Simplifies `StratifiedWaterModel` by fixing `water_nodes` to 1, making `water_vol_fractions` irrelevant (though technically still accepted, it’s effectively a single fraction of 1).
- **`TwoNodeWaterModel`**: Fixes `water_nodes` to 2 and `water_vol_fractions` to `[1/3, 2/3]`, reducing flexibility but retaining other settable parameters from the parent.
- **`IdealWaterModel`**: Further restricts settable parameters by fixing `Tank Volume (L)` to 1000 L and using idealized RC values (`R_WH1_AMB` = 1e6, `C_WH1` = `volume * water_c`), limiting RC customization.

### Notes
- **Inherited Parameters**: Parameters listed under inherited classes include only those still applicable or not overridden/fixed by the subclass.
- **`control_signal`**: Included as a settable parameter for all classes since `update_model` accepts an array of heat injections, which can be dynamically controlled during runtime.
- **RC Parameters**: `Heat Transfer Coefficient (W/m^2/K)` and `UA (W/K)` are mutually exclusive options in `load_rc_data`; only one needs to be provided.
- **Omitted Methods**: Unlike the water heater classes, these models don’t have an `update_external_control` method, so settable parameters are limited to initialization and model updates via `control_signal`.

Let me know if you'd like further clarification, additional details, or adjustments to the summary!