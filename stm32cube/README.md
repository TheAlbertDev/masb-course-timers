# _Timers_

<img align="left" src="https://img.shields.io/badge/Environment-STM32Cube-blue"><img align="left" src="https://img.shields.io/badge/Estimated_duration-2.5 h-green"></br>

Having seen the _timers_ in Arduino, now we are going to see them with STM32Cube. There is nothing new to introduce since **we already know what a _timer_ is**, **how it works** and what **some of its uses** are. Now we are going to see how to do it at the register level. Once again, we will encounter a small jump in complexity (**which is not difficulty, remember**) that will offer us greater flexibility when using the _timers_ of our microcontroller.

We will also take the opportunity to take a **first look at professional debugging tools** that will help us in our daily work to ensure that our programs work correctly. Let's go! 💪🏻

## Objectives

- Generation of an interruption based on a _timer_ at the register level.
- Generation and output of a square wave signal at the register level in _hardware_.
- Generation and output of a PWM signal at the register level.
- Debugging a program in STM32Cube.

## Procedure

From `main`, create a new git branch named `stm32cube-blink-led-interrupt` and create a STM32Cube project named `blink-led-interrupt`.

> [!NOTE]
> Remember to initialize the peripherals to their default state when creating the project.

### _Blink the LED_ with _timer_ interruptions

#### Timer configuration

Let's configure the microcontroller. First, configure the **`PA5` pin as `GPIO_Output` and label it `LED`**. Next, go to `Timers` in the left side menu and, from the dropdown, click on the **_timer_ `TIM3`**. The configuration form will open. **To enable the _timer_, we only need to choose a clock signal to control it**. In the `Clock Source` field, **choose `Internal Clock`**.

