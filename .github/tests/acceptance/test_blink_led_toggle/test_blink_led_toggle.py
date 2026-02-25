import pytest
import time
import RPi.GPIO as GPIO
import sys

def test_led_blinking_1_second_interval(setup_gpio):
    """Test that LED blinks at 1-second intervals using timer interrupts."""
    
    expected_interval = 1.0
    transitions = []
    last_state = GPIO.input(17)
    start_time = time.time()
    monitoring_duration = 5.0  # Monitor for 5 seconds to capture multiple cycles
    
    print(f"Monitoring LED blinking for {monitoring_duration} seconds...")
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

    # expected_interval is the duration for ON and OFF states individually
    # Transitions happen every expected_interval seconds
    expected_transitions = int(monitoring_duration / expected_interval)

    assert len(transitions) >= expected_transitions, f"Expected at least {expected_transitions} transitions in {monitoring_duration}s, found {len(transitions)}"
    
    # Check timing intervals between transitions (should be approximately 1 second)
    for i in range(1, len(transitions)):
        interval = transitions[i]['time'] - transitions[i-1]['time']
        print(f"Interval {i}: {interval:.3f}s")
        
        # Allow some tolerance for timer accuracy (±100ms)
        assert expected_interval - 0.1 <= interval <= expected_interval + 0.1, f"Interval {i} is {interval:.3f}s, expected ~{expected_interval}s"
    
    print(f"✓ LED blinks at correct {expected_interval}-second intervals")