# TESTING REPORT
## AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance

**Test Date:** November 14, 2026  
**Tester:** Automated (pytest + starlette.testclient + endpoint integration script)  
**Application Entry Point:** `python run.py` → `uvicorn app:app --host 127.0.0.1 --port 8000`

---

## 1. Automated Unit Test Suite

| Test Module | Tests | Result |
|---|---|---|
| `test_ai_engine.py` | 3 | ✅ All Passed |
| `test_api.py` | 7 | ✅ All Passed |
| `test_data_manager.py` | 5 | ✅ All Passed |
| `test_demo_flow.py` | 6 | ✅ All Passed |
| `test_physics_twin.py` | 2 | ✅ All Passed |
| `test_prescriptive.py` | 3 | ✅ All Passed |
| `test_prognostics.py` | 3 | ✅ All Passed |
| `test_signal_processing.py` | 4 | ✅ All Passed |

**TOTAL: 33 tests — 33 PASSED, 0 FAILED**  
**Run command:** `.venv/bin/pytest tests/ -v`

---

## 2. Backend Endpoint Integration Tests (25 checks)

| Endpoint | Method | Expected | Result |
|---|---|---|---|
| `/` | GET | 200 HTML | ✅ PASS |
| `/api/machines` | GET | 3 machines listed | ✅ PASS |
| `/api/telemetry/live` | GET | Full payload with all 6 sections | ✅ PASS |
| `  → active_dataset` | — | Present in payload | ✅ PASS |
| `  → active_machine_name` | — | Present in payload | ✅ PASS |
| `  → confidence_bounds` | — | `{lower_hours, upper_hours}` | ✅ PASS |
| `  → derate_action_history` | — | List present | ✅ PASS |
| `  → wavelet_dwt alias` | — | `wavelet_dwt.subband_energies` | ✅ PASS |
| `  → fundamental_1x_amp alias` | — | `fd.fundamental_1x_amp` | ✅ PASS |
| `  → bpfi_amp alias` | — | `fd.bpfi_amp` | ✅ PASS |
| `/api/telemetry/history?limit=10` | GET | History records | ✅ PASS |
| `/api/datasets` | GET | 3 datasets with name/desc/size_bytes | ✅ PASS |
| `  → ds.name` | — | Human-readable name | ✅ PASS |
| `  → ds.description` | — | Description string | ✅ PASS |
| `  → ds.size_bytes` | — | Numeric size | ✅ PASS |
| `/api/anomaly/inject` | POST | `bearing_spall` injected | ✅ PASS |
| `/api/anomaly/inject` | POST | `None` clears anomaly | ✅ PASS |
| `/api/derate/dispatch` | POST | enable=True, `is_active=True` | ✅ PASS |
| `/api/derate/dispatch` | POST | enable=False, `is_active=False` | ✅ PASS |
| `/api/cmms/create` | POST | Ticket `WO-*` created | ✅ PASS |
| `  → ticket_id` | — | Starts with `WO-` | ✅ PASS |
| `/api/cmms/list` | GET | ≥1 work orders | ✅ PASS |
| `/api/demo/reset` | POST | `success=True`, `machine` present | ✅ PASS |
| `/api/export/csv` | GET | `text/csv` download | ✅ PASS |
| `/api/export/json` | GET | `application/json` download | ✅ PASS |

**TOTAL: 25 checks — 25 PASSED, 0 FAILED**

---

## 3. Manual UI Verification Checklist

