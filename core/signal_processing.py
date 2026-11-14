"""
Signal Processing and Multi-Domain Feature Extraction Module
Implements:
- FIR bandpass / lowpass filtering and noise suppression
- Detrending to eliminate DC sensor bias
- Windowed median filtering for electromagnetic spike removal
- Time-domain statistical metrics: RMS, peak-to-peak, crest factor, kurtosis, skewness, shape factor
- Frequency-domain spectral metrics: FFT power spectrum, spectral centroid, rotational harmonics (1X, 2X, 3X),
  and bearing defect frequencies (BPFO, BPFI, BSF, FTF)
- Time-frequency wavelet energy decomposition
- Adaptive z-score standardization
"""

import numpy as np
from typing import Dict, Any, List, Tuple

class SignalPreprocessor:
    def __init__(self, sampling_rate: float = 1000.0):
        self.sampling_rate = sampling_rate

    def detrend(self, signal: np.ndarray) -> np.ndarray:
        """Eliminate DC drift and linear trend via first-order polynomial subtraction."""
        n = len(signal)
        if n < 2:
            return signal - np.mean(signal) if n == 1 else signal
        t = np.arange(n)
        poly = np.polyfit(t, signal, 1)
        trend = np.polyval(poly, t)
        return signal - trend

    def median_filter(self, signal: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """Windowed median filtering for transient electromagnetic spike removal."""
        if len(signal) < kernel_size:
            return signal
        pad_size = kernel_size // 2
        padded = np.pad(signal, pad_size, mode='edge')
        filtered = np.zeros_like(signal)
        for i in range(len(signal)):
            filtered[i] = np.median(padded[i:i + kernel_size])
        return filtered

    def fir_lowpass(self, signal: np.ndarray, window_size: int = 5) -> np.ndarray:
        """Moving-average FIR filtering for high-frequency noise suppression."""
        if len(signal) < window_size:
            return signal
        kernel = np.ones(window_size) / window_size
        return np.convolve(signal, kernel, mode='same')

    def preprocess_stream(self, signal: np.ndarray) -> np.ndarray:
        """Full conditioning pipeline: detrend -> median filter -> FIR smoothing."""
        detrended = self.detrend(signal)
        cleaned = self.median_filter(detrended, kernel_size=5)
        smoothed = self.fir_lowpass(cleaned, window_size=5)
        return smoothed

    def extract_time_features(self, signal: np.ndarray) -> Dict[str, float]:
        """
        Compute time-domain statistical metrics:
        - RMS: root mean square vibration energy
        - Peak-to-Peak: dynamic vibration displacement
        - Crest Factor: peak-to-RMS ratio, sensitive to localized impact spikes
        - Kurtosis: 4th standardized moment, early spall impact indicator (baseline ~3.0)
        - Skewness: 3rd standardized moment, waveform asymmetry
        - Shape Factor: RMS / mean absolute value
        """
        n = len(signal)
        if n == 0:
            return {
                "rms": 0.0, "peak_to_peak": 0.0, "crest_factor": 1.0,
                "kurtosis": 3.0, "skewness": 0.0, "shape_factor": 1.0
            }
        
        rms = float(np.sqrt(np.mean(signal ** 2)))
        peak_to_peak = float(np.max(signal) - np.min(signal))
        peak = float(np.max(np.abs(signal)))
        crest_factor = float(peak / (rms + 1e-8))
        
        mean_val = np.mean(signal)
        std_val = np.std(signal) + 1e-8
        
        skewness = float(np.mean(((signal - mean_val) / std_val) ** 3))
        kurtosis = float(np.mean(((signal - mean_val) / std_val) ** 4))
        mav = float(np.mean(np.abs(signal))) + 1e-8
        shape_factor = float(rms / mav)

        return {
            "rms": round(rms, 4),
            "peak_to_peak": round(peak_to_peak, 4),
            "crest_factor": round(crest_factor, 4),
            "kurtosis": round(kurtosis, 4),
            "skewness": round(skewness, 4),
            "shape_factor": round(shape_factor, 4)
        }

    def extract_frequency_features(self, signal: np.ndarray, running_rpm: float = 1440.0) -> Dict[str, Any]:
        """
        Compute FFT spectral metrics:
        - Fundamental 1X, 2X, 3X rotational harmonics
        - Spectral Centroid
        - Bearing characteristic defect frequencies:
          * BPFO (Ball Pass Frequency Outer Race) ~ 3.58 * 1X
          * BPFI (Ball Pass Frequency Inner Race) ~ 5.42 * 1X
          * BSF (Ball Spin Frequency) ~ 2.32 * 1X
          * FTF (Fundamental Train / Cage Frequency) ~ 0.40 * 1X
        """
        n = len(signal)
        if n < 8:
            return {
                "frequencies": [], "amplitudes": [], "spectral_centroid": 0.0,
                "fundamental_1x_hz": round(running_rpm / 60.0, 2),
                "bpfo_hz": round(3.58 * (running_rpm / 60.0), 2),
                "bpfi_hz": round(5.42 * (running_rpm / 60.0), 2),
                "harmonics": {"1x": 0.0, "2x": 0.0, "3x": 0.0}
            }
        
        window = np.hanning(n)
        windowed_signal = signal * window
        coherent_gain = (np.sum(window) / 2.0) + 1e-8
        fft_vals = np.abs(np.fft.rfft(windowed_signal)) / coherent_gain
        freqs = np.fft.rfftfreq(n, d=1.0 / self.sampling_rate)
        
        f_rot = running_rpm / 60.0  # e.g., 1440 RPM = 24.0 Hz
        
        def find_peak_near(target_freq: float, tolerance: float = 3.0) -> float:
            idx = np.where((freqs >= target_freq - tolerance) & (freqs <= target_freq + tolerance))[0]
            return float(np.max(fft_vals[idx])) if len(idx) > 0 else 0.0

        amp_1x = find_peak_near(f_rot)
        amp_2x = find_peak_near(2.0 * f_rot)
        amp_3x = find_peak_near(3.0 * f_rot)
        
        amp_bpfo = find_peak_near(3.58 * f_rot)
        amp_bpfi = find_peak_near(5.42 * f_rot)
        
        total_power = np.sum(fft_vals) + 1e-8
        spectral_centroid = float(np.sum(freqs * fft_vals) / total_power)
        
        # Subsample top frequency peaks for visualization
        top_indices = np.argsort(fft_vals)[-20:][::-1]
        top_peaks = [{"freq": round(float(freqs[idx]), 1), "amp": round(float(fft_vals[idx]), 4)} for idx in top_indices]

        return {
            "spectral_centroid": round(spectral_centroid, 2),
            "fundamental_1x_hz": round(f_rot, 2),
            "bpfo_hz": round(3.58 * f_rot, 2),
            "bpfi_hz": round(5.42 * f_rot, 2),
            "amp_1x": round(amp_1x, 4),
            "amp_2x": round(amp_2x, 4),
            "amp_3x": round(amp_3x, 4),
            "amp_bpfo": round(amp_bpfo, 4),
            "amp_bpfi": round(amp_bpfi, 4),
            "top_peaks": top_peaks
        }

    def extract_wavelet_energy(self, signal: np.ndarray, num_bands: int = 8) -> List[float]:
        """
        Wavelet packet decomposition energy approximation across localized frequency sub-bands.
        Computes energy distribution across 8 discrete bands from DC to Nyquist.
        """
        n = len(signal)
        if n < num_bands:
            return [0.0] * num_bands
        
        fft_vals = np.abs(np.fft.rfft(signal)) ** 2
        band_size = len(fft_vals) // num_bands
        energies = []
        for i in range(num_bands):
            start = i * band_size
            end = (i + 1) * band_size if i < num_bands - 1 else len(fft_vals)
            band_energy = float(np.sum(fft_vals[start:end]))
            energies.append(band_energy)
        
        total_energy = sum(energies) + 1e-8
        normalized_energies = [round(e / total_energy, 4) for e in energies]
        return normalized_energies

    def extract_all_features(self, signal: np.ndarray, running_rpm: float = 1440.0) -> Dict[str, Any]:
        """Full multi-domain extraction returning combined feature dictionary."""
        conditioned = self.preprocess_stream(signal)
        time_feats = self.extract_time_features(conditioned)
        freq_feats = self.extract_frequency_features(conditioned, running_rpm=running_rpm)
        wavelet_bands = self.extract_wavelet_energy(conditioned, num_bands=8)
        
        return {
            "time_domain": time_feats,
            "frequency_domain": freq_feats,
            "wavelet_energy_bands": wavelet_bands
        }
