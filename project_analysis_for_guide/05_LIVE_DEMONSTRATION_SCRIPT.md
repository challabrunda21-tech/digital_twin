# 05. Step-by-Step Live Demonstration Script

**Project Title:** AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance  
**Academic Context:** Demonstration Guide for Faculty Guide Review (Mrs. Prasanna Pabba)  
**Target Duration:** 5 to 7 Minutes  
**Demonstration URL:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
**Preparation Checklist:**
- Open terminal and run: `python run.py` (or `python -m uvicorn app:app --port 8000`).
- Open Google Chrome or Edge at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
- Maximize the browser window ($F11$ or full-screen).
- Ensure the streaming bar shows `Normal (Nominal Run)` and the master pill shows `Pristine (HI: 0.98)`.

---

## 1. Demonstration Timeline Overview

| Section | Target Time | Focus Area | Key Visuals Demonstrated |
| :--- | :--- | :--- | :--- |
| **Part 1: Introduction** | 0:00 – 0:45 | Motivation & Problem Statement | Header, Title, Patent Badge |
| **Part 2: Dashboard Overview** | 0:45 – 1:45 | Overview KPIs & Dual-Axis History | 8 KPI Cards, Dual-Axis Canvas Chart |
| **Part 3: Digital Twin Monitor** | 1:45 – 3:00 | Cyber-Physical Shadow & Heatmaps | SVG Schematic, Rotation, Discrepancy Table, Stress Bars |
| **Part 4: Live Sensor Analytics**| 3:00 – 4:00 | Frequency & Wavelet Analytics | FFT Power Spectrum, 1X & BPFI Harmonics, Multi-Domain Table |
| **Part 5: Fault Injection & AI** | 4:00 – 5:15 | Anomaly Detection & Explainable AI | Inject `bearing_spall`, Autoencoder Loss, Attention Attribution |
| **Part 6: Predictive Maintenance**| 5:15 – 6:15 | RUL Forecast & Closed-Loop Derate | Bayesian RUL Curve, Red Alert Banner, Dispatch VFD Derating |
| **Part 7: Conclusion & Reset** | 6:15 – 7:00 | Academic Summary & Clean Reset | Click Reset Demo, Q&A Handover |

---

## 2. Step-by-Step Script: ACTION vs. SPEAK

### Part 1: Project Introduction (0:00 – 0:45)

| ACTION (What to Click / Point To) | SPEAK (Exact Words to Say) |
| :--- | :--- |
| Stand beside your laptop. Look at your guide.<br>Point to the browser title bar: **Digital Twin \| Industrial Equipment Intelligence**.<br>Point to the sidebar footer: **VNR VJIET \| Patent Form 2** badge. | *"Respected Guide, good morning. Today, I am demonstrating our project: **'AI-Based Digital Twin for Industrial Equipment Monitoring and Predictive Maintenance'**.*<br><br>*In continuous manufacturing plants, unplanned equipment breakdown costs thousands of dollars per hour. Traditional maintenance is either reactive—waiting for machines to fail—or time-based, replacing healthy parts needlessly.*<br><br>*Our solution builds a **cyber-physical digital twin** for critical rotating machinery. It compares real-time sensor streams against a physics-informed shadow model, uses an AI autoencoder to detect micro-wear, forecasts Remaining Useful Life, and provides closed-loop speed derating to prevent catastrophic failure."* |

---

### Part 2: Overview Dashboard & Key Metrics (0:45 – 1:45)

| ACTION (What to Click / Point To) | SPEAK (Exact Words to Say) |
| :--- | :--- |
| Ensure you are on the **Overview Dashboard** (`#nav-overview`).<br><br>Hover your mouse over the top **8 KPI cards**: point to **Health Index**, **Vibration**, **Temperature**, and **Physics Discrepancy**.<br><br>Scroll down slightly to show the **Dual-Axis Sensor Timeline Chart**. | *"We are currently looking at the Overview Dashboard for our target asset: a **5.5 kW Induction Motor coupled to a Centrifugal Pump** operating at a nominal speed of 1440 RPM.*<br><br>*Across the top, the system tracks 8 Key Performance Indicators in real time. Right now, our machine is in its nominal baseline condition. The Health Index is 0.98, radial vibration is 0.85 mm/s, well within the ISO 10816 limit of 2.8 mm/s, and temperature is steady at 42°C.*<br><br>*Down here, our custom HTML5 Canvas chart renders a dual-axis rolling history of vibration velocity in blue alongside bearing temperature in amber, providing instant situational awareness."* |

