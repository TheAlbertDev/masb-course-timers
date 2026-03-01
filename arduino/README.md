# _Timers_

<img align="left" src="https://img.shields.io/badge/Lab_session-3--A-yellow"><img align="left" src="https://img.shields.io/badge/Environment-Arduino-blue"><img align="left" src="https://img.shields.io/badge/Estimated_duration-2 h-green"></br>

Tick, tock, tick, tock... The _timer_ has arrived! It's time to explore another essential peripheral: the _timer_ (or counter). As the name suggests, its main purpose is **to measure and work with time**.

**A _timer_ is simply a register that acts as a counter.** This counter increases its value with each clock cycle or with each transition of an input signal. The latter is often used for reading _encoders_. In this practice, we'll focus on the first case, where the counter increments with each clock cycle.

What will we learn with _timers_? We'll cover two of their main uses: executing tasks based on time and generating a [PWM](https://en.wikipedia.org/wiki/Pulse-width_modulation) signal.

## Objectives

- Introduction to pointers in C/C++.
- Generating an interrupt based on a _timer_ in Arduino.
- Generating and outputting a square wave signal in Arduino using _hardware_.
- Generating and outputting a PWM signal in Arduino.

## Procedure

As always: clone the repository and create a branch named `arduino-blink-led-interrupt`.

### _Blink the LED_ with _timers_

"~~F\*\*k~~ _Gosh_, Albert. Again with the _blink the LED_?" Yes, once more! But this time, we'll do it **using timer interrupts**. For now, the LED is our only visual indicator to demonstrate our microcontroller programming skills. Don't underestimate the humble LED!

We'll create a project named `blink-led-interrupt` as usual. The first step is to configure one of the microcontroller's _timers_.

