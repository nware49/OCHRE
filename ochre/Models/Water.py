import numpy as np

from ochre.Models import RCModel, ModelException
from ochre.utils import convert

# Water Constants
water_density = 1000  # kg/m^3
water_density_liters = 1  # kg/L
water_cp = 4.183  # kJ/kg-K
water_conductivity = 0.6406  # W/m-K
water_c = water_cp * water_density_liters * 1000  # heat capacity with useful units: J/K-L
gal2lit = 3.78541


class StratifiedWaterModel(RCModel):
    """
    Stratified Water Tank RC Thermal Model

    - Partitions a water tank into n nodes (12 by default).
    - Nodes can have different volumes, but are equal volume by default.
    - Node 1 is at the top of the tank (at outlet).
    - State names are [T_WH1, T_WH2, ...], length n
    - Input names are [T_AMB, H_WH1, H_WH2, ...], length n+1
    - The model can accept 2 additional inputs for water draw:
      - draw: volume of water to deliver
      - draw_tempered: volume to deliver at setpoint temperature.
      If tank temperature is higher than setpoint, the model assumes mixing with water mains.
    - The model considers the following effects on temperature at each time step:
      - Internal (node-to-node) conduction
      - External (node-to-ambient) conduction
      - Heat injections due to water heater
      - Heat injections due to water draw (calculated before the state-space update)
      - Heat transfer due to inversion mixing (assumes fast mixing, calculated after the state-space update)
    - At each time step, the model calculates:
      - The internal states (temperatures)
      - The heat delivered to the load (relative to mains temperature)
      - The heat lost to ambient air
    """
    name = 'Water Tank'
    optional_inputs = [
        'Water Fixtures (L/min)',
        'Showers (L/min)',
        'Clothes Washer (L/min)',
        'Dishwasher (L/min)',
        'Mains Temperature (C)',
        'Zone Temperature (C)',
    ]

    def __init__(self, water_nodes=12, water_vol_fractions=None, **kwargs):
        if water_vol_fractions is None:
            self.n_nodes = water_nodes
            self.vol_fractions = np.ones(self.n_nodes) / self.n_nodes
        else:
            self.n_nodes = len(water_vol_fractions)
            self.vol_fractions = np.array(water_vol_fractions) / sum(water_vol_fractions)

        self.volume = kwargs['Tank Volume (L)']  # in L

        super().__init__(external_nodes=['AMB'], **kwargs)
        self.next_states = self.states  # for holding state info for next time step

        self.t_amb_idx = self.input_names.index('T_AMB')
        assert self.t_amb_idx == 0  # should always be first
        self.t_1_idx = self.state_names.index('T_WH1')
        self.h_1_idx = self.input_names.index('H_WH1')

        # key variables for results
        self.draw_total = 0  # in L
        self.h_delivered = 0  # heat delivered in outlet water, in W
        self.h_injections = 0  # heat from water heater, in W
        self.h_loss = 0  # conduction heat loss from tank, in W
        self.h_unmet_load = 0  # unmet load from outlet temperature, fixtures only, in W
        self.mains_temp = 0  # water mains temperature, in C
        self.outlet_temp = 0  # temperature of outlet water, in C

        # mixed temperature (i.e. target temperature) setpoint for fixtures - Sink/Shower/Bath (SSB)
        self.tempered_draw_temp = kwargs.get('Mixed Delivery Temperature (C)', convert(105, 'degF', 'degC'))
        self.hot_draw_temp = kwargs.get('Tempering Valve Setpoint (C)', convert(125, 'degF', 'degC'))
        self.setpoint_temp = kwargs.get('Setpoint Temperature (C)', convert(125, 'degF', 'degC'))
        # Removing target temperature for clothes washers
        # self.washer_draw_temp = kwargs.get('Clothes Washer Delivery Temperature (C)', convert(92.5, 'degF', 'degC'))
        self.hot_water_stored = self.volume # initialize full of hot water
        self.heating_element = kwargs.get('Water Heating Max Power (kW)', 4.5)
        self.heating = False
        self.water_heated = 0
        self.water_heating_power = 0

        # GPT Behavior implementation
        self.battery_energy = 5.0  # in kWh
        self.total_power_from_outlet = 0.0
        self.total_power_from_battery = 0.0
        self.coil_on = False
        self.water_heated = 0.0

    def load_rc_data(self, **kwargs):
        # Get properties from input file
        h = kwargs['Tank Height (m)']  # in m
        top_area = self.volume / h / 1000  # in m^2
        r = (top_area / np.pi) ** 0.5

        if 'Heat Transfer Coefficient (W/m^2/K)' in kwargs:
            u = kwargs['Heat Transfer Coefficient (W/m^2/K)']
        elif 'UA (W/K)' in kwargs:
            ua = kwargs['UA (W/K)']
            total_area = 2 * top_area + 2 * np.pi * r * h
            u = ua / total_area
        else:
            raise ModelException('Missing heat transfer coefficient (UA) for {}'.format(self.name))

        # calculate general RC parameters for whole tank
        c_water_tot = self.volume * water_c  # Heat capacity of water (J/K)
        r_int = (h / self.n_nodes) / water_conductivity / top_area  # R between nodes (K/W)
        r_side_tot = 1 / u / (2 * np.pi * r * h)  # R from side of tank (K/W)
        r_top = 1 / u / top_area  # R from top/bottom of tank (K/W)

        # Capacitance per node
        rc_params = {'C_WH' + str(i + 1): c_water_tot * frac for i, frac in enumerate(self.vol_fractions)}

        # Resistance to exterior from side, top, and bottom
        rc_params.update({'R_WH{}_AMB'.format(i + 1): r_side_tot / frac for i, frac in enumerate(self.vol_fractions)})
        rc_params['R_WH1_AMB'] = self.par(rc_params['R_WH1_AMB'], r_top)
        rc_params['R_WH{}_AMB'.format(self.n_nodes)] = self.par(rc_params['R_WH{}_AMB'.format(self.n_nodes)], r_top)

        # Resistance between nodes
        if self.n_nodes > 1:
            rc_params.update({'R_WH{}_WH{}'.format(i + 1, i + 2): r_int for i in range(self.n_nodes - 1)})

        return rc_params

    @staticmethod
    def initialize_state(state_names, input_names, A_c, B_c, **kwargs):
        t_init = kwargs.get('Initial Temperature (C)')
        if t_init is None:
            t_max = kwargs.get('Setpoint Temperature (C)', convert(125, 'degF', 'degC'))
            t_db = kwargs.get('Deadband Temperature (C)', convert(10, 'degR', 'K'))
            # temp = t_max - np.random.rand(1) * t_db

            # set initial temperature close to top of deadband
            t_init = t_max - t_db / 10

        # Return states as a dictionary
        return {name: t_init for name in state_names}

    def update_water_draw(self):
        heats_to_model = np.zeros(self.nx)
        self.mains_temp = self.current_schedule.get('Mains Temperature (C)')
        self.outlet_temp = self.states[self.t_1_idx]  # initial outlet temp, for estimating draw volume

        # Note: removing target draw temperature for clothes washers, not implemented in ResStock
        draw_tempered = self.current_schedule.get('Water Fixtures (L/min)', 0)
        draw_showers = self.current_schedule.get('Showers (L/min)', 0)
        draw_hot = (self.current_schedule.get('Clothes Washer (L/min)', 0)
                    + self.current_schedule.get('Dishwasher (L/min)', 0))
        draw_all = (self.current_schedule.get('Clothes Washer (L/min)', 0)
                    + self.current_schedule.get('Dishwasher (L/min)', 0)
                    + self.current_schedule.get('Showers (L/min)', 0)
                    + self.current_schedule.get('Water Fixtures (L/min)', 0))
        # draw_cw = self.current_schedule.get('Clothes Washer (L/min)', 0)
        # draw_hot = self.current_schedule.get('Dishwasher (L/min)', 0)
        if not (draw_tempered + draw_hot):
            # No water draw
            self.draw_total = 0
            self.h_delivered = 0
            self.h_unmet_load = 0
            return heats_to_model

        if self.mains_temp is None:
            raise ModelException('Mains temperature required when water draw exists')

        # calculate total draw volume from tempered draw volume(s)
        # for tempered draw, assume outlet temperature == T1, slightly off if the water draw is very large
        if self.tempered_draw_temp < self.setpoint_temp:
            if self.outlet_temp <= self.hot_draw_temp:
                self.draw_total = draw_hot
            else:
                vol_ratio_hot = (self.hot_draw_temp - self.mains_temp) / (self.outlet_temp - self.mains_temp)
                self.draw_total = draw_hot * vol_ratio_hot
        else:
            self.draw_total = draw_hot

        if draw_tempered:
            if self.outlet_temp <= self.tempered_draw_temp:
                self.draw_total += draw_tempered
            else:
                vol_ratio = (self.tempered_draw_temp - self.mains_temp) / (self.outlet_temp - self.mains_temp)
                self.draw_total += draw_tempered * vol_ratio
        # if draw_cw:
        #     if self.outlet_temp <= self.washer_draw_temp:
        #         self.draw_total += draw_cw
        #     else:
        #         vol_ratio = (self.washer_draw_temp - self.mains_temp) / (self.outlet_temp - self.mains_temp)
        #         self.draw_total += draw_cw * vol_ratio

        time_interval = self.time_res.total_seconds()
        current_draw = draw_all
        #print(current_draw)
        current_draw_liters = current_draw * time_interval / 60  # in liters
        self.hot_water_stored = max((self.hot_water_stored - current_draw_liters), 0)  # subtract current usage

        heat_available = self.heating_element * 1000 * 60
        global water_c
        water_heated = heat_available / (water_c * (40))
        #print("WHeated:", water_heated)

        stored_status = self.hot_water_stored / self.volume

        if self.volume != 56 * gal2lit:
            #print(stored_status)
            if stored_status <= 0.95:
                self.heating = True
                self.hot_water_stored += water_heated
                self.water_heated = water_heated
                self.water_heating_power = heat_available
                #print(water_heated)
            elif self.heating == True and stored_status >= 0.95:
                self.heating = False
                #self.hot_water_stored += water_heated
            else:
                pass
            # print(heat_available)
            #elif self.heating == True and stored_status > 0.95:
                #self.heating = False


            if stored_status < 0.05 and current_draw > water_heated:
                #self.h_unmet_load = 
                self.h_unmet_load = current_draw - water_heated

                #print("Unmet Demand")

        if self.volume == 56 * gal2lit:
            # GPT gen behavior

            HEAT_PUMP_KW = 0.9

            time_interval = self.time_res.total_seconds()  # in seconds
            current_draw = draw_all
            current_draw_liters = current_draw * time_interval / 60  # liters per timestep
            self.hot_water_stored = max((self.hot_water_stored - current_draw_liters), 0)

            # Constants
            water_c = 4186  # J/kg·°C for water
            delta_T = 40  # Temperature rise (e.g., from 10°C to 50°C)
            outlet_max_kw = 1.8  # Max outlet draw (120V × 15A)
            coil_kw = 3.0  # Coil power requirement
            coil_energy_per_s = coil_kw * 1000  # in watts (J/s)
            battery_max_kwh = 5.0

            stored_status = self.hot_water_stored / self.volume
            heat_available = self.heating_element * 1000 * 60  # default heat pump in watts-min

            # Water heated by default heat pump
            water_heated = heat_available / (water_c * delta_T)
            if stored_status <= 0.75:
                self.heating = True
                self.hot_water_stored += water_heated
                self.water_heated = water_heated
                self.water_heating_power = heat_available
            else:
                self.heating = False

            # Battery charging logic (if extra energy available)
            if self.heating and self.battery_energy < battery_max_kwh:
                extra_power_kw = max(0, self.heating_element - HEAT_PUMP_KW)
                battery_charge = extra_power_kw * (time_interval / 3600)
                self.battery_energy = min(self.battery_energy + battery_charge, battery_max_kwh)

            # Resistance coil logic
            if stored_status < 0.25:
                self.coil_on = True

            if getattr(self, 'coil_on', False):
                if stored_status < 0.50:
                    energy_needed = coil_energy_per_s * time_interval
                    outlet_energy = min(outlet_max_kw * 1000 * time_interval, energy_needed)
                    battery_energy_needed = energy_needed - outlet_energy
                    battery_energy_j = self.battery_energy * 3.6e6  # kWh to J

                    if battery_energy_needed > 0:
                        battery_used = min(battery_energy_j, battery_energy_needed)
                        self.battery_energy -= battery_used / 3.6e6
                    else:
                        battery_used = 0

                    # Total energy used for coil
                    actual_energy_used = outlet_energy + battery_used
                    water_heated_coil = actual_energy_used / (water_c * delta_T)
                    self.hot_water_stored += water_heated_coil
                    self.water_heated += water_heated_coil
                    self.water_heating_power += actual_energy_used

                    # Update tracking
                    #self.total_power_from_outlet += outlet_energy / 3.6e6
                    self.total_power_from_battery += battery_used / 3.6e6

                    if self.hot_water_stored / self.volume >= 0.50:
                        self.coil_on = False
                else:
                    self.coil_on = False

            # If still not enough water, compute unmet load
            if stored_status < 0.05 and current_draw > self.water_heated:
                self.h_unmet_load = current_draw - self.water_heated
            else:
                self.h_unmet_load = 0

            
            # Track grid draw correctly: 1.8 kW anytime heating or battery charging
            if self.heating or getattr(self, 'coil_on', False) or (self.battery_energy < battery_max_kwh):
                # Draw 1.8 kW from grid
                #print("ese")
                grid_energy_kwh = 1.8 * (time_interval / 3600)  # kW × hours
                self.total_power_from_outlet += grid_energy_kwh


            

        t_s = self.time_res.total_seconds()
        draw_liters = self.draw_total * t_s / 60  # in liters
        draw_fraction = draw_liters / self.volume  # unitless

        if self.n_nodes == 2 and draw_fraction < self.vol_fractions[1]:
            # Use empirical factor for determining water flow by node
            flow_fraction = 0.95  # Totally empirical factor based on detailed lab validation
            if draw_fraction > self.vol_fractions[0]:
                # outlet temp is volume-weighted average of lower and upper temps
                self.outlet_temp = (self.states[0] * self.vol_fractions[0] +
                                    self.states[1] * (draw_fraction - self.vol_fractions[0])) / draw_fraction
            q_delivered = draw_liters * water_c * (self.outlet_temp - self.mains_temp)  # in J

            # q_to_mains_upper = self.state_capacitances[0] * (self.x[0] - self.mains_temp)
            q_to_mains_lower = self.capacitances[1] * (self.states[1] - self.mains_temp)
            if q_delivered * flow_fraction > q_to_mains_lower:
                # If you'd fully cool the bottom node to mains, set bottom node to mains and cool top node
                q_nodes = np.array([q_to_mains_lower - q_delivered, -q_to_mains_lower])
            else:
                q_nodes = np.array([-q_delivered * (1 - flow_fraction), -q_delivered * flow_fraction])

        else:
            if draw_fraction < min(self.vol_fractions):
                # water draw is smaller than all node volumes
                q_delivered = draw_liters * water_c * (self.outlet_temp - self.mains_temp)  # in J
                # all volume transfers are from the node directly below
                q_nodes = draw_liters * water_c * np.diff(self.states, append=self.mains_temp)  # in J
            else:
                # calculate volume transfers to/from each node, including q_delivered
                vols_pre = np.append(self.vol_fractions, draw_fraction).cumsum()
                vols_post = np.insert(self.vol_fractions, 0, draw_fraction).cumsum()
                temps = np.append(self.states, self.mains_temp)

                # update outlet temp as a weighted average of temps, by volume
                vols_delivered = np.diff(vols_pre.clip(max=draw_fraction), prepend=0)
                self.outlet_temp = np.dot(temps, vols_delivered) / draw_fraction
                q_delivered = draw_liters * water_c * (self.outlet_temp - self.mains_temp)  # in J

                # calculate heat in/out of each node (in J)
                q_nodes = []
                for i in range(self.n_nodes):
                    t_start = temps[i]
                    vols_delivered = np.diff(vols_pre.clip(min=vols_post[i], max=vols_post[i + 1]),
                                             prepend=vols_post[i])
                    t_end = np.dot(temps, vols_delivered) / self.vol_fractions[i]
                    q_nodes.append((t_end - t_start) * self.capacitances[i])
                q_nodes = np.array(q_nodes)

        # convert heat transfer from J to W
        self.h_delivered = q_delivered / t_s
        heats_to_model += q_nodes / t_s

        # calculate unmet loads, showers only, in W
        # Why only showers? Changing to full demand profile
        #self.h_unmet_load = max(
        #    draw_showers / 60 * water_c * (self.tempered_draw_temp - self.outlet_temp), 0
        #)  # in W

        
        
        #self.draw_total = self.current_schedule.get('Water Heating (L/min)', 0)

        return heats_to_model

    def update_inputs(self, schedule_inputs=None):
        # Note: self.inputs_init are not updated here, only self.current_schedule
        super().update_inputs(schedule_inputs)

        # get zone temperature from schedule
        t_zone = self.current_schedule['Zone Temperature (C)']

        # update heat injections from water draw
        # FUTURE: revise CW and DW when event based schedules are added
        heats_to_model = self.update_water_draw()

        # update water tank model
        self.inputs_init = np.concatenate(([t_zone], heats_to_model))

    def run_inversion_mixing_rule(self):
        # Inversion Mixing Rule
        # See https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v9.1.0/EngineeringReference.pdf
        #     p. 1528
        # Starting from the top, check for mixing at each node

        init_states = self.next_states.copy()
        for node_idx in range(self.n_nodes - 1):
            current_temp = self.next_states[node_idx]

            # new temp is the max of any possible mixings
            heats = self.next_states * self.vol_fractions  # note: excluding c_p and volume factors
            heat_sums = heats[node_idx:].cumsum()
            vol_sums = self.vol_fractions[node_idx:].cumsum()
            new_temp = (heat_sums / vol_sums).max()

            # Allow inversion mixing if a significant difference in temperature exists
            if new_temp > current_temp + 0.001:  # small computational errors are possible
                # print('Inversion mixing occuring at node {}. Temperature raises from {} to {}'.format(
                #     node + 1, self.x[node], new_temp))

                # calculate heat transfer, update temperatures of current node and node below
                q = (new_temp - current_temp) * self.vol_fractions[node_idx]
                self.next_states[node_idx] = new_temp
                self.next_states[node_idx + 1] -= q / self.vol_fractions[node_idx + 1]

                if not any(np.diff(self.next_states) > 0.1):
                    # no more inversions
                    return

            elif new_temp < current_temp - 0.001:  # small computational errors are possible:
                msg = 'Error in inversion mixing algorithm. ' \
                      'New temperature ({}) less than previous ({}) at node {}.'
                raise ModelException(msg.format(new_temp, self.next_states[node_idx], node_idx + 1))

        # check final heat to ensure no losses from mixing
        heat_check = np.dot(self.next_states - init_states, self.capacitances)  # in J
        if not abs(heat_check) < 1:
            raise ModelException(
                'Large error ({}) in water heater inversion mixing algorithm.'
                'Final state temperatures are: {}'.format(heat_check, self.next_states))

    def update_model(self, control_signal=None):
        if control_signal is not None:
            # control signal must be heat injections from water heater, by node
            assert isinstance(control_signal, np.ndarray) and len(control_signal) == self.nx
            self.h_injections = sum(control_signal)
            control_signal = self.inputs_init + np.insert(control_signal, 0, 0)  # adds heat injections in inputs_init
        else:
            self.h_injections = 0

        super().update_model(control_signal)

        q_change = (self.next_states - self.states).dot(self.capacitances)  # in J
        h_change = q_change / self.time_res.total_seconds()

        # calculate heat loss, in W
        self.h_loss = self.h_injections - h_change - self.h_delivered
        #if abs(self.h_loss) > 1000:
            #raise ModelException('Error in calculating heat loss for {} model'.format(self.name))

        # If any temperatures are inverted, run inversion mixing algorithm
        delta_t = 0.1 if self.high_res else 0.01
        if any(np.diff(self.next_states) > delta_t):
            self.run_inversion_mixing_rule()

    def update_results(self):
        current_results = super().update_results()

        # check that states are within reasonable range
        # Note: default max temp on water heater model is 60C (140F). Temps may exceed that slightly
        if max(self.states) > 62 or min(self.states) < self.mains_temp - 10:
            if max(self.states) > 65 or min(self.states) < self.mains_temp - 15:
                raise ModelException(f'Water temperatures are outside acceptable range: {self.states}')
            else:
                self.warn(f'Water temperatures are outside acceptable range: {self.states}')

        return current_results

    def generate_results(self):
        # Note: most results are included in Dwelling/WH. Only inputs and states are saved to self.results
        results = super().generate_results()

        if self.verbosity >= 3:
            results['Hot Water Delivered (L/min)'] = self.draw_total
            results['Hot Water Outlet Temperature (C)'] = self.outlet_temp
            results['Hot Water Delivered (W)'] = self.water_heating_power
            results['Hot Water Unmet Demand (kW)'] = self.h_unmet_load / 1000
            results['Hot Water Demand (L/min)'] = self.draw_total
            results['Water Heated (L/min)'] = self.water_heated
            results['Water Stored (L)'] = self.hot_water_stored
            results['Power Consumed (kW)'] = self.total_power_from_outlet
            results['Hot Water Heat Loss (W)'] = self.total_power_from_outlet
        if self.verbosity >= 6:
            results['Hot Water Heat Injected (W)'] = self.water_heated
            #results['Hot Water Heat Loss (W)'] = self.h_loss
            results['Hot Water Average Temperature (C)'] = self.states.dot(self.vol_fractions)
            results['Hot Water Maximum Temperature (C)'] = self.states.max()
            results['Hot Water Minimum Temperature (C)'] = self.states.min()
            results['Hot Water Mains Temperature (C)'] = self.mains_temp
        return results


