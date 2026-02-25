#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

extern "C"
{
#include "main.h"

    // Project source file functions
    void setup(void);
    void loop(void);
}

TEST_GROUP(BlinkLedHardware){// clang-format off
    void setup(){
        // No global state to reset
    }

    void teardown(){
        mock().clear();
    }
}; // clang-format on

TEST(BlinkLedHardware, Timer_Output_Compare_Setup)
{
    // Test timer output compare start for hardware control
    mock()
        .expectOneCall("HAL_TIM_OC_Start")
        .withPointerParameter("htim", &htim2)
        .withUnsignedIntParameter("Channel", TIM_CHANNEL_1)
        .andReturnValue(0);

    ::setup();

    mock().checkExpectations();
}

TEST(BlinkLedHardware, Empty_Loop_Function)
{
    // Test that loop function is empty (no HAL calls expected)
    // This verifies that the hardware timer handles LED toggling without CPU involvement

    ::loop(); // Should not trigger any mock calls

    mock().checkExpectations();
}