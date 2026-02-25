import pytest
import time
import RPi.GPIO as GPIO
import sys


def test_led_initially_off(setup_gpio):
    """Test that LED is initially off when the program starts."""
    
    # Monitor LED state for 1 second to ensure it's initially off
    try:
        initial_led_state = GPIO.input(17)
        print(f"Initial LED state (GPIO 17): {initial_led_state}")
    except Exception as e:
        pytest.fail(f"Failed to read GPIO 17: {e}. Make sure RPi.GPIO is properly set up.")
    
    # Monitor LED for 0.8 seconds to ensure it stays off initially
    transitions = 0
    last_state = initial_led_state
    start_time = time.time()
    monitoring_duration = 0.8
    
    print(f"Monitoring LED for {monitoring_duration} seconds to ensure it starts off...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transitions += 1
            transition_time = time.time() - start_time
            print(f"Transition at {transition_time:.3f}s: {last_state} -> {current_state}")
            last_state = current_state
        
        time.sleep(0.01)  # Check every 10ms
    
    final_state = GPIO.input(17)
    print(f"Final LED state after {monitoring_duration}s: {final_state}")
    print(f"Total transitions detected: {transitions}")
    
    # LED should start off (LOW)
    assert initial_led_state == GPIO.LOW, f"LED should be off (LOW) initially, but found {initial_led_state}"
    
    # LED should remain steady (no transitions) during initial period
    assert transitions == 0, f"LED should remain steady initially, but detected {transitions} transitions"
    
    # Final state should still be off
    assert final_state == GPIO.LOW, f"LED should remain off (LOW), but found {final_state}"
    
    print("✓ LED correctly starts and remains off")


def test_hardware_timer_blinking_1_second_interval(setup_gpio):
    """Test that LED blinks at 1-second intervals using hardware timer."""
    
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 6.0  # Monitor for 6 seconds to capture multiple cycles
    
    print(f"Monitoring hardware timer LED blinking for {monitoring_duration} seconds...")
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
            print(f"Transition at {transition_time:.3f}s: {last_state} -> {current_state}")
            last_state = current_state
        
        time.sleep(0.01)  # Check every 10ms
    
    final_state = GPIO.input(17)
    print(f"Final LED state: {final_state}")
    print(f"Total transitions: {len(transitions)}")
    
    # Should have at least 5 transitions in 6 seconds (2-3 complete cycles)
    assert len(transitions) >= 5, f"Expected at least 5 transitions in {monitoring_duration}s, found {len(transitions)}"
    
    # Check timing intervals between transitions (should be approximately 1 second)
    for i in range(1, len(transitions)):
        interval = transitions[i]['time'] - transitions[i-1]['time']
        print(f"Interval {i}: {interval:.3f}s")
        
        # Hardware timer should be more accurate than software timer (±50ms tolerance)
        assert 0.95 <= interval <= 1.05, f"Interval {i} is {interval:.3f}s, expected ~1.0s"
    
    print("✓ Hardware timer LED blinks at correct 1-second intervals")


def test_hardware_timer_precision(setup_gpio):
    """Test that hardware timer provides very precise timing."""
    
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 12.0  # Monitor for 12 seconds for better precision measurement
    
    print(f"Monitoring hardware timer precision for {monitoring_duration} seconds...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transition_time = time.time() - start_time
            transitions.append(transition_time)
            last_state = current_state
        
        time.sleep(0.01)
    
    print(f"Total transitions: {len(transitions)}")
    
    # Should have enough transitions for analysis
    assert len(transitions) >= 10, f"Need at least 10 transitions for precision test, found {len(transitions)}"
    
    # Calculate intervals
    intervals = []
    for i in range(1, len(transitions)):
        interval = transitions[i] - transitions[i-1]
        intervals.append(interval)
        print(f"Interval {i}: {interval:.3f}s")
    
    # Calculate average interval
    avg_interval = sum(intervals) / len(intervals)
    print(f"Average interval: {avg_interval:.3f}s")
    
    # Calculate standard deviation
    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
    std_dev = variance ** 0.5
    print(f"Standard deviation: {std_dev:.3f}s")
    
    # Hardware timer should be extremely precise
    assert 0.99 <= avg_interval <= 1.01, f"Average interval {avg_interval:.3f}s should be within ±10ms of 1.0s"
    assert std_dev <= 0.02, f"Standard deviation {std_dev:.3f}s should be ≤20ms for hardware precision"
    
    print("✓ Hardware timer provides extremely precise timing")


def test_cpu_free_operation(setup_gpio):
    """Test that LED continues blinking while CPU is theoretically free."""
    
    cycles_detected = 0
    last_state = GPIO.input(17)
    cycle_start_time = None
    start_time = time.time()
    monitoring_duration = 10.0  # Monitor for 10 seconds
    timing_consistency = []
    
    print(f"Testing CPU-free operation for {monitoring_duration} seconds...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            if current_state == GPIO.HIGH and cycle_start_time is None:
                # Start of a new cycle (LED turns ON)
                cycle_start_time = time.time()
            elif current_state == GPIO.LOW and cycle_start_time is not None:
                # End of a cycle (LED turns OFF)
                cycle_duration = time.time() - cycle_start_time
                cycles_detected += 1
                timing_consistency.append(cycle_duration)
                print(f"Cycle {cycles_detected}: {cycle_duration:.3f}s")
                cycle_start_time = None
                
                # Each cycle should be approximately 2 seconds (1s ON, 1s OFF)
                assert 1.9 <= cycle_duration <= 2.1, f"Cycle {cycles_detected} duration {cycle_duration:.3f}s should be ~2.0s"
            
            last_state = current_state
        
        time.sleep(0.01)
    
    print(f"Detected {cycles_detected} complete cycles")
    
    # Should have detected at least 4 complete cycles in 10 seconds
    assert cycles_detected >= 4, f"Expected at least 4 cycles in {monitoring_duration}s, found {cycles_detected}"
    
    # Check consistency of timing (hardware should be very consistent)
    if len(timing_consistency) >= 3:
        avg_cycle_time = sum(timing_consistency) / len(timing_consistency)
        cycle_variance = sum((x - avg_cycle_time) ** 2 for x in timing_consistency) / len(timing_consistency)
        cycle_std_dev = cycle_variance ** 0.5
        
        print(f"Average cycle time: {avg_cycle_time:.3f}s")
        print(f"Cycle timing standard deviation: {cycle_std_dev:.3f}s")
        
        # Hardware timer should have very consistent cycle timing
        assert cycle_std_dev <= 0.02, f"Cycle timing std dev {cycle_std_dev:.3f}s should be ≤20ms"
    
    print("✓ LED operates consistently with CPU-free hardware timer")


def test_empty_loop_validation(setup_gpio):
    """Test that blinking continues even with empty loop (confirms hardware operation)."""
    
    # This test specifically validates that the loop() function can be empty
    # and the LED will still blink because it's handled by hardware
    
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 8.0
    
    print(f"Validating hardware operation (empty loop) for {monitoring_duration} seconds...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transition_time = time.time() - start_time
            transitions.append(transition_time)
            print(f"Transition at {transition_time:.3f}s: {last_state} -> {current_state}")
            last_state = current_state
        
        time.sleep(0.01)
    
    print(f"Total transitions: {len(transitions)}")
    
    # Should have enough transitions to prove continuous operation
    assert len(transitions) >= 6, f"Expected at least 6 transitions in {monitoring_duration}s, found {len(transitions)}"
    
    # Verify that transitions are evenly spaced (within hardware precision)
    for i in range(1, len(transitions)):
        interval = transitions[i] - transitions[i-1]
        print(f"Interval {i}: {interval:.3f}s")
        assert 0.95 <= interval <= 1.05, f"Interval {i} is {interval:.3f}s, should be ~1.0s"
    
    print("✓ Hardware timer operates independently of software loop")