---

### Part 3: Digital Twin Monitor — Cyber-Physical Shadow (1:45 – 3:00)

| ACTION (What to Click / Point To) | SPEAK (Exact Words to Say) |
| :--- | :--- |
| Click **Digital Twin Monitor** in the left sidebar (`#nav-twin`).<br><br>Point to the **animated rotating shaft and pump impeller** in the center schematic.<br><br>Point to the **soft green glow circles** on the Drive-End bearing and stator.<br><br>Click directly on the **Drive-End (DE) Bearing** housing in the SVG schematic.<br><br>Show the right-side **Discrepancy Table** and **Sub-Assembly Stress Bars**. | *"This is our signature feature: the **Digital Twin Monitor**.*<br><br>*Rather than just plotting numbers, our platform maintains a mathematical cyber-physical shadow model. In the center viewport, you can see our technical vector schematic showing the 5.5 kW motor, the bearings, the flexible coupling, and the centrifugal pump.*<br><br>*Notice that the shaft and impeller rotate dynamically in real time, proportional to measured shaft RPM. The radial gradient glows represent localized stress.*<br><br>*When I click on the Drive-End Bearing, the inspection card immediately opens, showing a healthy stress level of 12% and adequate lubricant condition.*<br><br>*On the right panel, our system actively compares measured physical telemetry against our first-principles physics equations. Currently, the discrepancy norm is only 0.08, meaning the physical asset is fully synchronized with its digital twin."* |

---

### Part 4: Live Sensor Analytics & Harmonics (3:00 – 4:00)

| ACTION (What to Click / Point To) | SPEAK (Exact Words to Say) |
| :--- | :--- |
| Click **Live Sensor Analytics** in the left sidebar (`#nav-analytics`).<br><br>Point to the **FFT Power Spectrum** canvas chart.<br><br>Point to the **1X marker at 24.0 Hz**.<br><br>Point to the **Multi-Domain Feature Table** on the right. | *"Here in the Live Sensor Analytics view, we perform high-speed edge feature extraction across three domains: time, frequency, and wavelets.*<br><br>*On the left, our Fast Fourier Transform spectrum decomposes the vibration signal into frequency harmonics. The blue marker at 24 Hz represents the 1X rotational fundamental frequency for our 1440 RPM motor. We also track defect markers: BPFO at 86 Hz and BPFI at 130 Hz.*<br><br>*On the right, our edge pipeline calculates statistical indicators like Crest Factor and Kurtosis. Kurtosis is currently 3.05, perfectly conforming to a normal Gaussian baseline."* |

---

### Part 5: Fault Injection & AI Explainability (4:00 – 5:15)

| ACTION (What to Click / Point To) | SPEAK (Exact Words to Say) |
| :--- | :--- |
| In the top stream control bar, click the **Simulate Fault** dropdown.<br>Select **Inner-Race Bearing Spall (BPFI)**.<br><br>Point to the top master health pill turning **Orange/Red** (`Warning` or `Critical`).<br><br>Click **Fault Detection** in the left sidebar (`#nav-faults`).<br><br>Point to the **Autoencoder Reconstruction Loss** card.<br><br>Point to the **Multi-Head Self-Attention Attribution Bar Chart**. | *"Now, let us demonstrate how the AI engine detects an internal mechanical breakdown. I will simulate a classic industrial failure: **Inner-Race Bearing Spalling**.*<br><br>*Watch what happens immediately: The master health status pill turns orange, indicating an active alarm!*<br><br>*Under the Fault Detection view, our temporal autoencoder detects that incoming sensor patterns no longer fit the healthy baseline. Reconstruction loss has spiked from 0.02 to 0.28, completely breaching our adaptive threshold of 0.15.*<br><br>*Crucially, we do not treat AI as a black box. On the right, our **Multi-Head Self-Attention Attribution chart** reveals that Radial Vibration contributes 48% and Acoustic emission contributes 24% to this anomaly, proving that the fault originates mechanically in the bearing assembly."* |

---

### Part 6: Predictive Maintenance & Closed-Loop VFD Derating (5:15 – 6:15)

