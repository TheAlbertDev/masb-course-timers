#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"
#include "Arduino.h"

// Project source file functions
extern void setup(void);
extern void loop(void);

TEST_GROUP(BlinkLedIntensity) // clang-format off
{
    void setup()
    {
        mock().expectOneCall("HardwareTimer::constructor").withParameter("timer", TIM2);
        mock().expectOneCall("HardwareTimer::setPWM").withParameter("channel", 1).withParameter("pin", 13).withParameter("frequency", 200).withParameter("duty", 10.0);

        ::setup();

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

TEST(BlinkLedIntensity, Empty_Loop_Function)
{
    ::loop(); // Should not trigger any mock calls

    mock().checkExpectations();
}