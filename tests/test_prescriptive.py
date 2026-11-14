"""
Unit Tests for Prescriptive Maintenance Engine and Closed-Loop Control
"""

import pytest
from core.prescriptive import PrescriptiveEngine

def test_prescriptive_tri_factor_evaluation():
    engine = PrescriptiveEngine()
    
    # Healthy machine
    p_healthy = engine.evaluate_prescriptions(
        machine_id="MTR-01",
        machine_name="Motor 1",
        rul_hours=2400.0,
        health_index=0.95,
        fault_info={"state": "Normal"},
        dominant_component="Drive-End Bearing"
    )
    assert p_healthy["recommendations"][0]["priority_level"] == 4
    assert p_healthy["tri_factor_metrics"]["is_critical_lead_time_deficit"] is False

    # Machine with RUL less than lead time (e.g., RUL = 45h, lead time = 72h)
    p_critical = engine.evaluate_prescriptions(
        machine_id="MTR-01",
        machine_name="Motor 1",
        rul_hours=45.0,
        health_index=0.35,
        fault_info={"state": "Critical Condition"},
        dominant_component="Drive-End Bearing"
    )
    assert p_critical["recommendations"][0]["priority_level"] == 1
    assert p_critical["recommendations"][0]["needs_derating"] is True
    assert p_critical["tri_factor_metrics"]["is_critical_lead_time_deficit"] is True

def test_closed_loop_vfd_derating_dispatch():
    engine = PrescriptiveEngine()
    
    res = engine.dispatch_vfd_derating(enable=True, derate_pct=20.0)
    assert res["is_active"] is True
    assert res["speed_setpoint_pct"] == 80.0
    assert res["frequency_hz"] == 40.0
    assert res["target_rpm"] == 1152.0
    
    # Disengage
    res_disengage = engine.dispatch_vfd_derating(enable=False)
    assert res_disengage["is_active"] is False
    assert res_disengage["speed_setpoint_pct"] == 100.0

def test_cmms_work_order_creation():
    engine = PrescriptiveEngine()
    ticket = engine.create_cmms_work_order(
        machine_id="MTR-01",
        machine_name="Motor 1",
        component="Drive-End Bearing",
        priority="Urgent",
        action="Pull and replace 6205-2RS bearing"
    )
    assert ticket["ticket_id"].startswith("WO-")
    assert ticket["priority"] == "Urgent"
    assert len(engine.get_cmms_work_orders()) >= 1
