import pytest
import time
import RPi.GPIO as GPIO
import sys
import math
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import os


def test_pwm_frequency_200hz(setup_gpio):
    """Test that PWM signal operates at approximately 200Hz."""
    
    expected_frequency = 200.0
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 1.0  # Monitor for 1 second for frequency measurement
    
    print(f"Monitoring PWM frequency for {monitoring_duration} seconds...")
    print(f"Initial LED state: {last_state}")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transition_time = time.time() - start_time
            transitions.append({
                'time': transition_time,
                'from_state': last_state,
                'to_state': current_state
            })
            last_state = current_state
        
        time.sleep(0.0001)  # Check every 0.1ms for accurate PWM timing
    
    print(f"Total transitions in {monitoring_duration}s: {len(transitions)}")
    
    # At 200Hz, we expect 400 transitions per second (200 HIGH->LOW + 200 LOW->HIGH)
    # Allow some tolerance: 320-480 transitions (160-240 Hz effective)
    expected_transitions = int(expected_frequency * 2 * monitoring_duration)  # Each cycle has 2 transitions
    assert expected_transitions - 80 <= len(transitions) <= expected_transitions + 80, f"Expected {expected_transitions-80}-{expected_transitions+80} transitions for ~200Hz, found {len(transitions)}"
    
    # Calculate average period between HIGH->LOW transitions (complete cycles)
    high_to_low_times = []
    for transition in transitions:
        if transition['from_state'] == GPIO.HIGH and transition['to_state'] == GPIO.LOW:
            high_to_low_times.append(transition['time'])
    
    if len(high_to_low_times) >= 2:
        periods = []
        for i in range(1, len(high_to_low_times)):
            period = high_to_low_times[i] - high_to_low_times[i-1]
            periods.append(period)
            print(f"Period {i}: {period*1000:.2f}ms")
        
        avg_period = sum(periods) / len(periods)
        frequency = 1.0 / avg_period
        print(f"Average period: {avg_period*1000:.2f}ms")
        print(f"Calculated frequency: {frequency:.1f}Hz")
        
        # Frequency should be approximately 200Hz (±20Hz tolerance)
        assert expected_frequency - 20 <= frequency <= expected_frequency + 20, f"Frequency {frequency:.1f}Hz should be ~{expected_frequency}Hz"
    
    print(f"✓ PWM frequency is approximately {expected_frequency}Hz")


def test_heartbeat_duty_cycle_variation(setup_gpio):
    """Test that duty cycle varies over time in a sinusoidal pattern."""
    
    measurement_intervals = []
    measurement_duration = 0.3  # Short measurements to capture variations
    total_measurements = 15     # Take 15 measurements over ~4.5 seconds
    
    print(f"Measuring duty cycle variation over {total_measurements} intervals...")
    
    for measurement_idx in range(total_measurements):
        high_times = []
        low_times = []
        last_state = GPIO.input(17)
        state_start_time = time.time()
        start_time = time.time()
        
        while time.time() - start_time < measurement_duration:
            current_state = GPIO.input(17)
            current_time = time.time()
            
            if current_state != last_state:
                state_duration = current_time - state_start_time
                
                if last_state == GPIO.HIGH:
                    high_times.append(state_duration)
                else:
                    low_times.append(state_duration)
                
                state_start_time = current_time
                last_state = current_state
            
            time.sleep(0.0001)  # Check every 0.1ms
        
        if len(high_times) > 10 and len(low_times) > 10:  # Enough samples
            avg_high_time = sum(high_times) / len(high_times)
            avg_low_time = sum(low_times) / len(low_times)
            avg_period = avg_high_time + avg_low_time
            duty_cycle = (avg_high_time / avg_period) * 100
            
            measurement_time = measurement_idx * (measurement_duration + 0.1)
            measurement_intervals.append({
                'time': measurement_time,
                'duty_cycle': duty_cycle
            })
            print(f"  t={measurement_time:.1f}s: duty_cycle={duty_cycle:.1f}%")
        
        time.sleep(0.1)  # Small pause between measurements
    
    print(f"Collected {len(measurement_intervals)} duty cycle measurements")
    
    # Should have enough measurements
    assert len(measurement_intervals) >= 10, f"Need at least 10 measurements, got {len(measurement_intervals)}"
    
    # Extract duty cycle values
    duty_cycles = [m['duty_cycle'] for m in measurement_intervals]
    
    # Check that duty cycle varies significantly (not constant)
    min_duty = min(duty_cycles)
    max_duty = max(duty_cycles)
    duty_range = max_duty - min_duty
    
    print(f"Duty cycle range: {min_duty:.1f}% - {max_duty:.1f}% (range: {duty_range:.1f}%)")
    
    # For heartbeat with amplitude 12.5, expect variation from ~0% to ~25%
    expected_duty_min = 0.0
    expected_duty_max = 25.0
    expected_duty_range = expected_duty_max - expected_duty_min
    assert duty_range >= expected_duty_range * 0.6, f"Duty cycle range {duty_range:.1f}% should be ≥{expected_duty_range * 0.6:.1f}% for heartbeat effect"
    assert max_duty <= expected_duty_max + 2.0, f"Maximum duty cycle {max_duty:.1f}% should be ≤{expected_duty_max + 2.0:.1f}%"
    assert min_duty >= max(0, expected_duty_min - 2.0), f"Minimum duty cycle {min_duty:.1f}% should be ≥{max(0, expected_duty_min - 2.0):.1f}%"
    
    print("✓ Duty cycle varies significantly over time (heartbeat effect detected)")


