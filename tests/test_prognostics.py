"""
Unit Tests for Prognostic Health Index and Bayesian Monte Carlo RUL Estimation
"""

import pytest
from core.prognostics import PrognosticEngine

def test_health_index_zones():
    prog = PrognosticEngine()
    
    # Pristine condition
    hi_healthy = prog.compute_health_index(reconstruction_loss=0.02, discrepancy_norm=0.1, vibration_rms=0.85, temp_c=42.0)
    assert hi_healthy["health_index"] >= 0.75
    assert hi_healthy["zone"] == "Normal Operation"
    
    # Degraded condition
    hi_degraded = prog.compute_health_index(reconstruction_loss=0.35, discrepancy_norm=1.5, vibration_rms=3.5, temp_c=72.0)
    assert hi_degraded["health_index"] < 0.75
    assert hi_degraded["is_degraded"] is True

def test_rul_monte_carlo_trajectory():
    prog = PrognosticEngine()
    # Degraded HI = 0.55
    rul_res = prog.predict_rul_trajectory(current_hi=0.55, current_operating_hours=1250.0)
    
    assert "rul_hours" in rul_res
    assert "rul_lower_bound_hours" in rul_res
    assert "rul_upper_bound_hours" in rul_res
    assert rul_res["rul_lower_bound_hours"] <= rul_res["rul_hours"] <= rul_res["rul_upper_bound_hours"]
    assert len(rul_res["trajectory"]["operating_hours"]) > 10

def test_vfd_derating_life_extension():
    prog = PrognosticEngine()
    current_hi = 0.45
    # Normal operation without derating
    rul_normal = prog.predict_rul_trajectory(current_hi=current_hi, derated=False)
    # Derated operation by 20%
    rul_derated = prog.predict_rul_trajectory(current_hi=current_hi, derated=True, derate_pct=20.0)
    
    # Closed-loop derating must decelerate fatigue kinetics and extend RUL hours
    assert rul_derated["rul_hours"] > rul_normal["rul_hours"] * 1.5
