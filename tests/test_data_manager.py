"""
Unit Tests for Data Manager and CSV Ingestion Validation
"""

import pytest
from core.data_manager import DataManager

def test_load_default_datasets():
    dm = DataManager(datasets_dir="datasets")
    assert dm.active_df is not None
    assert len(dm.active_df) > 50
    assert "vibration_radial" in dm.active_df.columns
    assert "temperature" in dm.active_df.columns

def test_validate_csv_valid_content():
    dm = DataManager()
    valid_csv = """timestamp,vibration_radial,vibration_axial,temperature,current,speed_rpm,pressure,acoustic_db
2026-10-14 10:00:00,0.85,0.42,41.5,8.2,1440,4.2,35.0
2026-10-14 10:01:00,0.88,0.44,41.8,8.3,1441,4.2,35.2
"""
    res = dm.validate_csv(valid_csv)
    assert res["valid"] is True
    assert res["row_count"] == 2

def test_validate_csv_missing_columns():
    dm = DataManager()
    invalid_csv = """timestamp,vibration_radial,temperature
2026-10-14 10:00:00,0.85,41.5
"""
    res = dm.validate_csv(invalid_csv)
    assert res["valid"] is False
    assert "Missing required sensor columns" in res["error"]

def test_validate_csv_out_of_bounds():
    dm = DataManager()
    out_of_bounds_csv = """timestamp,vibration_radial,vibration_axial,temperature,current,speed_rpm
2026-10-14 10:00:00,0.85,0.42,550.0,8.2,1440
"""
    res = dm.validate_csv(out_of_bounds_csv)
    assert res["valid"] is False
    assert "outside physical range" in res["error"]

def test_anomaly_injection():
    dm = DataManager()
    msg = dm.inject_anomaly("bearing_spall")
    assert dm.injected_anomaly == "bearing_spall"
    
    frame = dm.get_next_telemetry_frame()
    # Vibration should be artificially boosted by anomaly injection
    assert frame["vibration_radial"] > 3.0
    
    dm.inject_anomaly(None)
    assert dm.injected_anomaly is None
