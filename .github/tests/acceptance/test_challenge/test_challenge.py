import pytest
import time
import RPi.GPIO as GPIO
import sys


def test_led_initially_off(setup_gpio):
    """Test that LED is initially off when the program starts."""
    
    # Monitor LED state for 2 seconds to ensure it stays consistently off
    try:
        initial_led_state = GPIO.input(17)
        print(f"Initial LED state (GPIO 17): {initial_led_state}")
    except Exception as e:
        pytest.fail(f"Failed to read GPIO 17: {e}. Make sure RPi.GPIO is properly set up.")
    
    # Monitor LED for 2 seconds to detect any unexpected blinking
    transitions = 0
    led_states = []
    last_state = initial_led_state
    start_time = time.time()
    monitoring_duration = 2.0
    
    print(f"Monitoring LED for {monitoring_duration} seconds to ensure it stays off...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        led_states.append(current_state)
        
        if current_state != last_state:
            transitions += 1
            transition_time = time.time() - start_time
            print(f"Unexpected transition at {transition_time:.3f}s: {last_state} -> {current_state}")
            last_state = current_state
        
        time.sleep(0.01)  # Check every 10ms
    
    final_state = GPIO.input(17)
    print(f"Final LED state after {monitoring_duration}s: {final_state}")
    print(f"Total transitions detected: {transitions}")
    
    # LED should have no transitions (stay consistently off)
    assert transitions == 0, f"LED should not blink initially, but detected {transitions} transitions"
    
    # LED should be off (LOW) throughout the monitoring period
    assert final_state == GPIO.LOW, f"LED should be off (LOW) initially, but found {final_state}"
    
    print("✓ LED is correctly and consistently off initially")


def test_button_press_starts_blinking(setup_gpio):
    """Test that pressing the button starts LED blinking."""
    
    print("Testing button press to start blinking...")
    
    # Confirm LED is initially off
    initial_state = GPIO.input(17)
    assert initial_state == GPIO.LOW, f"LED should be off initially, found {initial_state}"
    
    # Simulate button press (falling edge from HIGH to LOW)
    print("Simulating button press...")
    GPIO.output(27, GPIO.LOW)
    time.sleep(0.1)  # Hold button down for 100ms
    GPIO.output(27, GPIO.HIGH)
    
    # Wait a moment for interrupt to process
    time.sleep(0.3)
    
    # Monitor LED for blinking activity
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 3.0  # Monitor for 3 seconds to capture multiple blinks
    
    print(f"Monitoring LED for {monitoring_duration} seconds after button press...")
    print(f"Initial LED state after button press: {last_state}")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transition_time = time.time() - start_time
            transitions.append({
                'time': transition_time,
                'from_state': last_state,
                'to_state': current_state
            })
            print(f"LED transition at {transition_time:.3f}s: {last_state} -> {current_state}")
            last_state = current_state
        
        time.sleep(0.01)  # Check every 10ms
    
    print(f"Total transitions after button press: {len(transitions)}")
    
    # Should have transitions indicating blinking started
    assert len(transitions) >= 4, f"Expected at least 4 transitions in {monitoring_duration}s, found {len(transitions)}"
    
    # Check timing intervals (should be approximately 0.5 seconds for 500ms timer)
    for i in range(1, len(transitions)):
        interval = transitions[i]['time'] - transitions[i-1]['time']
        print(f"Interval {i}: {interval:.3f}s")
        
        # Allow some tolerance for timer accuracy (±100ms)
        assert 0.4 <= interval <= 0.6, f"Interval {i} is {interval:.3f}s, expected ~0.5s"
    
    print("✓ Button press successfully starts LED blinking")


def test_button_press_stops_blinking(setup_gpio):
    """Test that pressing the button again stops LED blinking."""
    
    print("Testing button press sequence: start -> stop...")
    
    # First button press to start blinking
    print("First button press to start blinking...")
    GPIO.output(27, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(27, GPIO.HIGH)
    time.sleep(0.3)  # Wait for blinking to start
    
    # Verify blinking has started
    transitions_before_stop = 0
    last_state = GPIO.input(17)
    check_start = time.time()
    
    while time.time() - check_start < 1.5:  # Check for 1.5 seconds
        current_state = GPIO.input(17)
        if current_state != last_state:
            transitions_before_stop += 1
            last_state = current_state
        time.sleep(0.01)
    
    assert transitions_before_stop >= 2, f"LED should be blinking before second button press, found {transitions_before_stop} transitions"
    print(f"Confirmed blinking with {transitions_before_stop} transitions")
    
    # Second button press to stop blinking
    print("Second button press to stop blinking...")
    GPIO.output(27, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(27, GPIO.HIGH)
    time.sleep(0.3)  # Wait for stop command to process
    
    # Monitor LED to confirm it stopped and stays off
    transitions_after_stop = 0
    led_states = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 2.0
    
    print(f"Monitoring LED for {monitoring_duration} seconds after stop command...")
    print(f"LED state immediately after stop: {last_state}")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        led_states.append(current_state)
        
        if current_state != last_state:
            transitions_after_stop += 1
            transition_time = time.time() - start_time
            print(f"Unexpected transition at {transition_time:.3f}s: {last_state} -> {current_state}")
            last_state = current_state
        
        time.sleep(0.01)
    
    final_state = GPIO.input(17)
    print(f"Final LED state: {final_state}")
    print(f"Transitions after stop: {transitions_after_stop}")
    
    # LED should have stopped blinking (no transitions) and be off
    assert transitions_after_stop == 0, f"LED should stop blinking, but detected {transitions_after_stop} transitions"
    assert final_state == GPIO.LOW, f"LED should be off after stop, but found {final_state}"
    
    print("✓ Button press successfully stops LED blinking")


def test_multiple_button_press_cycles(setup_gpio):
    """Test multiple button press cycles: off -> on -> off -> on."""
    
    print("Testing multiple button press cycles...")
    
    cycle_results = []
    
    for cycle in range(3):  # Test 3 cycles
        print(f"\n--- Cycle {cycle + 1} ---")
        
        # Button press to start blinking
        print(f"Cycle {cycle + 1}: Starting blinking...")
        GPIO.output(27, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(27, GPIO.HIGH)
        time.sleep(0.3)
        
        # Monitor for blinking activity
        transitions = 0
        last_state = GPIO.input(17)
        start_time = time.time()
        
        while time.time() - start_time < 1.5:
            current_state = GPIO.input(17)
            if current_state != last_state:
                transitions += 1
                last_state = current_state
            time.sleep(0.01)
        
        blinking_detected = transitions >= 2
        print(f"Cycle {cycle + 1}: Blinking transitions = {transitions}, detected = {blinking_detected}")
        
        # Button press to stop blinking
        print(f"Cycle {cycle + 1}: Stopping blinking...")
        GPIO.output(27, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(27, GPIO.HIGH)
        time.sleep(0.3)
        
        # Monitor to confirm stopped
        stop_transitions = 0
        last_state = GPIO.input(17)
        start_time = time.time()
        
        while time.time() - start_time < 1.0:
            current_state = GPIO.input(17)
            if current_state != last_state:
                stop_transitions += 1
                last_state = current_state
            time.sleep(0.01)
        
        final_state = GPIO.input(17)
        stopped_correctly = stop_transitions == 0 and final_state == GPIO.LOW
        print(f"Cycle {cycle + 1}: Stop transitions = {stop_transitions}, final state = {final_state}, stopped = {stopped_correctly}")
        
        cycle_results.append({
            'cycle': cycle + 1,
            'blinking_started': blinking_detected,
            'blinking_stopped': stopped_correctly
        })
        
        time.sleep(0.2)  # Brief pause between cycles
    
    # Verify all cycles worked
    print(f"\n--- Cycle Summary ---")
    for result in cycle_results:
        print(f"Cycle {result['cycle']}: Start={result['blinking_started']}, Stop={result['blinking_stopped']}")
        assert result['blinking_started'], f"Cycle {result['cycle']} failed to start blinking"
        assert result['blinking_stopped'], f"Cycle {result['cycle']} failed to stop blinking"
    
    print("✓ Multiple button press cycles work correctly")


def test_button_debounce_handling(setup_gpio):
    """Test that button debouncing prevents multiple triggers."""
    
    print("Testing button debounce handling...")
    
    # Rapid button presses (should be debounced)
    print("Sending rapid button presses (should be debounced)...")
    for i in range(5):
        GPIO.output(27, GPIO.LOW)
        time.sleep(0.05)  # 50ms pulses (faster than 200ms debounce)
        GPIO.output(27, GPIO.HIGH)
        time.sleep(0.05)
    
    time.sleep(0.5)  # Wait for any processing
    
    # Check LED state - should either be off or blinking consistently
    transitions = 0
    last_state = GPIO.input(17)
    start_time = time.time()
    
    while time.time() - start_time < 2.0:
        current_state = GPIO.input(17)
        if current_state != last_state:
            transitions += 1
            last_state = current_state
        time.sleep(0.01)
    
    print(f"Transitions after rapid presses: {transitions}")
    
    # Should either be stable (0 transitions) or blinking consistently
    # If blinking, should have reasonable number of transitions for 2 seconds at 0.5s intervals
    if transitions == 0:
        print("LED is stable (off) - debouncing prevented erratic behavior")
    else:
        # If blinking, should be consistent (approximately 4 transitions in 2 seconds)
        assert 3 <= transitions <= 6, f"If blinking, should be consistent, but found {transitions} transitions"
        print("LED is blinking consistently - debouncing allowed single activation")
    
    print("✓ Button debouncing works correctly")


def test_empty_loop_operation(setup_gpio):
    """Test that system works with empty loop (interrupt-driven)."""
    
    print("Testing interrupt-driven operation (simulating empty loop)...")
    
    # This test validates that all functionality works via interrupts
    # without requiring any code in the loop() function
    
    # Button press to start
    print("Starting blinking with interrupt...")
    GPIO.output(27, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(27, GPIO.HIGH)
    time.sleep(0.3)
    
    # Monitor blinking for extended period to ensure it's stable
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 4.0  # Monitor for 4 seconds
    
    print(f"Monitoring interrupt-driven blinking for {monitoring_duration} seconds...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transition_time = time.time() - start_time
            transitions.append(transition_time)
            last_state = current_state
        
        time.sleep(0.01)
    
    print(f"Total transitions in {monitoring_duration}s: {len(transitions)}")
    
    # Should have consistent transitions
    assert len(transitions) >= 6, f"Expected at least 6 transitions in {monitoring_duration}s, found {len(transitions)}"
    
    # Check timing consistency
    intervals = []
    for i in range(1, len(transitions)):
        interval = transitions[i] - transitions[i-1]
        intervals.append(interval)
        
        if i <= 5:  # Print first few intervals
            print(f"Interval {i}: {interval:.3f}s")
    
    # All intervals should be approximately 0.5s
    for i, interval in enumerate(intervals):
        assert 0.4 <= interval <= 0.6, f"Interval {i+1} is {interval:.3f}s, expected ~0.5s"
    
    # Stop with second button press
    print("Stopping blinking with interrupt...")
    GPIO.output(27, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(27, GPIO.HIGH)
    time.sleep(0.5)
    
    # Verify stopped
    final_state = GPIO.input(17)
    assert final_state == GPIO.LOW, f"LED should be off after stop, found {final_state}"
    
    print("✓ Interrupt-driven operation works correctly (empty loop validated)")


def test_timer_accuracy_500ms(setup_gpio):
    """Test that timer provides accurate 500ms intervals."""
    
    print("Testing timer accuracy for 500ms intervals...")
    
    # Start blinking
    GPIO.output(27, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(27, GPIO.HIGH)
    time.sleep(0.3)
    
    # Collect precise timing measurements
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 6.0  # Monitor for 6 seconds for good statistics
    
    print(f"Measuring timer accuracy over {monitoring_duration} seconds...")
    
    while time.time() - start_time < monitoring_duration:
        current_state = GPIO.input(17)
        
        if current_state != last_state:
            transition_time = time.time() - start_time
            transitions.append(transition_time)
            last_state = current_state
        
        time.sleep(0.001)  # High resolution sampling
    
    print(f"Collected {len(transitions)} transitions")
    
    # Calculate intervals
    intervals = []
    for i in range(1, len(transitions)):
        interval = transitions[i] - transitions[i-1]
        intervals.append(interval)
        if i <= 8:  # Print first 8 intervals
            print(f"Interval {i}: {interval:.3f}s")
    
    # Calculate statistics
    avg_interval = sum(intervals) / len(intervals)
    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
    std_dev = variance ** 0.5
    
    print(f"Average interval: {avg_interval:.3f}s")
    print(f"Standard deviation: {std_dev:.3f}s")
    
    # Timer should be accurate to 500ms ±30ms
    assert 0.47 <= avg_interval <= 0.53, f"Average interval {avg_interval:.3f}s should be ~0.5s"
    assert std_dev <= 0.02, f"Standard deviation {std_dev:.3f}s should be ≤20ms for timer accuracy"
    
    # Stop blinking
    GPIO.output(27, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(27, GPIO.HIGH)
    
    print("✓ Timer provides accurate 500ms intervals")