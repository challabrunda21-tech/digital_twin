/**
 * Main Application Controller & State Orchestrator
 * Connects the 8 application views with live telemetry, AI diagnostics,
 * Digital Twin synchronization, and prescriptive action dispatchers.
 */

class IndustrialTwinApp {
  constructor() {
    this.activeView = "overview";
    this.pollInterval = 1000;
    this.timerId = null;
    this.isStreaming = true;

    this.historyBuffer = [];
    this.discHistoryBuffer = [];
    this.maxBufferLen = 60;

    this.twinViewer = null;
    this.timelineChart = null;
    this.fftChart = null;
    this.attentionChart = null;
    this.rulChart = null;
    this.discChart = null;

    this.latestPayload = null;
    this.isPolling = false;
    this.historyFilterText = "";
    this.selectedComponent = "Drive-End (DE) Bearing";

    this.init();
  }

  // ─── INITIALIZATION ────────────────────────────────────────────────
  async init() {
    this.initNavigation();
    this.initCharts();
    this.initTwinViewer();
    this.initControls();
    this.initUploadDropzone();

    await this.fetchMachines();
    await this.fetchBundledDatasets();
    await this.fetchWorkOrders();
    await this.fetchInitialHistory();
    await this.pollLiveData();

    this.startPolling();
  }

  initNavigation() {
    document.querySelectorAll(".nav-item").forEach(item => {
      item.addEventListener("click", () => this.switchView(item.getAttribute("data-view")));
    });
    const menuBtn = document.getElementById("mobileMenuBtn");
    const sidebar = document.getElementById("sidebar");
    if (menuBtn && sidebar) {
      menuBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
    }
  }

  switchView(viewName) {
    this.activeView = viewName;
    document.querySelectorAll(".nav-item").forEach(item => {
      item.classList.toggle("active", item.getAttribute("data-view") === viewName);
    });
    document.querySelectorAll(".page-view").forEach(page => {
      page.classList.toggle("active", page.id === `view-${viewName}`);
    });
    const sidebar = document.getElementById("sidebar");
    if (sidebar) sidebar.classList.remove("open");
    if (viewName === "settings") this.fetchBundledDatasets();
    setTimeout(() => this.refreshVisibleCharts(), 50);
  }

  initCharts() {
    this.timelineChart = new SensorTimelineChart("chartSensorTimeline");
    this.fftChart = new FFTSpectrumChart("chartFFTSpectrum");
    this.attentionChart = new AttentionAttributionChart("chartAttentionAttribution");
    this.rulChart = new RULDegradationChart("chartRULDegradation");
    this.discChart = new DiscrepancyTimelineChart("chartDiscrepancyNorm");
  }

  initTwinViewer() {
    this.twinViewer = new DigitalTwinViewer("twinViewportContainer", (compName) => {
      this.showComponentDetails(compName);
    });
  }

