#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"
#include "Arduino.h"

// Project source file functions
extern void setup(void);
extern void loop(void);

TEST_GROUP(BlinkLedHardware) // clang-format off
{
    void setup()
    {
        // No global state to reset
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

TEST(BlinkLedHardware, Timer_Hardware_Configuration)
{
    mock().expectOneCall("HardwareTimer::constructor").withParameter("timer", TIM2);
    mock().expectOneCall("HardwareTimer::setMode").withParameter("channel", 1).withParameter("mode", TIMER_OUTPUT_COMPARE_TOGGLE).withParameter("pin", 13);
    mock().expectOneCall("HardwareTimer::setOverflow").withParameter("period", 1000000).withParameter("format", MICROSEC_FORMAT);
    mock().expectOneCall("HardwareTimer::resume");

    ::setup();

    mock().checkExpectations();
}

TEST(BlinkLedHardware, Empty_Loop_Function)
{
    ::loop(); // Should not trigger any mock calls

    mock().checkExpectations();
}