| ACTION (What to Click / Point To) | SPEAK (Exact Words to Say) |
| :--- | :--- |
| Click **Predictive Maintenance (RUL)** in the left sidebar (`#nav-prognostics`).<br><br>Point to the **Health Index (0.38)** and **Remaining Useful Life (45 Operating Hours)**.<br><br>Point to the **95% Bayesian Confidence Funnel** on the chart.<br><br>Point to the **Red Closed-Loop VFD Derating Alert Banner** at the top of the screen.<br><br>Click the red button: **Dispatch VFD Derating (20%)**. | *"Next, let us examine the prognostics. Our Health Index has degraded to 0.38, placing the equipment in the Maintenance Alarm Zone.*<br><br>*Our Paris-Erdogan degradation model extrapolates the wear curve down to the critical 0.20 threshold. Through 100 stochastic Monte Carlo dropout passes, it forecasts a Remaining Useful Life of only **45 operating hours**, with a 95% Bayesian confidence interval between 38 and 52 hours.*<br><br>*Now observe our prescriptive logic: In an industrial plant, replacement bearings take 72 hours to ship, plus 8 hours for technician prep—a total of 80 hours! Our asset will fail in 45 hours, meaning **it will suffer catastrophic seizure before the replacement part arrives!***<br><br>*Notice this prominent red alert banner. Our system prescribes **Patent Claim 8: Closed-Loop Operational Derating**.*<br><br>*I will click 'Dispatch VFD Derating (20%)'.*<br><br>*Instantly, the system commands the simulated drive to throttle speed to 80% (1152 RPM). Vibration drops immediately, fatigue kinetics decelerate by over 3 times, and RUL is extended beyond the 80-hour parts arrival window, successfully saving the physical machine!"* |

---

### Part 7: Clean Reset & Conclusion (6:15 – 7:00)

| ACTION (What to Click / Point To) | SPEAK (Exact Words to Say) |
| :--- | :--- |
| In the top stream control bar, click the teal **Reset Demo** button.<br><br>Observe the health pill return to green: `Pristine (HI: 0.98)`.<br><br>Click **Overview Dashboard** (`#nav-overview`) to show the pristine state restored.<br><br>Smile and turn to your guide. | *"Finally, when maintenance is complete, I click the teal 'Reset Demo' button.*<br><br>*The derating is disengaged, baseline telemetry is restored, and the Health Index returns to a pristine 0.98.*<br><br>*In summary, we have built a complete, end-to-end cyber-physical digital twin platform that bridges physical state-space modeling, explainable deep learning, probabilistic RUL forecasting, and autonomous closed-loop maintenance control.*<br><br>*Thank you, Ma'am. I am now ready to answer any questions about our source code, mathematics, or system architecture."* |

---

## 3. Backup Demonstration Plan (Contingency Procedures)

In live academic presentations, unexpected issues (network dropouts, accidental port conflicts, browser caching) can occur. Use this battle-tested backup plan:

| Scenario / Failure | Immediate Symptoms | Exact Troubleshooting Action | Verbal Recovery Line to Faculty |
| :--- | :--- | :--- | :--- |
| **Server is not running / Connection Refused** | Browser shows `This site can't be reached` or `ERR_CONNECTION_REFUSED`. | Open PowerShell in project directory and execute:<br>`python run.py --port 8000`<br>Refresh browser. | *"The local ASGI server is initializing its sensor cache. It is now bound to port 8000."* |
| **Port 8000 is occupied by another app** | Terminal logs `[Errno 10048] address already in use`. | Run on alternative port:<br>`python run.py --port 8080`<br>Open `http://127.0.0.1:8080/`. | *"Port 8000 was held by a system service; our ASGI architecture effortlessly re-binds to port 8080."* |
| **Browser charts look blank or distorted** | Canvas elements render small or don't redraw on tab switch. | Simply switch tabs in the sidebar (e.g. click **Digital Twin** and click back to **Overview**). `app.js:L90-L92` automatically triggers `refreshVisibleCharts()`. | *"The charts automatically adjust their canvas scaling dynamically when switching between operational views."* |
| **Anomaly selection does not clear** | Injected anomaly keeps running after selecting Normal. | Click the teal **Reset Demo** button directly. It dispatches a master reset to `/api/demo/reset`, clearing backend anomaly flags and rewinding the CSV index. | *"The master Reset Demo endpoint restores our initial nominal baseline state."* |
| **Faculty asks to see custom data upload** | Guide asks: *"Can this system work on our lab data?"* | Open **Data Management** (`#nav-settings`). Drag and drop `datasets/ims_bearing_degradation.csv` into the upload zone. The schema validator will verify and load it in 1 second. | *"Yes Ma'am, our data management module accepts custom CSV streams and validates headers and physical bounds."* |
