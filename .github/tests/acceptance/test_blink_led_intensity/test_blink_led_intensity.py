import pytest
import time
import RPi.GPIO as GPIO
import sys


def test_led_initially_off(setup_gpio):
    """Test that LED starts with PWM signal generation."""
    
    # For PWM, the LED won't be completely off, but will show PWM pattern
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
    
    # PWM should show activity (transitions), not a static state
    assert transitions > 10, f"Expected PWM activity (>10 transitions), found {transitions}"
    
    print("✓ LED shows PWM activity from startup")


def test_pwm_frequency_200hz(setup_gpio):
    """Test that PWM signal operates at approximately 200Hz."""
    
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
    assert 320 <= len(transitions) <= 480, f"Expected 320-480 transitions for ~200Hz, found {len(transitions)}"
    
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
        assert 180 <= frequency <= 220, f"Frequency {frequency:.1f}Hz should be ~200Hz"
    
    print("✓ PWM frequency is approximately 200Hz")


def test_pwm_duty_cycle_10_percent(setup_gpio):
    """Test that PWM duty cycle is approximately 10%."""
    
    high_times = []
    low_times = []
    last_state = GPIO.input(17)
    state_start_time = time.time()
    start_time = time.time()
    monitoring_duration = 2.0  # Monitor for 2 seconds for accurate duty cycle measurement
    
    print(f"Monitoring PWM duty cycle for {monitoring_duration} seconds...")
    
    while time.time() - start_time < monitoring_duration:
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
    
    print(f"Captured {len(high_times)} HIGH periods and {len(low_times)} LOW periods")
    
    # Need enough samples for accurate measurement
    assert len(high_times) >= 100, f"Need at least 100 HIGH periods for duty cycle test, found {len(high_times)}"
    assert len(low_times) >= 100, f"Need at least 100 LOW periods for duty cycle test, found {len(low_times)}"
    
    # Calculate average HIGH and LOW times
    avg_high_time = sum(high_times) / len(high_times)
    avg_low_time = sum(low_times) / len(low_times)
    
    # Calculate duty cycle
    avg_period = avg_high_time + avg_low_time
    duty_cycle = (avg_high_time / avg_period) * 100
    
    print(f"Average HIGH time: {avg_high_time*1000:.3f}ms")
    print(f"Average LOW time: {avg_low_time*1000:.3f}ms")
    print(f"Average period: {avg_period*1000:.3f}ms")
    print(f"Calculated duty cycle: {duty_cycle:.1f}%")
    
    # Duty cycle should be approximately 10% (±2% tolerance)
    assert 8.0 <= duty_cycle <= 12.0, f"Duty cycle {duty_cycle:.1f}% should be ~10%"
    
    print("✓ PWM duty cycle is approximately 10%")


def test_pwm_consistency(setup_gpio):
    """Test that PWM signal remains consistent over time."""
    
    duty_cycles = []
    measurement_intervals = 5  # Take 5 measurements over time
    interval_duration = 1.0   # Each measurement lasts 1 second
    
    print(f"Testing PWM consistency over {measurement_intervals} intervals of {interval_duration}s each...")
    
    for interval in range(measurement_intervals):
        print(f"Measurement interval {interval + 1}/{measurement_intervals}")
        
        high_times = []
        low_times = []
        last_state = GPIO.input(17)
        state_start_time = time.time()
        start_time = time.time()
        
        while time.time() - start_time < interval_duration:
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
            
            time.sleep(0.0001)
        
        if len(high_times) > 0 and len(low_times) > 0:
            avg_high_time = sum(high_times) / len(high_times)
            avg_low_time = sum(low_times) / len(low_times)
            avg_period = avg_high_time + avg_low_time
            duty_cycle = (avg_high_time / avg_period) * 100
            
            duty_cycles.append(duty_cycle)
            print(f"  Interval {interval + 1} duty cycle: {duty_cycle:.2f}%")
        
        time.sleep(0.1)  # Small pause between measurements
    
    print(f"Duty cycles measured: {[f'{dc:.2f}%' for dc in duty_cycles]}")
    
    # Should have collected enough measurements
    assert len(duty_cycles) >= 3, f"Need at least 3 duty cycle measurements, got {len(duty_cycles)}"
    
    # Calculate consistency metrics
    avg_duty_cycle = sum(duty_cycles) / len(duty_cycles)
    duty_std_dev = (sum((dc - avg_duty_cycle)**2 for dc in duty_cycles) / len(duty_cycles)) ** 0.5
    
    print(f"Average duty cycle: {avg_duty_cycle:.2f}%")
    print(f"Standard deviation: {duty_std_dev:.2f}%")
    
    # PWM should be consistent (low standard deviation)
    assert duty_std_dev <= 1.0, f"Duty cycle std dev {duty_std_dev:.2f}% should be ≤1.0%"
    
    # Average should still be around 10%
    assert 8.0 <= avg_duty_cycle <= 12.0, f"Average duty cycle {avg_duty_cycle:.2f}% should be ~10%"
    
    print("✓ PWM signal remains consistent over time")


def test_fixed_intensity_no_variation(setup_gpio):
    """Test that LED intensity remains fixed (no variation like in heartbeat mode)."""
    
    # Sample duty cycles at different times to ensure they're constant
    duty_samples = []
    sample_count = 10
    sample_interval = 0.5  # Sample every 0.5 seconds
    
    print(f"Sampling duty cycle {sample_count} times over {sample_count * sample_interval}s to check for variations...")
    
    for sample in range(sample_count):
        high_times = []
        low_times = []
        last_state = GPIO.input(17)
        state_start_time = time.time()
        start_time = time.time()
        measurement_duration = 0.2  # Quick measurement
        
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
            
            time.sleep(0.0001)
        
        if len(high_times) > 0 and len(low_times) > 0:
            avg_high_time = sum(high_times) / len(high_times)
            avg_low_time = sum(low_times) / len(low_times)
            avg_period = avg_high_time + avg_low_time
            duty_cycle = (avg_high_time / avg_period) * 100
            
            duty_samples.append(duty_cycle)
            print(f"Sample {sample + 1}: {duty_cycle:.2f}%")
        
        time.sleep(sample_interval - measurement_duration)  # Wait until next sample
    
    print(f"Duty cycle samples: {[f'{dc:.2f}%' for dc in duty_samples]}")
    
    # Should have enough samples
    assert len(duty_samples) >= 5, f"Need at least 5 samples, got {len(duty_samples)}"
    
    # All samples should be close to 10% (very low variation expected)
    min_duty = min(duty_samples)
    max_duty = max(duty_samples)
    duty_range = max_duty - min_duty
    
    print(f"Duty cycle range: {min_duty:.2f}% - {max_duty:.2f}% (±{duty_range/2:.2f}%)")
    
    # Fixed intensity mode should have very little variation
    assert duty_range <= 2.0, f"Duty cycle range {duty_range:.2f}% should be ≤2.0% for fixed intensity"
    
    print("✓ LED intensity remains fixed (no variation detected)")