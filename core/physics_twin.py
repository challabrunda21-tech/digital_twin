"""
Physics-Informed Digital Twin Modeling and Dynamic State Synchronization Engine
Implements:
- First-principles electromechanical, thermal, and hydrodynamic state-space equations
- Real-time physics simulation of nominal baseline telemetry y_sim(t)
- Dynamic Euclidean State Discrepancy Vector: Δ(t) = || y_obs(t) - y_sim(t) ||_2
- Localized component-level stress and degradation attribution:
  * Drive-End (DE) Bearing
  * Non-Drive-End (NDE) Bearing
  * Stator Winding & Core
  * Rotating Shaft & Coupling
  * Pump Impeller & Hydraulic Casing
  * Helical Gearbox & Pinion
"""

import numpy as np
import math
from typing import Dict, Any, List

class PhysicsTwinEngine:
    def __init__(self, machine_type: str = "motor_pump", rated_power_kw: float = 5.5):
        self.machine_type = machine_type
        self.rated_power_kw = rated_power_kw
        
        # Physical parameters for 5.5 kW 4-pole induction motor coupled to centrifugal pump
        self.nominal_rpm = 1440.0
        self.nominal_freq_hz = 50.0
        self.nominal_current_a = 11.2       # Full load rated stator current
        self.no_load_current_a = 4.2        # Magnetizing magnet current
        self.stator_resistance_ohm = 1.15   # Per phase stator resistance
        self.thermal_capacitance = 1800.0   # J / °C (thermal mass)
        self.thermal_resistance = 0.52      # °C / W (heat dissipation to ambient)
        self.ambient_temp_c = 25.0
        
        # State tracking for thermal differential equation
        self.simulated_temp_c = 28.0
        self.last_update_time = 0.0
        
        # Nominal vibration calibration constants (ISO 10816 Class 1/2 rigid mount)
        self.base_vibration_rms = 0.85      # mm/s healthy baseline
        self.base_pressure_bar = 4.2        # bar nominal pump discharge pressure

    def simulate_nominal_state(self, speed_rpm: float, load_factor: float, dt_seconds: float = 1.0) -> Dict[str, float]:
        """
        Solve physical state-space equations for nominal expected operation:
        y_sim(t) = [speed_rpm, current_a, temperature_c, vibration_rms, pressure_bar]
        """
        # 1. Electrical Current baseline: I_nom = I_0 + load_factor * (I_rated - I_0)
        norm_load = max(0.0, min(1.2, load_factor))
        expected_current = self.no_load_current_a + norm_load * (self.nominal_current_a - self.no_load_current_a)
        
        # 2. Thermal state-space differential equation:
        # P_loss = 3 * I^2 * R + P_core + P_friction
        p_copper_loss = 3.0 * (expected_current ** 2) * self.stator_resistance_ohm
        p_core_loss = 180.0 * (speed_rpm / self.nominal_rpm)
        p_mech_loss = 75.0 * ((speed_rpm / self.nominal_rpm) ** 2)
        total_heat_gen = p_copper_loss + p_core_loss + p_mech_loss
        
        # dT/dt = (P_loss - (T - T_amb)/R_th) / C_th
        heat_dissipated = (self.simulated_temp_c - self.ambient_temp_c) / self.thermal_resistance
        dt_temp = (total_heat_gen - heat_dissipated) / self.thermal_capacitance
        
        # Numerical Euler integration
        self.simulated_temp_c += dt_temp * dt_seconds
        # Bound to physical equilibrium limits
        self.simulated_temp_c = max(self.ambient_temp_c, min(120.0, self.simulated_temp_c))
        
        # 3. Vibration baseline (proportional to rotational kinetic energy and nominal hydraulic turbulence)
        speed_ratio = speed_rpm / self.nominal_rpm
        expected_vibration = self.base_vibration_rms * (speed_ratio ** 1.8) * (0.8 + 0.2 * norm_load)
        
        # 4. Fluid Pump Head / Pressure baseline (Euler turbomachinery affinity laws: H ~ N^2)
        expected_pressure = self.base_pressure_bar * (speed_ratio ** 2) * (1.0 - 0.15 * norm_load)

        return {
            "speed_rpm": round(speed_rpm, 1),
            "current_a": round(expected_current, 2),
            "temperature_c": round(self.simulated_temp_c, 2),
            "vibration_rms": round(expected_vibration, 3),
            "pressure_bar": round(expected_pressure, 2)
        }

    def compute_state_discrepancy(self, observed: Dict[str, float], simulated: Dict[str, float]) -> Dict[str, Any]:
        """
        Compute the dynamic Euclidean state discrepancy vector:
        Δ(t) = || y_obs(t) - y_sim(t) ||_2 (normalized)
        And calculate localized component-level stress indicators.
        """
        # Map incoming telemetry keys (e.g. from CSV datasets) to simulated state keys
        obs_mapped = {
            "vibration_rms": float(observed.get("vibration_rms") if observed.get("vibration_rms") is not None 
                                   else observed.get("vibration_radial", 0.85)),
            "temperature_c": float(observed.get("temperature_c") if observed.get("temperature_c") is not None 
                                   else observed.get("temperature", 42.0)),
            "current_a": float(observed.get("current_a") if observed.get("current_a") is not None 
                               else observed.get("current", 8.5)),
            "pressure_bar": float(observed.get("pressure_bar") if observed.get("pressure_bar") is not None 
                                 else observed.get("pressure", 4.2)),
            "speed_rpm": float(observed.get("speed_rpm", self.nominal_rpm))
        }

        # Standardized weights for physical state vector components
        weights = {
            "vibration_rms": 0.35,  # mm/s (most sensitive to mechanical wear)
            "temperature_c": 0.25,  # °C (sensitive to thermal degradation/friction)
            "current_a": 0.20,      # A (sensitive to stator/rotor electrical imbalance)
            "pressure_bar": 0.10,   # bar (sensitive to pump cavitation/hydraulic wear)
            "speed_rpm": 0.10       # rpm
        }
        
        # Normalization scale factors
        scale = {
            "vibration_rms": 2.0,   # 2 mm/s deviation is significant
            "temperature_c": 25.0,  # 25 °C deviation is significant
            "current_a": 5.0,       # 5 A deviation is significant
            "pressure_bar": 1.5,    # 1.5 bar deviation is significant
            "speed_rpm": 150.0      # 150 RPM deviation is significant
        }

        residuals = {}
        weighted_sq_sum = 0.0

        for key, w in weights.items():
            obs_val = obs_mapped.get(key, simulated.get(key, 0.0))
            sim_val = simulated.get(key, 0.0)
            diff = obs_val - sim_val
            residuals[f"delta_{key}"] = round(diff, 3)
            
            # Normalized component residual
            norm_res = (diff / scale[key])
            weighted_sq_sum += w * (norm_res ** 2)

        # Dynamic Euclidean discrepancy norm
        discrepancy_norm = math.sqrt(weighted_sq_sum)
        
        # Localized component stress indicators [0.0 = nominal, 1.0 = severe stress]
        vib_delta = max(0.0, obs_mapped["vibration_rms"] - simulated.get("vibration_rms", 0.85))
        temp_delta = max(0.0, obs_mapped["temperature_c"] - simulated.get("temperature_c", 40.0))
        curr_delta = max(0.0, obs_mapped["current_a"] - simulated.get("current_a", 8.5))
        press_delta = max(0.0, abs(obs_mapped["pressure_bar"] - simulated.get("pressure_bar", 4.2)))

        vib_ratio = min(1.0, vib_delta / 3.0)
        temp_ratio = min(1.0, temp_delta / 30.0)
        curr_ratio = min(1.0, curr_delta / 4.5)
        press_ratio = min(1.0, press_delta / 1.5)
        
        # Localized component stresses:
        # Drive-End bearing is heavily affected by radial vibration and localized frictional heat
        de_bearing_stress = min(1.0, max(0.08, 0.70 * vib_ratio + 0.30 * temp_ratio))
        # Non-Drive-End bearing has lower direct load
        nde_bearing_stress = min(1.0, max(0.06, 0.45 * vib_ratio + 0.25 * temp_ratio))
        # Stator winding is dominated by temperature rise and phase current draw
        stator_stress = min(1.0, max(0.08, 0.65 * temp_ratio + 0.35 * curr_ratio))
        # Shaft & coupling is sensitive to unbalance vibration and dynamic current swing
        axial_vib = float(observed.get("vibration_axial", 0.45))
        axial_ratio = min(1.0, max(0.0, (axial_vib - 0.45) / 1.2))
        shaft_stress = min(1.0, max(0.08, 0.50 * vib_ratio + 0.35 * axial_ratio + 0.15 * curr_ratio))
        # Centrifugal pump impeller is dominated by discharge pressure fluctuations and hydraulic turbulence
        pump_stress = min(1.0, max(0.08, 0.60 * press_ratio + 0.40 * vib_ratio))
        # Helical gearbox mesh is sensitive to vibration harmonics and torque
        gearbox_stress = min(1.0, max(0.08, 0.55 * vib_ratio + 0.45 * temp_ratio))

        # Determine highest stressed component
        component_stresses = {
            "Drive-End (DE) Bearing": round(de_bearing_stress, 3),
            "Non-Drive-End (NDE) Bearing": round(nde_bearing_stress, 3),
            "Stator Winding": round(stator_stress, 3),
            "Shaft & Coupling": round(shaft_stress, 3),
            "Pump Impeller": round(pump_stress, 3),
            "Gearbox Mesh": round(gearbox_stress, 3)
        }
        
        dominant_component = max(component_stresses.items(), key=lambda x: x[1])[0]

        return {
            "discrepancy_norm": round(discrepancy_norm, 4),
            "residuals": residuals,
            "simulated_nominal": simulated,
            "component_stresses": component_stresses,
            "dominant_stressed_component": dominant_component,
            "synchronization_status": "Synchronized" if discrepancy_norm < 0.8 else "Divergence Detected"
        }
