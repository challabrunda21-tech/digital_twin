"""
AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance
Full-Stack Starlette Application Server
Provides:
- Real-time telemetry streaming and state synchronization
- Cyber-physical Digital Twin state discrepancy calculations
- AI temporal autoencoder inference with self-attention attribution
- Continuous Health Index tracking and Bayesian Monte Carlo RUL forecasting
- Prescriptive tri-factor optimization and closed-loop VFD/PLC derating
- Dynamic CSV dataset ingestion and validation
- Comprehensive REST APIs for all 8 application views
"""

import os
import json
import numpy as np
import pandas as pd
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from core.signal_processing import SignalPreprocessor
from core.physics_twin import PhysicsTwinEngine
from core.ai_engine import DiagnosticAIEngine
from core.prognostics import PrognosticEngine
from core.prescriptive import PrescriptiveEngine
from core.data_manager import DataManager

# Initialize subsystem singletons
data_mgr = DataManager(datasets_dir="datasets")
signal_proc = SignalPreprocessor(sampling_rate=1000.0)
physics_twin = PhysicsTwinEngine(machine_type="motor_pump", rated_power_kw=5.5)
ai_engine = DiagnosticAIEngine(input_dim=6)
prognostic_engine = PrognosticEngine()
prescriptive_engine = PrescriptiveEngine()

# Simulation state
raw_signal_buffer = []

async def get_machines(request):
    """Return list of available industrial machines."""
    return JSONResponse({
        "active_machine_id": data_mgr.active_machine_id,
        "machines": data_mgr.machines
    })

async def select_machine(request):
    """Switch active machinery asset."""
    try:
        body = await request.json()
        machine_id = body.get("machine_id")
        machine = data_mgr.select_machine(machine_id)
        if not machine:
            return JSONResponse({"success": False, "error": "Machine ID not found"}, status_code=404)
        
        # Reset physics twin state for new machine
        physics_twin.nominal_rpm = float(machine.get("nominal_rpm", 1440.0))
        return JSONResponse({"success": True, "machine": machine})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

