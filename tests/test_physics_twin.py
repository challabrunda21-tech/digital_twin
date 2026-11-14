"""
Unit Tests for Physics-Informed Digital Twin and Dynamic Discrepancy Vector
"""

import pytest
from core.physics_twin import PhysicsTwinEngine

def test_nominal_state_simulation():
    engine = PhysicsTwinEngine(machine_type="motor_pump", rated_power_kw=5.5)
    sim = engine.simulate_nominal_state(speed_rpm=1440.0, load_factor=0.8)
    
    assert "speed_rpm" in sim
    assert "current_a" in sim
    assert "temperature_c" in sim
    assert "vibration_rms" in sim
    assert "pressure_bar" in sim
    
    # Physics ranges for 5.5 kW unit
    assert 4.0 <= sim["current_a"] <= 12.0
    assert 25.0 <= sim["temperature_c"] <= 100.0
    assert 0.5 <= sim["vibration_rms"] <= 2.0
    assert 3.0 <= sim["pressure_bar"] <= 6.0

def test_discrepancy_vector_healthy_vs_faulty():
    engine = PhysicsTwinEngine()
    sim = engine.simulate_nominal_state(1440.0, 0.8)
    
    # Healthy observation matching simulation
    healthy_obs = {
        "vibration_rms": sim["vibration_rms"] + 0.05,
        "temperature_c": sim["temperature_c"] + 1.0,
        "current_a": sim["current_a"] + 0.2,
        "speed_rpm": sim["speed_rpm"],
        "pressure_bar": sim["pressure_bar"]
    }
    disc_healthy = engine.compute_state_discrepancy(healthy_obs, sim)
    assert disc_healthy["discrepancy_norm"] < 0.5
    assert disc_healthy["synchronization_status"] == "Synchronized"
    
    # Faulty observation with high vibration and thermal rise
    faulty_obs = {
        "vibration_rms": sim["vibration_rms"] + 3.8,  # Huge vibration spike
        "temperature_c": sim["temperature_c"] + 35.0, # High friction heating
        "current_a": sim["current_a"] + 4.0,
        "speed_rpm": sim["speed_rpm"] - 30.0,
        "pressure_bar": sim["pressure_bar"] - 1.2
    }
    disc_faulty = engine.compute_state_discrepancy(faulty_obs, sim)
    assert disc_faulty["discrepancy_norm"] > 1.0
    assert disc_faulty["synchronization_status"] == "Divergence Detected"
    assert "Drive-End (DE) Bearing" in disc_faulty["component_stresses"]
