import os
from ochre import HeatPumpWaterHeater, ElectricResistanceWaterHeater, \
    GasWaterHeater, TanklessWaterHeater, GasTanklessWaterHeater, WaterHeater, \
    ESEHeatPumpWaterHeater, ESEElectricResistanceWaterHeater, LPHeatPumpWaterHeater

g2l = 3.78541

# Configuration parameters for each water heater type
configurations = {
    'ESELPHPWH': {
        'class': ESEHeatPumpWaterHeater,
        'params': {
            'Low Power HPWH': True,
            #'PCM': True, # PCM Water Tank
            #'water_nodes': 12,  # for pcm behavior
            'Tank Volume (L)': 56 * g2l,  # equivalent water tank volume
            # 79 gallons available at 104 deg F
            # * 50 deg temperature rise
            # Capacity (W)': 79 * g2l * (50 / 1.8) * 4184,  # Liters * Temp Rise * kJ/kg/C * W/kJ
            'Capacity (W)': 4500,  # watts
            #'ambient_temperature': 20,  # Celsius
            'Water Heating Max Power (kW)': 0.18, # heating element
            'Setpoint Temperature (C)': 51.7,  # Celsius (125°F)
            'Tank Height (m)': 1.22,
            'UA (W/K)': 2.17,
            'HPWH Power (W)': 180,
            'HPWH COP (-)': 3.2,  # Example coefficient of performance
            "batt_cap_kwh": 5, 
            "soc_init": 0.5,
            "soc_max": 0.9,
            "soc_min": 0.1,
            "ah_cell": 100,
            "v_cell": 3.6,
            "efficiency_inverter": 0.95,
            "r_cell": 0.01,
            "initial_voltage": 50.4,
            "n_series": 14,

            "discharge_pct": 0.5,
            "save_results": True,  # if True, must specify output_path
            "output_path": os.getcwd(),
        }
    },
    'HPWH': {
        'class': HeatPumpWaterHeater,
        'params': {
            'Tank Volume (L)': 50 * g2l,  # gallons to liters
            'Capacity (W)': 4500,  # watts
            #'ambient_temperature': 20,  # Celsius
            'Water Heating Max Power (kW)': 4.5, # heating element
            'HPWH Power (W)': 4500,
            'Setpoint Temperature (C)': 51.7,  # Celsius (125°F)
            'Tank Height (m)': 1.22,
            'UA (W/K)': 2.17,
            'HPWH COP (-)': 3.2,  # Example coefficient of performance
            
            "save_results": True,  # if True, must specify output_path
            "output_path": os.getcwd(),
        }
    },
    'ERWH': {
        'class': ElectricResistanceWaterHeater,
        'params': {
            'water_nodes': 2,

            'Tank Volume (L)': 40 * g2l, # 55 gal normal
            'Capacity (W)': 4500, # W
            #'ambient_temperature': 20,
            'Water Heating Setpoint (C)': 51.7,
            'Water Heating Max Power (kW)': 5.5, # heating element
            'Setpoint Temperature (C)': 51.7,
            'Tank Height (m)': 1.22,
            'Efficiency (-)': 0.92,
            'UA (W/K)': 2.17,
            "save_results": True,  # if True, must specify output_path
            "output_path": os.getcwd(),
            "verbosity": 3,
        }
    },
    'Gas': {
        'class': GasWaterHeater,
        'params': {
            'Tank Volume (L)': 50 * g2l,
            'rated_power': 50000,  # BTU/hr
            #'ambient_temperature': 20,
            'Water Heating Max Power (kW)': 5.5, # heating element
            'Setpoint Temperature (C)': 51.7,
            'Tank Height (m)': 1.22,
            'Efficiency (-)': 0.88,
            'UA (W/K)': 2.17,
            'Energy Factor (-)': 0.8,
            "save_results": True,  # if True, must specify output_path
            "output_path": os.getcwd(),
        }
    },
    'ElectricTankless': {
        'class': TanklessWaterHeater,
        'params': {
            'rated_power': 7920, # W
            #'ambient_temperature': 20,
            'Water Heating Max Power (kW)': 7.92, # heating element
            'Setpoint Temperature (C)': 51.7,
            'Tank Height (m)': 0,
            'Efficiency (-)': 0.99,
            'UA (W/K)': 2.17,
            'Tank Volume (L)': 0,
            "save_results": True,  # if True, must specify output_path
            "output_path": os.getcwd(),
        }
    },
    'GasTankless': {
        'class': GasTanklessWaterHeater,
        'params': {
            'Tank Volume (L)': 0,
            'rated_power': 157000,  # BTU/hr
            #'ambient_temperature': 20,
            'Water Heating Max Power (kW)': 199900 / 3.412, # heating element
            'Setpoint Temperature (C)': 51.7,
            'Efficiency (-)': 0.96,
            'UA (W/K)': 2.17,
            'Parasitic Power (W)': 100,
            "save_results": True,  # if True, must specify output_path
            "output_path": os.getcwd(),
        }
    },
    'LowPowerHPWH': {
        'class': LPHeatPumpWaterHeater,
        'params': {
            'Low Power HPWH': True,
            'Tank Volume (L)': 50 * g2l,  # gallons to liters
            'Capacity (W)': 4500,  # watts
            'Water Heating Max Power (kW)': 0.9, # heating element
            'HPWH Power (W)': 1800,
            
            #'ambient_temperature': 20,  # Celsius
            'Setpoint Temperature (C)': 51.7,  # Celsius (125°F)
            'Tank Height (m)': 1.22,
            'UA (W/K)': 2.17,
            'HPWH COP (-)': 3.2,  # Example coefficient of performance
            "save_results": True,  # if True, must specify output_path
            "output_path": os.getcwd(),
        }
    },
    # 'ESELowPowerHPWH': {
    #    'class': ESEHeatPumpWaterHeater,
    #    'params': {
    #        'PCM': True,
    #        'Low Power HPWH': True,
    #        'Tank Volume (L)': 50 * g2l,  # gallons to liters
    #        'Capacity (W)': 4500,  # watts
    #        #'ambient_temperature': 20,  # Celsius
    #        'Setpoint Temperature (C)': 51.7,  # Celsius (125°F)
    #        'Tank Height (m)': 1.22,
    #        'UA (W/K)': 2.17,
    #        'HPWH COP (-)': 3.2,  # Example coefficient of performance
    #        "capacity_kwh": 10,
    #        "soc_init": 0.5,
    #        "soc_max": 0.9,
    #        "soc_min": 0.1,
    #        "ah_cell": 100,
    #        "v_cell": 3.6,
    #        "efficiency_inverter": 0.95,
    #        "r_cell": 0.01,
    #       "initial_voltage": 50.4,
    #        "n_series": 14,
    # 
    #        "discharge_pct": 0.5,
    #        "save_results": True,  # if True, must specify output_path
    #        "output_path": os.getcwd(),
    #    }
    #},

}