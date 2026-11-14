/**
 * Digital Twin Equipment Viewer
 * Technical cyber-physical visualization of rotating machinery (Motor-Pump-Gearbox assembly)
 * Features:
 * - Interactive SVG asset rendering with dynamic thermal/vibration stress heatmaps
 * - Dynamic shaft rotation proportional to measured RPM
 * - Localized hotspot glows (Drive-End bearing, Stator, Shaft, Pump impeller)
 * - Clickable component inspection drawer
 * - Sensor probe callouts with live telemetry badges
 */

class DigitalTwinViewer {
  constructor(containerId, onComponentSelect) {
    this.container = document.getElementById(containerId);
    this.onComponentSelect = onComponentSelect;
    this.selectedComponent = "Drive-End (DE) Bearing";
    this.rotationAngle = 0;
    this.currentData = null;
    this.animFrameId = null;
    
    this.init();
  }

  init() {
    if (!this.container) return;
    this.renderBaseSVG();
    this.startAnimationLoop();
  }

  renderBaseSVG() {
    this.container.innerHTML = `
      <svg id="twinSvg" viewBox="0 0 850 420" width="100%" height="100%" style="background:#FFFFFF; border-radius:8px;">
        <defs>
          <!-- Gradients for components -->
          <linearGradient id="motorGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#3B82F6" stop-opacity="0.15" />
            <stop offset="100%" stop-color="#1E40AF" stop-opacity="0.25" />
          </linearGradient>

          <linearGradient id="shaftGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#E2E8F0" />
            <stop offset="50%" stop-color="#CBD5E1" />
            <stop offset="100%" stop-color="#94A3B8" />
          </linearGradient>

          <linearGradient id="pumpGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0D9488" stop-opacity="0.15" />
            <stop offset="100%" stop-color="#0F766E" stop-opacity="0.30" />
          </linearGradient>

          <!-- Dynamic Stress Heatmap Radial Glows -->
          <radialGradient id="deBearingHeat" cx="50%" cy="50%" r="50%">
            <stop offset="0%" id="deStop0" stop-color="#10B981" stop-opacity="0.8" />
            <stop offset="70%" id="deStop70" stop-color="#10B981" stop-opacity="0.2" />
            <stop offset="100%" stop-color="#10B981" stop-opacity="0.0" />
          </radialGradient>

          <radialGradient id="ndeBearingHeat" cx="50%" cy="50%" r="50%">
            <stop offset="0%" id="ndeStop0" stop-color="#10B981" stop-opacity="0.8" />
            <stop offset="100%" stop-color="#10B981" stop-opacity="0.0" />
          </radialGradient>

          <radialGradient id="statorHeat" cx="50%" cy="50%" r="50%">
            <stop offset="0%" id="statorStop0" stop-color="#10B981" stop-opacity="0.7" />
            <stop offset="100%" stop-color="#10B981" stop-opacity="0.0" />
          </radialGradient>

          <radialGradient id="pumpHeat" cx="50%" cy="50%" r="50%">
            <stop offset="0%" id="pumpStop0" stop-color="#10B981" stop-opacity="0.7" />
            <stop offset="100%" stop-color="#10B981" stop-opacity="0.0" />
          </radialGradient>

          <!-- Drop shadow filter -->
          <filter id="twinShadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#0F172A" flood-opacity="0.08" />
          </filter>
        </defs>

        <!-- Machine Baseplate / Bed -->
        <rect x="40" y="320" width="770" height="24" rx="4" fill="#E2E8F0" stroke="#94A3B8" stroke-width="1.5" />
        <rect x="60" y="344" width="730" height="8" rx="2" fill="#CBD5E1" />
        <!-- Anchor Bolts -->
        <circle cx="80" cy="332" r="4" fill="#64748B" />
        <circle cx="280" cy="332" r="4" fill="#64748B" />
        <circle cx="560" cy="332" r="4" fill="#64748B" />
        <circle cx="760" cy="332" r="4" fill="#64748B" />

        <!-- === MOTOR SUBSYSTEM === -->
        <!-- Motor Stator Casing -->
        <g id="comp-stator" class="twin-comp" cursor="pointer">
          <rect x="90" y="110" width="220" height="200" rx="10" fill="url(#motorGrad)" stroke="#2563EB" stroke-width="2" filter="url(#twinShadow)" />
          <!-- Stator Cooling Fins -->
          <line x1="90" y1="135" x2="310" y2="135" stroke="#93C5FD" stroke-width="2" />
          <line x1="90" y1="160" x2="310" y2="160" stroke="#93C5FD" stroke-width="2" />
          <line x1="90" y1="185" x2="310" y2="185" stroke="#93C5FD" stroke-width="2" />
          <line x1="90" y1="210" x2="310" y2="210" stroke="#93C5FD" stroke-width="2" />
          <line x1="90" y1="235" x2="310" y2="235" stroke="#93C5FD" stroke-width="2" />
          <line x1="90" y1="260" x2="310" y2="260" stroke="#93C5FD" stroke-width="2" />
          <line x1="90" y1="285" x2="310" y2="285" stroke="#93C5FD" stroke-width="2" />
          <!-- Stator Thermal Heatmap Overlay -->
          <circle id="statorHeatCircle" cx="200" cy="210" r="85" fill="url(#statorHeat)" opacity="0.6" pointer-events="none" />
          <!-- Stator Label -->
          <text x="200" y="215" text-anchor="middle" fill="#1E3A8A" font-size="12" font-weight="700">MOTOR STATOR (5.5 kW)</text>
        </g>

        <!-- Motor Terminal Box -->
        <rect x="160" y="75" width="80" height="35" rx="4" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5" />
        <text x="200" y="97" text-anchor="middle" fill="#1E40AF" font-size="10" font-weight="600">400V 3-PH</text>

        <!-- Non-Drive-End (NDE) Bearing Housing -->
        <g id="comp-nde" class="twin-comp" cursor="pointer">
          <rect x="65" y="150" width="25" height="120" rx="4" fill="#F1F5F9" stroke="#64748B" stroke-width="1.5" />
          <!-- NDE Bearing Dynamic Heatmap Glow -->
          <circle id="ndeHeatCircle" cx="77" cy="210" r="28" fill="url(#ndeBearingHeat)" opacity="0.7" pointer-events="none" />
          <circle cx="77" cy="210" r="10" fill="#94A3B8" stroke="#475569" stroke-width="1.5" />
          <!-- NDE Sensor Marker -->
          <circle cx="77" cy="130" r="5" fill="#2563EB" />
          <text x="77" y="120" text-anchor="middle" fill="#475569" font-size="10" font-weight="600">NDE</text>
        </g>

        <!-- Drive-End (DE) Bearing Housing (High-fatigue zone) -->
        <g id="comp-de" class="twin-comp" cursor="pointer">
          <rect x="310" y="145" width="35" height="130" rx="4" fill="#F8FAFC" stroke="#2563EB" stroke-width="2" />
          <!-- DE Bearing Dynamic Stress Heatmap Glow -->
          <circle id="deHeatCircle" cx="327" cy="210" r="55" fill="url(#deBearingHeat)" opacity="0.8" pointer-events="none" />
          <!-- Bearing outer race & balls -->
          <circle cx="327" cy="210" r="18" fill="none" stroke="#334155" stroke-width="2" />
          <circle cx="327" cy="197" r="3.5" fill="#64748B" />
          <circle cx="327" cy="223" r="3.5" fill="#64748B" />
          <circle cx="314" cy="210" r="3.5" fill="#64748B" />
          <circle cx="340" cy="210" r="3.5" fill="#64748B" />
          <!-- DE Sensor Probe Callout -->
          <line x1="327" y1="145" x2="327" y2="70" stroke="#2563EB" stroke-width="1.5" stroke-dasharray="3,3" />
          <rect x="290" y="48" width="75" height="22" rx="4" fill="#EFF6FF" stroke="#2563EB" stroke-width="1" />
          <text id="probeDeText" x="327" y="63" text-anchor="middle" fill="#1D4ED8" font-size="10" font-weight="700">DE: 0.85 mm/s</text>
        </g>

        <!-- === ROTATING SHAFT & COUPLING === -->
        <g id="comp-shaft" class="twin-comp" cursor="pointer">
          <!-- Main Shaft -->
          <rect x="345" y="198" width="220" height="24" rx="2" fill="url(#shaftGrad)" stroke="#64748B" stroke-width="1.5" />
          <!-- Flexible Coupling -->
          <rect x="430" y="180" width="35" height="60" rx="4" fill="#475569" stroke="#1E293B" stroke-width="1.5" />
          <line x1="447" y1="180" x2="447" y2="240" stroke="#E2E8F0" stroke-width="2" stroke-dasharray="4,4" />
          <text x="447" y="172" text-anchor="middle" fill="#475569" font-size="9" font-weight="600">COUPLING</text>
          
          <!-- Dynamic rotation animation indicator -->
          <g id="shaftRotator" transform="translate(400, 210)">
            <line x1="-12" y1="0" x2="12" y2="0" stroke="#1E293B" stroke-width="3" stroke-linecap="round" />
            <circle cx="0" cy="0" r="3" fill="#2563EB" />
          </g>
        </g>

        <!-- === CENTRIFUGAL PUMP & VOLUTE CASING === -->
        <g id="comp-pump" class="twin-comp" cursor="pointer">
          <!-- Pump Bearing Pedestal -->
          <rect x="560" y="160" width="30" height="110" rx="4" fill="#F1F5F9" stroke="#0D9488" stroke-width="1.5" />
          
          <!-- Pump Volute Casing (Spiral chamber) -->
          <path d="M 590,210 C 590,130 680,120 730,150 C 780,180 770,260 720,290 C 660,320 590,270 590,210 Z" 
                fill="url(#pumpGrad)" stroke="#0D9488" stroke-width="2.5" filter="url(#twinShadow)" />
          
          <!-- Pump Heatmap Overlay -->
          <circle id="pumpHeatCircle" cx="680" cy="210" r="70" fill="url(#pumpHeat)" opacity="0.6" pointer-events="none" />

          <!-- Discharge Pipe (Top) -->
          <rect x="660" y="70" width="45" height="70" rx="2" fill="#E6FFFA" stroke="#0D9488" stroke-width="2" />
          <rect x="650" y="60" width="65" height="12" rx="2" fill="#CCFBF1" stroke="#0D9488" stroke-width="1.5" />
          <text x="682" y="52" text-anchor="middle" fill="#0F766E" font-size="10" font-weight="700">DISCHARGE (4.2 bar)</text>

          <!-- Suction Eye (Front inlet) -->
          <circle cx="680" cy="210" r="36" fill="#F0FDFA" stroke="#0D9488" stroke-width="2" />
          <!-- Impeller Vanes -->
          <g id="impellerVanes" transform="translate(680, 210)">
            <path d="M0,0 Q12,-15 24,-5" fill="none" stroke="#0D9488" stroke-width="2.5" />
            <path d="M0,0 Q-15,-12 -5,-24" fill="none" stroke="#0D9488" stroke-width="2.5" />
            <path d="M0,0 Q-12,15 -24,5" fill="none" stroke="#0D9488" stroke-width="2.5" />
            <path d="M0,0 Q15,12 5,24" fill="none" stroke="#0D9488" stroke-width="2.5" />
          </g>

          <text x="680" y="270" text-anchor="middle" fill="#0F766E" font-size="11" font-weight="700">CENTRIFUGAL PUMP</text>
        </g>

        <!-- === LIVE SENSOR PROBES & LABELS === -->
        <!-- Probe 1: Vibration (Radial) -->
        <g transform="translate(327, 275)">
          <circle cx="0" cy="0" r="4" fill="#2563EB" />
          <line x1="0" y1="0" x2="0" y2="25" stroke="#2563EB" stroke-width="1.5" />
          <rect x="-35" y="25" width="70" height="18" rx="3" fill="#FFFFFF" stroke="#2563EB" stroke-width="1" />
          <text id="probeVibText" x="0" y="38" text-anchor="middle" font-size="9" font-weight="700" fill="#1D4ED8">VIB: 0.85</text>
        </g>

        <!-- Probe 2: Temperature (PT100) -->
        <g transform="translate(200, 110)">
          <circle cx="0" cy="0" r="4" fill="#F59E0B" />
          <line x1="0" y1="0" x2="0" y2="-20" stroke="#F59E0B" stroke-width="1.5" />
          <rect x="-35" y="-38" width="70" height="18" rx="3" fill="#FFFFFF" stroke="#F59E0B" stroke-width="1" />
          <text id="probeTempText" x="0" y="-25" text-anchor="middle" font-size="9" font-weight="700" fill="#B45309">TEMP: 42°C</text>
        </g>

        <!-- Real-Time Synchronization Watermark -->
        <g transform="translate(50, 45)">
          <circle cx="0" cy="0" r="5" id="syncIndicatorDot" fill="#10B981" />
          <text x="12" y="4" font-size="11" font-weight="600" id="syncStatusText" fill="#475569">Physics Model: Synchronized (Δ = 0.08)</text>
        </g>
      </svg>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const comps = [
      { id: "comp-de", name: "Drive-End (DE) Bearing" },
      { id: "comp-nde", name: "Non-Drive-End (NDE) Bearing" },
      { id: "comp-stator", name: "Stator Winding" },
      { id: "comp-shaft", name: "Shaft & Coupling" },
      { id: "comp-pump", name: "Pump Impeller" }
    ];

    comps.forEach(c => {
      const el = document.getElementById(c.id);
      if (el) {
        el.addEventListener("click", () => {
          this.selectedComponent = c.name;
          comps.forEach(other => {
            const otherEl = document.getElementById(other.id);
            if (otherEl) otherEl.style.opacity = "0.75";
          });
          el.style.opacity = "1.0";
          if (this.onComponentSelect) {
            this.onComponentSelect(c.name);
          }
        });
      }
    });
  }

  update(data) {
    if (!data) return;
    this.currentData = data;
    
    const telemetry = data.telemetry || {};
    const pt = data.physics_twin || {};
    const stresses = pt.component_stresses || {};
    
    // 1. Update probes text
    const vibVal = telemetry.vibration_radial || 0.85;
    const tempVal = telemetry.temperature || 42.0;
    
    const probeDe = document.getElementById("probeDeText");
    if (probeDe) probeDe.textContent = `DE: ${vibVal.toFixed(2)} mm/s`;

    const probeVib = document.getElementById("probeVibText");
    if (probeVib) probeVib.textContent = `VIB: ${vibVal.toFixed(2)}`;

    const probeTemp = document.getElementById("probeTempText");
    if (probeTemp) probeTemp.textContent = `TEMP: ${tempVal.toFixed(1)}°C`;

    // 2. Update Dynamic Stress Heatmap Colors
    const getStressColor = (val) => {
      if (val < 0.35) return "#10B981";       // Healthy green
      if (val < 0.70) return "#F59E0B";       // Warning amber
      return "#EF4444";                      // Critical red
    };

    const deStress = stresses["Drive-End (DE) Bearing"] || 0.1;
    const ndeStress = stresses["Non-Drive-End (NDE) Bearing"] || 0.1;
    const statorStress = stresses["Stator Winding"] || 0.1;
    const shaftStress = stresses["Shaft & Coupling"] || 0.1;
    const pumpStress = stresses["Pump Impeller"] || 0.1;

    const deColor = getStressColor(deStress);
    const ndeColor = getStressColor(ndeStress);
    const statorColor = getStressColor(statorStress);
    const shaftColor = getStressColor(shaftStress);
    const pumpColor = getStressColor(pumpStress);

    // Update SVG Radial Gradients
    const deStop0 = document.getElementById("deStop0");
    const deStop70 = document.getElementById("deStop70");
    if (deStop0 && deStop70) {
      deStop0.setAttribute("stop-color", deColor);
      deStop70.setAttribute("stop-color", deColor);
    }

    const ndeStop0 = document.getElementById("ndeStop0");
    if (ndeStop0) ndeStop0.setAttribute("stop-color", ndeColor);

    const statorStop0 = document.getElementById("statorStop0");
    if (statorStop0) statorStop0.setAttribute("stop-color", statorColor);

    const pumpStop0 = document.getElementById("pumpStop0");
    if (pumpStop0) pumpStop0.setAttribute("stop-color", pumpColor);

    // 3. Update Sync Indicator
    const syncDot = document.getElementById("syncIndicatorDot");
    const syncText = document.getElementById("syncStatusText");
    const discNorm = pt.discrepancy_norm || 0.0;
    
    if (syncDot && syncText) {
      if (discNorm < 0.6) {
        syncDot.setAttribute("fill", "#10B981");
        syncText.textContent = `Physics Model: Synchronized (Δ = ${discNorm.toFixed(3)})`;
      } else if (discNorm < 1.2) {
        syncDot.setAttribute("fill", "#F59E0B");
        syncText.textContent = `Physics Model: Minor Discrepancy (Δ = ${discNorm.toFixed(3)})`;
      } else {
        syncDot.setAttribute("fill", "#EF4444");
        syncText.textContent = `Physics Model: DIVERGENCE DETECTED (Δ = ${discNorm.toFixed(3)})`;
      }
    }
  }

  startAnimationLoop() {
    const animate = () => {
      if (this.currentData && this.currentData.streaming && this.currentData.streaming.is_streaming) {
        const rpm = (this.currentData.telemetry && this.currentData.telemetry.speed_rpm) || 1440;
        // Rotation speed delta
        this.rotationAngle = (this.rotationAngle + (rpm / 60.0) * 1.5) % 360;
        
        const shaftRot = document.getElementById("shaftRotator");
        if (shaftRot) {
          shaftRot.setAttribute("transform", `translate(400, 210) rotate(${this.rotationAngle})`);
        }

        const impeller = document.getElementById("impellerVanes");
        if (impeller) {
          impeller.setAttribute("transform", `translate(680, 210) rotate(${this.rotationAngle})`);
        }
      }
      this.animFrameId = requestAnimationFrame(animate);
    };
    this.animFrameId = requestAnimationFrame(animate);
  }

  destroy() {
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
    }
  }
}