The microcontroller has up to [11 _timers_](https://www.st.com/resource/en/datasheet/stm32f401re.pdf). Arduino uses some of these _timers_ to implement the `millis` or `delay` functions we've seen in other exercises. If we use one of those _timers_, those functions may stop working correctly. That's actually good—it means we won't use them! 😜

#### Pointers in C/C++

Before configuring a _timer_, we need to understand pointers in C/C++, since we'll need them.

**A pointer is something that points.** There you go. Now you know what pointers are.

It may sound absurdly simple (and it is), but although pointers can be confusing at first, they do exactly what their name suggests: they point.

A pointer is simply a variable that stores the memory address of another variable. Let's see this quickly with an example in a made-up programming file.

```c++
uint8_t numericVariable = 0;
```

Imagine we have a numeric variable of type `uint8_t` called `numericVariable`, initialized to 0. Nothing strange so far. In the microcontroller, this variable will be stored in memory—specifically, at a certain address.

If we made a table of the microcontroller's memory, it would look like this:

|     Address     |  Value   |
| :-------------: | :------: |
|       ...       |   ...    |
|   0x003A 58E0   |   0x3A   |
| **0x003A 58E1** | **0x00** |
|   0x003A 58E2   |   0x21   |
|       ...       |   ...    |

The value of our variable would be stored in memory at address `0x003A 58E1`.

> [!NOTE]
> The notation `0x` indicates that the value is written in [hexadecimal](https://en.wikipedia.org/wiki/Hexadecimal). The address shown is completely invented for this example.

Now, let's create a pointer:

```c++
uint8_t *pointerToNumericValue;
uint8_t numericVariable = 0;

pointerToNumericValue = &numericVariable;
```

Let's break down what we've done. In the first line, we've created a pointer. **The type indicated in the pointer declaration doesn't specify the type of the pointer itself, but the type of variable the pointer points to.** A pointer always has the size of the microcontroller's address bus. In this case, the STM32 microcontroller is 32 bits, so all pointers are 32 bits. To be clear, the type in the pointer declaration refers to the variable it points to. **Pointers are declared with an asterisk before the name.**

In the second line, we declare and initialize an 8-bit unsigned variable called `numericVariable` to 0. Nothing new here.

In the third line, **we use the `&` character before the variable** `numericVariable`. This way, **we extract** not the value of `numericVariable`, but **its pointer or memory address**. This memory address is stored in the pointer we've created. Notice that outside of declarations, the asterisk is not used for pointers. It's only necessary in the declaration. Outside of declarations, the asterisk has another purpose, which we'll see later.

Let's be honest: 1) pointers are confusing the first time you see or use them, and 2) pointers are easy once you understand what they are and do. ([+info](https://www.tutorialspoint.com/cprogramming/c_pointers.htm))

#### Let's initialize the _timer_

Let's move to our `main.cpp` file. Enter the following code:

```c++
#include <Arduino.h>

void setup()
{
  // put your setup code here, to run once:

  // create a pointer to the configuration of timer 3 in memory
  HardwareTimer *MyTim = new HardwareTimer(TIM3);

  MyTim->setMode(2, TIMER_OUTPUT_COMPARE);      // configure the timer mode
  MyTim->setOverflow(1000000, MICROSEC_FORMAT); // configure the timer period to 1 second
  MyTim->attachInterrupt(changeLEDState);       // indicate the name of the ISR to execute
  MyTim->resume();                              // start the timer
}

void loop()
{
  // put your main code here, to run repeatedly:
}
```

The code isn't complete yet, so it won't compile correctly.

What we've done is first create a pointer to the memory location where the configuration of _timer_ 3 is stored. We chose 3, but you could choose any of the other 10.

The pointer `MyTim` points to a variable of type `HardwareTimer`, which is a structure. **A [structure](https://www.tutorialspoint.com/cprogramming/c_structures.htm) is simply a variable that groups variables of different types.** In this case, it groups functions.

> [!NOTE]
> In fact, the name of a function is nothing more than a pointer to the memory location where the code for that function is stored.
>
> ![Mind explosion](/.github/images/mind-explosion.webp)

To access different elements in a structure using its pointer, we use the `->` operator. To configure the _timer_, we simply follow [the Arduino library instructions](https://github.com/stm32duino/Arduino_Core_STM32/wiki/HardwareTimer-library):

- Configure the timer mode.
- Set the timer period. Once the timer counts up to the specified period, the counter resets and starts again.
- Specify the name of the ISR to execute when the counter reaches the configured period.
- Start the timer to begin counting.

#### Let's make the LED blink

We'll use the approach from previous exercises: use a boolean variable to control the LED and toggle its value in the interrupt. The code would look like this:

```c++
#include <Arduino.h>

#define LED 13

bool ledState = false;

void setup()
{
  // put your setup code here, to run once:

  // create a pointer to the configuration of timer 3 in memory
  HardwareTimer *MyTim = new HardwareTimer(TIM3);

  MyTim->setMode(2, TIMER_OUTPUT_COMPARE);      // configure the timer mode without output to any pin
  MyTim->setOverflow(1000000, MICROSEC_FORMAT); // configure the timer period to 1 second
  MyTim->attachInterrupt(changeLEDState);       // indicate the name of the ISR to execute
  MyTim->resume();                              // start the timer

  pinMode(LED, OUTPUT);        // LED pin as output
  digitalWrite(LED, ledState); // off by default
}

void loop()
{
  // put your main code here, to run repeatedly:

  digitalWrite(LED, ledState);
}

// ISR of the timer
void changeLEDState(void)
{
  ledState = !ledState; // toggle the LED
}
```

Build the project.

Still not working? Check the error message. It says that the function `changeLEDState` is not declared. We've seen this before. The function prototype is simply missing before it's used in the `setup` function. Let's add it.

```diff
#include <Arduino.h>

#define LED 13

bool ledState = false;

+void changeLEDState(void);
+
void setup()
{
  // put your setup code here, to run once:

  // create a pointer to the configuration of timer 3 in memory
  HardwareTimer *MyTim = new HardwareTimer(TIM3);

  MyTim->setMode(2, TIMER_OUTPUT_COMPARE);      // configure the timer mode without output to any pin
  MyTim->setOverflow(1000000, MICROSEC_FORMAT); // configure the timer period to 1 second
  MyTim->attachInterrupt(changeLEDState);       // indicate the name of the ISR to execute
  MyTim->resume();                              // start the timer

  pinMode(LED, OUTPUT);        // LED pin as output
  digitalWrite(LED, ledState); // off by default
}

void loop()
{
  // put your main code here, to run repeatedly:

  digitalWrite(LED, ledState);
}

// ISR of the timer
void changeLEDState(void)
{
  ledState = !ledState; // toggle the LED
}
```

Now it works! With this, the LED blinks using timer interrupts. Unlike the previous exercise (where we used the `millis` function), this approach offers much more accurate timing. Using `millis` to toggle the LED could cause a delay if the code execution is held up before checking `millis`. Here, that's not the case. Every exact second, the interrupt occurs and the LED toggles.

You should now have the program running with the LED blinking every 1 second. Make a commit, push your changes, and create a Pull Request to the main branch. Wait for the test results. If there are any issues, fix them, and once all tests pass, merge the Pull Request.

Let's move on to the next use of the _timer_, where we won't even use the `digitalWrite` function to toggle the LED. We'll do it purely by _hardware_, without _software_.

### _Blink the LED like a Greek God_

Now we'll make the LED blink in a very special way: without using _software_. **The LED toggle will be handled entirely by the _timer_ peripheral, and the CPU won't execute any code for it.** This leaves the CPU completely free for other tasks.

How do we do this? A _timer_, in addition to the counter itself, has **channels**. These channels, which **can be redirected to a microcontroller pin** for output, can be configured to perform certain actions based on the _timer_.

For example, we can configure a comparison value and a period for the _timer_. The _timer_ increments its value until it reaches the period, then resets. One of the _timer_ channels can be set to be low when the counter is below the comparison value and high when above. This way, we generate a periodic rectangular signal whose low and high times are configurable with the _timer_ comparison value—a PWM.

Another option is the one we'll use next: not configuring a comparison value, just a period. We set the **timer mode to `toggle`** so that **a channel**, which can be redirected to a pin, **toggles every time the _timer_ reaches the configured period**.

Create a new branch from `main` called `arduino-blink-led-hardware` and create a new project named `blink-led-hardware`.

Let's see it in code.

```c++
#include <Arduino.h>

#define LED 13

void setup()
{
  // put your setup code here, to run once:

  // create a pointer to the configuration of timer 2 in memory
  HardwareTimer *MyTim = new HardwareTimer(TIM2);

  MyTim->setMode(1, TIMER_OUTPUT_COMPARE_TOGGLE, LED); // toggle mode of channel 1 of timer 2
  MyTim->setOverflow(1000000, MICROSEC_FORMAT);        // configure the timer period to 1 second
  MyTim->resume();                                     // start the timer
}

void loop()
{
  // put your main code here, to run repeatedly:
}
```

First, we've created a pointer to _timer_ 2. In this case, **the choice of _timer_ is crucial**. If we check the [microcontroller's datasheet](https://www.st.com/resource/en/datasheet/stm32f401re.pdf) (page 40, Table 8), the `PA5` pin of the LED has an alternate function `TIM2_CH1`, among others. This means this pin can output channel 1 of _timer_ 2. So, we must use _timer_ 2 to operate with the LED.

Next, we set the mode. Of all the modes the [Arduino library](https://github.com/stm32duino/Arduino_Core_STM32/wiki/HardwareTimer-library) allows, we choose `TIMER_OUTPUT_COMPARE_TOGGLE`, which makes our LED change state when the _timer_ completes a count up to the period. In that instruction, we also specify the channel and the pin for output.

> [!NOTE]
> Some microcontrollers/peripherals offer more than one pin for the same channel to provide flexibility.

Then, we set the _timer_ period to 1 second and start the _timer_.

Build and load the program, and you'll have your LED blinking every 1 second. Notice something: how much code is in the `loop` function? None! The CPU is currently doing absolutely nothing, and the _timer_ handles the LED toggle.

Looks like it's working! Make a commit, push your changes, and create a Pull Request to the main branch. Wait for the test results. If there are any issues, fix them, and once all tests pass, merge the Pull Request.

Let's move on to the next section, where we'll see how to vary the LED intensity with PWM.

### Regulate the LED intensity

We can control the intensity of an LED using a PWM signal. A [PWM signal](https://en.wikipedia.org/wiki/Pulse-width_modulation) is simply a periodic rectangular signal whose ratio between the time the signal is high and the period, called _duty cycle_, is configurable. **The LED will shine brighter with a PWM with a high _duty cycle_ and dimmer with a low _duty cycle_.**

Let's set a fixed intensity for the LED using PWM. Create a branch called `arduino-blink-led-intensity` from the `main` branch, and create a project named `blink-led-intensity`.

Since we'll configure a _timer_ channel for this, we'll use the _timer_ that connects to the LED pin: _timer_ 2.

```c++
#define LED     13

void setup() {
  // put your setup code here, to run once:

  // create a pointer to the configuration of timer 2 in memory
  HardwareTimer *MyTim = new HardwareTimer(TIM2);

  // pwm at 10% at 200Hz
  MyTim->setPWM(1, 13, 200, 10);
}

void loop() {
  // put your main code here, to run repeatedly:

}
```

We've created our pointer to the _timer_ configuration. Nothing new. Then we use a function Arduino provides to automatically configure a PWM: `setPWM`. According to the [library documentation](https://github.com/stm32duino/Arduino_Core_STM32/wiki/HardwareTimer-library), this function needs the following parameters: channel, pin, PWM frequency in hertz, and _duty cycle_ in percentage.

Try the program several times, modifying the _duty cycle_, and you'll see how the LED intensity changes. The variations are most noticeable for _duty cycle_ values between 0 and 25%.

If it works as expected, leave a final _duty cycle_ value of 10%, make a commit, push your changes, and create a Pull Request to the main branch. Wait for the test results. If there are any issues, fix them, and once all tests pass, merge the Pull Request.

#### Heartbeats in the LED

It's a bit... "boring" to change the _duty cycle_ manually just to see it works. Let's vary the _duty cycle_ in code, using a sinusoidal variation. This also lets us demonstrate including a math library.

To generate [a sinusoidal signal](https://en.wikipedia.org/wiki/Sine_wave), we need an amplitude, an oscillation frequency, and time. The signal should also have an _offset_ to generate only positive values. We'll eliminate the phase shift. The formula is:

```math
y(t)=A\sin (2\pi ft)+A
```

The amplitude should range from 0 to 25 for noticeable intensity changes. The frequency can be set between 200 Hz and 1 kHz. We're missing time... Any ideas? Exactly! We'll use the `millis` function! 😉

The `sin` function to compute the sine is part of the `math.h` library. We'll include it with `#include <math.h>`.

Create a new branch from `main` called `arduino-blink-led-heartbeat` and create a project named `blink-led-heartbeat`.

The code would look like this:

```c++
#include <Arduino.h>

#include <math.h>

#define LED 13

// constants that define our sinusoidal signal
const double pi = 3.14, // constant pi
    amplitude = 25 / 2, // amplitude of oscillation
    period = 2;         // period of oscillation

double duty = 0;

// create a pointer to the configuration of timer 2 in memory
// declare it globally so that it is available in the loop function
HardwareTimer *MyTim = new HardwareTimer(TIM2);

void setup()
{
  // put your setup code here, to run once:
}

void loop()
{
  // put your main code here, to run repeatedly:

  // calculate the pwm duty from a sinusoidal signal
  duty = amplitude * sin(2 * pi / period * millis() / 1000) + amplitude;

  // apply the duty to the pwm
  MyTim->setPWM(1, LED, 200, duty);
}
```

Try it and you'll have your LED blinking smoothly. Oh my, the crazy things we'll be able to do next year with the Christmas lights on our tree! 🎄

We have a code that works perfectly! Make a commit, push your changes, and create a Pull Request to the main branch. Wait for the test results. If there are any issues, fix them, and once all tests pass, merge the Pull Request.

## Challenge

Let's repeat the previous exercise: toggle the LED mode from off to blinking and vice versa with the button. This time, all through interrupts. **There must be no code in the `loop` function**.

As you can see, the same challenge can be approached in different ways. From this, we can deduce that there is no single or "correct" way to perform the same task. There are ways that are more or less optimal depending on the scenario, and as engineers, we must choose the most optimal option.

Implement the challenge in a branch called `arduino-challenge` and name the project `challenge`.

## Evaluation

### Deliverables

These are the elements that should be available to the teacher for your evaluation:

- [ ] **Commits**
      Your remote GitHub repository must contain at least the following required commits: LED blinking using interrupts, LED blinking using hardware, LED blinking with variable intensity, and LED heartbeat blinking.
- [ ] **Challenge**
      The challenge must be solved and included with its own commit.

- [ ] **Pull Requests**
      The different Pull Requests requested throughout the practice must also be present in your repository.

## Conclusions

In this practice, we've introduced a new peripheral: the _timer_. This peripheral is useful for all actions related to time measurement.

We've seen how to implement an interrupt that triggers every time the _timer_ counts up to a given value. We've also seen that _timers_ have channels we can use to generate periodic rectangular signals. These channels allow us to toggle output pins without CPU involvement. They also let us generate very useful PWM signals (controlling LED intensity, motors, DC/DC converters, and more).

We've also explored pointers, structures, and including libraries in C/C++.

In the next practice, we'll implement _timers_ at the register level with the HAL.
