"""
API and Endpoint Async Integration Tests
"""

import pytest
import asyncio
import json
from app import (
    get_machines, select_machine, get_live_telemetry,
    control_streaming, inject_anomaly, dispatch_vfd_derating,
    create_cmms_ticket, get_cmms_tickets
)

class MockRequest:
    def __init__(self, json_data=None, query_params=None):
        self._json_data = json_data or {}
        self.query_params = query_params or {}

    async def json(self):
        return self._json_data

def test_api_get_machines():
    res = asyncio.run(get_machines(MockRequest()))
    assert res.status_code == 200
    data = json.loads(res.body)
    assert "machines" in data
    assert len(data["machines"]) >= 3

def test_api_select_machine():
    req = MockRequest(json_data={"machine_id": "GBX-HELICAL-03"})
    res = asyncio.run(select_machine(req))
    assert res.status_code == 200
    data = json.loads(res.body)
    assert data["success"] is True
    assert data["machine"]["id"] == "GBX-HELICAL-03"

def test_api_get_live_telemetry():
    res = asyncio.run(get_live_telemetry(MockRequest()))
    assert res.status_code == 200
    data = json.loads(res.body)
    assert "telemetry" in data
    assert "physics_twin" in data
    assert "prognostics" in data
    assert "ai_diagnostics" in data
    assert "prescriptive" in data
    assert data["prognostics"]["health_index"] is not None

def test_api_control_streaming():
    req = MockRequest(json_data={"action": "pause"})
    res = asyncio.run(control_streaming(req))
    assert res.status_code == 200
    data = json.loads(res.body)
    assert data["is_streaming"] is False

    req2 = MockRequest(json_data={"action": "play"})
    res2 = asyncio.run(control_streaming(req2))
    assert json.loads(res2.body)["is_streaming"] is True

def test_api_inject_anomaly():
    req = MockRequest(json_data={"anomaly_type": "bearing_spall"})
    res = asyncio.run(inject_anomaly(req))
    assert res.status_code == 200
    data = json.loads(res.body)
    assert data["active_anomaly"] == "bearing_spall"

    # Clear
    req_clear = MockRequest(json_data={"anomaly_type": None})
    res_clear = asyncio.run(inject_anomaly(req_clear))
    assert json.loads(res_clear.body)["active_anomaly"] is None

def test_api_dispatch_vfd_derating():
    req = MockRequest(json_data={"enable": True, "derate_pct": 20.0})
    res = asyncio.run(dispatch_vfd_derating(req))
    assert res.status_code == 200
    data = json.loads(res.body)
    assert data["is_active"] is True
    assert data["speed_setpoint_pct"] == 80.0

def test_api_cmms_ticket_lifecycle():
    req_create = MockRequest(json_data={
        "component": "Drive-End Bearing",
        "priority": "Critical",
        "action": "Immediate replacement",
        "notes": "Automated test ticket"
    })
    res_create = asyncio.run(create_cmms_ticket(req_create))
    assert res_create.status_code == 200
    data_ticket = json.loads(res_create.body)
    assert data_ticket["success"] is True
    assert data_ticket["ticket"]["ticket_id"].startswith("WO-")

    res_list = asyncio.run(get_cmms_tickets(MockRequest()))
    assert res_list.status_code == 200
    data_list = json.loads(res_list.body)
    assert len(data_list["work_orders"]) > 0
