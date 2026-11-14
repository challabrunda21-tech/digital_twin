/**
 * Industrial Analytics Charting Engine
 * High-performance, pixel-crisp Canvas charts conforming to the technical industrial theme:
 * 1. SensorTimelineChart - Live multi-channel sensor trends with anomaly threshold bands
 * 2. FFTSpectrumChart - FFT spectral power with 1X, 2X, BPFI, BPFO harmonic markers
 * 3. AttentionAttributionChart - Explainable AI multi-modal self-attention bar chart
 * 4. RULDegradationChart - Health Index degradation curve with 95% Bayesian Monte Carlo confidence funnel
 * 5. DiscrepancyTimelineChart - Physics shadow state discrepancy vector Δ(t)
 */

class HighDpiCanvas {
  static setup(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width || canvas.width || 400;
    const height = rect.height || canvas.height || 220;
    
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    return { ctx, width, height, dpr };
  }
}

class SensorTimelineChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
  }

  render(history, options = {}) {
    if (!this.canvas || !history || history.length === 0) return;
    const { ctx, width, height } = HighDpiCanvas.setup(this.canvas);
    
    ctx.clearRect(0, 0, width, height);

    const padLeft = 45;
    const padRight = 45;
    const padTop = 20;
    const padBottom = 30;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    // Series 1: Vibration Radial (mm/s), Series 2: Temperature (°C)
    const vibVals = history.map(h => h.vibration_radial || 0);
    const tempVals = history.map(h => h.temperature || 0);

    const maxVib = Math.max(4.0, ...vibVals) * 1.15;
    const minTemp = Math.min(30, ...tempVals) * 0.9;
    const maxTemp = Math.max(80, ...tempVals) * 1.1;

    // Gridlines
    ctx.strokeStyle = "#EDF2F7";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (plotH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + plotW, y);
      ctx.stroke();

      // Left Axis (Vibration)
      const vVal = (maxVib * (1 - i / 4)).toFixed(1);
      ctx.fillStyle = "#2563EB";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(vVal, padLeft - 6, y + 3);

      // Right Axis (Temperature)
      const tVal = (minTemp + (maxTemp - minTemp) * (1 - i / 4)).toFixed(0);
      ctx.fillStyle = "#F59E0B";
      ctx.textAlign = "left";
      ctx.fillText(`${tVal}°C`, padLeft + plotW + 6, y + 3);
    }

    // Vibration Warning Threshold line (ISO 10816 Alert @ 2.8 mm/s)
    if (maxVib >= 2.8) {
      const yWarn = padTop + plotH * (1 - 2.8 / maxVib);
      ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(padLeft, yWarn);
      ctx.lineTo(padLeft + plotW, yWarn);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#EF4444";
      ctx.font = "9px Inter, sans-serif";
      ctx.fillText("ISO 10816 Alarm (2.8 mm/s)", padLeft + 6, yWarn - 4);
    }

    const n = history.length;
    const getX = (idx) => padLeft + (idx / Math.max(1, n - 1)) * plotW;

    // Draw Temperature Line (Series 2)
    ctx.strokeStyle = "#F59E0B";
    ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((h, i) => {
      const t = h.temperature || 0;
      const y = padTop + plotH * (1 - (t - minTemp) / (maxTemp - minTemp + 1e-8));
      if (i === 0) ctx.moveTo(getX(i), y);
      else ctx.lineTo(getX(i), y);
    });
    ctx.stroke();

    // Draw Vibration Line (Series 1)
    ctx.strokeStyle = "#2563EB";
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    history.forEach((h, i) => {
      const v = h.vibration_radial || 0;
      const y = padTop + plotH * (1 - v / maxVib);
      if (i === 0) ctx.moveTo(getX(i), y);
      else ctx.lineTo(getX(i), y);
    });
    ctx.stroke();

    // Time Axis labels
    ctx.fillStyle = "#64748B";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "center";
    if (n > 1) {
      const tStart = (history[0].timestamp || "").split(" ")[1] || "T0";
      const tEnd = (history[n - 1].timestamp || "").split(" ")[1] || "T_now";
      ctx.fillText(tStart, padLeft + 15, height - 8);
      ctx.fillText(tEnd, padLeft + plotW - 15, height - 8);
    }
  }
}

class FFTSpectrumChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
  }

  render(freqData) {
    if (!this.canvas || !freqData) return;
    const { ctx, width, height } = HighDpiCanvas.setup(this.canvas);
    ctx.clearRect(0, 0, width, height);

    const padLeft = 40;
    const padRight = 20;
    const padTop = 25;
    const padBottom = 30;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const f1x = freqData.fundamental_1x_hz || 24.0;
    const maxFreq = 200.0; // Hz
    const maxAmp = Math.max(1.5, (freqData.amp_1x || 0) * 1.5, (freqData.amp_bpfi || 0) * 1.5);

    // Gridlines
    ctx.strokeStyle = "#EDF2F7";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (plotH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + plotW, y);
      ctx.stroke();

      const aVal = (maxAmp * (1 - i / 4)).toFixed(2);
      ctx.fillStyle = "#64748B";
      ctx.font = "9px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(aVal, padLeft - 6, y + 3);
    }

    // Synthetic FFT Spectrum Envelope
    const getX = (f) => padLeft + (f / maxFreq) * plotW;
    const getY = (a) => padTop + plotH * (1 - Math.min(1.0, a / maxAmp));

    // Baseline noise floor
    ctx.fillStyle = "rgba(37, 99, 235, 0.08)";
    ctx.strokeStyle = "#2563EB";
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(padLeft, getY(0));

    for (let f = 0; f <= maxFreq; f += 1.0) {
      let amp = 0.03 + 0.02 * Math.sin(f * 0.1);
      // Add peaks at 1X, 2X, 3X, BPFO, BPFI
      if (Math.abs(f - f1x) < 2) amp += (freqData.amp_1x || 0.8) * Math.exp(-0.5 * Math.pow(f - f1x, 2));
      if (Math.abs(f - 2 * f1x) < 2) amp += (freqData.amp_2x || 0.4) * Math.exp(-0.5 * Math.pow(f - 2 * f1x, 2));
      if (Math.abs(f - 3 * f1x) < 2) amp += (freqData.amp_3x || 0.2) * Math.exp(-0.5 * Math.pow(f - 3 * f1x, 2));
      if (Math.abs(f - (freqData.bpfi_hz || 130)) < 2.5) amp += (freqData.amp_bpfi || 0.1) * Math.exp(-0.5 * Math.pow(f - freqData.bpfi_hz, 2));
      if (Math.abs(f - (freqData.bpfo_hz || 86)) < 2.5) amp += (freqData.amp_bpfo || 0.1) * Math.exp(-0.5 * Math.pow(f - freqData.bpfo_hz, 2));

      ctx.lineTo(getX(f), getY(amp));
    }
    ctx.lineTo(padLeft + plotW, getY(0));
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Defect Markers
    const drawMarker = (freq, label, color) => {
      if (freq > maxFreq) return;
      const x = getX(freq);
      ctx.strokeStyle = color;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(x, padTop);
      ctx.lineTo(x, padTop + plotH);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = color;
      ctx.font = "bold 9px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${label} (${freq.toFixed(0)}Hz)`, x, padTop - 5);
    };

    drawMarker(f1x, "1X Rot", "#2563EB");
    drawMarker(2 * f1x, "2X", "#64748B");
    if (freqData.bpfi_hz) drawMarker(freqData.bpfi_hz, "BPFI (Inner)", "#EF4444");
    if (freqData.bpfo_hz) drawMarker(freqData.bpfo_hz, "BPFO", "#F59E0B");

    // X Axis
    ctx.fillStyle = "#64748B";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "center";
    for (let f = 0; f <= maxFreq; f += 50) {
      ctx.fillText(`${f} Hz`, getX(f), height - 8);
    }
  }
}

class AttentionAttributionChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
  }

  render(attributions) {
    if (!this.canvas || !attributions || attributions.length === 0) return;
    const { ctx, width, height } = HighDpiCanvas.setup(this.canvas);
    ctx.clearRect(0, 0, width, height);

    const padLeft = 130;
    const padRight = 40;
    const padTop = 15;
    const padBottom = 15;
    const plotW = width - padLeft - padRight;
    const rowH = (height - padTop - padBottom) / attributions.length;

    attributions.forEach((attr, idx) => {
      const y = padTop + idx * rowH;
      const pct = Math.min(100, Math.max(0, attr.attribution_pct || 0));
      const barW = (pct / 100.0) * plotW;

      // Channel Label
      ctx.fillStyle = "#172033";
      ctx.font = "11px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(attr.channel, padLeft - 10, y + rowH * 0.65);

      // Background Bar Track
      ctx.fillStyle = "#EDF2F7";
      ctx.fillRect(padLeft, y + rowH * 0.25, plotW, rowH * 0.5);

      // Value Fill Bar (Color coded by contribution severity)
      let barColor = "#2563EB"; // Default Blue
      if (pct > 35) barColor = "#EF4444"; // Red for high contributor
      else if (pct > 20) barColor = "#F59E0B"; // Amber

      ctx.fillStyle = barColor;
      ctx.fillRect(padLeft, y + rowH * 0.25, barW, rowH * 0.5);

      // Pct Label
      ctx.fillStyle = "#475569";
      ctx.font = "bold 10px Inter, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`${pct.toFixed(1)}%`, padLeft + barW + 6, y + rowH * 0.65);
    });
  }
}

class RULDegradationChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
  }

  render(prognostics) {
    if (!this.canvas || !prognostics) return;
    const { ctx, width, height } = HighDpiCanvas.setup(this.canvas);
    ctx.clearRect(0, 0, width, height);

    const padLeft = 45;
    const padRight = 30;
    const padTop = 25;
    const padBottom = 30;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const traj = prognostics.trajectory || {};
    const hours = traj.operating_hours || [];
    const meanHI = traj.health_index_mean || [];
    const lowerHI = traj.confidence_lower_5pct || [];
    const upperHI = traj.confidence_upper_95pct || [];

    if (hours.length === 0) return;

    const startH = hours[0];
    const endH = hours[hours.length - 1];

    const getX = (h) => padLeft + ((h - startH) / Math.max(1, endH - startH)) * plotW;
    const getY = (hi) => padTop + plotH * (1.0 - Math.max(0.0, Math.min(1.0, hi)));

    // Gridlines for HI [0.0 to 1.0]
    ctx.strokeStyle = "#EDF2F7";
    ctx.lineWidth = 1;
    [1.0, 0.75, 0.50, 0.20, 0.0].forEach(val => {
      const y = getY(val);
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + plotW, y);
      ctx.stroke();

      ctx.fillStyle = "#64748B";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(val.toFixed(2), padLeft - 6, y + 3);
    });

    // Warning Threshold Band (0.75)
    const yWarn = getY(0.75);
    ctx.strokeStyle = "rgba(245, 158, 11, 0.6)";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, yWarn);
    ctx.lineTo(padLeft + plotW, yWarn);
    ctx.stroke();
    ctx.fillStyle = "#D97706";
    ctx.font = "9px Inter, sans-serif";
    ctx.textAlign = "right";
    ctx.fillText("Warning (0.75)", padLeft + plotW, yWarn - 4);

    // Critical Failure Threshold Band (0.20)
    const yCrit = getY(0.20);
    ctx.strokeStyle = "rgba(239, 68, 68, 0.8)";
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(padLeft, yCrit);
    ctx.lineTo(padLeft + plotW, yCrit);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#EF4444";
    ctx.font = "bold 9px Inter, sans-serif";
    ctx.fillText("Critical Failure (0.20)", padLeft + plotW, yCrit - 4);

    // Shaded 95% Bayesian Monte Carlo Confidence Interval Funnel
    if (lowerHI.length > 0 && upperHI.length > 0) {
      ctx.fillStyle = "rgba(37, 99, 235, 0.12)";
      ctx.beginPath();
      // Upper curve
      upperHI.forEach((val, i) => {
        const x = getX(hours[i]);
        const y = getY(val);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      // Lower curve (reverse)
      for (let i = lowerHI.length - 1; i >= 0; i--) {
        const x = getX(hours[i]);
        const y = getY(lowerHI[i]);
        ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.fill();
    }

    // Mean Projected Degradation Curve
    ctx.strokeStyle = "#2563EB";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    meanHI.forEach((val, i) => {
      const x = getX(hours[i]);
      const y = getY(val);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Current State Dot
    const currentX = getX(hours[0]);
    const currentY = getY(meanHI[0]);
    ctx.fillStyle = "#10B981";
    ctx.beginPath();
    ctx.arc(currentX, currentY, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Projected RUL Failure Point Marker
    const rulHours = prognostics.rul_hours || 0;
    const failH = startH + rulHours;
    if (failH <= endH) {
      const xFail = getX(failH);
      const yFail = getY(0.20);
      ctx.fillStyle = "#EF4444";
      ctx.beginPath();
      ctx.arc(xFail, yFail, 5, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillText(`tRUL = ${rulHours.toFixed(0)}h`, xFail, yFail - 8);
    }

    // Time Axis
    ctx.fillStyle = "#64748B";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${startH.toFixed(0)}h (Current)`, padLeft + 30, height - 8);
    ctx.fillText(`${endH.toFixed(0)}h (Forecast Horizon)`, padLeft + plotW - 45, height - 8);
  }
}

class DiscrepancyTimelineChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
  }

  render(discHistory) {
    if (!this.canvas || !discHistory || discHistory.length === 0) return;
    const { ctx, width, height } = HighDpiCanvas.setup(this.canvas);
    ctx.clearRect(0, 0, width, height);

    const padLeft = 40;
    const padRight = 20;
    const padTop = 15;
    const padBottom = 25;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const maxVal = Math.max(1.5, ...discHistory.map(d => d.val || 0)) * 1.2;
    const getX = (i) => padLeft + (i / Math.max(1, discHistory.length - 1)) * plotW;
    const getY = (val) => padTop + plotH * (1 - val / maxVal);

    // Tolerance limit line (Δ = 1.0)
    const yTol = getY(1.0);
    ctx.strokeStyle = "rgba(245, 158, 11, 0.5)";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, yTol);
    ctx.lineTo(padLeft + plotW, yTol);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#D97706";
    ctx.font = "9px Inter, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Discrepancy Warning Limit (Δ = 1.0)", padLeft + 6, yTol - 4);

    // Area & Line
    ctx.fillStyle = "rgba(13, 148, 136, 0.12)";
    ctx.strokeStyle = "#0D9488";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padLeft, getY(0));

    discHistory.forEach((d, i) => {
      ctx.lineTo(getX(i), getY(d.val));
    });
    ctx.lineTo(padLeft + plotW, getY(0));
    ctx.closePath();
    ctx.fill();

    ctx.beginPath();
    discHistory.forEach((d, i) => {
      if (i === 0) ctx.moveTo(getX(i), getY(d.val));
      else ctx.lineTo(getX(i), getY(d.val));
    });
    ctx.stroke();
  }
}
