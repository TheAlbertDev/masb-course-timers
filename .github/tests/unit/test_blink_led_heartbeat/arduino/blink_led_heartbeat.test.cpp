#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"
#include "Arduino.h"
#include <math.h>

// Project source file functions
extern void setup(void);
extern void loop(void);

TEST_GROUP(BlinkLedHeartbeat) // clang-format off
{
    void setup()
    {
        mock().expectOneCall("HardwareTimer::constructor").withParameter("timer", TIM2);

        ::setup(); // Call the actual setup function

        mock().checkExpectations();
    }

    void teardown()
    {
        HardwareTimer *tim = SPY_HARDWARE_TIMER_GetLastCreatedInstance();
        if (tim != nullptr)
        {
            delete tim;
            SPY_HARDWARE_TIMER_ClearLastCreatedInstance();
        }
        mock().clear();
    }
}; // clang-format on

TEST(BlinkLedHeartbeat, Sinusoidal_PWM_Generation)
{
    // Constants from the implementation
    const double pi = 3.14;
    const double amplitude = 25.0 / 2.0; // 12.5
    const double period = 2.0;

    // Mock millis to return a specific time value
    mock().expectOneCall("millis").andReturnValue(1000); // 1 second

    // Calculate expected duty cycle at t=1s
    double expected_duty = amplitude * sin(2 * pi / period * 1000 / 1000) + amplitude;

    mock().expectOneCall("HardwareTimer::setPWM").withParameter("channel", 1).withParameter("pin", 13).withParameter("frequency", 200).withParameter("duty", expected_duty);

    ::loop();

    mock().checkExpectations();
}

TEST(BlinkLedHeartbeat, Duty_Cycle_At_Different_Times)
{
    // Constants from the implementation
    const double pi = 3.14;
    const double amplitude = 25.0 / 2.0; // 12.5
    const double period = 2.0;

    // Test at t=0s: sin(0) = 0, so duty = amplitude + amplitude = 2*amplitude
    mock().expectOneCall("millis").andReturnValue(0);
    double expected_duty_0ms = amplitude * sin(2 * pi / period * 0 / 1000) + amplitude;

    mock().expectOneCall("HardwareTimer::setPWM").withParameter("channel", 1).withParameter("pin", 13).withParameter("frequency", 200).withParameter("duty", expected_duty_0ms);

    ::loop();

    // Test at t=0.5s: sin(pi) = 0, so duty = amplitude
    mock().expectOneCall("millis").andReturnValue(500); // 0.5 seconds
    double expected_duty_500ms = amplitude * sin(2 * pi / period * 500 / 1000) + amplitude;
    mock().expectOneCall("HardwareTimer::setPWM").withParameter("channel", 1).withParameter("pin", 13).withParameter("frequency", 200).withParameter("duty", expected_duty_500ms);

    ::loop();

    // Test at t=1s: sin(2pi) = 0, so duty = amplitude
    mock().expectOneCall("millis").andReturnValue(1000); // 1 second
    double expected_duty_1000ms = amplitude * sin(2 * pi / period * 1000 / 1000) + amplitude;
    mock().expectOneCall("HardwareTimer::setPWM").withParameter("channel", 1).withParameter("pin", 13).withParameter("frequency", 200).withParameter("duty", expected_duty_1000ms);

    ::loop();

    mock().checkExpectations();
}