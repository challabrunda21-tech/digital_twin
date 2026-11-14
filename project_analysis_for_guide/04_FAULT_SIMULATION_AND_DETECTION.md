# 04. Fault Simulation, Anomaly Injection, and Detection Mechanics

**Project Title:** AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance  
**Academic Context:** Comprehensive Guide to Fault Modeling, Injection Scenarios, and Diagnostic Logic  
**Primary Source Files:** [core/data_manager.py](file:///c:/Users/DELL/OneDrive/文档/dt/core/data_manager.py), [core/ai_engine.py](file:///c:/Users/DELL/OneDrive/文档/dt/core/ai_engine.py), [core/physics_twin.py](file:///c:/Users/DELL/OneDrive/文档/dt/core/physics_twin.py), [app.py](file:///c:/Users/DELL/OneDrive/文档/dt/app.py)

---

## 1. Overview of Fault Injection Architecture

In an industrial operating environment, critical mechanical failures (such as bearing raceway spalling, catastrophic unbalance, or electrical stator short circuits) occur over months or years of continuous duty. To demonstrate the detection and prescriptive capabilities of the digital twin during a 5-to-8-minute presentation, the application provides a **Dynamic Anomaly Injection Engine**.

```
[User Selects Fault in Dropdown] ──▶ POST /api/anomaly/inject
                                              │
                                              ▼
[DataManager.injected_anomaly set] ──▶ Modifies live telemetry frame in memory
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
      [PhysicsTwinEngine Divergence]                     [DiagnosticAIEngine Loss]
      - Nominal vs Measured residual Δ spikes            - Autoencoder reconstruction MSE breaches τ
      - Component stress attribution updates             - Multi-head self-attention isolates channel
                    │                                                  │
                    └─────────────────────────┬────────────────────────┘
                                              ▼
                               [PrognosticEngine Degradation]
                               - Health Index drops (e.g. 0.98 -> 0.38)
                               - Operational Zone transitions to Alarm/Critical
                               - Paris-Erdogan RUL curve plunges
                                              │
                                              ▼
                               [PrescriptiveEngine Intervention]
                               - Tri-factor logistics deficit identified
                               - Emergency derating alert banner appears
                               - Work-order ticket generated
```

---

## 2. Documented Fault Scenarios & Internal Implementation

The dashboard provides a dedicated dropdown selector (`#anomalySelect`) located in the global stream control bar.

### Scenario 1: Normal (Nominal Run)
- **Dropdown Value:** `none`
- **Internal Behavior:** `data_mgr.injected_anomaly = None`. No modifications are applied to the active dataset row.
- **Observed Physical Parameters:**
  - Radial Vibration: $\approx 0.85\text{ mm/s RMS}$
  - Axial Vibration: $\approx 0.45\text{ mm/s RMS}$
  - Temperature: $41.0 - 43.0^\circ\text{C}$
  - Phase Current: $\approx 8.50\text{ A}$
  - Discharge Pressure: $\approx 4.20\text{ bar}$
  - Rotational Speed: $1440.0\text{ RPM}$
- **System Response:**
  - Physics Discrepancy Norm $\Delta(t) \approx 0.08$ (Synchronized).
  - Autoencoder Reconstruction Loss $L_{rec} \approx 0.0210$ (well below $\tau = 0.1500$).
  - Health Index: $HI \approx 0.98$ (Normal Operation Zone).
  - Remaining Useful Life: $2400\text{ Operating Hours}$ (Nominal unconstrained life).
  - Digital Twin Viewer: All components glow soft green ($< 35\%$ stress).
  - VFD Derating Banner: Hidden.

---

### Scenario 2: Inner-Race Bearing Spalling (BPFI)
- **Dropdown Value:** `bearing_spall`
- **Internal Code Implementation:** [core/data_manager.py:L218-L221](file:///c:/Users/DELL/OneDrive/文档/dt/core/data_manager.py#L218-L221):
  ```python
  if self.injected_anomaly == "bearing_spall":
      row["vibration_radial"] = round(row.get("vibration_radial", 0.8) + 3.8, 3)
      row["temperature"] = round(row.get("temperature", 42.0) + 24.0, 2)
      row["acoustic_db"] = round(row.get("acoustic_db", 35.0) + 25.0, 1)
  ```
- **Physical Defect Meaning:** A subsurface fatigue spall or flaking pit has formed on the rotating inner raceway of the Drive-End bearing. As rolling elements pass over the defect, high-impact mechanical shock pulses are generated at the Ball Pass Frequency Inner Race:
  $$f_{BPFI} \approx 5.42 \times f_{rot} = 5.42 \times 24.0\text{ Hz} = 130.1\text{ Hz}$$
- **Observed Physical Parameter Changes:**
  - **Radial Vibration:** Jumps from $0.85\text{ mm/s}$ to **$4.65\text{ mm/s RMS}$** (Breaches ISO 10816 Alarm of $2.8\text{ mm/s}$).
  - **Temperature:** Rises from $42^\circ\text{C}$ to **$66.0^\circ\text{C}$** due to localized rolling friction.
  - **Acoustic Emission:** Increases from $35\text{ dB}$ to **$60.0\text{ dB}$**.
- **Diagnostic Rules Triggered:**
  - In [app.py:L99-L103](file:///c:/Users/DELL/OneDrive/文档/dt/app.py#L99-L103), the synthesized waveform injects high-frequency BPFI harmonic energy ($amp_{bpfi} = (vib_{rms} - 1.5) \times 0.4 \approx 1.26\text{ mm/s}$).
  - In [core/ai_engine.py:L161-L167](file:///c:/Users/DELL/OneDrive/文档/dt/core/ai_engine.py#L161-L167):
    `if amp_bpfi > 0.15 or (kurtosis > 5.0 and raw_vec[0] > 2.5)`
    Triggers specific fault: **"Inner-Race Bearing Spalling (BPFI)"**.
  - Attribution Engine: Radial Vibration ($48\%$) and Acoustic ($24\%$) dominate the attention attribution bar chart.
- **Prognostic & Prescriptive Changes:**
  - Health Index plunges to **$HI \approx 0.38$** (**Maintenance Alarm Zone**).
  - RUL forecast collapses from $2400\text{ h}$ down to **$\approx 45.0\text{ Operating Hours}$**.
  - Prescriptive engine detects **Critical Lead-Time Deficit**: $t_{RUL} (45\text{ h}) \le t_{lead} (72\text{ h}) + t_{staff} (8\text{ h}) = 80\text{ h}$.
  - **Closed-Loop VFD Derating Alert Banner pops up in Red**, urging speed throttling.
  - Digital Twin Viewer: Drive-End bearing turns **bright pulsing red ($> 75\%$ stress)**.

---

### Scenario 3: Dynamic Rotor Unbalance (1X Harmonic)
- **Dropdown Value:** `unbalance`
- **Internal Code Implementation:** [core/data_manager.py:L222-L224](file:///c:/Users/DELL/OneDrive/文档/dt/core/data_manager.py#L222-L224):
  ```python
  elif self.injected_anomaly == "unbalance":
      row["vibration_radial"] = round(row.get("vibration_radial", 0.8) + 2.5, 3)
      row["vibration_axial"] = round(row.get("vibration_axial", 0.4) + 1.2, 3)
  ```
- **Physical Defect Meaning:** Non-uniform mass distribution on the motor rotor or pump impeller (e.g., uneven particulate buildup, missing balance weight, or broken vane). Produces a pure radial centrifugal force rotating synchronously at shaft speed ($1X = 24.0\text{ Hz}$).
- **Observed Physical Parameter Changes:**
  - **Radial Vibration:** Increases from $0.85\text{ mm/s}$ to **$3.35\text{ mm/s RMS}$**.
  - **Axial Vibration:** Increases from $0.45\text{ mm/s}$ to **$1.65\text{ mm/s RMS}$**.
  - **Temperature:** Remains normal ($\approx 42^\circ\text{C}$).
- **Diagnostic Rules Triggered:**
  - In [core/ai_engine.py:L186-L192](file:///c:/Users/DELL/OneDrive/文档/dt/core/ai_engine.py#L186-L192):
    `if amp_1x > 1.8 and amp_2x < 0.4 * amp_1x`
    Triggers specific fault: **"Dynamic Rotor Unbalance"**.
  - FFT power spectrum displays a massive single peak at **$24.0\text{ Hz}$ (1X)** with no elevated defect frequencies.
  - Sub-assembly stress: Shaft & Coupling stress jumps to $> 60\%$ (Amber).
- **Prognostic & Prescriptive Changes:**
  - Health Index drops to **$HI \approx 0.62$** (**Warning Stage**).
  - RUL forecast decreases to $\approx 310\text{ Operating Hours}$.
  - Because $310\text{ h} > 80\text{ h}$, no emergency derating is required; the prescriptive engine issues a **Proactive Dynamic Balancing Work-Order**.

---

### Scenario 4: Stator Thermal Overload
- **Dropdown Value:** `thermal_overload`
- **Internal Code Implementation:** [core/data_manager.py:L225-L227](file:///c:/Users/DELL/OneDrive/文档/dt/core/data_manager.py#L225-L227):
  ```python
  elif self.injected_anomaly == "thermal_overload":
      row["temperature"] = round(row.get("temperature", 42.0) + 40.0, 2)
      row["current"] = round(row.get("current", 8.5) + 4.5, 2)
  ```
- **Physical Defect Meaning:** Blocked cooling fan shroud, high ambient temperature, or severe supply phase voltage unbalance causing excessive $I^2 R$ copper ohmic loss in the stator windings.
- **Observed Physical Parameter Changes:**
  - **Temperature:** Soars from $42^\circ\text{C}$ to **$82.0^\circ\text{C}$** (Breaches rated Class F insulation limit of $75.0^\circ\text{C}$).
  - **Phase Current:** Rises from $8.5\text{ A}$ to **$13.0\text{ A}$** (Exceeds full-load rated current of $11.2\text{ A}$).
  - **Vibration:** Stays relatively normal ($\approx 0.85\text{ mm/s}$).
- **Diagnostic Rules Triggered:**
  - In [core/ai_engine.py:L195-L201](file:///c:/Users/DELL/OneDrive/文档/dt/core/ai_engine.py#L195-L201):
    `if temp_val > 78.0`
    Triggers specific fault: **"Stator Winding Thermal Overload"**.
  - Multi-head self-attention attribution shows **Temperature ($68\%$)** and **Current ($22\%$)** as the overwhelming root causes.
  - Sub-assembly stress: Stator Winding stress turns red ($> 70\%$).
- **Prognostic & Prescriptive Changes:**
  - Health Index drops to **$HI \approx 0.44$** (**Maintenance Alarm Zone**).
  - Prescriptive engine prescribes fan airflow inspection and electrical phase balancing.

---

## 3. Comparison Table: Normal vs. Fault Scenarios

| Operational State | Radial Vib ($v_{rad}$) | Axial Vib ($v_{ax}$) | Temp ($T$) | Current ($I$) | Discrepancy ($\Delta$) | Autoencoder Loss ($L_{rec}$) | Health Index ($HI$) | Operational Zone | Forecasted RUL | Primary Prescriptive Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal Baseline** | 0.85 mm/s | 0.45 mm/s | 42.0 °C | 8.50 A | 0.080 | 0.0210 | **0.98** | Normal (Green) | 2400 h | Routine monitoring; quarterly check |
| **Bearing Spall (BPFI)**| 4.65 mm/s | 0.45 mm/s | 66.0 °C | 8.50 A | 1.450 | 0.2850 | **0.38** | Alarm (Orange) | 45 h | **Emergency VFD Derating (-20%)** |
| **Rotor Unbalance** | 3.35 mm/s | 1.65 mm/s | 42.0 °C | 8.50 A | 0.920 | 0.1450 | **0.62** | Warning (Amber) | 310 h | Dynamic balancing at next shift |
| **Thermal Overload**| 0.85 mm/s | 0.45 mm/s | 82.0 °C | 13.00 A | 1.280 | 0.2100 | **0.44** | Alarm (Orange) | 78 h | Fan inspection & VFD derating |

---

## 4. How the Fault Detection Model Executes Internally

The application runs a **hybrid physics-data diagnostic decision tree**:

```
[Incoming Telemetry Vector]
           │
           ├─▶ Physics Discrepancy: Δ(t) = || y_obs - y_sim ||_2
           │
           ├─▶ Autoencoder: L_rec(t) = MSE(x_norm, x̂_norm)
           │
           ▼
[Evaluate Condition Severity Level]
   ├── If L_rec < 0.1500 and Δ < 0.60 ──▶ "Normal" (Confidence 98%)
   ├── If L_rec < 0.3000 and Δ < 1.10 ──▶ "Warning" (Confidence 94%)
   ├── If L_rec < 0.6000 and Δ < 1.80 ──▶ "Anomaly Detected" (Confidence 96%)
   └── Else                             ──▶ "Critical Condition" (Confidence 99%)
           │
           ▼
[Spectral & Attribution Feature Analysis]
   ├── Check BPFI Peak (> 0.15 mm/s) or (Kurtosis > 5.0 and Vib > 2.5)
   │     └── Yes ──▶ Classify: "Inner-Race Bearing Spalling (BPFI)"
   ├── Check BPFO Peak (> 0.15 mm/s)
   │     └── Yes ──▶ Classify: "Outer-Race Bearing Flaking (BPFO)"
   ├── Check 2X Harmonic (> 0.6 * 1X and > 0.4 mm/s)
   │     └── Yes ──▶ Classify: "Dynamic Shaft Misalignment"
   ├── Check 1X Harmonic (> 1.8 mm/s and 2X < 0.4 * 1X)
   │     └── Yes ──▶ Classify: "Dynamic Rotor Unbalance"
   └── Check Temperature (> 78.0 °C)
         └── Yes ──▶ Classify: "Stator Winding Thermal Overload"
```

---

## 5. How to Reset the System Afterward

To restore the system to pristine nominal baseline:
1. In the global stream control bar, click the **Reset Demo** button (teal button).
2. Or change the **Simulate Fault** dropdown back to **Normal (Nominal Run)**.
3. Behind the scenes:
   - Dispatches `POST /api/demo/reset`.
   - Clears `data_mgr.injected_anomaly = None`.
   - Resets VFD derating state to inactive (100% speed setpoint).
   - Rewinds the dataset playback index to frame 0.
   - Clears all rolling history buffers in the browser.
   - The master health pill instantly returns to green: `Pristine (HI: 0.98)`.