class PhaseChangeMaterialModel(StratifiedWaterModel):
    """
    Phase Change Material (PCM) Tank RC Thermal Model

    Extends StratifiedWaterModel to model a water tank with PCM, accounting for latent heat storage
    during phase transitions. The model partitions the tank into n nodes (12 by default) and tracks
    both sensible and latent heat storage in each node.

    - Nodes can have different volumes, but are equal volume by default.
    - Node 1 is at the top of the tank (at outlet).
    - State names include temperatures and PCM phase fractions: [T_WH1, T_WH2, ..., PCM_Frac_WH1, PCM_Frac_WH2, ...]
    - Input names are [T_AMB, H_WH1, H_WH2, ...], length n+1
    - Additional inputs for PCM properties and water draw are supported.
    - The model considers:
      - Sensible heat storage (based on specific heat capacity)
      - Latent heat storage (based on phase change fraction and latent heat of fusion)
      - Internal (node-to-node) conduction
      - External (node-to-ambient) conduction
      - Heat injections from water heater
      - Heat injections/removals from water draw
      - Inversion mixing, adjusted for PCM phase states

    Optional inputs:
    - 'Water Fixtures (L/min)', 'Showers (L/min)', 'Clothes Washer (L/min)', 'Dishwasher (L/min)'
    - 'Mains Temperature (C)', 'Zone Temperature (C)'
    - 'PCM Phase Change Temperature (C)', 'PCM Latent Heat (J/kg)', 'PCM Specific Heat Solid (J/kg/K)', 
      'PCM Specific Heat Liquid (J/kg/K)', 'PCM Density (kg/L)'
    """
    name = 'PCM Water Tank'


    optional_inputs = [
        'Water Fixtures (L/min)',
        'Showers (L/min)',
        'Clothes Washer (L/min)',
        'Dishwasher (L/min)',
        'Mains Temperature (C)',
        'Zone Temperature (C)',
    ]

    def update_water_draw(self):
        heats_to_model = np.zeros(self.nx)
        self.mains_temp = self.current_schedule.get('Mains Temperature (C)')
        self.outlet_temp = self.states[self.t_1_idx]  # initial outlet temp, for estimating draw volume

        # Note: removing target draw temperature for clothes washers, not implemented in ResStock
        draw_tempered = self.current_schedule.get('Water Fixtures (L/min)', 0)
        draw_showers = self.current_schedule.get('Showers (L/min)', 0)
        draw_hot = (self.current_schedule.get('Clothes Washer (L/min)', 0)
                    + self.current_schedule.get('Dishwasher (L/min)', 0))
        draw_all = (self.current_schedule.get('Clothes Washer (L/min)', 0)
                    + self.current_schedule.get('Dishwasher (L/min)', 0)
                    + self.current_schedule.get('Showers (L/min)', 0)
                    + self.current_schedule.get('Water Fixtures (L/min)', 0))
        # draw_cw = self.current_schedule.get('Clothes Washer (L/min)', 0)
        # draw_hot = self.current_schedule.get('Dishwasher (L/min)', 0)
        if not (draw_tempered + draw_hot):
            # No water draw
            self.draw_total = 0
            self.h_delivered = 0
            self.h_unmet_load = 0
            return heats_to_model

        if self.mains_temp is None:
            raise ModelException('Mains temperature required when water draw exists')

        # calculate total draw volume from tempered draw volume(s)
        # for tempered draw, assume outlet temperature == T1, slightly off if the water draw is very large
        if self.tempered_draw_temp < self.setpoint_temp:
            if self.outlet_temp <= self.hot_draw_temp:
                self.draw_total = draw_hot
            else:
                vol_ratio_hot = (self.hot_draw_temp - self.mains_temp) / (self.outlet_temp - self.mains_temp)
                self.draw_total = draw_hot * vol_ratio_hot
        else:
            self.draw_total = draw_hot

        if draw_tempered:
            if self.outlet_temp <= self.tempered_draw_temp:
                self.draw_total += draw_tempered
            else:
                vol_ratio = (self.tempered_draw_temp - self.mains_temp) / (self.outlet_temp - self.mains_temp)
                self.draw_total += draw_tempered * vol_ratio
        # if draw_cw:
        #     if self.outlet_temp <= self.washer_draw_temp:
        #         self.draw_total += draw_cw
        #     else:
        #         vol_ratio = (self.washer_draw_temp - self.mains_temp) / (self.outlet_temp - self.mains_temp)
        #         self.draw_total += draw_cw * vol_ratio

        time_interval = self.time_res.total_seconds()
        current_draw = draw_all
        #print(current_draw)
        current_draw_liters = current_draw * time_interval / 60  # in liters
        self.hot_water_stored = max((self.hot_water_stored - current_draw_liters), 0)  # subtract current usage

        heat_available = self.heating_element * 1000 * 60
        water_heated = heat_available / (water_c * (40)) # 40 is temperature rise in C
        #print("WHeated:", water_heated)

        stored_status = self.hot_water_stored / self.volume
        #print(stored_status)
        if stored_status <= 0.75:
            self.heating = True
            self.hot_water_stored += water_heated
            self.water_heated = water_heated
            self.water_heating_power = heat_available
            #print(water_heated)
        elif self.heating == True and stored_status >= 0.95:
            self.heating = False
            #self.hot_water_stored += water_heated
        elif self.heating == True:
            self.hot_water_stored += water_heated
            self.water_heated = water_heated
            self.water_heating_power = heat_available
        else:
            pass
        # print(heat_available)
        #elif self.heating == True and stored_status > 0.95:
            #self.heating = False


        if stored_status < 0.05 and current_draw > water_heated:
            #self.h_unmet_load = 
            self.h_unmet_load = current_draw - water_heated

            



            # print("Unmet Demand")
            

        t_s = self.time_res.total_seconds()
        draw_liters = self.draw_total * t_s / 60  # in liters
        draw_fraction = draw_liters / self.volume  # unitless

        if self.n_nodes == 2 and draw_fraction < self.vol_fractions[1]:
            # Use empirical factor for determining water flow by node
            flow_fraction = 0.95  # Totally empirical factor based on detailed lab validation
            if draw_fraction > self.vol_fractions[0]:
                # outlet temp is volume-weighted average of lower and upper temps
                self.outlet_temp = (self.states[0] * self.vol_fractions[0] +
                                    self.states[1] * (draw_fraction - self.vol_fractions[0])) / draw_fraction
            q_delivered = draw_liters * water_c * (self.outlet_temp - self.mains_temp)  # in J

            # q_to_mains_upper = self.state_capacitances[0] * (self.x[0] - self.mains_temp)
            q_to_mains_lower = self.capacitances[1] * (self.states[1] - self.mains_temp)
            if q_delivered * flow_fraction > q_to_mains_lower:
                # If you'd fully cool the bottom node to mains, set bottom node to mains and cool top node
                q_nodes = np.array([q_to_mains_lower - q_delivered, -q_to_mains_lower])
            else:
                q_nodes = np.array([-q_delivered * (1 - flow_fraction), -q_delivered * flow_fraction])

        else:
            if draw_fraction < min(self.vol_fractions):
                # water draw is smaller than all node volumes
                q_delivered = draw_liters * water_c * (self.outlet_temp - self.mains_temp)  # in J
                # all volume transfers are from the node directly below
                q_nodes = draw_liters * water_c * np.diff(self.states, append=self.mains_temp)  # in J
            else:
                # calculate volume transfers to/from each node, including q_delivered
                vols_pre = np.append(self.vol_fractions, draw_fraction).cumsum()
                vols_post = np.insert(self.vol_fractions, 0, draw_fraction).cumsum()
                temps = np.append(self.states, self.mains_temp)

                # update outlet temp as a weighted average of temps, by volume
                vols_delivered = np.diff(vols_pre.clip(max=draw_fraction), prepend=0)
                self.outlet_temp = np.dot(temps, vols_delivered) / draw_fraction
                q_delivered = draw_liters * water_c * (self.outlet_temp - self.mains_temp)  # in J

                # calculate heat in/out of each node (in J)
                q_nodes = []
                for i in range(self.n_nodes):
                    t_start = temps[i]
                    vols_delivered = np.diff(vols_pre.clip(min=vols_post[i], max=vols_post[i + 1]),
                                             prepend=vols_post[i])
                    t_end = np.dot(temps, vols_delivered) / self.vol_fractions[i]
                    q_nodes.append((t_end - t_start) * self.capacitances[i])
                q_nodes = np.array(q_nodes)

        # convert heat transfer from J to W
        self.h_delivered = q_delivered / t_s
        heats_to_model += q_nodes / t_s

        # calculate unmet loads, showers only, in W
        # Why only showers? Changing to full demand profile
        #self.h_unmet_load = max(
        #    draw_showers / 60 * water_c * (self.tempered_draw_temp - self.outlet_temp), 0
        #)  # in W

        
        
        #self.draw_total = self.current_schedule.get('Water Heating (L/min)', 0)

        return heats_to_model

    '''
    def __init__(self, water_nodes=12, water_vol_fractions=None, **kwargs):
        # Initialize PCM-specific parameters
        self.pcm_phase_change_temp = kwargs.get('PCM Phase Change Temperature (C)', 58.0)  # Default phase change temp (e.g., 58°C for common PCMs)
        self.pcm_latent_heat = kwargs.get('PCM Latent Heat (J/kg)', 200000)  # Latent heat of fusion (J/kg), e.g., for paraffin-based PCM
        self.pcm_specific_heat_solid = kwargs.get('PCM Specific Heat Solid (J/kg/K)', 2000)  # J/kg/K for solid phase
        self.pcm_specific_heat_liquid = kwargs.get('PCM Specific Heat Liquid (J/kg/K)', 2400)  # J/kg/K for liquid phase
        self.pcm_density = kwargs.get('PCM Density (kg/L)', 0.88)  # Density of PCM (kg/L), e.g., for paraffin

        # Calculate total PCM mass per node based on volume and density
        if water_vol_fractions is None:
            self.n_nodes = water_nodes
            self.vol_fractions = np.ones(self.n_nodes) / self.n_nodes
        else:
            self.n_nodes = len(water_vol_fractions)
            self.vol_fractions = np.array(water_vol_fractions) / sum(water_vol_fractions)

        self.volume = kwargs['Tank Volume (L)']  # in L
        self.pcm_mass_per_node = self.vol_fractions * self.volume * self.pcm_density  # kg per node

        # Initialize state variables: temperature and PCM phase fraction for each node
        super().__init__(water_nodes=water_nodes, water_vol_fractions=water_vol_fractions, **kwargs)

        # Extend state names to include PCM phase fractions
        self.state_names = [f'T_WH{i+1}' for i in range(self.n_nodes)] + [f'PCM_Frac_WH{i+1}' for i in range(self.n_nodes)]
        self.states = np.zeros(2 * self.n_nodes)  # [T_WH1, T_WH2, ..., PCM_Frac_WH1, PCM_Frac_WH2, ...]
        self.next_states = self.states.copy()

        # Update indices for temperature and PCM fraction states
        self.t_1_idx = self.state_names.index('T_WH1')
        self.pcm_frac_1_idx = self.state_names.index('PCM_Frac_WH1')

        # Key variables for results, extended for PCM
        self.pcm_latent_energy_stored = 0  # Total latent energy stored in the tank (J)
        self.pcm_sensible_energy_stored = 0  # Total sensible energy stored (J)

    def load_rc_data(self, **kwargs):
        # Override to account for PCM thermal properties
        rc_params = super().load_rc_data(**kwargs)

        # Adjust thermal conductivity and heat capacity for PCM
        # Assume PCM has different thermal conductivity; for simplicity, use a factor (e.g., 0.5x water conductivity)
        pcm_thermal_conductivity = water_conductivity * 0.5  # Adjust based on PCM material
        h = kwargs['Tank Height (m)']  # in m
        top_area = self.volume / h / 1000  # in m^2

        r_int = (h / self.n_nodes) / pcm_thermal_conductivity / top_area  # R between nodes (K/W) for PCM
        if self.n_nodes > 1:
            rc_params.update({'R_WH{}_WH{}'.format(i + 1, i + 2): r_int for i in range(self.n_nodes - 1)})

        # Capacitance per node includes both sensible and latent heat capacity
        # Use average specific heat for initial calculation (will be adjusted dynamically)
        pcm_specific_heat_avg = (self.pcm_specific_heat_solid + self.pcm_specific_heat_liquid) / 2
        c_pcm_tot = sum(self.pcm_mass_per_node * pcm_specific_heat_avg)  # Total heat capacity (J/K)
        rc_params.update({'C_WH' + str(i + 1): c_pcm_tot * frac for i, frac in enumerate(self.vol_fractions)})

        return rc_params

    def initialize_state(self, state_names, input_names, A_c, B_c, **kwargs):
        # Initialize temperatures and PCM phase fractions
        t_init = kwargs.get('Initial Temperature (C)')
        if t_init is None:
            t_max = kwargs.get('Setpoint Temperature (C)', convert(125, 'degF', 'degC'))
            t_db = kwargs.get('Deadband Temperature (C)', convert(10, 'degR', 'K'))
            t_init = t_max - t_db / 10  # Start near top of deadband

        # Initialize PCM fraction (0 = fully solid, 1 = fully liquid)
        pcm_frac_init = 0.0 if t_init < self.pcm_phase_change_temp else 1.0  # Assume fully solid or liquid initially

        # Return states as a dictionary
        states = {}
        for i in range(self.n_nodes):
            states[f'T_WH{i+1}'] = t_init
            states[f'PCM_Frac_WH{i+1}'] = pcm_frac_init
        return states


    def update_heat_capacity(self, node_idx):
        """Calculate effective heat capacity for a node, accounting for PCM phase and latent heat."""
        temp = self.states[node_idx]
        pcm_frac = self.states[node_idx + self.n_nodes]  # PCM fraction for this node

        # Determine specific heat based on temperature relative to phase change
        if temp < self.pcm_phase_change_temp - 0.5:  # Fully solid
            specific_heat = self.pcm_specific_heat_solid
            pcm_frac = 0.0
        elif temp > self.pcm_phase_change_temp + 0.5:  # Fully liquid
            specific_heat = self.pcm_specific_heat_liquid
            pcm_frac = 1.0
        else:  # In phase change region, use weighted average and latent heat
            # Linear interpolation for specific heat in transition region
            specific_heat = (self.pcm_specific_heat_solid + self.pcm_specific_heat_liquid) / 2
            # Latent heat contribution (dQ = m * L * d(frac))
            latent_capacity = self.pcm_mass_per_node[node_idx] * self.pcm_latent_heat  # J per unit fraction

        # Total heat capacity for the node (J/K)
        sensible_capacity = self.pcm_mass_per_node[node_idx] * specific_heat
        total_capacity = sensible_capacity + latent_capacity if abs(temp - self.pcm_phase_change_temp) < 0.5 else sensible_capacity

        return total_capacity, pcm_frac

    def update_model(self, control_signal=None):
        # Update base model but adjust for PCM heat capacity and phase changes
        if control_signal is not None:
            assert isinstance(control_signal, np.ndarray) and len(control_signal) == self.n_nodes
            self.h_injections = sum(control_signal)
            control_signal = np.insert(control_signal, 0, 0)  # Add to inputs_init
        else:
            self.h_injections = 0

        # Update temperatures and PCM fractions
        super().update_model(control_signal)

        # Adjust next_states for PCM phase changes
        for node_idx in range(self.n_nodes):
            t_idx = self.t_1_idx + node_idx
            pcm_idx = self.pcm_frac_1_idx + node_idx

            # Calculate effective heat capacity and update PCM fraction
            capacity, new_pcm_frac = self.update_heat_capacity(node_idx)
            temp_change = (self.next_states[t_idx] - self.states[t_idx])
            energy_change = temp_change * capacity  # J

            # Update PCM fraction based on energy change (simplified linear model)
            if abs(self.next_states[t_idx] - self.pcm_phase_change_temp) < 0.5:
                # In phase change region, adjust PCM fraction
                latent_energy_available = self.pcm_mass_per_node[node_idx] * self.pcm_latent_heat * (1 - self.states[pcm_idx])  # J remaining
                if energy_change > 0 and latent_energy_available > 0:  # Melting
                    delta_frac = min(energy_change / (self.pcm_mass_per_node[node_idx] * self.pcm_latent_heat), 1 - self.states[pcm_idx])
                    self.next_states[pcm_idx] += delta_frac
                    # Adjust temperature to account for latent heat (keep temp constant during phase change)
                    self.next_states[t_idx] = self.pcm_phase_change_temp
                elif energy_change < 0 and self.states[pcm_idx] > 0:  # Freezing
                    delta_frac = max(energy_change / (self.pcm_mass_per_node[node_idx] * self.pcm_latent_heat), -self.states[pcm_idx])
                    self.next_states[pcm_idx] += delta_frac
                    self.next_states[t_idx] = self.pcm_phase_change_temp

            # Ensure PCM fraction stays within [0, 1]
            self.next_states[pcm_idx] = np.clip(self.next_states[pcm_idx], 0, 1)

        # Recalculate heat loss and energy storage
        q_change = np.dot(self.next_states[:self.n_nodes] - self.states[:self.n_nodes], 
                         [self.update_heat_capacity(i)[0] for i in range(self.n_nodes)])  # in J
        h_change = q_change / self.time_res.total_seconds()

        self.h_loss = self.h_injections - h_change - self.h_delivered
        if abs(self.h_loss) > 1000:
            raise ModelException('Error in calculating heat loss for {} model'.format(self.name))

        # Adjust inversion mixing for PCM
        self.run_pcm_inversion_mixing_rule()

    def run_pcm_inversion_mixing_rule(self):
        """Modified inversion mixing rule for PCM, conserving both sensible and latent energy."""
        init_states = self.next_states.copy()
        for node_idx in range(self.n_nodes - 1):
            current_temp = self.next_states[node_idx]
            current_pcm_frac = self.next_states[node_idx + self.n_nodes]

            # Calculate effective temperatures considering PCM phase
            heats = self.next_states[:self.n_nodes] * [self.update_heat_capacity(i)[0] for i in range(self.n_nodes)]
            latent_heats = self.next_states[self.n_nodes:] * self.pcm_mass_per_node * self.pcm_latent_heat
            total_heats = heats + latent_heats
            vol_sums = self.vol_fractions[node_idx:].cumsum()
            new_temp = (total_heats[node_idx:].cumsum() / vol_sums).max() / self.update_heat_capacity(node_idx)[0]

            if new_temp > current_temp + 0.001:
                # Mixing occurs; redistribute energy while conserving total energy
                q_total = np.dot(self.next_states[:self.n_nodes] - init_states[:self.n_nodes], 
                                [self.update_heat_capacity(i)[0] for i in range(self.n_nodes)]) + \
                         np.dot(self.next_states[self.n_nodes:] - init_states[self.n_nodes:], 
                                self.pcm_mass_per_node * self.pcm_latent_heat)
                
                # Update temperatures and PCM fractions for mixing (simplified)
                self.next_states[node_idx] = new_temp
                self.next_states[node_idx + self.n_nodes] = current_pcm_frac  # Assume fraction conserved for simplicity
                self.next_states[node_idx + 1] -= (new_temp - current_temp) * self.vol_fractions[node_idx] / self.vol_fractions[node_idx + 1]
                self.next_states[node_idx + 1 + self.n_nodes] = self.next_states[node_idx + self.n_nodes]  # Assume same fraction

        # Check energy conservation
        heat_check = np.dot(self.next_states[:self.n_nodes] - init_states[:self.n_nodes], 
                           [self.update_heat_capacity(i)[0] for i in range(self.n_nodes)]) + \
                    np.dot(self.next_states[self.n_nodes:] - init_states[self.n_nodes:], 
                           self.pcm_mass_per_node * self.pcm_latent_heat)
        if not abs(heat_check) < 1:
            raise ModelException(
                'Large error in PCM water heater inversion mixing algorithm. Final states: {}'.format(self.next_states))
        
    '''

    
    
    '''

    def _calculate_outlet_temp(self, draw_fraction):
        """Calculate outlet temperature and PCM fraction considering PCM properties."""
        temps = self.states[:self.n_nodes]
        pcm_fracs = self.states[self.n_nodes:]
        if draw_fraction < min(self.vol_fractions):
            return temps[0], pcm_fracs[0]
        else:
            vols_delivered = np.diff(np.append(self.vol_fractions, draw_fraction).cumsum().clip(max=draw_fraction), prepend=0)
            temp_out = np.dot(temps, vols_delivered) / draw_fraction
            pcm_frac_out = np.dot(pcm_fracs, vols_delivered) / draw_fraction
            return temp_out, pcm_frac_out

    '''

    def generate_results(self):
        results = super().generate_results()

        if self.verbosity >= 3:
            results['PCM Latent Energy Stored (J)'] = self.pcm_latent_energy_stored
            results['PCM Sensible Energy Stored (J)'] = self.pcm_sensible_energy_stored
            results['PCM Average Phase Fraction (-)'] = self.states[self.n_nodes:].dot(self.vol_fractions)
            results['Hot Water Delivered (L/min)'] = self.draw_total
            results['Hot Water Outlet Temperature (C)'] = self.outlet_temp
            results['Hot Water Delivered (W)'] = self.h_delivered
            results['Hot Water Unmet Demand (kW)'] = self.h_unmet_load / 1000
        if self.verbosity >= 6:
            for i in range(self.n_nodes):
                results[f'PCM Phase Fraction WH{i+1} (-)'] = self.states[self.n_nodes + i]
                results[f'PCM Temperature WH{i+1} (C)'] = self.states[i]
                results['Hot Water Heat Injected (W)'] = self.h_injections
                results['Hot Water Heat Loss (W)'] = self.h_loss
                results['Hot Water Average Temperature (C)'] = self.states.dot(self.vol_fractions)
                results['Hot Water Maximum Temperature (C)'] = self.states.max()
                results['Hot Water Minimum Temperature (C)'] = self.states.min()
                results['Hot Water Mains Temperature (C)'] = self.mains_temp

        return results