def test_fft_sinusoidal_analysis(setup_gpio):
    """Test that heartbeat pattern is truly sinusoidal using FFT analysis."""
    
    measurements = []
    measurement_duration = 0.08  # Short measurements for better temporal resolution
    total_time = 8.0  # Collect data for 8 seconds (4 complete cycles)
    
    print(f"Collecting heartbeat data for FFT analysis over {total_time} seconds...")
    
    absolute_start_time = time.time()
    
    while time.time() - absolute_start_time < total_time:
        measurement_start = time.time()
        relative_time = measurement_start - absolute_start_time
        
        high_times = []
        low_times = []
        last_state = GPIO.input(17)
        state_start_time = time.time()
        
        # Quick duty cycle measurement
        while time.time() - measurement_start < measurement_duration:
            current_state = GPIO.input(17)
            now = time.time()
            
            if current_state != last_state:
                state_duration = now - state_start_time
                
                if last_state == GPIO.HIGH:
                    high_times.append(state_duration)
                else:
                    low_times.append(state_duration)
                
                state_start_time = now
                last_state = current_state
            
            time.sleep(0.0001)
        
        if len(high_times) > 2 and len(low_times) > 2:
            avg_high_time = sum(high_times) / len(high_times)
            avg_low_time = sum(low_times) / len(low_times)
            avg_period = avg_high_time + avg_low_time
            duty_cycle = (avg_high_time / avg_period) * 100
            
            measurements.append({
                'time': relative_time,
                'duty_cycle': duty_cycle
            })
        
        time.sleep(0.02)  # Small pause between measurements
    
    print(f"Collected {len(measurements)} measurements for FFT analysis")
    
    # Should have enough measurements
    assert len(measurements) >= 50, f"Need at least 50 measurements for FFT, got {len(measurements)}"
    
    # Extract times and duty cycles
    times = np.array([m['time'] for m in measurements])
    duties = np.array([m['duty_cycle'] for m in measurements])
    
    # Print some sample measurements
    print("Sample measurements:")
    for i in range(0, min(10, len(measurements))):
        m = measurements[i]
        print(f"  t={m['time']:.1f}s: {m['duty_cycle']:.1f}%")
    
    # Handle non-uniform sampling by interpolating to uniform grid
    # Create uniform time grid for FFT
    uniform_dt = 0.1  # 100ms sampling interval
    uniform_times = np.arange(0, total_time - uniform_dt, uniform_dt)
    
    # Interpolate duty cycle measurements to uniform grid
    try:
        uniform_duties = np.interp(uniform_times, times, duties)
    except Exception as e:
        pytest.fail(f"Failed to interpolate data for FFT analysis: {e}")
    
    print(f"Interpolated to {len(uniform_duties)} uniform samples at {uniform_dt}s intervals")
    
    # Remove DC component for better AC analysis
    dc_component = np.mean(uniform_duties)
    ac_signal = uniform_duties - dc_component
    
    print(f"DC component (average duty cycle): {dc_component:.1f}%")
    print(f"AC signal amplitude: ±{np.abs(ac_signal).max():.1f}%")
    
    # Apply window function to reduce spectral leakage
    windowed_signal = ac_signal * np.hanning(len(ac_signal))
    
    # Perform FFT
    fft_result = np.fft.fft(windowed_signal)
    freqs = np.fft.fftfreq(len(windowed_signal), uniform_dt)
    
    # Only analyze positive frequencies
    positive_freqs = freqs[:len(freqs)//2]
    positive_fft = np.abs(fft_result[:len(fft_result)//2])
    
    # Find dominant frequency
    max_idx = np.argmax(positive_fft[1:]) + 1  # Skip DC component
    dominant_freq = positive_freqs[max_idx]
    dominant_amplitude = positive_fft[max_idx]
    
    print(f"Dominant frequency: {dominant_freq:.3f} Hz")
    print(f"Dominant amplitude: {dominant_amplitude:.1f}")
    
    # Expected frequency is 0.5 Hz (2-second period)
    expected_freq = 0.5
    freq_tolerance = 0.1  # ±0.1 Hz tolerance
    
    assert abs(dominant_freq - expected_freq) <= freq_tolerance, \
        f"Dominant frequency {dominant_freq:.3f} Hz should be ~{expected_freq} Hz (±{freq_tolerance} Hz)"
    
    # Check for harmonic content (should be low for pure sinusoid)
    # Find harmonics (2f, 3f, etc.)
    harmonic_freqs = []
    harmonic_amplitudes = []
    
    for harmonic in range(2, 5):  # Check 2nd, 3rd, 4th harmonics
        expected_harmonic_freq = harmonic * dominant_freq
        
        # Find closest frequency bin to expected harmonic
        harmonic_idx = np.abs(positive_freqs - expected_harmonic_freq).argmin()
        
        if harmonic_idx < len(positive_fft) and positive_freqs[harmonic_idx] < freqs.max() / 2:
            harmonic_freqs.append(positive_freqs[harmonic_idx])
            harmonic_amplitudes.append(positive_fft[harmonic_idx])
            
            harmonic_ratio = positive_fft[harmonic_idx] / dominant_amplitude
            print(f"Harmonic {harmonic} ({positive_freqs[harmonic_idx]:.3f} Hz): {harmonic_ratio*100:.1f}% of fundamental")
    
    # Calculate Total Harmonic Distortion (THD)
    if len(harmonic_amplitudes) > 0:
        total_harmonic_power = sum(amp**2 for amp in harmonic_amplitudes)
        fundamental_power = dominant_amplitude**2
        thd = np.sqrt(total_harmonic_power / fundamental_power) * 100
        
        print(f"Total Harmonic Distortion (THD): {thd:.1f}%")
        
        # For a good sinusoidal signal, THD should be reasonably low
        # Allow for some distortion due to PWM sampling and system limitations
        assert thd <= 30.0, f"THD {thd:.1f}% should be ≤30% for reasonably sinusoidal signal"
    else:
        print("No significant harmonics found (excellent sinusoidal purity)")
    
    # Verify DC component is around expected value (amplitude = 12.5)
    expected_dc = 12.5  # From code: amplitude = 25/2 = 12.5, offset = amplitude
    dc_tolerance = 3.0  # ±3% tolerance
    
    assert abs(dc_component - expected_dc) <= dc_tolerance, \
        f"DC component {dc_component:.1f}% should be ~{expected_dc}% (±{dc_tolerance}%)"
    
    # Verify AC amplitude is close to expected (amplitude = 12.5)
    ac_amplitude = np.abs(ac_signal).max()
    expected_ac_amplitude = 12.5
    ac_tolerance = 4.0  # ±4% tolerance for AC amplitude
    
    assert abs(ac_amplitude - expected_ac_amplitude) <= ac_tolerance, \
        f"AC amplitude {ac_amplitude:.1f}% should be ~{expected_ac_amplitude}% (±{ac_tolerance}%)"
    
    # Create and save charts
    artifacts_dir = "../../../../artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Chart 1: Transient waveform (duty cycle over time)
    plt.figure(figsize=(12, 6))
    plt.plot(times, duties, 'b-', linewidth=1.5, label='Measured Duty Cycle')
    plt.plot(uniform_times, uniform_duties, 'r--', linewidth=1, alpha=0.7, label='Interpolated Duty Cycle')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Duty Cycle (%)')
    plt.title('PWM Duty Cycle Transient Waveform (Heartbeat Pattern)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xlim(0, total_time)
    waveform_path = os.path.join(artifacts_dir, 'heartbeat_waveform.png')
    plt.savefig(waveform_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved transient waveform chart: {waveform_path}")
    
    # Chart 2: FFT spectrum
    plt.figure(figsize=(12, 6))
    plt.semilogy(positive_freqs, positive_fft, 'b-', linewidth=1.5)
    plt.axvline(dominant_freq, color='r', linestyle='--', linewidth=2, 
                label=f'Dominant Freq: {dominant_freq:.3f} Hz')
    
    # Mark harmonics if they exist
    for i, (freq, amp) in enumerate(zip(harmonic_freqs, harmonic_amplitudes)):
        plt.axvline(freq, color='orange', linestyle=':', alpha=0.7,
                   label=f'Harmonic {i+2}: {freq:.3f} Hz')
    
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.title('FFT Spectrum of Heartbeat Pattern')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xlim(0, min(2.0, freqs.max()/2))  # Show up to 2 Hz or Nyquist freq
    fft_path = os.path.join(artifacts_dir, 'heartbeat_fft_spectrum.png')
    plt.savefig(fft_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved FFT spectrum chart: {fft_path}")
    
    print("✓ FFT analysis confirms sinusoidal heartbeat pattern")