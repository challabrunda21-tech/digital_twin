"""
Unit Tests for Signal Preprocessing and Multi-Domain Feature Extraction
"""

import numpy as np
import pytest
from core.signal_processing import SignalPreprocessor

def test_detrend_and_noise_suppression():
    sp = SignalPreprocessor(sampling_rate=1000.0)
    # Signal with linear drift + DC offset + transient spike
    t = np.linspace(0, 1, 500)
    drift = 2.5 * t + 5.0
    sig = np.sin(2 * np.pi * 20 * t) + drift
    sig[150] += 50.0  # Spike

    cleaned = sp.preprocess_stream(sig)
    assert len(cleaned) == len(sig)
    # DC offset should be largely eliminated
    assert abs(np.mean(cleaned)) < 1.0
    # Spike should be attenuated by median filter
    assert abs(cleaned[150]) < 10.0

def test_time_features():
    sp = SignalPreprocessor()
    t = np.linspace(0, 1, 1000)
    sig = 2.0 * np.sin(2 * np.pi * 10 * t)
    feats = sp.extract_time_features(sig)
    
    assert "rms" in feats
    assert "kurtosis" in feats
    assert "crest_factor" in feats
    # For a pure sine wave with amplitude 2.0:
    # RMS ~ 2 / sqrt(2) ~ 1.414
    assert abs(feats["rms"] - 1.414) < 0.1
    # Crest factor for pure sine ~ sqrt(2) ~ 1.414
    assert abs(feats["crest_factor"] - 1.414) < 0.1

def test_frequency_features():
    sp = SignalPreprocessor(sampling_rate=1000.0)
    t = np.linspace(0, 1, 1000)
    # Fundamental 24 Hz (1440 RPM) + 48 Hz (2X harmonic)
    sig = 1.0 * np.sin(2 * np.pi * 24.0 * t) + 0.5 * np.sin(2 * np.pi * 48.0 * t)
    freq_feats = sp.extract_frequency_features(sig, running_rpm=1440.0)
    
    assert freq_feats["fundamental_1x_hz"] == 24.0
    assert freq_feats["amp_1x"] > 0.7
    assert freq_feats["amp_2x"] > 0.3
    assert freq_feats["spectral_centroid"] > 10.0

def test_wavelet_energy_bands():
    sp = SignalPreprocessor()
    sig = np.random.randn(500)
    bands = sp.extract_wavelet_energy(sig, num_bands=8)
    assert len(bands) == 8
    # Sum of normalized energies should be ~ 1.0
    assert abs(sum(bands) - 1.0) < 0.05