async def get_live_telemetry(request):
    """
    Core synchronization endpoint.
    Computes real-time telemetry, physics shadow state, discrepancy norm,
    FFT features, AI autoencoder reconstruction loss, attention attribution,
    Health Index, RUL curve, and prescriptive recommendations.
    """
    frame = data_mgr.get_next_telemetry_frame()
    if not frame:
        return JSONResponse({"error": "No telemetry dataset loaded"}, status_code=503)

    speed_rpm = frame.get("speed_rpm", 1440.0)
    
    # Apply closed-loop PLC/VFD derating speed throttling if active (Patent Claim 8)
    if prescriptive_engine.vfd_derating_active:
        throttle_ratio = prescriptive_engine.vfd_speed_setpoint_pct / 100.0
        speed_rpm = round(speed_rpm * throttle_ratio, 1)
        frame["speed_rpm"] = speed_rpm
        if "vibration_radial" in frame:
            frame["vibration_radial"] = round(frame["vibration_radial"] * (throttle_ratio ** 1.5), 3)

    # 1. Simulate nominal state via physics shadow model
    load_factor = min(1.2, max(0.2, (frame.get("current") or 8.5) / 11.2))
    sim_nominal = physics_twin.simulate_nominal_state(speed_rpm, load_factor, dt_seconds=1.0)
    
    # 2. Dynamic state discrepancy vector Δ(t)
    discrepancy = physics_twin.compute_state_discrepancy(frame, sim_nominal)
    
    # 3. Multi-domain signal feature extraction
    # Synthesize realistic high-frequency vibration signal window centered on current RMS
    vib_rms = frame.get("vibration_radial", 0.85)
    f_rot = speed_rpm / 60.0
    t = np.linspace(0, 0.5, 500)
    # Add fundamental 1X, 2X, and defect frequencies if degraded
    harm_1x = min(3.0, vib_rms * 0.7)
    harm_2x = min(1.5, vib_rms * 0.3)
    bpfi_amp = max(0.0, (vib_rms - 1.5) * 0.4)
    sig = (harm_1x * np.sin(2 * np.pi * f_rot * t) + 
           harm_2x * np.sin(2 * np.pi * 2.0 * f_rot * t) + 
           bpfi_amp * np.sin(2 * np.pi * 5.42 * f_rot * t) + 
           0.15 * np.random.randn(500))
    
    features = signal_proc.extract_all_features(sig, running_rpm=speed_rpm)
    freq_data = features["frequency_domain"]
    # Provide backward/frontend compatibility aliases
    freq_data["fundamental_1x_amp"] = freq_data.get("amp_1x", 0.0)
    freq_data["bpfi_amp"] = freq_data.get("amp_bpfi", 0.0)
    features["wavelet_dwt"] = {"subband_energies": features.get("wavelet_energy_bands", [])}
    
    # 4. AI-Driven Diagnostic Engine (Reconstruction & Attention)
    ai_diag = ai_engine.diagnose_condition(frame, freq_data, discrepancy["discrepancy_norm"])
    
    # 5. Prognostic Degradation & Continuous Health Index
    hi_res = prognostic_engine.compute_health_index(
        ai_diag["reconstruction_loss"],
        discrepancy["discrepancy_norm"],
        frame.get("vibration_radial", 0.85),
        frame.get("temperature", 42.0)
    )
    
    # 6. RUL Trajectory Forecasting (with 95% Bayesian Monte Carlo intervals)
    op_hours = frame.get("operating_hours", 1200.0)
    rul_res = prognostic_engine.predict_rul_trajectory(
        hi_res["health_index"],
        current_operating_hours=op_hours,
        derated=prescriptive_engine.vfd_derating_active,
        derate_pct=prescriptive_engine.derate_percentage
    )
    
    # 7. Prescriptive Maintenance Recommendation Engine
    machine = data_mgr.get_current_machine()
    prescript = prescriptive_engine.evaluate_prescriptions(
        machine["id"],
        machine["name"],
        rul_res["rul_hours"],
        hi_res["health_index"],
        ai_diag,
        discrepancy["dominant_stressed_component"]
    )

    response_payload = {
        "timestamp": frame.get("timestamp"),
        "active_dataset": data_mgr.active_dataset_name,
        "active_machine_name": machine.get("name", "5.5 kW Induction Motor - Pump"),
        "machine": machine,
        "streaming": {
            "is_streaming": data_mgr.is_streaming,
            "playback_speed": data_mgr.playback_speed,
            "current_frame_index": data_mgr.current_index,
            "total_frames": len(data_mgr.active_df) if data_mgr.active_df is not None else 0,
            "injected_anomaly": data_mgr.injected_anomaly
        },
        "telemetry": frame,
        "physics_twin": {
            "simulated_nominal": sim_nominal,
            "discrepancy_norm": discrepancy["discrepancy_norm"],
            "residuals": discrepancy["residuals"],
            "component_stresses": discrepancy["component_stresses"],
            "dominant_stressed_component": discrepancy["dominant_stressed_component"],
            "synchronization_status": discrepancy["synchronization_status"]
        },
        "signal_features": features,
        "ai_diagnostics": ai_diag,
        "prognostics": {
            "health_index": hi_res["health_index"],
            "zone": hi_res["zone"],
            "zone_color": hi_res["zone_color"],
            "zone_desc": hi_res["zone_desc"],
            "rul_hours": rul_res["rul_hours"],
            "rul_lower_bound_hours": rul_res["rul_lower_bound_hours"],
            "rul_upper_bound_hours": rul_res["rul_upper_bound_hours"],
            "confidence_bounds": {
                "lower_hours": rul_res["rul_lower_bound_hours"],
                "upper_hours": rul_res["rul_upper_bound_hours"]
            },
            "confidence_level": rul_res["confidence_level"],
            "trajectory": rul_res.get("trajectory", {})
        },
        "prescriptive": prescript
    }

    return JSONResponse(response_payload)

