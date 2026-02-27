import pytest
import time
import RPi.GPIO as GPIO
import sys


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


def test_pwm_duty_cycle_10_percent(setup_gpio):
    """Test that PWM duty cycle is approximately 10%."""
    
    expected_duty_cycle = 10.0
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
    assert expected_duty_cycle - 2 <= duty_cycle <= expected_duty_cycle + 2, f"Duty cycle {duty_cycle:.1f}% should be ~{expected_duty_cycle}%"
    
    print(f"✓ PWM duty cycle is approximately {expected_duty_cycle}%")