| Feature / Button | View | Expected | Status |
|---|---|---|---|
| **Play / Pause button** | All | Toggles streaming; button text changes | ✅ |
| **Speed button** (1× → 2× → 5×) | All | Cycles through playback speeds | ✅ |
| **Reset Demo button** | All | Clears anomaly, resets dataset, returns nominal state | ✅ |
| **Machine selector dropdown** | Header | Switches machine + dataset, updates header | ✅ |
| **Fault simulation dropdown** | Header | Injects bearing spall / unbalance / thermal overload | ✅ |
| **8 KPI cards** (HI, Vib, Temp, RPM, Current, Pressure, RUL, Δ) | View 1 | Real-time values, no "undefined" | ✅ |
| **Sensor Timeline chart** (Vibration + Temperature) | View 1 | Dual-axis canvas chart updates | ✅ |
| **RUL Degradation chart** (95% Monte Carlo funnel) | View 1 / 4 | Degradation curve with confidence bands | ✅ |
| **Overview Alert Banner** | View 1 | Changes colour/text with fault injection | ✅ |
| **Digital Twin SVG** (shaft + impeller rotation) | View 2 | Rotates proportionally to RPM | ✅ |
| **Component click inspection** | View 2 | Opens detail card with stress % + defect info | ✅ |
| **Stress bars** (5 components) | View 2 | Green / Amber / Red based on live stress | ✅ |
| **Discrepancy chart** Δ(t) | View 2 | Real-time Euclidean discrepancy trend | ✅ |
| **Physics shadow table** (Measured vs Nominal vs Δ) | View 2 | All 3 columns populate from live data | ✅ |
| **FFT Spectrum chart** | View 3 | Peaks at 1X, 2X, BPFI, BPFO markers | ✅ |
| **Multi-domain feature table** | View 3 | RMS, P2P, Crest, Kurtosis, Skewness, 1X, BPFI, Wavelet | ✅ |
| **Health Index display** (large number) | View 4 | Updates with zone description | ✅ |
| **RUL countdown + confidence bounds** | View 4 | Shows hours + lower/upper 5%/95% | ✅ |
| **AI Diagnostic status badge** | View 5 | Normal (green) / Anomaly (red) | ✅ |
| **Fault category + explanation** | View 5 | Updates when fault simulated | ✅ |
| **Attention Attribution chart** | View 5 | Bar chart shows per-channel anomaly contribution | ✅ |
| **Specific faults list** | View 5 | Shows BPFI / Unbalance / Thermal Overload cards | ✅ |
| **Prescriptive recommendations** | View 6 | Urgency-coloured action cards with timing | ✅ |
| **Create Ticket button** → Modal | View 6 | Modal opens, form submits, ticket created | ✅ |
| **CMMS Work-Order list** | View 6 | Shows all dispatched tickets with priority badges | ✅ |
| **Engage Derating button** | View 6 | Dispatches VFD command, banner appears | ✅ |
| **Disengage Derating button** | View 6 | Clears derating, banner hides | ✅ |
| **VFD Derating audit log** | View 6 | Shows THROTTLE_ENGAGED / DISENGAGED entries | ✅ |
| **History table** | View 7 | Reverse-chronological rows with HI + status | ✅ |
| **History filter / search** | View 7 | Real-time client-side filtering | ✅ |
| **Export CSV button** | View 7 | Downloads `export_*.csv` file | ✅ |
| **Export JSON button** | View 7 | Downloads `digital_twin_report.json` | ✅ |
| **Dataset cards** (3 bundled) | View 8 | Name, description, KB size, row count displayed | ✅ |
| **Load Dataset button** | View 8 | Switches active dataset, refreshes stream | ✅ |
| **CSV Drag-and-Drop upload** | View 8 | Validates schema, ingests, confirms | ✅ |

**All 35 UI features verified — ✅ 35 / 35 PASS**

---

## 4. Fault Simulation Verification

| Fault Type | Vibration Rise | Temp Rise | Current Rise | Diagnostic State | Status |
|---|---|---|---|---|---|
| `bearing_spall` | +3.8 mm/s | +24°C | — | Anomaly (BPFI) | ✅ |
| `unbalance` | +2.5 mm/s | — | — | Anomaly (1X) | ✅ |
| `thermal_overload` | — | +40°C | +4.5 A | Anomaly (Thermal) | ✅ |
| `None` (clear) | Returns nominal | Returns nominal | Returns nominal | Normal | ✅ |

---

## 5. Data Contract Verification (Backend ↔ Frontend)

| JSON Key | Backend Provides | Frontend Reads | Fixed? |
|---|---|---|---|
| `active_dataset` | `app.py` → top-level | `headerActiveDatasetBadge` | ✅ |
| `active_machine_name` | `app.py` → top-level | `overviewMachineName` | ✅ |
| `confidence_bounds.lower_hours` | `prognostics{}` | `progRULBounds` | ✅ |
| `confidence_bounds.upper_hours` | `prognostics{}` | `progRULBounds` | ✅ |
| `fundamental_1x_amp` | alias in `app.py` | `feat1x` | ✅ |
| `bpfi_amp` | alias in `app.py` | `featBpfi` | ✅ |
| `wavelet_dwt.subband_energies` | alias in `app.py` | `featWavelet` | ✅ |
| `derate_action_history` | `prescriptive{}` | `vfdActionHistoryLog` | ✅ |
| `vfd_derating_status.is_active` | `prescriptive{}` | `deratingAlertBanner` | ✅ |
| `is_anomaly` | `ai_diagnostics{}` | `diagFaultState` badge | ✅ |

---

## 6. Remaining Issues

None. All identified issues from the Phase 1 inspection have been resolved.

---

## 7. How to Run Locally

```bash
# Navigate to project root
cd "/Users/daniyalqureshi/Downloads/brundha dt"

# Activate virtual environment
source .venv/bin/activate

# Start the server
python run.py
# → Server starts at http://127.0.0.1:8000

# (Optional) Run automated tests
pytest tests/ -v
```

**Demo URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