async def get_telemetry_history(request):
    """Return recent historical telemetry records."""
    limit = int(request.query_params.get("limit", 50))
    history = data_mgr.get_history(limit=limit)
    return JSONResponse({
        "machine": data_mgr.get_current_machine(),
        "total_records": len(history),
        "history": history
    })

async def control_streaming(request):
    """Pause, play, seek, or change playback speed."""
    try:
        body = await request.json()
        action = body.get("action")
        
        if action == "play":
            data_mgr.is_streaming = True
        elif action == "pause":
            data_mgr.is_streaming = False
        elif action == "speed":
            data_mgr.playback_speed = float(body.get("speed", 1.0))
        elif action == "seek":
            idx = int(body.get("index", 0))
            data_mgr.seek_frame(idx)
        
        return JSONResponse({
            "success": True,
            "is_streaming": data_mgr.is_streaming,
            "current_index": data_mgr.current_index,
            "playback_speed": data_mgr.playback_speed
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

async def inject_anomaly(request):
    """Inject or clear live simulated anomaly."""
    try:
        body = await request.json()
        anomaly_type = body.get("anomaly_type")  # bearing_spall, unbalance, thermal_overload, or None
        msg = data_mgr.inject_anomaly(anomaly_type)
        return JSONResponse({"success": True, "message": msg, "active_anomaly": data_mgr.injected_anomaly})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

async def dispatch_vfd_derating(request):
    """Dispatch closed-loop PLC/VFD derating command."""
    try:
        body = await request.json()
        enable = bool(body.get("enable", True))
        derate_pct = float(body.get("derate_pct", 20.0))
        res = prescriptive_engine.dispatch_vfd_derating(enable=enable, derate_pct=derate_pct)
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

async def create_cmms_ticket(request):
    """Create a new CMMS work-order."""
    try:
        body = await request.json()
        machine = data_mgr.get_current_machine()
        ticket = prescriptive_engine.create_cmms_work_order(
            machine_id=machine["id"],
            machine_name=machine["name"],
            component=body.get("component", "Drive-End Bearing"),
            priority=body.get("priority", "Urgent"),
            action=body.get("action", "Replace bearing and check shaft runout"),
            notes=body.get("notes", "")
        )
        return JSONResponse({"success": True, "ticket": ticket})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

async def get_cmms_tickets(request):
    """Return all CMMS work-orders."""
    return JSONResponse({"work_orders": prescriptive_engine.get_cmms_work_orders()})

async def reset_demo(request):
    """Restore initial nominal demonstration baseline."""
    res = data_mgr.reset_demo()
    prescriptive_engine.dispatch_vfd_derating(enable=False)
    # Reset physics nominal RPM
    machine = data_mgr.get_current_machine()
    physics_twin.nominal_rpm = float(machine.get("nominal_rpm", 1440.0))
    return JSONResponse({
        "success": True,
        "message": "Demonstration successfully reset to initial pristine nominal state.",
        "machine": machine,
        "state": res
    })

async def list_datasets(request):
    """Return list of available bundled and uploaded datasets."""
    datasets = data_mgr.list_available_datasets()
    return JSONResponse({
        "active_dataset": data_mgr.active_dataset_name,
        "total_datasets": len(datasets),
        "datasets": datasets
    })

async def select_dataset(request):
    """Switch active dataset by filename."""
    try:
        body = await request.json()
        filename = body.get("filename")
        if not filename:
            return JSONResponse({"success": False, "error": "No filename provided"}, status_code=400)
        
        success = data_mgr.load_dataset(filename)
        if not success:
            return JSONResponse({"success": False, "error": f"Failed to load dataset '{filename}'"}, status_code=404)
        
        return JSONResponse({
            "success": True,
            "message": f"Active dataset switched to: {filename}",
            "active_dataset": filename,
            "row_count": len(data_mgr.active_df) if data_mgr.active_df is not None else 0
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

async def upload_dataset(request):
    """Upload and validate a custom sensor CSV file with size and path safety."""
    try:
        form = await request.form()
        file = form.get("file")
        if not file:
            return JSONResponse({"valid": False, "error": "No file uploaded in form field 'file'"}, status_code=400)
        
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            return JSONResponse({"valid": False, "error": "File size exceeds 10 MB limit."}, status_code=413)

        csv_str = contents.decode("utf-8", errors="replace")
        raw_name = getattr(file, "filename", "uploaded_sensor_data.csv") or "uploaded_sensor_data.csv"
        safe_filename = os.path.basename(raw_name).replace(" ", "_")
        if not safe_filename.lower().endswith(".csv"):
            safe_filename += ".csv"
        
        res = data_mgr.save_uploaded_dataset(safe_filename, csv_str)
        if not res["valid"]:
            return JSONResponse(res, status_code=422)
            
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"valid": False, "error": f"Upload processing error: {str(e)}"}, status_code=500)

async def export_csv(request):
    """Export current dataset as CSV download."""
    if data_mgr.active_df is None or len(data_mgr.active_df) == 0:
        return JSONResponse({"error": "No dataset loaded"}, status_code=404)
    csv_data = data_mgr.active_df.to_csv(index=False)
    headers = {"Content-Disposition": f"attachment; filename=export_{data_mgr.active_dataset_name}"}
    return Response(content=csv_data, media_type="text/csv", headers=headers)

async def export_json(request):
    """Export comprehensive digital twin and diagnostic report."""
    history = data_mgr.get_history(limit=100)
    payload = {
        "report_generated_at": pd.Timestamp.now().isoformat(),
        "application": "AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance",
        "machine": data_mgr.get_current_machine(),
        "work_orders": prescriptive_engine.get_cmms_work_orders(),
        "derating_status": {
            "is_active": prescriptive_engine.vfd_derating_active,
            "derate_pct": prescriptive_engine.derate_percentage,
            "speed_setpoint_pct": prescriptive_engine.vfd_speed_setpoint_pct
        },
        "telemetry_records_count": len(history),
        "telemetry_sample": history[:20]
    }
    json_str = json.dumps(payload, indent=2)
    headers = {"Content-Disposition": "attachment; filename=digital_twin_report.json"}
    return Response(content=json_str, media_type="application/json", headers=headers)

async def serve_index(request):
    """Serve the primary HTML application shell."""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>AI-Based Digital Twin</h1><p>UI loading...</p>")

# Routing definition
routes = [
    Route("/", serve_index),
    Route("/api/machines", get_machines, methods=["GET"]),
    Route("/api/machine/select", select_machine, methods=["POST"]),
    Route("/api/telemetry/live", get_live_telemetry, methods=["GET"]),
    Route("/api/telemetry/history", get_telemetry_history, methods=["GET"]),
    Route("/api/streaming/control", control_streaming, methods=["POST"]),
    Route("/api/anomaly/inject", inject_anomaly, methods=["POST"]),
    Route("/api/derate/dispatch", dispatch_vfd_derating, methods=["POST"]),
    Route("/api/cmms/create", create_cmms_ticket, methods=["POST"]),
    Route("/api/cmms/list", get_cmms_tickets, methods=["GET"]),
    Route("/api/demo/reset", reset_demo, methods=["POST"]),
    Route("/api/datasets", list_datasets, methods=["GET"]),
    Route("/api/dataset/select", select_dataset, methods=["POST"]),
    Route("/api/upload", upload_dataset, methods=["POST"]),
    Route("/api/export/csv", export_csv, methods=["GET"]),
    Route("/api/export/json", export_json, methods=["GET"]),
    Mount("/static", StaticFiles(directory="static"), name="static")
]

app = Starlette(debug=True, routes=routes)
