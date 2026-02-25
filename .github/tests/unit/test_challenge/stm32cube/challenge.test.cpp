#include "CppUTest/TestHarness.h"
#include "CppUTestExt/MockSupport.h"

extern "C"
{
#include "main.h"
}

TEST_GROUP(ChallengeSTM32) // clang-format off
{
    void setup()
    {
        // Reset test state
    }

    void teardown()
    {
        mock().clear();
    }
}; // clang-format on

TEST(ChallengeSTM32, Setup_Calls_Basic_Functions)
{
  // Allow any setup calls - students have implementation freedom
  // They can configure EXTI, timers, GPIO, etc. as needed
  mock().ignoreOtherCalls();

  ::setup();

  // Verify setup completed without errors
  // (Specific interrupt setup verification would need additional spy functions)
  mock().checkExpectations();
}

TEST(ChallengeSTM32, Empty_Loop_Function)
{
  // RESTRICTION: Loop function must be empty (no software polling)
  // LED control should be handled entirely by hardware timer interrupt
  // Button handling should be done via EXTI interrupt

  ::loop(); // Should not trigger any mock calls

  mock().checkExpectations();
}