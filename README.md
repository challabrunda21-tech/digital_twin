# AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance

A full-stack, cyber-physical monitoring, diagnostic, and prognostic platform developed in accordance with Indian Patent Form 2 (The Patent Act 1970) and Design Thinking Batch 2022–2026, **Vallurupalli Nageswara Rao Vignana Jyothi Institute of Engineering & Technology (VNR VJIET)**, Hyderabad.

---

## 1. System Architecture

The platform implements the **4-Tier Cyber-Physical Architecture** specified in Patent Claims 1 to 10:

```
[Tier 1: Physical Asset & Sensor Layer]
   - 3-Phase 5.5 kW Induction Motor, Centrifugal Pump, Helical Gearbox
   - Tri-axial Accelerometers (25.6 kHz), PT100 RTD (10 Hz), Hall Current (5 kHz), Acoustic (100 kHz)
               │ (OPC-UA / MQTT / Modbus TCP)
               ▼
[Tier 2: Edge Telemetry Ingestion & Signal Preprocessing]
   - FIR Bandpass Filtering, Detrending, Median Filtering
   - Time-Domain: RMS, Peak-to-Peak, Crest Factor, Kurtosis, Skewness, Shape Factor
   - Frequency-Domain: FFT Power Spectra, Harmonics (1X, 2X, 3X), Defect Frequencies (BPFO, BPFI)
   - Time-Frequency: Wavelet Packet Decomposition (Daubechies db4, 8 sub-bands)
               │ (Adaptive z-score vector x_t)
               ▼
[Tier 3: Cyber-Physical Digital Twin & AI Prognostic Engine]
   - Physics-Informed Shadow Model: Electromechanical & hydrodynamic state-space equations
   - Dynamic Euclidean State Discrepancy: Δ(t) = || y_obs(t) - y_sim(t) ||_2
   - AI Diagnostic Engine: Temporal Autoencoder with Multi-Head Self-Attention Attribution
   - Prognostics: Continuous Health Index HI(t) ∈ [0.0, 1.0] across 4 operational zones
   - RUL Forecaster: Degradation kinetics with 95% Bayesian Monte Carlo dropout confidence bounds
               │ (Prognostic & Diagnostic State)
               ▼
[Tier 4: Prescriptive Maintenance & Interactive HMI]
   - Tri-Factor Optimizer: Correlates t_RUL against t_lead, t_staff, and t_window
   - Closed-Loop PLC/VFD Derating (Claim 8): Autonomous speed throttling (15-25%) decelerates wear
   - Interactive HMI: 8 comprehensive operational views with real-time 2D/3D SVG/Canvas heatmaps
```

---

## 2. Implemented Pages & Views

1. **Overview Dashboard**: Fleet-wide equipment summary, 8 Key Performance Indicators (Health Index, Vibration RMS, Temperature, RPM, Stator Current, Pressure, Discrepancy Norm Δ, and RUL), real-time sensor timeline charts, and RUL degradation curves.
2. **Digital Twin Monitor (Signature Feature)**: Technical vector/Canvas visualization of rotating machinery with dynamic thermal and vibration stress heatmaps, speed-proportional rotating shaft and impeller animation, sensor probe pins, and a side-by-side discrepancy telemetry panel.
3. **Live Sensor Analytics**: Fast Fourier Transform (FFT) power spectrogram, harmonic tracking (1X rotational fundamental, 2X, BPFI inner race, BPFO outer race), and multi-domain statistical feature tables.
4. **Predictive Maintenance (RUL)**: Continuous normalized Health Index ($HI \in [0.0, 1.0]$) categorized across 4 zones (Normal $\ge 0.75$, Warning $0.75-0.50$, Alarm $0.50-0.20$, Critical $< 0.20$), degradation trajectory curves, and 95% Bayesian Monte Carlo confidence intervals.
5. **Fault Detection**: Temporal autoencoder reconstruction loss ($L_{rec}(t)$) compared against dynamic adaptive thresholds ($\tau(t) = \mu + 2.5\sigma$), multi-head self-attention attribution radar/bar charts, and automated root-cause explanations.
6. **Maintenance Recommendations**: Prescriptive tri-factor decision model ($t_{RUL}$ vs. $t_{lead} + t_{staff}$ vs. $t_{window}$), automated CMMS work-order dispatch, and closed-loop VFD derating control.
7. **Historical Data & Reports**: Tabular telemetry inspection with live search, sorting, column formatting, and one-click export to CSV and JSON.
8. **Data Management & Ingestion**: Ingest custom CSV datasets with client-side drag-and-drop and strict schema/physical-bound validation.

---

## 3. Visual Design System

Designed according to industrial engineering specifications:
- **Background**: Technical light `#F5F7FA`
- **Cards**: Pure white `#FFFFFF` with thin `#DCE3EC` borders
- **Primary Accent**: Corporate blue `#2563EB`
- **Digital Twin Accent**: Restrained teal/cyan `#0D9488`
- **Headings & Body**: Charcoal `#172033` and slate gray `#475569`
- **Status Indicators**: Soft green (`#10B981`), amber (`#F59E0B`), and restrained red (`#EF4444`)

---

## 4. How to Run the Application

### Prerequisites
- Python 3.10+ (tested on Python 3.14.4)
- Installed dependencies: `starlette`, `uvicorn`, `numpy`, `pandas`, `pytest`

### Start Server
Run the runner script:
```bash
python run.py
```
Or start directly with uvicorn:
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 5. Running the Test Suite

Execute the complete 27-test suite using `pytest`:
```bash
pytest tests/
```
Output:
```
tests/test_ai_engine.py ...             [11%]
tests/test_api.py .......               [37%]
tests/test_data_manager.py .....        [55%]
tests/test_physics_twin.py ..           [62%]
tests/test_prescriptive.py ...          [74%]
tests/test_prognostics.py ...           [85%]
tests/test_signal_processing.py ....    [100%]
===================== 27 passed in 1.00s =====================
```

---

## 6. Patent Particulars & Academic Citation

- **Invention Title**: AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance
- **Statutory Framework**: Form 2 Specification (Section 10 & Rule 13), The Patent Act 1970
- **Filing Date**: 30th October 2025
- **Applicant**: Vallurupalli Nageswara Rao Vignana Jyothi Institute of Engineering & Technology (VNR VJIET)
- **Faculty Guide**: Mrs. Prasanna Pabba (Assistant Professor, Dept. of CSE)
- **Inventors & Researchers**:
  - Ms. Challa Brundha (22071A0501)
  - Ms. Venkata Sai Srija Chevuturi (22071A0502)
  - Ms. Jeevani Sabbineni (22071A0503)
  - Ms. Udvisha Samudrala (22071A0504)
  - Mr. Mohammad Hussen Shaik (22071A0505)
  - Ms. Kotla Sreenidhi (22071A0506)
