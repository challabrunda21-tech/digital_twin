"""
Comprehensive Integration Tests for Demonstration Flow, Cyber-Physical Discrepancy,
Dataset Management, and Closed-Loop VFD Throttling.
"""

import pytest
import asyncio
import json
import numpy as np
from app import (
    reset_demo, list_datasets, select_dataset,
    dispatch_vfd_derating, get_live_telemetry, inject_anomaly
)
from core.physics_twin import PhysicsTwinEngine
from core.prognostics import PrognosticEngine
from core.prescriptive import PrescriptiveEngine

class MockRequest:
    def __init__(self, json_data=None, query_params=None):
        self._json_data = json_data or {}
        self.query_params = query_params or {}

    async def json(self):
        return self._json_data


def test_datasets_list_and_selection():
    # 1. Test listing bundled datasets
    res = asyncio.run(list_datasets(MockRequest()))
    assert res.status_code == 200
    data = json.loads(res.body)
    assert "datasets" in data
    assert len(data["datasets"]) >= 3
    filenames = [d["filename"] for d in data["datasets"]]
    assert "testbed_motor_pump_run.csv" in filenames
    assert "ims_bearing_degradation.csv" in filenames

    # 2. Test selecting a valid dataset
    req_sel = MockRequest(json_data={"filename": "ims_bearing_degradation.csv"})
    res_sel = asyncio.run(select_dataset(req_sel))
    assert res_sel.status_code == 200
    data_sel = json.loads(res_sel.body)
    assert data_sel["success"] is True
    assert data_sel["active_dataset"] == "ims_bearing_degradation.csv"
    assert data_sel["row_count"] > 0

    # 3. Test selecting an invalid dataset safely
    req_bad = MockRequest(json_data={"filename": "non_existent_dataset.csv"})
    res_bad = asyncio.run(select_dataset(req_bad))
    assert res_bad.status_code == 404
    data_bad = json.loads(res_bad.body)
    assert "error" in data_bad


def test_demo_reset_endpoint():
    # Inject anomaly and derate first
    req_anom = MockRequest(json_data={"anomaly_type": "bearing_spall"})
    asyncio.run(inject_anomaly(req_anom))
    req_derate = MockRequest(json_data={"enable": True, "derate_pct": 20.0})
    asyncio.run(dispatch_vfd_derating(req_derate))

    # Reset demo
    res_reset = asyncio.run(reset_demo(MockRequest()))
    assert res_reset.status_code == 200
    data_reset = json.loads(res_reset.body)
    assert data_reset["success"] is True

    # Check that live telemetry reflects pristine state
    res_live = asyncio.run(get_live_telemetry(MockRequest()))
    live_data = json.loads(res_live.body)
    assert live_data["prescriptive"]["vfd_derating_status"]["is_active"] is False
    assert live_data["streaming"]["injected_anomaly"] is None
    assert live_data["ai_diagnostics"]["state"] == "Normal"


def test_cyber_physical_discrepancy_with_real_keys():
    twin = PhysicsTwinEngine()
    sim = twin.simulate_nominal_state(speed_rpm=1440.0, load_factor=0.8)
    
    # 1. Nominal frame with standard dataset keys (vibration_radial, temperature, etc.)
    nominal_frame = {
        "vibration_radial": sim["vibration_rms"] + 0.05,
        "vibration_axial": 0.42,
        "temperature": sim["temperature_c"] + 1.0,
        "current": sim["current_a"] + 0.2,
        "pressure": sim["pressure_bar"],
        "speed_rpm": 1440.0
    }
    state_nom = twin.compute_state_discrepancy(nominal_frame, sim)
    assert "discrepancy_norm" in state_nom
    assert "residuals" in state_nom
    assert "component_stresses" in state_nom
    # Under nominal conditions discrepancy should be small and state synchronized
    assert state_nom["discrepancy_norm"] < 0.35
    assert state_nom["synchronization_status"] == "Synchronized"

    # 2. Severe bearing anomaly frame (elevated radial vibration and temperature)
    fault_frame = {
        "vibration_radial": sim["vibration_rms"] + 4.5,
        "vibration_axial": 1.20,
        "temperature": sim["temperature_c"] + 35.0,
        "current": sim["current_a"] + 4.5,
        "pressure": sim["pressure_bar"] - 1.0,
        "speed_rpm": 1440.0
    }
    state_fault = twin.compute_state_discrepancy(fault_frame, sim)
    # Discrepancy norm must increase significantly
    assert state_fault["discrepancy_norm"] > state_nom["discrepancy_norm"]
    assert state_fault["component_stresses"]["Drive-End (DE) Bearing"] > 0.50
    assert "Drive-End" in state_fault["dominant_stressed_component"]


def test_prognostic_trajectory_consistency():
    prog = PrognosticEngine()

    # 1. Test healthy baseline (HI >= 0.75)
    healthy_res = prog.predict_rul_trajectory(0.95)
    assert "trajectory" in healthy_res
    assert len(healthy_res["trajectory"]) > 0
    assert healthy_res["rul_hours"] > 1000
    assert "rul_lower_bound_hours" in healthy_res

    # 2. Test degraded state (HI < 0.75)
    degraded_res = prog.predict_rul_trajectory(0.60)
    assert "trajectory" in degraded_res
    assert len(degraded_res["trajectory"]) > 0
    assert degraded_res["rul_hours"] < healthy_res["rul_hours"]
    assert degraded_res["rul_lower_bound_hours"] < degraded_res["rul_upper_bound_hours"]


def test_closed_loop_derating_audit_trail():
    pres = PrescriptiveEngine()
    
    # Dispatch derate
    action_res = pres.dispatch_vfd_derating(enable=True, derate_pct=25.0)
    assert action_res["is_active"] is True
    assert action_res["speed_setpoint_pct"] == 75.0
    assert action_res["target_rpm"] == 1080.0
    assert len(pres.derate_action_history) == 1
    assert pres.derate_action_history[0]["action"] == "THROTTLE_ENGAGED"

    # Disengage
    action_res2 = pres.dispatch_vfd_derating(enable=False)
    assert action_res2["is_active"] is False
    assert action_res2["speed_setpoint_pct"] == 100.0
    assert len(pres.derate_action_history) == 2
    assert pres.derate_action_history[0]["action"] == "THROTTLE_DISENGAGED"
    assert "speed_setpoint_pct" in pres.derate_action_history[0]


def test_schema_consistency_and_field_presence():
    # 1. Reset demo verifies correct active machine ID
    res_reset = asyncio.run(reset_demo(MockRequest()))
    reset_data = json.loads(res_reset.body)
    assert reset_data["success"] is True
    assert reset_data["machine"]["id"] == "MTR-PUMP-5.5KW-01"

    # 2. Datasets list contains both human metadata and size bytes
    res_ds = asyncio.run(list_datasets(MockRequest()))
    ds_data = json.loads(res_ds.body)
    for ds in ds_data["datasets"]:
        assert "name" in ds
        assert "description" in ds
        assert "size_bytes" in ds
        assert "size_kb" in ds

    # 3. Live telemetry contains top-level active names and confidence bounds
    res_live = asyncio.run(get_live_telemetry(MockRequest()))
    live_data = json.loads(res_live.body)
    assert "active_dataset" in live_data
    assert "active_machine_name" in live_data
    assert "confidence_bounds" in live_data["prognostics"]
    assert "lower_hours" in live_data["prognostics"]["confidence_bounds"]
    assert "upper_hours" in live_data["prognostics"]["confidence_bounds"]
    assert "derate_action_history" in live_data["prescriptive"]
    assert "wavelet_dwt" in live_data["signal_features"]

