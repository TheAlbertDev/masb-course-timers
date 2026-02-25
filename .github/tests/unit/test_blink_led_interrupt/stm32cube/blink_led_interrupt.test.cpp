#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

extern "C"
{
#include "main.h"

    // Project source file functions
    void setup(void);
    void loop(void);
    void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim);
    extern bool ledState;
}

TEST_GROUP(BlinkLedInterrupt) // clang-format off
{
    void setup()
    {
        ledState = false;
    }

    void teardown()
    {
        mock().clear();
    }
}; // clang-format on

TEST(BlinkLedInterrupt, Timer_Setup)
{
    mock()
        .expectOneCall("HAL_TIM_Base_Start_IT")
        .withPointerParameter("htim", &htim3)
        .andReturnValue(0);

    ::setup();

    mock().checkExpectations();
}

TEST(BlinkLedInterrupt, LED_Write_in_Loop)
{
    mock()
        .expectOneCall("HAL_GPIO_WritePin")
        .withPointerParameter("GPIOx", LED_GPIO_Port)
        .withIntParameter("GPIO_Pin", LED_Pin)
        .withIntParameter("PinState", GPIO_PIN_RESET); // ledState is false initially

    ::loop();

    // Change ledState and test again
    ledState = true;
    mock()
        .expectOneCall("HAL_GPIO_WritePin")
        .withPointerParameter("GPIOx", LED_GPIO_Port)
        .withIntParameter("GPIO_Pin", LED_Pin)
        .withIntParameter("PinState", GPIO_PIN_SET);

    ::loop();

    mock().checkExpectations();
}

TEST(BlinkLedInterrupt, Callback_Toggles_LED_State)
{
    // Test initial state
    CHECK_FALSE(ledState);

    // Call callback with htim3 and verify state toggle
    HAL_TIM_PeriodElapsedCallback(&htim3);
    CHECK_TRUE(ledState);

    // Call callback again and verify state toggle back
    HAL_TIM_PeriodElapsedCallback(&htim3);
    CHECK_FALSE(ledState);

    // Multiple toggles to ensure consistent behavior
    HAL_TIM_PeriodElapsedCallback(&htim3);
    CHECK_TRUE(ledState);

    HAL_TIM_PeriodElapsedCallback(&htim3);
    CHECK_FALSE(ledState);
}