  // ─── CONTROLS ──────────────────────────────────────────────────────
  initControls() {
    // Machine selector
    const selector = document.getElementById("machineSelect");
    if (selector) selector.addEventListener("change", (e) => this.selectMachine(e.target.value));

    // Play / Pause
    const btnPlayPause = document.getElementById("btnPlayPause");
    if (btnPlayPause) {
      btnPlayPause.addEventListener("click", async () => {
        const action = this.isStreaming ? "pause" : "play";
        await this.controlStreaming(action);
      });
    }

    // Playback Speed
    const btnSpeed = document.getElementById("btnPlaybackSpeed");
    if (btnSpeed) {
      btnSpeed.addEventListener("click", async () => {
        const cur = parseFloat(btnSpeed.getAttribute("data-speed") || "1.0");
        const next = cur === 1.0 ? 2.0 : cur === 2.0 ? 5.0 : 1.0;
        btnSpeed.setAttribute("data-speed", next);
        btnSpeed.textContent = `${next}x`;
        await this.controlStreaming("speed", { speed: next });
      });
    }

    // Reset Demo
    const btnReset = document.getElementById("btnResetDemo");
    if (btnReset) btnReset.addEventListener("click", () => this.resetDemo());

    // Anomaly Injection
    const anomalySel = document.getElementById("anomalySelect");
    if (anomalySel) {
      anomalySel.addEventListener("change", (e) => {
        this.injectAnomaly(e.target.value === "none" ? null : e.target.value);
      });
    }

    // VFD Derating — Header Banner
    const btnDerate = document.getElementById("btnDispatchDerate");
    if (btnDerate) {
      btnDerate.addEventListener("click", async () => {
        const isActive = btnDerate.getAttribute("data-active") === "true";
        await this.toggleVfdDerating(!isActive);
      });
    }

    // VFD Derating — View 6 dedicated controls
    const btnV6Engage = document.getElementById("btnView6EngageDerate");
    const btnV6Disengage = document.getElementById("btnView6DisengageDerate");
    const vfdPctSel = document.getElementById("vfdDeratePctSelect");
    const vfdTargetText = document.getElementById("vfdTargetSpeedText");

    if (vfdPctSel && vfdTargetText) {
      vfdPctSel.addEventListener("change", (e) => {
        const pct = parseFloat(e.target.value || "20");
        const target = 100 - pct;
        const rpm = Math.round(1440 * (target / 100));
        const hz = (50 * (target / 100)).toFixed(1);
        vfdTargetText.textContent = `${target}% (${rpm} RPM / ${hz} Hz)`;
      });
    }
    if (btnV6Engage) {
      btnV6Engage.addEventListener("click", () => {
        const pct = parseFloat(vfdPctSel ? vfdPctSel.value : "20");
        this.toggleVfdDerating(true, pct);
      });
    }
    if (btnV6Disengage) {
      btnV6Disengage.addEventListener("click", () => this.toggleVfdDerating(false));
    }

    // View 7 History Filter
    const searchInput = document.getElementById("historySearchInput");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.historyFilterText = e.target.value.toLowerCase().trim();
        this.renderHistoryTable(this.historyBuffer);
      });
    }

    // CMMS Ticket Modal
    const btnOpenTicket = document.getElementById("btnOpenCreateTicket");
    const modalTicket = document.getElementById("modalCreateTicket");
    const btnCloseModal = document.getElementById("btnCloseModalTicket");
    const formTicket = document.getElementById("formCreateTicket");

    if (btnOpenTicket && modalTicket) btnOpenTicket.addEventListener("click", () => modalTicket.classList.add("active"));
    if (btnCloseModal && modalTicket) btnCloseModal.addEventListener("click", () => modalTicket.classList.remove("active"));
    if (formTicket && modalTicket) {
      formTicket.addEventListener("submit", async (e) => {
        e.preventDefault();
        const comp = document.getElementById("ticketComponent").value;
        const priority = document.getElementById("ticketPriority").value;
        const action = document.getElementById("ticketAction").value;
        const notes = document.getElementById("ticketNotes").value;
        await this.createWorkOrder(comp, priority, action, notes);
        modalTicket.classList.remove("active");
        formTicket.reset();
      });
    }

    // Export buttons
    const btnExpCsv = document.getElementById("btnExportCsv");
    if (btnExpCsv) btnExpCsv.addEventListener("click", () => { window.location.href = "/api/export/csv"; });
    const btnExpJson = document.getElementById("btnExportJson");
    if (btnExpJson) btnExpJson.addEventListener("click", () => { window.location.href = "/api/export/json"; });
  }

  // ─── UPLOAD DROPZONE ───────────────────────────────────────────────
  initUploadDropzone() {
    const dropzone = document.getElementById("uploadDropzone");
    const fileInput = document.getElementById("csvFileInput");
    if (!dropzone || !fileInput) return;

    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", async (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) await this.uploadFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener("change", async (e) => {
      if (e.target.files.length > 0) await this.uploadFile(e.target.files[0]);
    });
  }

  async uploadFile(file) {
    const statusBox = document.getElementById("uploadStatusMessage");
    if (statusBox) {
      statusBox.style.display = "block";
      statusBox.className = "status-banner info";
      statusBox.innerHTML = `<strong>Validating & Ingesting:</strong> ${file.name}...`;
    }
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok && data.valid) {
        if (statusBox) { statusBox.className = "status-banner success"; statusBox.innerHTML = `<strong>Success:</strong> ${data.message} (${data.row_count} rows ingested).`; }
        this.showToast(`Dataset '${file.name}' loaded!`, "success");
        this.historyBuffer = [];
        this.discHistoryBuffer = [];
        await this.fetchBundledDatasets();
        await this.pollLiveData();
      } else {
        if (statusBox) { statusBox.className = "status-banner error"; statusBox.innerHTML = `<strong>Error:</strong> ${data.error || "Rejected."}`; }
        this.showToast(data.error || "Validation failed", "error");
      }
    } catch (err) {
      if (statusBox) { statusBox.className = "status-banner error"; statusBox.innerHTML = `<strong>Upload Failed:</strong> ${err.message}`; }
      this.showToast(`Upload failed: ${err.message}`, "error");
    }
  }

  // ─── API CALLS ─────────────────────────────────────────────────────
  async fetchMachines() {
    try {
      const res = await fetch("/api/machines");
      const data = await res.json();
      const selector = document.getElementById("machineSelect");
      if (selector && data.machines) {
        selector.innerHTML = "";
        data.machines.forEach(m => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `${m.name} (${m.id})`;
          if (m.id === data.active_machine_id) opt.selected = true;
          selector.appendChild(opt);
        });
      }
    } catch (e) { console.error("Error fetching machines:", e); }
  }

  async selectMachine(machineId) {
    try {
      const res = await fetch("/api/machine/select", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ machine_id: machineId }) });
      const data = await res.json();
      if (data.success) {
        this.showToast(`Switched to: ${data.machine.name}`, "info");
        this.historyBuffer = [];
        this.discHistoryBuffer = [];
        await this.pollLiveData();
      }
    } catch (e) { this.showToast(`Failed: ${e.message}`, "error"); }
  }

  async controlStreaming(action, params = {}) {
    try {
      const res = await fetch("/api/streaming/control", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, ...params }) });
      const data = await res.json();
      if (data.success) {
        this.isStreaming = data.is_streaming;
        const btn = document.getElementById("btnPlayPause");
        if (btn) {
          btn.innerHTML = this.isStreaming
            ? `<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Pause`
            : `<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg> Stream`;
        }
      }
    } catch (e) { console.error("Streaming control error:", e); }
  }

  async injectAnomaly(anomalyType) {
    try {
      const res = await fetch("/api/anomaly/inject", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ anomaly_type: anomalyType }) });
      const data = await res.json();
      if (data.success) this.showToast(data.message, anomalyType ? "warning" : "info");
    } catch (e) { this.showToast(`Anomaly injection failed: ${e.message}`, "error"); }
  }

  async toggleVfdDerating(enable, deratePct = 20.0) {
    try {
      const res = await fetch("/api/derate/dispatch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enable, derate_pct: deratePct }) });
      const data = await res.json();
      if (data.success) {
        this.showToast(data.message, enable ? "warning" : "info");
        await this.pollLiveData();
      }
    } catch (e) { this.showToast(`VFD error: ${e.message}`, "error"); }
  }

  async createWorkOrder(component, priority, action, notes) {
    try {
      const res = await fetch("/api/cmms/create", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ component, priority, action, notes }) });
      const data = await res.json();
      if (data.success) {
        this.showToast(`CMMS Ticket ${data.ticket.ticket_id} dispatched!`, "success");
        await this.fetchWorkOrders();
      }
    } catch (e) { this.showToast(`Work order failed: ${e.message}`, "error"); }
  }

  async fetchWorkOrders() {
    try {
      const res = await fetch("/api/cmms/list");
      const data = await res.json();
      this.renderWorkOrders(data.work_orders || []);
    } catch (e) { console.error("Error fetching work orders:", e); }
  }

  async fetchInitialHistory(limit = 100) {
    try {
      const res = await fetch(`/api/telemetry/history?limit=${limit}`);
      const data = await res.json();
      if (data.history && Array.isArray(data.history)) {
        this.historyBuffer = data.history.map(rec => ({
          ...rec,
          health_index: rec.health_index !== undefined ? rec.health_index : 1.0,
          operational_status: rec.operational_status || "Nominal"
        }));
        this.renderHistoryTable(this.historyBuffer);
      }
    } catch (e) { console.error("Error fetching initial history:", e); }
  }

  async fetchBundledDatasets() {
    try {
      const res = await fetch("/api/datasets");
      const data = await res.json();
      const container = document.getElementById("bundledDatasetsContainer");
      if (!container || !data.datasets) return;
      container.innerHTML = "";
      data.datasets.forEach(ds => {
        const card = document.createElement("div");
        card.style.cssText = `background:${ds.is_active ? "#EFF6FF" : "#F8FAFC"}; border:${ds.is_active ? "2px solid #2563EB" : "1px solid #E2E8F0"}; border-radius:8px; padding:14px; display:flex; flex-direction:column; justify-content:space-between;`;
        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <strong style="font-size:13px; color:#172033;">${ds.name}</strong>
              ${ds.is_active ? `<span class="badge-tag" style="background:#2563EB; color:#fff;">Active</span>` : `<span class="badge-tag">${(ds.size_bytes / 1024).toFixed(0)} KB</span>`}
            </div>
            <p style="font-size:11px; color:#64748B; margin-bottom:8px;">${ds.description}</p>
            <div style="font-size:11px; color:#475569; margin-bottom:10px;">
              <strong>Rows:</strong> ${ds.row_count} &bull; <strong>Columns:</strong> ${ds.columns.length}
            </div>
          </div>
          <button class="btn ${ds.is_active ? 'btn-outline' : 'btn-primary'} btn-sm" style="width:100%;" ${ds.is_active ? 'disabled' : ''} onclick="window.app.loadDataset('${ds.filename}')">
            ${ds.is_active ? 'Currently Loaded' : 'Load Dataset'}
          </button>`;
        container.appendChild(card);
      });
    } catch (e) { console.error("Error fetching datasets:", e); }
  }

  async loadDataset(filename) {
    try {
      const res = await fetch("/api/dataset/select", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename }) });
      const data = await res.json();
      if (data.success) {
        this.showToast(`Switched to '${filename}' (${data.row_count} rows)`, "success");
        this.historyBuffer = [];
        this.discHistoryBuffer = [];
        await this.fetchBundledDatasets();
        await this.pollLiveData();
      } else {
        this.showToast(data.error || "Failed to load dataset", "error");
      }
    } catch (e) { this.showToast(`Failed: ${e.message}`, "error"); }
  }

  async resetDemo() {
    try {
      const res = await fetch("/api/demo/reset", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        this.historyBuffer = [];
        this.discHistoryBuffer = [];
        const anomalySel = document.getElementById("anomalySelect");
        if (anomalySel) anomalySel.value = "none";
        this.showToast("Demo reset to nominal baseline.", "success");
        await this.fetchMachines();
        await this.fetchBundledDatasets();
        await this.pollLiveData();
      }
    } catch (e) { this.showToast(`Reset error: ${e.message}`, "error"); }
  }

  // ─── LIVE POLLING ──────────────────────────────────────────────────
  startPolling() {
    this.timerId = setInterval(() => this.pollLiveData(), this.pollInterval);
  }

  async pollLiveData() {
    if (this.isPolling) return;
    this.isPolling = true;
    try {
      const res = await fetch("/api/telemetry/live");
      if (!res.ok) return;
      const data = await res.json();
      this.latestPayload = data;
      this.updateState(data);
    } catch (e) {
      console.warn("Polling error:", e);
    } finally {
      this.isPolling = false;
    }
  }

  // ─── STATE UPDATE (core rendering loop) ────────────────────────────
  updateState(data) {
    const tel = data.telemetry || {};
    const pt = data.physics_twin || {};
    const prog = data.prognostics || {};
    const diag = data.ai_diagnostics || {};
    const pres = data.prescriptive || {};
    const feats = data.signal_features || {};

    const hiVal = prog.health_index !== undefined ? prog.health_index : 1.0;
    const opStatus = diag.state || (hiVal >= 0.75 ? "Nominal" : hiVal >= 0.50 ? "Degraded" : "Critical");

    // ── History Buffers ──
    this.historyBuffer.push({ ...tel, health_index: hiVal, operational_status: opStatus });
    if (this.historyBuffer.length > this.maxBufferLen) this.historyBuffer.shift();
    this.discHistoryBuffer.push({ val: pt.discrepancy_norm || 0 });
    if (this.discHistoryBuffer.length > this.maxBufferLen) this.discHistoryBuffer.shift();

    // ── Header Health Pill ──
    const healthPill = document.getElementById("headerHealthPill");
    const healthPillText = document.getElementById("headerHealthText");
    const lastUpdate = document.getElementById("headerLastUpdate");

    if (healthPill && healthPillText) {
      healthPill.className = "health-pill";
      if (hiVal >= 0.75) { healthPill.classList.add("healthy"); healthPillText.textContent = `Pristine (HI: ${hiVal.toFixed(2)})`; }
      else if (hiVal >= 0.50) { healthPill.classList.add("warning"); healthPillText.textContent = `Warning (HI: ${hiVal.toFixed(2)})`; }
      else { healthPill.classList.add("critical"); healthPillText.textContent = `Critical (HI: ${hiVal.toFixed(2)})`; }
    }
    if (lastUpdate && tel.timestamp) lastUpdate.textContent = tel.timestamp;

    // ── Header Badges ──
    if (data.active_dataset) {
      this.setVal("headerActiveDatasetBadge", `Dataset: ${data.active_dataset}`);
      this.setVal("overviewActiveDataset", data.active_dataset);
      this.setVal("view8ActiveDatasetTag", `Active: ${data.active_dataset}`);
    }
    if (data.active_machine_name) this.setVal("overviewMachineName", data.active_machine_name);

    // ── KPI Cards ──
    this.setVal("kpiHealthIndex", prog.health_index !== undefined ? prog.health_index.toFixed(2) : "--");
    this.setVal("kpiVibration", tel.vibration_radial !== undefined ? tel.vibration_radial.toFixed(2) : "--");
    this.setVal("kpiTemperature", tel.temperature !== undefined ? tel.temperature.toFixed(1) : "--");
    this.setVal("kpiRPM", tel.speed_rpm !== undefined ? tel.speed_rpm.toFixed(0) : "--");
    this.setVal("kpiCurrent", tel.current !== undefined ? tel.current.toFixed(2) : "--");
    this.setVal("kpiPressure", tel.pressure !== undefined ? tel.pressure.toFixed(2) : "--");
    this.setVal("kpiRUL", prog.rul_hours !== undefined ? `${prog.rul_hours.toFixed(0)} h` : "--");
    this.setVal("kpiDiscrepancy", pt.discrepancy_norm !== undefined ? `Δ ${pt.discrepancy_norm.toFixed(3)}` : "--");

    // ── Health Zone ──
    const zone = prog.zone || (hiVal >= 0.75 ? "Normal" : hiVal >= 0.5 ? "Warning" : hiVal >= 0.2 ? "Alarm" : "Critical");
    this.setVal("kpiHealthZone", zone);

    // ── View 1: Alerts ──
    this.updateOverviewAlerts(diag, hiVal);

    // ── View 2: Digital Twin ──
    if (this.twinViewer) this.twinViewer.update(data);
    this.updateTwinInfoPanel(data);
    this.updateComponentDetailCard(this.selectedComponent, data);

    // ── View 3: Signal Features ──
    const td = feats.time_domain || {};
    const fd = feats.frequency_domain || {};
    const wd = feats.wavelet_dwt || {};
    this.setVal("featRms", td.rms !== undefined ? `${td.rms.toFixed(3)} mm/s` : "--");
    this.setVal("featP2p", td.peak_to_peak !== undefined ? `${td.peak_to_peak.toFixed(3)} mm/s` : "--");
    this.setVal("featCrest", td.crest_factor !== undefined ? td.crest_factor.toFixed(2) : "--");
    this.setVal("featKurtosis", td.kurtosis !== undefined ? td.kurtosis.toFixed(2) : "--");
    this.setVal("featSkewness", td.skewness !== undefined ? td.skewness.toFixed(3) : "--");
    this.setVal("featShapeFactor", td.shape_factor !== undefined ? td.shape_factor.toFixed(3) : "--");
    this.setVal("featCentroid", fd.spectral_centroid !== undefined ? `${fd.spectral_centroid.toFixed(1)} Hz` : "--");
    this.setVal("feat1x", fd.fundamental_1x_amp !== undefined ? `${fd.fundamental_1x_amp.toFixed(3)} mm/s` : "--");
    this.setVal("featBpfi", fd.bpfi_amp !== undefined ? `${fd.bpfi_amp.toFixed(3)} mm/s` : "--");
    if (wd.subband_energies && wd.subband_energies.length > 0) {
      this.setVal("featWavelet", `8 Bands (E₀: ${wd.subband_energies[0].toFixed(2)})`);
    } else {
      this.setVal("featWavelet", "8 Sub-Bands Active");
    }

    // ── View 4: Prognostics ──
    this.setVal("progHIValue", prog.health_index !== undefined ? prog.health_index.toFixed(2) : "--");
    let zoneDesc = "Asset operating in pristine condition.";
    if (hiVal < 0.20) zoneDesc = "Critical Stage: Immediate seizure risk. Automatic derate recommended.";
    else if (hiVal < 0.50) zoneDesc = "Maintenance Alarm: Work-order priority window reached.";
    else if (hiVal < 0.75) zoneDesc = "Warning Stage: Degradation kinetics active, RUL tracking.";
    this.setVal("progZoneDesc", zoneDesc);
    this.setVal("progRULDisplay", prog.rul_hours !== undefined ? `${prog.rul_hours.toFixed(0)} Operating Hours` : "--");
    if (prog.confidence_bounds) {
      this.setVal("progRULBounds", `${prog.confidence_bounds.lower_hours.toFixed(0)} h (Lower 5%) — ${prog.confidence_bounds.upper_hours.toFixed(0)} h (Upper 95%)`);
    }

    // ── View 5: Fault Detection ──
    this.updateFaultCards(diag);

    // ── View 6: Prescriptive ──
    this.updateDeratingBanner(pres);
    this.renderRecommendations(pres.recommendations || []);

    // ── View 7: History Table ──
    this.renderHistoryTable(this.historyBuffer);

    // ── Charts ──
    this.refreshVisibleCharts();
  }

  // ─── HELPER: set text content ──────────────────────────────────────
  setVal(elemId, text) {
    const el = document.getElementById(elemId);
    if (el) el.textContent = text;
  }

  // ─── VIEW 1: OVERVIEW ALERTS ──────────────────────────────────────
  updateOverviewAlerts(diag, hiVal) {
    const alertBadge = document.getElementById("overviewAlertBadge");
    const diagSummary = document.getElementById("overviewDiagSummary");
    const alertList = document.getElementById("overviewAlertList");
    if (!alertBadge || !diagSummary || !alertList) return;

    if (diag.state === "Normal" || !diag.is_anomaly) {
      alertBadge.style.background = "#ECFDF5"; alertBadge.style.color = "#065F46";
      alertBadge.textContent = "All Systems Nominal";
      diagSummary.textContent = "Physics shadow model conforms within ±0.08 Δ tolerance. Continuous HI is pristine.";
      alertList.innerHTML = `<li style="color:#059669;">● Normal baseline: All sensors within ISO 10816 standards.</li>`;
    } else {
      const isCrit = hiVal < 0.5 || diag.state === "Critical" || diag.state === "Alarm";
      alertBadge.style.background = isCrit ? "#FEE2E2" : "#FEF3C7";
      alertBadge.style.color = isCrit ? "#991B1B" : "#92400E";
      alertBadge.textContent = `${diag.state || "Anomaly"} - Action Required`;
      diagSummary.textContent = `${diag.fault_category || "Anomaly Detected"}: ${diag.explanation || "Reconstruction error exceeded threshold."}`;
      const faults = diag.specific_faults || [];
      if (faults.length > 0) {
        alertList.innerHTML = faults.map(f => `<li style="color:${isCrit ? '#B91C1C' : '#D97706'}; margin-bottom:4px;"><strong>[${f.component}]</strong> ${f.type} — ${f.evidence}</li>`).join("");
      } else {
        alertList.innerHTML = `<li style="color:#B91C1C;">● Anomaly score ${(diag.reconstruction_loss || 0).toFixed(4)} &gt; threshold ${(diag.adaptive_threshold || 0.15).toFixed(4)}</li>`;
      }
    }
  }

  // ─── VIEW 2: TWIN INFO PANEL ──────────────────────────────────────
  updateTwinInfoPanel(data) {
    const tel = data.telemetry || {};
    const pt = data.physics_twin || {};
    const sim = pt.simulated_nominal || {};
    const res = pt.residuals || {};
    const stresses = pt.component_stresses || {};

    this.setVal("dtMeasuredVib", `${(tel.vibration_radial || 0).toFixed(2)} mm/s`);
    this.setVal("dtNominalVib", `${(sim.vibration_rms || 0).toFixed(2)} mm/s`);
    this.setVal("dtDeltaVib", `${(res.delta_vibration_rms || 0).toFixed(2)} mm/s`);
    this.setVal("dtMeasuredTemp", `${(tel.temperature || 0).toFixed(1)} °C`);
    this.setVal("dtNominalTemp", `${(sim.temperature_c || 0).toFixed(1)} °C`);
    this.setVal("dtDeltaTemp", `${(res.delta_temperature_c || 0).toFixed(1)} °C`);
    this.setVal("dtMeasuredCurr", `${(tel.current || 0).toFixed(2)} A`);
    this.setVal("dtNominalCurr", `${(sim.current_a || 0).toFixed(2)} A`);
    this.setVal("dtDeltaCurr", `${(res.delta_current_a || 0).toFixed(2)} A`);
    this.setVal("dtDominantComponent", pt.dominant_stressed_component || "Drive-End Bearing");
    this.setVal("dtSyncStatus", pt.synchronization_status || "Synchronized");

    // Stress bars
    const container = document.getElementById("componentStressBars");
    if (container && stresses) {
      container.innerHTML = "";
      Object.entries(stresses).forEach(([comp, val]) => {
        const pct = Math.round(val * 100);
        let barColor = "#10B981";
        if (val > 0.65) barColor = "#EF4444";
        else if (val > 0.35) barColor = "#F59E0B";
        const row = document.createElement("div");
        row.className = "component-stress-row";
        row.innerHTML = `<span>${comp}</span><div style="display:flex;align-items:center;gap:8px;"><div class="stress-bar-wrap"><div class="stress-bar-fill" style="width:${pct}%;background:${barColor};"></div></div><strong style="font-size:11px;width:30px;text-align:right;">${pct}%</strong></div>`;
        container.appendChild(row);
      });
    }
  }

  // ─── VIEW 2: COMPONENT DETAIL CARD ─────────────────────────────────
  showComponentDetails(compName) {
    this.selectedComponent = compName;
    if (this.latestPayload) this.updateComponentDetailCard(compName, this.latestPayload);
  }

  updateComponentDetailCard(compName, data) {
    if (!compName) compName = "Drive-End (DE) Bearing";
    this.selectedComponent = compName;
    const pt = (data && data.physics_twin) ? data.physics_twin : {};
    const stresses = pt.component_stresses || {};
    const val = stresses[compName] !== undefined ? stresses[compName] : 0.12;
    const pct = Math.round(val * 100);

    this.setVal("dtInspectedCompName", compName);
    this.setVal("dtInspectedCompStress", `${pct}%`);

    const statusEl = document.getElementById("dtInspectedCompStatus");
    if (statusEl) {
      if (val > 0.65) { statusEl.style.background = "#FEE2E2"; statusEl.style.color = "#991B1B"; statusEl.textContent = "Critical Stress"; }
      else if (val > 0.35) { statusEl.style.background = "#FEF3C7"; statusEl.style.color = "#92400E"; statusEl.textContent = "Elevated Stress"; }
      else { statusEl.style.background = "#ECFDF5"; statusEl.style.color = "#065F46"; statusEl.textContent = "Nominal"; }
    }

    // Contextual component diagnostics
    const diag = (data && data.ai_diagnostics) ? data.ai_diagnostics : {};
    const faults = diag.specific_faults || [];
    const matched = faults.find(f => (f.component || "").toLowerCase().includes(compName.toLowerCase().split(" ")[0]));
    const defectEl = document.getElementById("dtInspectedCompDefect");
    if (defectEl) defectEl.textContent = matched ? `${matched.type} (${matched.evidence})` : "None Detected";

    // Component-specific descriptions
    const descriptions = {
      "Drive-End (DE) Bearing": "Primary high-fatigue assembly. Monitored for inner/outer race spalling, ball pass harmonics, and thermal rise.",
      "Non-Drive-End (NDE) Bearing": "Support bearing absorbing residual shaft loads. Lower fatigue but requires lubrication monitoring.",
      "Stator Winding": "3-Phase copper winding, insulation class F (155°C). Monitored for winding temperature and phase current imbalance.",
      "Shaft & Coupling": "Flexible coupling transmits torque. Monitored for alignment, runout, and 2X harmonic (misalignment signature).",
      "Pump Impeller": "Centrifugal impeller generating discharge head. Monitored for cavitation, flow instability, and pressure pulsations."
    };
    const descEl = document.getElementById("dtInspectedCompDesc");
    if (descEl) descEl.textContent = descriptions[compName] || "Industrial rotating machinery sub-assembly.";
  }

  // ─── VIEW 5: FAULT CARDS ──────────────────────────────────────────
  updateFaultCards(diag) {
    this.setVal("diagLoss", (diag.reconstruction_loss || 0).toFixed(4));
    this.setVal("diagThreshold", (diag.adaptive_threshold || 0.15).toFixed(4));
    const conf = diag.reconstruction_loss < diag.adaptive_threshold ? 98 : Math.max(40, 98 - Math.round((diag.reconstruction_loss - diag.adaptive_threshold) * 500));
    this.setVal("diagConfidence", `${conf}%`);

    const stateEl = document.getElementById("diagFaultState");
    if (stateEl) {
      if (diag.is_anomaly) {
        stateEl.style.background = "#FEE2E2"; stateEl.style.color = "#991B1B";
        stateEl.textContent = diag.state || "Anomaly";
      } else {
        stateEl.style.background = "#ECFDF5"; stateEl.style.color = "#065F46";
        stateEl.textContent = "Normal";
      }
    }
    this.setVal("diagFaultCategory", diag.fault_category || "Healthy Nominal Operation");
    this.setVal("diagExplanation", diag.explanation || "All empirical telemetry vectors conform to nominal baseline distribution.");

    // Specific faults list
    const container = document.getElementById("specificFaultsContainer");
    if (container) {
      const faults = diag.specific_faults || [];
      if (faults.length === 0) {
        container.innerHTML = `<p style="font-size:12px; color:#64748B;">No localized defect signatures identified. Equipment is in nominal condition.</p>`;
      } else {
        container.innerHTML = faults.map(f => `
          <div style="background:#FEF2F2; border:1px solid #FECACA; padding:10px 14px; border-radius:6px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between;">
              <strong style="font-size:13px; color:#991B1B;">${f.type}</strong>
              <span class="badge-tag" style="background:#FEE2E2; color:#991B1B;">${f.component}</span>
            </div>
            <p style="font-size:11px; color:#7F1D1D; margin-top:4px;">${f.evidence}</p>
          </div>`).join("");
      }
    }
  }

  // ─── VIEW 6: DERATING BANNER ──────────────────────────────────────
  updateDeratingBanner(pres) {
    const banner = document.getElementById("deratingAlertBanner");
    const summary = document.getElementById("deratingStatusSummary");
    const btn = document.getElementById("btnDispatchDerate");
    const vfdStatus = pres.vfd_derating_status || {};

    if (banner) banner.style.display = vfdStatus.is_active ? "flex" : "none";
    if (summary) {
      summary.textContent = vfdStatus.is_active
        ? `VFD derating ACTIVE — speed reduced to ${vfdStatus.speed_setpoint_pct}% (${vfdStatus.target_rpm} RPM / ${vfdStatus.frequency_hz} Hz). Fatigue kinetics decelerated ~3.5x.`
        : "Evaluating fatigue deceleration kinetics...";
    }
    if (btn) {
      btn.textContent = vfdStatus.is_active ? "Disengage Derating" : `Dispatch VFD Derating (20%)`;
      btn.dataset.active = vfdStatus.is_active ? "true" : "false";
    }

    // View 6 status badge
    const v6Badge = document.getElementById("view6DerateStatusBadge");
    if (v6Badge) {
      v6Badge.textContent = vfdStatus.is_active ? `ACTIVE: ${vfdStatus.speed_setpoint_pct}% Speed` : "Simulated Modbus TCP (Port 502)";
      v6Badge.style.background = vfdStatus.is_active ? "#FEF3C7" : "#EFF6FF";
      v6Badge.style.color = vfdStatus.is_active ? "#92400E" : "#1D4ED8";
    }

    // Derating action history log
    const historyLog = document.getElementById("vfdActionHistoryLog");
    const actions = pres.derate_action_history || pres.action_history || [];
    if (historyLog) {
      if (actions.length === 0) {
        historyLog.innerHTML = `<span style="color:#94A3B8;">No derating actions dispatched yet.</span>`;
      } else {
        historyLog.innerHTML = actions.map(a => `
          <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:6px 10px; border-radius:4px;">
            <strong style="color:${a.action === 'THROTTLE_ENGAGED' ? '#B45309' : '#059669'};">${a.action}</strong>
            — Speed: ${a.speed_setpoint_pct}% | RPM: ${a.target_rpm} | <small style="color:#94A3B8;">${a.timestamp}</small>
          </div>`).join("");
      }
    }
  }

  // ─── VIEW 6: RECOMMENDATIONS ──────────────────────────────────────
  renderRecommendations(recommendations) {
    const container = document.getElementById("recommendationsList");
    if (!container) return;
    if (!recommendations || recommendations.length === 0) {
      container.innerHTML = `<p style="font-size:12px; color:#64748B;">No active prescriptive recommendations.</p>`;
      return;
    }
    container.innerHTML = recommendations.map(rec => {
      const urgencyColors = { 1: "#EF4444", 2: "#F97316", 3: "#F59E0B", 4: "#10B981" };
      const color = urgencyColors[rec.priority_level] || "#64748B";
      return `
        <div style="border-left:4px solid ${color}; padding:12px 16px; background:#F8FAFC; border-radius:0 6px 6px 0; margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <strong style="font-size:13px; color:#172033;">${rec.title}</strong>
            <span class="badge-tag" style="background:${color}22; color:${color}; font-weight:700;">${rec.urgency}</span>
          </div>
          <p style="font-size:12px; color:#475569; margin-bottom:6px;">${rec.description}</p>
          <div style="font-size:11px; color:#64748B;">
            <strong>Timing:</strong> ${rec.recommended_timing} &bull; <strong>RUL:</strong> ${rec.t_rul_hours}h &bull; <strong>Lead:</strong> ${rec.t_lead_hours}h
          </div>
        </div>`;
    }).join("");
  }

  // ─── VIEW 6: WORK ORDERS ──────────────────────────────────────────
  renderWorkOrders(tickets) {
    const container = document.getElementById("cmmsWorkOrdersContainer");
    const badge = document.getElementById("cmmsOrderCountBadge");
    if (!container) return;

    if (badge) badge.textContent = `${tickets.length} Dispatched`;

    if (tickets.length === 0) {
      container.innerHTML = `<span style="font-size:12px; color:#94A3B8;">No work orders dispatched yet.</span>`;
      return;
    }
    container.innerHTML = tickets.map(t => `
      <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:10px 14px; border-radius:6px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <strong style="font-size:12px; color:#172033;">${t.ticket_id}</strong>
          <span class="badge-tag" style="background:${t.priority === 'Critical' || t.priority === 'Urgent' ? '#FEE2E2' : '#FEF3C7'}; color:${t.priority === 'Critical' || t.priority === 'Urgent' ? '#991B1B' : '#92400E'}; font-size:10px;">${t.priority}</span>
        </div>
        <div style="font-size:11px; color:#475569;">
          <strong>${t.component}</strong> — ${t.action}<br>
          <span style="color:#94A3B8;">Crew: ${t.assigned_crew} | ${t.status} | ${t.created_at}</span>
        </div>
      </div>`).join("");
  }

  // ─── VIEW 7: HISTORY TABLE ────────────────────────────────────────
  renderHistoryTable(history) {
    const tbody = document.getElementById("historyTableBody");
    if (!tbody) return;

    let filtered = history;
    if (this.historyFilterText) {
      filtered = history.filter(h => {
        const searchStr = `${h.timestamp || ""} ${h.operational_status || ""} ${h.speed_rpm || ""}`.toLowerCase();
        return searchStr.includes(this.historyFilterText);
      });
    }

    // Show most recent first
    const reversed = [...filtered].reverse();
    tbody.innerHTML = reversed.slice(0, 50).map(h => {
      const statusColor = h.operational_status === "Nominal" ? "#059669" : h.operational_status === "Degraded" ? "#D97706" : "#DC2626";
      return `<tr>
        <td>${h.timestamp || "--"}</td>
        <td>${(h.vibration_radial || 0).toFixed(2)}</td>
        <td>${(h.vibration_axial || 0).toFixed(2)}</td>
        <td>${(h.temperature || 0).toFixed(1)}</td>
        <td>${(h.current || 0).toFixed(2)}</td>
        <td>${(h.speed_rpm || 0).toFixed(0)}</td>
        <td>${(h.pressure || 0).toFixed(2)}</td>
        <td>${(h.health_index || 0).toFixed(2)}</td>
        <td style="color:${statusColor}; font-weight:600;">${h.operational_status || "--"}</td>
      </tr>`;
    }).join("");
  }

  // ─── CHART REFRESH ────────────────────────────────────────────────
  refreshVisibleCharts() {
    if (!this.latestPayload) return;
    const data = this.latestPayload;
    const feats = data.signal_features || {};
    const fd = feats.frequency_domain || {};
    const prog = data.prognostics || {};
    const diag = data.ai_diagnostics || {};

    // View 1 — Timeline chart
    if (this.activeView === "overview" && this.timelineChart) {
      this.timelineChart.render(this.historyBuffer);
    }

    // View 1 — RUL degradation
    if (this.activeView === "overview" && this.rulChart) {
      this.rulChart.render(prog);
    }

    // View 2 — Discrepancy chart
    if (this.activeView === "twin" && this.discChart) {
      this.discChart.render(this.discHistoryBuffer);
    }

    // View 3 — FFT Spectrum
    if (this.activeView === "analytics" && this.fftChart) {
      this.fftChart.render(fd);
    }

    // View 4 — RUL chart (also shown in prognostics view)
    if (this.activeView === "prognostics" && this.rulChart) {
      this.rulChart.render(prog);
    }

    // View 5 — Attention Attribution
    if (this.activeView === "faults" && this.attentionChart) {
      this.attentionChart.render(diag.attention_attributions || []);
    }
  }

  // ─── TOAST NOTIFICATIONS ──────────────────────────────────────────
  showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${message}</span>
      <button onclick="this.parentElement.remove()" style="background:none; border:none; cursor:pointer; font-size:16px; color:inherit; margin-left:12px;">&times;</button>`;
    container.appendChild(toast);

    setTimeout(() => { if (toast.parentElement) toast.remove(); }, 4000);
  }
}

// ─── APP BOOTSTRAP ──────────────────────────────────────────────────
window.app = new IndustrialTwinApp();