When selecting the clock source, a configuration form will appear below. There we can tweak anything about the _timer_: its **counting mode** (up, down, centered,...), its **period** (the _timer_ counts up to the period and resets), its **frequency prescaler** (maybe the internal clock frequency used is not suitable and we cannot modify it because it affects other peripherals, so we can prescale the clock frequency to obtain a different frequency), etc. There are a thousand different configurations and if you want to see them all, do you know where we have to go? Eeeexactly. To the [documentation](https://www.st.com/content/ccc/resource/technical/document/reference_manual/5d/b1/ef/b2/a1/66/40/80/DM00096844.pdf/files/DM00096844.pdf/jcr:content/translations/en.DM00096844.pdf). (I'll look it up for you, page 316.)

For a _timer_ with a period of 1 second, in the form, we will configure a **prescaler of 8,399** in the `Prescaler` field and a **period of 10,000** in the `Counter Period` field. Why those values? Let's start by going to the **`Clock Configuration` tab** at the top of STM32CubeMX. We will go to a form where the entire **microcontroller clock system** that we can configure is displayed. We will not touch anything, but we will notice that the clock going to the _timers_, the `APB2`, has a frequency of 84 MHz.

![](/.github/images/apb2-clock.png)

If we want the _timer_ to have a period of 1 second, the first thing one would do is set a `Counter Period` of 84,000,000. The calculation comes from:

```math
1\ \textup{s}\frac{84\times10^{6}\ \textup{cycles}}{1\ \textup{s}}=84,000,000\ \textup{ticks}
```

If the _timer_ operates at a frequency of 84 MHz, we need to let the _timer_ count up to 84,000,000 for 1 second to pass. The thing is, if we put 84,000,000 in the `Counter Period` field... It doesn't let us. And that's because we can only put a **maximum 16-bit number** (which is equivalent to a maximum of 65,535). Alternative? Lower the _timer_ frequency. To avoid touching the `APB2` clock, we will use the prescaler. Looking at the [documentation](https://www.st.com/content/ccc/resource/technical/document/reference_manual/5d/b1/ef/b2/a1/66/40/80/DM00096844.pdf/files/DM00096844.pdf/jcr:content/translations/en.DM00096844.pdf) (page 368), we see that the formula for prescaling the frequency is $\frac{f_{CK\_PSC}}{(PSC[15:0] + 1)}$. To make the frequency go from 84 MHz to, for example, **10 kHz**, we will set the prescaler to 8,399. Now yes. Applying the previous calculation, we need a **period of 10,000** to achieve a _timer_ with a period of 1 second.

```math
1\ \textup{s}\frac{10\times10^{3}\ \textup{cycles}}{1\ \textup{s}}=10,000\ \textup{ticks}
```

Configured the period, let's go to the **`NVIC Settings` tab** of the same configuration form and **enable the `TIM3 global interrupt`**.

With this, we have the microcontroller fully configured. Save the configuration file and generate the code.

#### Callback implementation

Let's go to `app.c` and create a **global variable called `ledState`** that we will initialize to `false`. Remember to implement the `setup`/`loop` code organization, and to include `stdbool.h` to use booleans. Then, inside the `loop`function`, we will write:

```c
#include "main.h"
#include <stdbool.h>

bool ledState = false;

void setup(void) {}

void loop(void) { HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, ledState); }
```

Finally, what we will do is, in the _timer_ ISR, toggle the value of the `ledState` variable. We will implement it in the **_pertinent callback_** that we can find in the [HAL documentation](https://www.st.com/content/ccc/resource/technical/document/user_manual/2f/71/ba/b8/75/54/47/cf/DM00105879.pdf/files/DM00105879.pdf/jcr:content/translations/en.DM00105879.pdf).

```diff
#include "main.h"
#include <stdbool.h>

bool ledState = false;

void setup(void) {}

void loop(void) { HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, ledState); }

+ void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
+   ledState = !ledState;
+ }
```

We build and upload the program and... **Nothing blinks.** Let's see what happens using the STM32Cube tools to debug code.

#### Breakpoints

What we are going to do is start debugging the program. As we already know, whenever we start debugging, the IDE pauses the program execution at the first instruction of the `main` function. That is a breakpoint. A **_breakpoint_** is nothing more than a **point in the program configured so that, when the program execution passes through that point, the program execution pauses**. The initial breakpoint always comes by default, but we can configure other breakpoints throughout the code.

For the case at hand, it is usually very useful to place a **_breakpoint in the callback_**. If the interruption is well implemented, by placing a breakpoint there, **when the interruption occurs, the program should pause there**. If it does not pause, it means that the callback is not being executed and something is wrong.

To **add a breakpoint**, we only need to **click to the left of the line number** where we want to add the breakpoint. A small ball will appear next to the line number indicating that a breakpoint has been configured there.

![](/.github/images/breakpoint.png)

Once the breakpoint is configured, we press the icon to start/resume the program execution. We see that the program does not pause at that breakpoint, so the interruption is not being executed.

Another check can be to see if the _timer_ is working. Let's see if the _timer_ counter is counting. We press the icon to manually pause the code execution. Then, we go to the side bar, to the Debug tab, and then to the **STM32Cube Registers Tree** section. This section shows the value of the microcontroller registers.

> [!NOTE]
> It is **essential** to pause the code execution so that the microcontroller can update the values to the IDE.

![](/.github/images/register-tree.png)

If we check the `CNT` register (the counter, as we can see in the [documentation](https://www.st.com/content/ccc/resource/technical/document/reference_manual/5d/b1/ef/b2/a1/66/40/80/DM00096844.pdf/files/DM00096844.pdf/jcr:content/translations/en.DM00096844.pdf) (page 353)) of _timer_ 3 by manually pausing and resuming the program several times, we see that it is always 0. The _timer_ is not working.

> [!NOTE]
> To check if the _timer_ is working, you need to resume and pause the program because **while the program is paused, nothing works. Everything is paused.**

If we look a bit at the [HAL documentation](https://www.st.com/content/ccc/resource/technical/document/user_manual/2f/71/ba/b8/75/54/47/cf/DM00105879.pdf/files/DM00105879.pdf/jcr:content/translations/en.DM00105879.pdf), we see that we need to use the `HAL_TIM_Base_Start_IT` function to start the _timer_ operation with interruptions enabled. We add that function to the `setup`:

```diff
#include "main.h"
#include <stdbool.h>

+ extern TIM_HandleTypeDef htim3;
bool ledState = false;

+ void setup(void) { HAL_TIM_Base_Start_IT(&htim3); }

void loop(void) { HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, ledState); }

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
  ledState = !ledState;
}
```

We need to pass the pointer of the `htim3` variable with the _timer_ configuration to the function. That variable with the configuration is created by STM32Cube for us. However, this variable is created in the `main.c` file and it is outside the scope of the `app.c` file. To allow the contents of the `app.c` to access the `htim3` variable, we have declared the variable as external in the `app.c` file.

We run the code and, **if we haven't removed the previous breakpoint**, the code pauses inside the callback indicating that it is being executed. We can also check how the LED does not blink since the program is paused.

> [!NOTE]
> To disable a breakpoint, we click on it.

If we remove the breakpoint, we can manually pause/resume the code execution to see how the `CNT` register value of _timer_ 3 is now changing.

We already have our LED blinking through interruptions. Create a Pull Request to the main branch. Wait for the test results. If there are any issues, fix them, and once all tests pass, merge the Pull Request.

Let's see how to do it through _hardware_.

### _Blink the LED_ with only _hardware_

As we did with Arduino, we are going to configure the _timer_ so that, through one of its channels, it takes care of blinking the LED by itself.

From `main`, create a git branch named `stm32cube-blink-led-hardware`, and create a project named `blink-led-hardware`.

The _timer_ with a channel on the `PA5` pin is 2. So first, let's **enable _timer_ 2** by going to its configuration form and choosing `Internal Clock` as `Clock Source`. Next, we configure the prescaler and the period. This _timer_ has a **32-bit** counter instead of the 16 bits of _timer_ 3. Therefore, we can leave the **prescaler at 0** and directly use a **period of 84,000,000** in the `Counter Period` field. In this case, **there is no need to enable interruptions since we will do everything with _hardware_**.

What we are going to do is **configure channel 1**. In the `Channel1` field, choose `Output Compare CH1`. Below, in the _timer_ configuration form, a section for configuring channel 1 will have appeared. Set the mode to `Toggle on match` in the `Mode` field. In this mode, the channel output will toggle each time the counter is equal to the value configured in the `Pulse` field.

![](/.github/images/tim2-config.png)

Finally, in the `GPIO Settings` tab, STM32CubeMX, with all its good intentions, has configured the `PA0` pin as the channel 1 output pin since the `PA5` pin is configured as `GPIO_Output`. **We don't want this.** Let's go to the `Pinout view` and select the `PA5` pin function as `TIM2_CH1`. The `PA0` pin will stop outputting channel 1 and the output will be `PA5`.

Save the configuration file and generate the code.

In our `app.c` file, we put:

```c
#include "main.h"

extern TIM_HandleTypeDef htim2;

void setup() { HAL_TIM_OC_Start(&htim2, TIM_CHANNEL_1); }

void loop() {}
```

We use `HAL_TIM_OC_Start` to start the output compare mode of timer 2 for its channel 1. **The function does not come out of nowhere.** Remember that these functions must be looked up in the [HAL documentation](https://www.st.com/content/ccc/resource/technical/document/user_manual/2f/71/ba/b8/75/54/47/cf/DM00105879.pdf/files/DM00105879.pdf/jcr:content/translations/en.DM00105879.pdf).

We build, test the program, and the LED should be blinking perfectly without having any piece of code in the `loop` function that takes care of it 😉

Make a commit, push your changes, and create a Pull Request to the main branch. Wait for the test results. If there are any issues, fix them, and once all tests pass, merge the Pull Request.

### Regulate the LED intensity

In this last section, we are going to regulate the LED intensity with a [PWM](https://en.wikipedia.org/wiki/Pulse-width_modulation). For that, from `main` branch, create a new git branch named `stm32cube-blink-led-heartbeat`, and create a project named `blink-led-heartbeat`.

Let's start by configuring _timer_ 2. Go to the **configuration of _timer_ 2**. In the configuration form, let's start by editing the `Counter Period` field to configure a **period for the _timer_ so that its inverse (the frequency) is 200 Hz**. We achieve this with a `Counter Period` of 420,000.

```math
\frac{1\ \textup{s}}{200\ \textup{ticks}}\frac{84\times10^{6}\ \textup{ticks}}{1\ \textup{s}}=420,000
```

Next, change the mode of channel 1 and **choose `PWM Generation CH1`**. In the PWM configuration, at the bottom, indicate **10,000 in the `Pulse` field**. When the _timer_ counter is **below 10,000, the LED output will be high**; and when the _timer_ value is **greater than 10,000, the LED output will be low**. This is the way to set the _duty cycle_. With a period of 420,000 and a `Pulse` of 10,000, we have a **_duty cycle_ of 2.4 %**. Remember to choose PA5 as the output of channel 1. Save the configuration and generate the code.

In our `app.c` file, we are going to use the function `HAL_TIM_PWM_Start` to start the generation of the PWM signal at pin PA5.

```c
#include "main.h"

extern TIM_HandleTypeDef htim2;

void setup(void) { HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1); }

void loop(void) {}
```

Build and debug the program, and see how **the LED shines with a slight intensity**. We can edit the microcontroller configuration to change the `Pulse` field value to see how the LED intensity varies (I recommend doing it), but let's do it with a sine wave as in the Arduino case.

As in Arduino, let's go to `app.c` and include the standard `math.h` library. **Create the constants** `pi`, `amplitude`, and `period`, and the variable `duty`. Since the value of **`Pulse` is an absolute integer and not a percentage**, **create the constant** `TIM2Period` to store the _timer_ period, and the **variable** `varPulse` to calculate the `Pulse` value based on the calculated _duty_. Since they should not be accessible in any function beyond `loop`, **there is no need to declare them as global constants/variables**. **Calculate the _duty_ with the `sin` function**, calculate the **value for `Pulse` based on the calculated _duty_**, and **use the `__HAL_TIM_SET_COMPARE` macro** from the HAL to modify the `Pulse` value of _timer_ 2.

```c
#include "main.h"
#include <math.h>

extern TIM_HandleTypeDef htim2;

void setup(void) { HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1); }

void loop(void) {
  const float pi = 3.14159265359,     // constant pi
      amplitude = 25.0 / 2.0,         // oscillation amplitude
      period = 2.0;                   // oscillation period
  const uint32_t TIM2Period = 420000; // TIM2 period
  float duty =
      amplitude * sin(2.0 * pi / period * HAL_GetTick() / 1000.0) + amplitude;
  uint32_t varPulse = TIM2Period * duty / 100.0;
  __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, varPulse);
}
```

Save, compile, build, and load the program, and we have our LED blinking **with style!** 😎

Make a commit, push your changes, and create a Pull Request to the main branch. Wait for the test results. If there are any issues, fix them, and once all tests pass, merge the Pull Request.

## Challenge

The challenge will be to toggle the LED state between off and on with the `B1` button using button and _timer_ interruptions. **There should be no code in the `loop` function.**

Come on, let's go. I probably won't make you do this challenge anymore 😅

Implement the challenge in a branch called `stm32cube-challenge` and name the project `challenge`.

## Evaluation

### Deliverables

These are the elements that should be available to the teacher for your evaluation:

- [ ] **Commits**
      Your remote GitHub repository must contain at least the following required commits: LED blinking using interrupts, LED blinking using hardware, and LED heartbeat blinking.

- [ ] **Challenge**
      The challenge must be solved and included with its own commit.

- [ ] **Pull Requests**
      The different Pull Requests requested throughout the practice must also be present in your repository.

## Conclusions

With the completion of this practice, we can say that **we know how to control at the register level** those **most important actions performed by a _timer_**. These actions range from **periodic task execution through interruptions**, to the **generation of periodic square waves without CPU involvement**, to the modulation of a pulse train to **generate a PWM**.

We have also seen **how to use breakpoints** and **how to view the microcontroller registers** within the range of professional debugging tools offered by STM32CubeIDE compared to Arduino.

In the next practice, we will see the **ADC** to be able to read/convert **analog signals** with our microcontroller.