class OneNodeWaterModel(StratifiedWaterModel):
    """
    1-node Water Tank Model
    """

    def __init__(self, **kwargs):
        kwargs.pop('water_nodes', None)
        super().__init__(water_nodes=1, **kwargs)


class TwoNodeWaterModel(StratifiedWaterModel):
    """
    2-node Water Tank Model

    - Partitions tank into 2 nodes
    - Top node is 1/3 of volume, Bottom node is 2/3
    """

    def __init__(self, **kwargs):
        kwargs.pop('water_nodes', None)
        super().__init__(water_nodes=2, water_vol_fractions=[1 / 3, 2 / 3], **kwargs)


class IdealWaterModel(OneNodeWaterModel):
    """
    Ideal water tank with near-perfect insulation. Used for TanklessWaterHeater. Modeled as 1-node tank.
    """

    def load_rc_data(self, **kwargs):
        # ignore RC parameters from the properties file
        self.volume = 1000
        return {'R_WH1_AMB': 1e6,
                'C_WH1': self.volume * water_c}

    @staticmethod
    def initialize_state(state_names, input_names, A_c, B_c, **kwargs):
        # set temperature to upper threshold
        t_max = kwargs.get('Setpoint Temperature (C)', convert(125, 'degF', 'degC'))

        # Return states as a dictionary
        return {name: t_max for name in state_names}
