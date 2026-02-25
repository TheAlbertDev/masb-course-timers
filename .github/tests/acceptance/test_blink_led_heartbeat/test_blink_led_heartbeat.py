import pytest
import time
import RPi.GPIO as GPIO
import sys
import math
import numpy as np
from scipy import signal


def test_led_pwm_activity(setup_gpio):
    """Test that LED shows PWM activity (not static)."""
    
    # For PWM heartbeat, the LED should show continuous PWM activity
    try:
        initial_led_state = GPIO.input(17)
        print(f"Initial LED state (GPIO 17): {initial_led_state}")
    except Exception as e:
        pytest.fail(f"Failed to read GPIO 17: {e}. Make sure RPi.GPIO is properly set up.")
    
    # Monitor for PWM activity in the first 0.5 seconds
    transitions = 0
    last_state = initial_led_state
    start_time = time.time()
    monitoring_duration = 0.5
    
    print(f"Monitoring for PWM activity for {monitoring_duration} seconds...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transitions += 1
            last_state = current_state
        
        time.sleep(0.001)  # Check every 1ms for PWM detection
    
    print(f"Total transitions detected in {monitoring_duration}s: {transitions}")
    
    # PWM should show significant activity
    assert transitions > 20, f"Expected significant PWM activity (>20 transitions), found {transitions}"
    
    print("✓ LED shows PWM activity from startup")


def test_pwm_frequency_200hz(setup_gpio):
    """Test that PWM signal operates at approximately 200Hz."""
    
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 1.0  # Monitor for 1 second for frequency measurement
    
    print(f"Monitoring PWM frequency for {monitoring_duration} seconds...")
    
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
    
    # At 200Hz, we expect approximately 400 transitions per second
    # Allow some tolerance for heartbeat duty cycle variation: 320-480 transitions
    assert 320 <= len(transitions) <= 480, f"Expected 320-480 transitions for ~200Hz, found {len(transitions)}"
    
    print("✓ PWM frequency is approximately 200Hz")


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
    assert duty_range >= 15.0, f"Duty cycle range {duty_range:.1f}% should be ≥15% for heartbeat effect"
    assert max_duty <= 30.0, f"Maximum duty cycle {max_duty:.1f}% should be ≤30%"
    assert min_duty >= 0.0, f"Minimum duty cycle {min_duty:.1f}% should be ≥0%"
    
    print("✓ Duty cycle varies significantly over time (heartbeat effect detected)")


def test_heartbeat_period_2_seconds(setup_gpio):
    """Test that heartbeat pattern repeats approximately every 2 seconds."""
    
    duty_measurements = []
    measurement_duration = 0.2
    total_time = 6.0  # Measure for 6 seconds to capture 3 heartbeat cycles
    measurements_per_second = int(1.0 / (measurement_duration + 0.1))
    
    print(f"Analyzing heartbeat period over {total_time} seconds...")
    
    start_time = time.time()
    while time.time() - start_time < total_time:
        current_time = time.time() - start_time
        
        high_times = []
        low_times = []
        last_state = GPIO.input(17)
        state_start_time = time.time()
        measurement_start = time.time()
        
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
        
        if len(high_times) > 5 and len(low_times) > 5:
            avg_high_time = sum(high_times) / len(high_times)
            avg_low_time = sum(low_times) / len(low_times)
            avg_period = avg_high_time + avg_low_time
            duty_cycle = (avg_high_time / avg_period) * 100
            
            duty_measurements.append({
                'time': current_time,
                'duty_cycle': duty_cycle
            })
            print(f"  t={current_time:.1f}s: {duty_cycle:.1f}%")
        
        time.sleep(0.1)
    
    print(f"Collected {len(duty_measurements)} measurements over {total_time}s")
    
    # Should have enough measurements
    assert len(duty_measurements) >= 15, f"Need at least 15 measurements, got {len(duty_measurements)}"
    
    # Look for periodicity by checking if pattern repeats
    # Expected: sinusoidal with period = 2 seconds
    # duty(t) = amplitude * sin(2π * f * t) + amplitude
    # where amplitude = 12.5, f = 1/period = 1/2 = 0.5 Hz
    
    # Check if values at t and t+2 are similar (within tolerance)
    period_matches = 0
    tolerance = 3.0  # ±3% tolerance for duty cycle matching
    expected_period = 2.0
    
    for i, measurement in enumerate(duty_measurements):
        t1 = measurement['time']
        duty1 = measurement['duty_cycle']
        
        # Find measurement closest to t1 + expected_period
        closest_match = None
        closest_time_diff = float('inf')
        
        for j, other_measurement in enumerate(duty_measurements):
            t2 = other_measurement['time']
            time_diff = abs(t2 - (t1 + expected_period))
            
            if time_diff < closest_time_diff and time_diff < 0.3:  # Within 0.3s
                closest_time_diff = time_diff
                closest_match = other_measurement
        
        if closest_match:
            duty2 = closest_match['duty_cycle']
            duty_diff = abs(duty1 - duty2)
            
            print(f"  t={t1:.1f}s ({duty1:.1f}%) vs t={closest_match['time']:.1f}s ({duty2:.1f}%) -> diff={duty_diff:.1f}%")
            
            if duty_diff <= tolerance:
                period_matches += 1
    
    # Should find several matches indicating 2-second periodicity
    match_ratio = period_matches / len(duty_measurements)
    print(f"Period matches: {period_matches}/{len(duty_measurements)} ({match_ratio*100:.1f}%)")
    
    # Should have at least 40% of measurements showing 2-second periodicity
    assert match_ratio >= 0.4, f"Period match ratio {match_ratio*100:.1f}% should be ≥40% for 2-second period"
    
    print("✓ Heartbeat pattern shows approximately 2-second periodicity")


def test_sinusoidal_pattern_characteristics(setup_gpio):
    """Test that the duty cycle follows sinusoidal characteristics."""
    
    measurements = []
    measurement_duration = 0.15
    total_time = 4.0  # Measure for 4 seconds (2 complete cycles)
    
    print(f"Analyzing sinusoidal characteristics over {total_time} seconds...")
    
    start_time = time.time()
    while time.time() - start_time < total_time:
        current_time = time.time() - start_time
        
        high_times = []
        low_times = []
        last_state = GPIO.input(17)
        state_start_time = time.time()
        measurement_start = time.time()
        
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
        
        if len(high_times) > 3 and len(low_times) > 3:
            avg_high_time = sum(high_times) / len(high_times)
            avg_low_time = sum(low_times) / len(low_times)
            avg_period = avg_high_time + avg_low_time
            duty_cycle = (avg_high_time / avg_period) * 100
            
            measurements.append({
                'time': current_time,
                'duty_cycle': duty_cycle
            })
        
        time.sleep(0.05)
    
    print(f"Collected {len(measurements)} measurements")
    
    # Should have enough measurements
    assert len(measurements) >= 20, f"Need at least 20 measurements, got {len(measurements)}"
    
    # Extract times and duty cycles
    times = [m['time'] for m in measurements]
    duties = [m['duty_cycle'] for m in measurements]
    
    # Print some sample measurements
    for i in range(0, len(measurements), len(measurements)//5):
        m = measurements[i]
        print(f"  t={m['time']:.1f}s: {m['duty_cycle']:.1f}%")
    
    # Check sinusoidal characteristics
    # 1. Should have smooth transitions (no abrupt jumps)
    abrupt_changes = 0
    change_threshold = 8.0  # More than 8% change between consecutive measurements
    
    for i in range(1, len(duties)):
        change = abs(duties[i] - duties[i-1])
        if change > change_threshold:
            abrupt_changes += 1
    
    change_ratio = abrupt_changes / (len(duties) - 1)
    print(f"Abrupt changes: {abrupt_changes}/{len(duties)-1} ({change_ratio*100:.1f}%)")
    
    # Should have mostly smooth transitions for sinusoidal pattern
    assert change_ratio <= 0.2, f"Abrupt change ratio {change_ratio*100:.1f}% should be ≤20% for smooth sinusoid"
    
    # 2. Should reach both high and low values
    min_duty = min(duties)
    max_duty = max(duties)
    
    print(f"Duty cycle extremes: {min_duty:.1f}% - {max_duty:.1f}%")
    
    # For amplitude=12.5, expect range roughly 0% to 25%
    assert max_duty >= 20.0, f"Maximum duty {max_duty:.1f}% should be ≥20% (near peak)"
    assert min_duty <= 5.0, f"Minimum duty {min_duty:.1f}% should be ≤5% (near trough)"
    
    print("✓ Duty cycle pattern shows sinusoidal characteristics")


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
    
    print("✓ FFT analysis confirms sinusoidal heartbeat pattern")


def test_continuous_heartbeat_operation(setup_gpio):
    """Test that heartbeat continues operating consistently over extended time."""
    
    # Sample duty cycles at regular intervals over a longer period
    samples = []
    sample_interval = 0.5  # Sample every 0.5 seconds
    total_samples = 20     # Over 10 seconds
    measurement_time = 0.1 # Quick measurements
    
    print(f"Testing continuous operation over {total_samples * sample_interval} seconds...")
    
    for sample_idx in range(total_samples):
        sample_start = time.time()
        
        high_times = []
        low_times = []
        last_state = GPIO.input(17)
        state_start_time = time.time()
        
        while time.time() - sample_start < measurement_time:
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
            
            sample_time = sample_idx * sample_interval
            samples.append({
                'time': sample_time,
                'duty_cycle': duty_cycle
            })
            
            if sample_idx % 4 == 0:  # Print every 4th sample
                print(f"  t={sample_time:.1f}s: {duty_cycle:.1f}%")
        
        # Wait until next sample time
        elapsed = time.time() - sample_start
        if elapsed < sample_interval:
            time.sleep(sample_interval - elapsed)
    
    print(f"Collected {len(samples)} samples over extended operation")
    
    # Should have most samples
    assert len(samples) >= total_samples * 0.8, f"Should capture at least 80% of samples, got {len(samples)}/{total_samples}"
    
    # Check that variation continues throughout (not stuck)
    first_half = samples[:len(samples)//2]
    second_half = samples[len(samples)//2:]
    
    first_duties = [s['duty_cycle'] for s in first_half]
    second_duties = [s['duty_cycle'] for s in second_half]
    
    first_range = max(first_duties) - min(first_duties)
    second_range = max(second_duties) - min(second_duties)
    
    print(f"First half duty range: {first_range:.1f}%")
    print(f"Second half duty range: {second_range:.1f}%")
    
    # Both halves should show significant variation
    assert first_range >= 10.0, f"First half range {first_range:.1f}% should be ≥10%"
    assert second_range >= 10.0, f"Second half range {second_range:.1f}% should be ≥10%"
    
    print("✓ Heartbeat operates consistently over extended period")