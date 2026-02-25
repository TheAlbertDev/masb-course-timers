#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"
#include <math.h>

extern "C"
{
#include "main.h"

    // Project source file functions
    void setup(void);
    void loop(void);
}

TEST_GROUP(BlinkLedHeartbeat) // clang-format off
{
    void setup()
    {
        // Reset tick counter
        SPY_setCurrentTicks(0);
    }

    void teardown()
    {
        mock().clear();
    }
}; // clang-format on

TEST(BlinkLedHeartbeat, PWM_Setup)
{
    // Test PWM start
    mock()
        .expectOneCall("HAL_TIM_PWM_Start")
        .withPointerParameter("htim", &htim2)
        .withUnsignedIntParameter("Channel", TIM_CHANNEL_1)
        .andReturnValue(0);

    ::setup();

    mock().checkExpectations();
}

TEST(BlinkLedHeartbeat, Sinusoidal_PWM_Calculation)
{
    // Set specific tick value for testing
    SPY_setCurrentTicks(1000); // 1 second

    // Mock HAL_GetTick call
    mock().expectOneCall("HAL_GetTick");

    // Calculate expected values
    const float pi = 3.14;
    const float amplitude = 25.0 / 2.0;
    const float period = 2.0;
    const uint32_t TIM2Period = 420000;

    float expected_duty = amplitude * sin(2.0 * pi / period * 1000 / 1000.0) + amplitude;
    uint32_t expected_pulse = TIM2Period * expected_duty / 100.0;

    // Expect __HAL_TIM_SET_COMPARE call with calculated value
    mock()
        .expectOneCall("__HAL_TIM_SET_COMPARE")
        .withPointerParameter("htim", &htim2)
        .withUnsignedIntParameter("channel", TIM_CHANNEL_1)
        .withUnsignedIntParameter("compare", expected_pulse);

    ::loop();

    mock().checkExpectations();
}

TEST(BlinkLedHeartbeat, PWM_Value_Range)
{
    // Test duty cycle calculation at different time points

    // At t=0, sin(0) = 0, so duty = amplitude * 0 + amplitude = amplitude
    SPY_setCurrentTicks(0);
    mock().expectOneCall("HAL_GetTick");

    const float pi = 3.14;
    const float amplitude = 25.0 / 2.0;
    const float period = 2.0;
    const uint32_t TIM2Period = 420000;

    float expected_duty_t0 = amplitude * sin(2.0 * pi / period * 0 / 1000.0) + amplitude;
    uint32_t expected_pulse_t0 = TIM2Period * expected_duty_t0 / 100.0;

    mock()
        .expectOneCall("__HAL_TIM_SET_COMPARE")
        .withPointerParameter("htim", &htim2)
        .withUnsignedIntParameter("channel", TIM_CHANNEL_1)
        .withUnsignedIntParameter("compare", expected_pulse_t0);

    ::loop();

    // At t=500ms, sin(pi/2) should give maximum value
    SPY_setCurrentTicks(500);
    mock().expectOneCall("HAL_GetTick");

    float expected_duty_t500 = amplitude * sin(2.0 * pi / period * 500 / 1000.0) + amplitude;
    uint32_t expected_pulse_t500 = TIM2Period * expected_duty_t500 / 100.0;

    mock()
        .expectOneCall("__HAL_TIM_SET_COMPARE")
        .withPointerParameter("htim", &htim2)
        .withUnsignedIntParameter("channel", TIM_CHANNEL_1)
        .withUnsignedIntParameter("compare", expected_pulse_t500);

    ::loop();

    mock().checkExpectations();
}