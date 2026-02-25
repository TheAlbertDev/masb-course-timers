#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"
#include "Arduino.h"

// Project source file functions
extern void setup(void);
extern void loop(void);
extern void changeLEDState(void);
extern bool ledState;

TEST_GROUP(BlinkLedInterrupt) // clang-format off
{
    void setup(){
        ledState = false;
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

TEST(BlinkLedInterrupt, Timer_Configuration)
{
    mock().expectOneCall("HardwareTimer::constructor").withParameter("timer", TIM3);
    mock().expectOneCall("HardwareTimer::setMode").withParameter("channel", 2).withParameter("mode", TIMER_OUTPUT_COMPARE).withParameter("pin", 13);
    mock().expectOneCall("HardwareTimer::setOverflow").withParameter("period", 1000000).withParameter("format", MICROSEC_FORMAT);
    mock().expectOneCall("HardwareTimer::attachInterrupt").withParameter("callback", changeLEDState);
    mock().expectOneCall("HardwareTimer::resume");

    mock().expectOneCall("pinMode").withParameter("dwPin", 13).withParameter("dwMode", OUTPUT);
    mock().expectOneCall("digitalWrite").withParameter("dwPin", 13).withParameter("dwVal", LOW);

    ::setup();

    mock().checkExpectations();
}

TEST(BlinkLedInterrupt, LED_State_Update_in_Loop)
{
    mock().expectOneCall("digitalWrite").withParameter("dwPin", 13).withParameter("dwVal", LOW); // ledState is false initially

    ::loop();

    ledState = true;

    mock().expectOneCall("digitalWrite").withParameter("dwPin", 13).withParameter("dwVal", HIGH);

    ::loop();

    mock().checkExpectations();
}

TEST(BlinkLedInterrupt, ISR_Toggles_LED_State)
{
    CHECK_FALSE(ledState);

    // Call ISR and verify state toggle
    changeLEDState();
    CHECK_TRUE(ledState);

    // Call ISR again and verify state toggle back
    changeLEDState();
    CHECK_FALSE(ledState);

    // Multiple toggles to ensure consistent behavior
    changeLEDState();
    CHECK_TRUE(ledState);

    changeLEDState();
    CHECK_FALSE(ledState);
}