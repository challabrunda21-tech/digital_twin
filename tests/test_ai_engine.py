"""
Unit Tests for AI Diagnostic Engine (Temporal Autoencoder & Attention Attribution)
"""

import numpy as np
import pytest
from core.ai_engine import DiagnosticAIEngine

def test_autoencoder_reconstruction():
    ai = DiagnosticAIEngine(input_dim=6)
    # Baseline nominal vector
    raw = np.array([0.85, 0.45, 42.0, 8.5, 4.2, 35.0])
    res = ai.evaluate_reconstruction(raw)
    
    assert "reconstruction_loss" in res
    assert "attributions" in res
    assert len(res["attributions"]) == 6
    # Nominal error should be low
    assert res["reconstruction_loss"] < 0.10

def test_diagnose_nominal_condition():
    ai = DiagnosticAIEngine()
    telemetry = {
        "vibration_radial": 0.85,
        "vibration_axial": 0.45,
        "temperature": 42.0,
        "current": 8.5,
        "pressure": 4.2,
        "acoustic_db": 35.0
    }
    spectral = {"amp_1x": 0.8, "amp_2x": 0.2, "amp_bpfi": 0.02, "amp_bpfo": 0.02}
    diag = ai.diagnose_condition(telemetry, spectral, discrepancy_norm=0.15)
    
    assert diag["state"] == "Normal"
    assert diag["fault_category"] == "Healthy Nominal Operation"
    assert diag["confidence"] > 0.90

def test_diagnose_bearing_fault_condition():
    ai = DiagnosticAIEngine()
    telemetry = {
        "vibration_radial": 3.85,  # High vibration
        "vibration_axial": 1.65,
        "temperature": 68.0,      # High temperature
        "current": 10.8,
        "pressure": 3.6,
        "acoustic_db": 62.0       # High acoustic emission
    }
    spectral = {"amp_1x": 1.1, "amp_2x": 0.3, "amp_bpfi": 0.45, "amp_bpfo": 0.05, "kurtosis": 6.8}
    diag = ai.diagnose_condition(telemetry, spectral, discrepancy_norm=1.85)
    
    assert diag["state"] in ["Anomaly Detected", "Critical Condition"]
    assert any("Inner-Race Bearing Spalling" in f["type"] for f in diag["specific_faults"])
