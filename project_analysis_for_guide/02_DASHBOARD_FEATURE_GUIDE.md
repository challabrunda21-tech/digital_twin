# 02. Dashboard Feature Guide & Operational Walkthrough

**Project Title:** AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance  
**Dashboard URL:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
**Primary Source Files:** [static/index.html](file:///c:/Users/DELL/OneDrive/文档/dt/static/index.html), [static/js/app.js](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/app.js), [static/js/charts.js](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/charts.js), [static/js/twin_viewer.js](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/twin_viewer.js), [app.py](file:///c:/Users/DELL/OneDrive/文档/dt/app.py)

---

## 1. Top Navigation, Header & Global Stream Control Bar

### 1.1 Header Bar & Global Controls

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  [DT Logo] Digital Twin | Industrial Intelligence         [Machine Selector ▼]  [Health Pill: Pristine]│
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  [|| Pause]  [1.0x]  [Reset Demo]  |  Simulate Fault: [Normal (Nominal Run) ▼]   Dataset: motor_pump...│
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Feature: Equipment Asset Selector
- **Purpose:** Switch between monitored industrial machinery units.
- **What You See:** A dropdown in the top-right header displaying available machines (e.g. `5.5 kW Induction Motor - Centrifugal Pump Unit #1 (MTR-PUMP-5.5KW-01)`).
- **Internal Mechanism:** Populated from `data_mgr.machines` via `GET /api/machines`. On selection change, dispatches `POST /api/machine/select` with `machine_id`. The backend resets the nominal RPM in the physics model and loads the corresponding dataset.
- **Backend API:** `GET /api/machines`, `POST /api/machine/select` ([app.py:L41-L61](file:///c:/Users/DELL/OneDrive/文档/dt/app.py#L41-L61)).
- **Verification Status:** **Verified Working.**
- **How to Demonstrate:** Click the dropdown and select `NASA IMS Bearing Endurance Testbed #2`. Observe how the active asset switches, the nominal RPM updates to 2000 RPM, and the active dataset changes to `ims_bearing_degradation.csv`.
- **What to Say to Guide:** *"The system supports a multi-asset registry. When an asset is selected, the platform synchronizes its specific physics twin parameters such as rated power and nominal RPM."*

#### Feature: Master Health Status Pill
- **Purpose:** Provide instant, high-level operational condition feedback visible on every page.
- **What You See:** A pill-shaped badge in the top-right header with a glowing status dot:
  - Green: `Pristine (HI: 0.98)`
  - Amber: `Warning (HI: 0.65)`
  - Red: `Critical (HI: 0.18)`
- **Internal Mechanism:** Evaluated every second in `app.js:L576-L592` based on `prognostics.health_index` from `GET /api/telemetry/live`.
- **Verification Status:** **Verified Working.**

#### Feature: Stream Controls (Pause / Play / Speed)
- **Purpose:** Control real-time telemetry playback.
- **What You See:** `Pause/Stream` button, `1.0x` speed toggle (`1.0x -> 2.0x -> 5.0x -> 1.0x`).
- **Internal Mechanism:** Calls `POST /api/streaming/control` with `action: "pause"`, `"play"`, or `"speed"`. When paused, the dataset index stops incrementing, holding the current sensor frame frozen for analysis.
- **Backend API:** `POST /api/streaming/control` ([app.py:L186-L210](file:///c:/Users/DELL/OneDrive/文档/dt/app.py#L186-L210)).
- **Verification Status:** **Verified Working.**

#### Feature: Anomaly Simulator Dropdown
- **Purpose:** Inject simulated mechanical and electrical faults into the live data stream for live demonstration and validation.
- **What You See:** A dropdown containing:
  1. `Normal (Nominal Run)`
  2. `Inner-Race Bearing Spall (BPFI)`
  3. `Rotor Dynamic Unbalance (1X)`
  4. `Stator Thermal Overload`
- **Internal Mechanism:** Calls `POST /api/anomaly/inject` with `anomaly_type`. In [core/data_manager.py:L218-L228](file:///c:/Users/DELL/OneDrive/文档/dt/core/data_manager.py#L218-L228), dynamic additive offsets are applied to the active telemetry frame before being passed to the physics and AI engines.
- **Verification Status:** **Verified Working.**
- **How to Demonstrate:** Select `Inner-Race Bearing Spall (BPFI)`. Notice that vibration jumps from $0.85\text{ mm/s}$ to $> 4.5\text{ mm/s}$, temperature rises, Health Index drops, the digital twin bearing turns red, and the prescriptive alert banner appears!

#### Feature: Reset Demo Button
- **Purpose:** Instantly restore the entire application to its pristine baseline state.
- **What You See:** A teal button with a circular reload icon labeled `Reset Demo`.
- **Internal Mechanism:** Calls `POST /api/demo/reset` ([app.py:L253-L265](file:///c:/Users/DELL/OneDrive/文档/dt/app.py#L253-L265)). Clears any injected anomaly, rewinds dataset index to 0, resets VFD derating to false (100% nominal speed), and clears frontend rolling buffers.
- **Verification Status:** **Verified Working.**

---

## 2. Closed-Loop VFD Derating Alert Banner (Patent Claim 8)

- **Purpose:** Alert plant operators to critical lead-time deficits and provide one-click autonomous operational speed throttling.
- **What You See:** A full-width prominent alert banner appearing directly below the streaming bar when equipment degrades into an emergency state ($HI < 0.50$ and $t_{RUL} \le t_{lead} + t_{staff}$):
  - In alert state: Red border and background: *"CRITICAL LEAD TIME DEFICIT: Remaining life (45h) is LESS than parts lead time (72h). Engage VFD derating to prevent catastrophic seizure before replacement bearing arrives!"*
  - Button: `Dispatch VFD Derating (20%)`.
  - When active: Amber background: *"CLOSED-LOOP VFD DERATING ACTIVE: Speed throttled to 80% (1152 RPM). Degradation kinetics decelerated by ~3.5x."*
- **Internal Mechanism:** Dispatches `POST /api/derate/dispatch` with `enable: true` and `derate_pct: 20.0`. In [app.py:L76-L83](file:///c:/Users/DELL/OneDrive/文档/dt/app.py#L76-L83), subsequent frames have their `speed_rpm` scaled by $0.80$, radial vibration scaled by $(0.80)^{1.5} \approx 0.715$, and RUL extended in [core/prognostics.py:L114-L117](file:///c:/Users/DELL/OneDrive/文档/dt/core/prognostics.py#L114-L117) by factor $(1 - 0.20)^{-2.8} \approx 1.87$.
- **Backend API:** `POST /api/derate/dispatch` ([app.py:L221-L230](file:///c:/Users/DELL/OneDrive/文档/dt/app.py#L221-L230)).
- **Verification Status:** **Verified Working.**

---

## 3. View 1: Overview Dashboard

**Navigation:** Click **Overview Dashboard** in the left sidebar (`#nav-overview`).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  [HI: 0.98 / 1.00]      [Vib: 0.85 mm/s]       [Temp: 42.0 °C]       [RUL: 2400 h]     │
│  [Speed: 1440 RPM]      [Current: 8.50 A]      [Pressure: 4.20 bar]  [Discrepancy: Δ0.08]│
├────────────────────────────────────────────────────┬───────────────────────────────────┤
│  Chart: Dual-Axis Sensor Timeline (Vib & Temp)     │  Chart: RUL Degradation Trajectory │
├────────────────────────────────────────────────────┴───────────────────────────────────┤
│  Card: Recent Operational Alerts & Prescriptive Status | Equipment Registry Info       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Eight Key Performance Indicator (KPI) Metric Cards

1. **Health Index (HI) Card (`#kpiHealthIndex`):**
   - Displays continuous health index ($0.02 - 1.00$). Subtitle shows operational zone: `Normal`, `Warning`, `Alarm`, or `Critical`.
2. **Radial Vibration Card (`#kpiVibration`):**
   - Displays radial vibration velocity in $\text{mm/s RMS}$. Subtitle cites ISO 10816 Class 1/2 rigid mounting limit ($2.8\text{ mm/s}$).
3. **Temperature Card (`#kpiTemperature`):**
   - Displays Drive-End bearing / stator temperature in $^\circ\text{C}$. Subtitle shows rated Class F insulation limit ($75.0^\circ\text{C}$).
4. **Remaining Useful Life Card (`#kpiRUL`):**
   - Displays forecasted operating hours until $HI = 0.20$ (e.g. `2400 h` when pristine, or active countdown when degraded). Subtitle notes 95% Bayesian confidence bounds.
5. **Rotational Speed Card (`#kpiRPM`):**
   - Displays current shaft speed in RPM (e.g. `1440 RPM`). Subtitle calculates fundamental rotational frequency $1X = RPM/60$ (e.g. `24.0 Hz`).
6. **Phase Current Card (`#kpiCurrent`):**
   - Displays stator electrical current draw in Amperes (e.g. `8.50 A`). Subtitle shows full-load rated current ($11.2\text{ A}$).
7. **Discharge Pressure Card (`#kpiPressure`):**
   - Displays centrifugal pump head in bar (e.g. `4.20 bar`). Subtitle calculates equivalent hydrodynamic head ($42.8\text{ m}$).
8. **Physics Discrepancy Card (`#kpiDiscrepancy`):**
   - Displays Euclidean state discrepancy scalar norm $\Delta(t)$ (e.g. `Δ 0.080`). Subtitle shows nominal synchronization tolerance ($\Delta < 1.00$).

### 3.2 Dual-Axis Sensor Telemetry History Chart (`#chartSensorTimeline`)
- **Canvas Element:** Custom high-DPI HTML5 canvas drawn by `SensorTimelineChart` in [static/js/charts.js:L27-L130](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/charts.js#L27-L130).
- **What You See:** Real-time dual-axis rolling trend line over the past 60 frames. Blue curve represents Radial Vibration ($\text{mm/s RMS}$, left axis). Amber curve represents Temperature ($^\circ\text{C}$, right axis). Red dashed horizontal line marks ISO 10816 Alarm threshold ($2.8\text{ mm/s}$).

### 3.3 Prognostic RUL Degradation Trajectory Chart (`#chartRULDegradation`)
- **Canvas Element:** Drawn by `RULDegradationChart` in [static/js/charts.js:L279-L416](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/charts.js#L279-L416).
- **What You See:** Extrapolated degradation trajectory curve starting from the current operating hours. Solid blue line represents mean projected Health Index. Shaded translucent blue funnel represents the **95% Bayesian Monte Carlo confidence interval** (between 5th and 95th percentiles). Dashed amber line shows Warning threshold ($HI = 0.75$), and dashed red line shows Critical Breakdown ($HI = 0.20$).

### 3.4 Operational Alerts & Equipment Registry Card
- **What You See:** Left panel lists active diagnostic alarms, root-cause statements, and component attributions. Right panel shows asset registry metadata (machine name, rated power, nominal RPM, and active dataset name).

---

## 4. View 2: Digital Twin Monitor (Signature Feature)

**Navigation:** Click **Digital Twin Monitor** in the left sidebar (`#nav-twin`).

```
┌────────────────────────────────────────────────────────┬──────────────────────────────────────┐
│  Cyber-Physical Machinery Virtual Shadow (SVG Viewport)│  Physics Shadow vs. Telemetry Panel  │
│                                                        ├──────────────────────────────────────┤
│  [Motor Stator]──[DE Bearing]──[Shaft]──[Pump Impeller]│  Modality   y_obs    y_sim    Residual│
│         │              │          │            │       │  Vib RMS    0.85     0.85     0.00   │
│     (RTD Probe)   (Vib Probe) (Coupling)  (Discharge)  │  Temp       42.0     42.0     0.0    │
│                                                        │  Current    8.50     8.50     0.00   │
│  Dynamic Thermal/Vibration Glow Heatmaps               ├──────────────────────────────────────┤
│  Speed-Proportional Rotating Shaft & Impeller          │  Sub-Assembly Stress Progress Bars   │
│                                                        ├──────────────────────────────────────┤
│  Legend: [Green: <35%]  [Amber: 35-70%]  [Red: >70%]   │  Clicked Component Deep-Dive Card    │
│  Instruction: "Click components to inspect state"      ├──────────────────────────────────────┤
│                                                        │  Canvas Chart: Discrepancy Norm Δ(t) │
└────────────────────────────────────────────────────────┴──────────────────────────────────────┘
```

### 4.1 Interactive Vector Machinery Schematic
- **Element Container:** `#twinViewportContainer` rendered by `DigitalTwinViewer` in [static/js/twin_viewer.js](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/twin_viewer.js).
- **Rendered Machine Assemblies:**
  1. **Motor Stator (5.5 kW):** Blue casing with cooling fins, 400V 3-phase terminal box, and central thermal heat glow.
  2. **Non-Drive-End (NDE) Bearing:** Rear bearing housing with localized stress glow circle and NDE sensor marker.
  3. **Drive-End (DE) Bearing:** Main high-fatigue bearing housing with dynamic radial stress glow, visible bearing balls, and connected vibration sensor probe badge (`DE: 0.85 mm/s`).
  4. **Rotating Shaft & Flexible Coupling:** Gray shaft with animated rotation indicator line and elastomeric coupling interface.
  5. **Centrifugal Volute Pump:** Teal spiral casing, top discharge flange (`4.2 bar`), suction eye inlet, and rotating 4-blade impeller.
  6. **Machine Baseplate:** Heavy structural steel bed with 4 anchor bolts.
- **Dynamic Speed Animation:** In [static/js/twin_viewer.js:L270-L290](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/twin_viewer.js#L270-L290), the shaft rotation angle and pump impeller vane rotation update on every `requestAnimationFrame` proportionally to measured `speed_rpm`:
  $$\Delta\theta = (RPM / 60) \times 360^\circ \times \Delta t$$
- **Dynamic Stress Heatmaps:** Radial SVG gradient glow circles (`#deHeatCircle`, `#ndeHeatCircle`, `#statorHeatCircle`, `#pumpHeatCircle`) change color and opacity dynamically:
  - Stress $< 35\%$: Soft green (`#10B981`)
  - Stress $35\% - 70\%$: Amber warning (`#F59E0B`)
  - Stress $> 70\%$: Intense red hotspot (`#EF4444`) with expanded radius and high opacity.

### 4.2 Interactive Component Click-to-Inspect Drawer
- **How It Works:** Clicking on any component in the SVG (e.g. Drive-End Bearing or Stator) triggers `DigitalTwinViewer.onComponentSelect`, highlighting the component and updating `#dtComponentDetailCard`.
- **Displayed Detail Information:** Component name, stress level percentage, lubricant state (e.g. `Adequate (ISO VG 46)` vs `Degraded / Contaminated`), monitored sensing modalities, and specific detected defect signatures.

### 4.3 Physics vs. Measured Telemetry Table
- Displays side-by-side comparison of:
  - **Vibration RMS:** Measured $y_{obs}$ vs. Physics $y_{sim}$ vs. Residual $\Delta$
  - **Temperature:** Measured $y_{obs}$ vs. Physics $y_{sim}$ vs. Residual $\Delta$
  - **Stator Current:** Measured $y_{obs}$ vs. Physics $y_{sim}$ vs. Residual $\Delta$

### 4.4 Sub-Assembly Stress Progress Bars
- Six animated horizontal progress bars showing individual stress levels for:
  - Drive-End (DE) Bearing
  - Non-Drive-End (NDE) Bearing
  - Stator Winding
  - Shaft & Coupling
  - Pump Impeller
  - Gearbox Mesh

### 4.5 Dynamic Euclidean Discrepancy Norm Chart (`#chartDiscrepancyNorm`)
- High-DPI canvas showing the scalar history of $\Delta(t) = \|y_{obs} - y_{sim}\|_2$. Amber dashed horizontal line indicates the divergence threshold ($\Delta = 1.0$).

---

## 5. View 3: Live Sensor Analytics

**Navigation:** Click **Live Sensor Analytics** in the left sidebar (`#nav-analytics`).

```
┌────────────────────────────────────────────────────┬──────────────────────────────────────────┐
│  FFT Power Spectrum & Rotational Harmonics (Canvas)│  Multi-Domain Feature Table (10 Rows)    │
│  - Fundamental 1X (24.0 Hz) marker [Blue]          │  - Vibration RMS (Time)                  │
│  - 2X Harmonic (48.0 Hz) marker [Gray]             │  - Peak-to-Peak Displacement (Time)      │
│  - BPFO Outer Race (86.0 Hz) marker [Amber]        │  - Crest Factor & Kurtosis (Time)        │
│  - BPFI Inner Race (130.1 Hz) marker [Red]         │  - Skewness & Shape Factor (Time)        │
│                                                    │  - Spectral Centroid (Frequency)         │
│  Bottom: 1X = 24.0 Hz | BPFO = 86.0 Hz | BPFI = 130│  - Wavelet db4 Sub-Band Energy #1-8      │
└────────────────────────────────────────────────────┴──────────────────────────────────────────┘
```

### 5.1 Fast Fourier Transform (FFT) Power Spectrum Chart (`#chartFFTSpectrum`)
- **Canvas Element:** Rendered by `FFTSpectrumChart` in [static/js/charts.js:L132-L228](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/charts.js#L132-L228).
- **Frequency Range:** $0\text{ to }200\text{ Hz}$.
- **Harmonic Markers:**
  - **1X Rotational Fundamental:** $f_{rot} = 1440/60 = 24.0\text{ Hz}$ (Blue marker).
  - **2X Harmonic:** $2 \times 24.0 = 48.0\text{ Hz}$ (Gray marker, sensitive to coupling misalignment).
  - **BPFO (Ball Pass Frequency Outer Race):** $\approx 3.58 \times 24.0 = 86.0\text{ Hz}$ (Amber marker).
  - **BPFI (Ball Pass Frequency Inner Race):** $\approx 5.42 \times 24.0 = 130.1\text{ Hz}$ (Red marker).
- **Demonstration Note:** When `bearing_spall` is injected, observe the sharp red spectral peak erupting at $130.1\text{ Hz}$ (BPFI), mathematically demonstrating inner race micro-spall detection!

### 5.2 Multi-Domain Statistical Feature Table
Presents a structured engineering table across 3 signal processing domains:
1. **Time Domain:**
   - **Vibration RMS:** Overall kinetic energy ($\text{mm/s}$).
   - **Peak-to-Peak:** Dynamic displacement range ($\text{mm/s}$).
   - **Crest Factor:** $\text{Peak} / \text{RMS}$ ratio. Values $> 3.5$ indicate localized bearing impact shocks.
   - **Kurtosis:** 4th standardized statistical moment. Baseline is $\approx 3.0$ (Gaussian); spikes $> 5.0$ on spalling.
   - **Skewness:** 3rd standardized moment indicating waveform asymmetry.
   - **Shape Factor:** $\text{RMS} / \text{Mean Absolute Value}$.
2. **Frequency Domain:**
   - **Spectral Centroid:** Center of gravity of spectral power distribution ($\text{Hz}$).
   - **Rotational 1X Amplitude:** Amplitude at running speed fundamental.
   - **Bearing BPFI Amplitude:** Amplitude at inner ring defect frequency.
3. **Time-Frequency Domain:**
   - **Wavelet Packet Decomposition (Daubechies db4):** 8 localized frequency sub-bands dividing the spectrum from DC to Nyquist.

---

## 6. View 4: Predictive Maintenance (RUL)

**Navigation:** Click **Predictive Maintenance (RUL)** in the left sidebar (`#nav-prognostics`).

```
┌──────────────────────────────────────────────┬───────────────────────────────────────────────┐
│  Continuous Health Index HI(t) Card          │  Bayesian Monte Carlo RUL Forecast Card       │
│                                              │                                               │
│             [HI: 0.98 / 1.00]                │  Predicted Hours: 2400 Operating Hours        │
│   "Asset operating in pristine condition."   │  95% Bounds: 2100 h (Lower) — 2700 h (Upper)  │
│                                              ├───────────────────────────────────────────────┤
│  Four Operational Zones:                     │  Prognostic Methodology Note:                 │
│  - Normal Stage (1.00 - 0.75)   [Pristine]   │  100 stochastic Monte Carlo dropout forward   │
│  - Warning Stage (0.75 - 0.50)  [Tracking]   │  passes over Paris-Erdogan degradation        │
│  - Alarm Stage (0.50 - 0.20)    [Work-Order] │  kinetics, quantifying prediction             │
│  - Critical Stage (< 0.20)      [Derate]     │  uncertainty before maintenance execution.    │
└──────────────────────────────────────────────┴───────────────────────────────────────────────┘
```

### 6.1 Continuous Normalized Health Index HI(t)
- Large typography score displaying health on a continuous normalized scale $[0.0, 1.0]$.
- Categorized across 4 standard industrial health stages:
  - **Normal Operation ($1.00 \ge HI \ge 0.75$):** Soft green. Nominal baseline.
  - **Warning Stage ($0.75 > HI \ge 0.50$):** Amber. Micro-wear detected; RUL extrapolation active.
  - **Maintenance Alarm ($0.50 > HI \ge 0.20$):** Orange. Accelerated wear; work order dispatched.
  - **Critical Failure Stage ($HI < 0.20$):** Red. Immediate seizure risk; emergency derating initiated.

### 6.2 Remaining Useful Life (RUL) Countdown & Confidence Bounds
- **Operating Hours to Failure:** Displays mean $t_{RUL}$ hours until the degradation curve crosses $HI = 0.20$.
- **95% Bayesian Confidence Bounds:** Displays lower 5th percentile and upper 95th percentile bounds calculated from 100 stochastic Monte Carlo dropout passes in [core/prognostics.py:L121-L144](file:///c:/Users/DELL/OneDrive/文档/dt/core/prognostics.py#L121-L144).

---

## 7. View 5: Fault Detection

**Navigation:** Click **Fault Detection** in the left sidebar (`#nav-faults`).

```
┌─────────────────────────────────────────────────────┬───────────────────────────────────────────┐
│  Temporal Deep Learning Autoencoder Status          │  Multi-Head Self-Attention Attribution    │
│  Classification: Healthy Nominal Operation          │  Bar Chart (Explainable AI):              │
│  Summary: All vectors conform to baseline.          │                                           │
│  ┌─────────────────┬─────────────────┬───────────┐  │  Vibration (Radial)  ████████████  42.5%  │
│  │ Loss: 0.0210    │ Thresh: 0.1500  │ Conf: 98% │  │  Temperature         ██████        24.1%  │
│  └─────────────────┴─────────────────┴───────────┘  │  Current             ████          15.2%  │
│                                                     │  Acoustic / Shock    ███           10.8%  │
│  Identified Localized Fault Signatures:             │  Pressure            ██             4.5%  │
│  [List of specific faults, components, & actions]   │  Vibration (Axial)   █              2.9%  │
└─────────────────────────────────────────────────────┴───────────────────────────────────────────┘
```

### 7.1 Temporal Autoencoder Anomaly Scoring
- **Reconstruction Loss ($L_{rec}$):** Mean squared error between normalized input vector $x_t$ and reconstructed vector $\hat{x}_t$.
- **Adaptive Threshold ($\tau$):** Dynamic decision threshold set to $0.1500$. If $L_{rec} > \tau$, the asset is classified as anomalous.
- **Model Confidence:** Percentage confidence (e.g. $98\%$).

### 7.2 Multi-Head Self-Attention Attribution Bar Chart (`#chartAttentionAttribution`)
- **Canvas Element:** Rendered by `AttentionAttributionChart` in [static/js/charts.js:L230-L277](file:///c:/Users/DELL/OneDrive/文档/dt/static/js/charts.js#L230-L277).
- **Purpose:** Solves the "black-box AI" problem by providing **Explainable AI (XAI)**.
- **How It Works:** Multiplies component-wise reconstruction errors by self-attention weights ($Q \times K^T / \sqrt{d_k}$), revealing the exact percentage contribution of each sensor modality to the anomaly:
  - In bearing spall: Radial Vibration and Acoustic channels contribute $> 65\%$.
  - In thermal overload: Temperature channel contributes $> 70\%$.

### 7.3 Identified Localized Fault Signatures
Displays structured diagnostic cards containing:
- Fault Type (e.g. `Inner-Race Bearing Spalling (BPFI)`)
- Evidence String (e.g. `BPFI peak amplitude 0.452 mm/s with shock kurtosis 6.8 (baseline ~3.0)`)
- Affected Sub-Assembly (e.g. `Drive-End (DE) Bearing`)
- Prescribed Immediate Action (e.g. `Schedule vibration deep-dive and prepare bearing replacement (6205-2RS)`)

---

## 8. View 6: Prescriptive Maintenance

**Navigation:** Click **Prescriptive Maintenance** in the left sidebar (`#nav-prescriptive`).

```
┌──────────────────────────────────────────────┬────────────────────────────────────────────────┐
│  Tri-Factor Prescriptive Decision Model Card │  Active Prescriptive Action Recommendations    │
│  - Parts Lead Time (t_lead):    72.0 h       │  [Card: Urgent Replacement Work-Order]         │
│  - Staff Preparation (t_staff):  8.0 h       │  - Action: Replace Drive-End Bearing           │
│  - Production Window (t_window):48.0 h       │  - Logistics: tRUL (45h) < tlead+tstaff (80h)  │
│                                              │  - Button: [Create CMMS Ticket]                │
│  Button: [Dispatch Manual CMMS Ticket]       ├────────────────────────────────────────────────┤
│                                              │  Autonomous VFD/PLC Speed Throttling Controller│
│                                              │  - Throttle Selector: [20% Speed Reduction ▼]  │
│                                              │  - Target Setpoint: 80% (1152 RPM / 40.0 Hz)   │
│                                              │  - Fatigue Deceleration: ~3.5x Life Extension  │
│                                              │  - Buttons: [Engage Derating] [Restore Nominal]│
│                                              │  - Audit History Log (Holding Register 40001)  │
└──────────────────────────────────────────────┴────────────────────────────────────────────────┘
```

### 8.1 Tri-Factor Optimization Model
Correlates three factory parameters against $t_{RUL}$:
1. **$t_{lead}$ (72.0 hours):** Supply chain delivery time for replacement components (bearings, mechanical seals, coupling inserts).
2. **$t_{staff}$ (8.0 hours):** Technician shift scheduling and specialized tooling preparation time.
3. **$t_{window}$ (48.0 hours):** Next scheduled factory shift maintenance shutdown.
- **Safety Margin:** $t_{margin} = t_{RUL} - (t_{lead} + t_{staff})$. If negative, a **Critical Lead-Time Deficit** occurs, meaning the machine will suffer catastrophic failure before spare parts arrive without operational throttling.

### 8.2 Autonomous VFD/PLC Speed Throttling Controller (Patent Claim 8)
- **Throttle Selector:** Choose between 15%, 20%, or 25% speed derating.
- **Target Setpoint Display:** Shows throttled target RPM and electrical frequency (e.g. $80\% \to 1152\text{ RPM} / 40.0\text{ Hz}$).
- **Buttons:** `Engage Closed-Loop Derating` and `Restore Nominal Speed (100%)`.
- **Derating Command Audit History:** A scrollable audit log showing every dispatched throttle command with timestamp, target RPM, and simulated Modbus Holding Register 40001 status.

### 8.3 CMMS Work-Order Dispatch Modal
- Click `Dispatch Manual CMMS Ticket` to open the modal overlay (`#modalCreateTicket`).
- Input fields: Target Sub-Assembly, Priority Level (`Normal`, `Elevated`, `Urgent`, `Critical`), Prescribed Maintenance Action, and Technician Notes.
- On submit: Dispatches `POST /api/cmms/create`, assigning a formal ticket ID (`WO-YYYYMMDD-###`) and adding it to the in-memory work-order queue.

---

## 9. View 7: Historical Data & Reports

**Navigation:** Click **Historical Data & Reports** in the left sidebar (`#nav-history`).

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│  Historical Telemetry & Audit Logs                [Search Filter...]  [Export CSV] [Export JSON]│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│  Timestamp         Vib Radial  Vib Axial  Temp    Current  Speed  Pressure  HI    Status      │
│  2026-10-14 10:00  0.98 mm/s   0.46 mm/s  41.9°C  8.48 A   1442   4.18 bar  0.98  Nominal     │
│  2026-10-14 10:01  0.86 mm/s   0.38 mm/s  41.8°C  8.48 A   1438   4.21 bar  0.98  Nominal     │
│  ... (up to 30 recent records rendered with live search filtering)                           │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 9.1 Searchable 9-Column Telemetry Table
- Displays recent telemetry records: Timestamp, Vibration Radial, Vibration Axial, Temperature, Current, Speed, Pressure, Health Index, and Operational Status badge.
- **Live Search Filter (`#historySearchInput`):** Filters rows in real time as the user types timestamps, speeds, or status keywords (`Nominal`, `Warning`, `Critical`).

### 9.2 Export Capabilities
- **Export CSV Button (`#btnExportCsv`):** Calls `GET /api/export/csv`. Downloads the currently active dataset as a browser attachment (`export_<filename>.csv`).
- **Export JSON Report Button (`#btnExportJson`):** Calls `GET /api/export/json`. Generates and downloads a comprehensive diagnostic JSON report containing machine metadata, active derating status, generated CMMS work orders, and recent telemetry snapshots.

---

## 10. View 8: Data Management & Ingestion

**Navigation:** Click **Data Management** in the left sidebar (`#nav-settings`).

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│  Bundled Industrial Datasets Library:                                                         │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐        │
│  │ Motor-Pump Run (Active) │  │ NASA IMS Bearing Bench  │  │ Helical Gearbox Run     │        │
│  │ 151 rows • 10.0 KB      │  │ 121 rows • 8.1 KB       │  │ 101 rows • 6.7 KB       │        │
│  │ [Currently Loaded]      │  │ [Load Dataset]          │  │ [Load Dataset]          │        │
│  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘        │
├────────────────────────────────────────────────────┬──────────────────────────────────────────┤
│  Ingest Custom Sensor Dataset (Drag-and-Drop)      │  System Architecture & Patent Claims     │
│  - Validates required columns                      │  - Invention Title & Application Details │
│  - Enforces physical realistic bounds              │  - Faculty Guide & Inventor List         │
│  - Maximum upload size: 10 MB                      │  - Patent Claims 1 to 10 Mapping         │
└────────────────────────────────────────────────────┴──────────────────────────────────────────┘
```

### 10.1 Bundled Datasets Library
- Displays cards for all CSV files in `datasets/` retrieved via `GET /api/datasets`.
- Shows filename, description, row count, column count, and size.
- One-click `Load Dataset` button calls `POST /api/dataset/select`, switching active playback without restarting the server.

### 10.2 Drag-and-Drop CSV Ingestion with Strict Validation
- **Dropzone Element:** `#uploadDropzone` with click-to-browse file input.
- **Strict Validation Engine:** In [core/data_manager.py:L103-L170](file:///c:/Users/DELL/OneDrive/文档/dt/core/data_manager.py#L103-L170), validates:
  1. **Schema Check:** Verifies presence of required headers (`timestamp, vibration_radial, vibration_axial, temperature, current, speed_rpm`).
  2. **Numeric Check:** Rejects non-numeric data and missing values (NaN).
  3. **Physical Bounds Enforcement:**
     - Vibration: $0.0\text{ to }50.0\text{ mm/s}$
     - Temperature: $-10.0\text{ to }180.0^\circ\text{C}$
     - Current: $0.0\text{ to }100.0\text{ A}$
     - Speed: $0.0\text{ to }15000.0\text{ RPM}$
     - Pressure: $0.0\text{ to }100.0\text{ bar}$
  4. **File Size Limit:** Rejects files $> 10\text{ MB}$.

### 10.3 Patent Claims Specification Card
- Summarizes the formal patent details:
  - **Invention Title:** AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance
  - **Applicant:** VNR VJIET, Hyderabad
  - **Faculty Guide:** Mrs. Prasanna Pabba
  - **Inventors:** Ms. Challa Brundha, Ms. Venkata Sai Srija Chevuturi, Ms. Jeevani Sabbineni, Ms. Udvisha Samudrala, Mr. Mohammad Hussen Shaik, Ms. Kotla Sreenidhi
  - **Claims Reference:** Claims 1–10 covering cyber-physical discrepancy, temporal autoencoder, self-attention, Bayesian RUL, and closed-loop VFD derating.
