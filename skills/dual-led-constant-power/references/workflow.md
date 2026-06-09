# Dual LED Constant-Power Reference

The final smooth controller uses a calibration/inverse-LUT method, not RL and not raw feedback chasing.

Core firmware:

```text
firmware/dual_led_constant_power_lut/dual_led_constant_power_lut.ino
```

Capture script:

```text
scripts/capture_dual_led_power_plot.py
```

Working monitor mapping:

```text
logical LED A = PWM D9  = INA219 0x41
logical LED B = PWM D10 = INA219 0x40
```

Correct I2C power wiring:

```text
Monitor HAT pin 1 / 3V3 -> Arduino 3.3V
Monitor HAT pin 3 / SDA -> Arduino A4 / SDA
Monitor HAT pin 5 / SCL -> Arduino A5 / SCL
Monitor HAT pin 6 / GND -> Arduino GND
```

Expected I2C scanner output:

```text
found 0x40
found 0x41
found 0x42
found 0x43
```

Runtime method:

```text
1. Calibrate LED A alone.
2. Calibrate LED B alone.
3. Enforce monotonic power curves.
4. Set total target to 65% of weaker branch max.
5. Use sinusoidal crossfade w(t).
6. Convert desired branch powers through inverse LUTs.
7. Slew-limit PWM updates.
```

Retained result:

```text
measurements/dual_led_constant_power_20260609_105229.csv
measurements/dual_led_constant_power_20260609_105229.png
target total power = 33.2475 mW
mean total power   = 31.117 mW
std total power    = 2.329 mW
CV                 = 7.49%
```

If output flickers:

```text
Use LUT firmware, not feedback firmware.
Lower TARGET_FRACTION_OF_WEAKER_LED.
Keep MAX_DUTY_STEP small.
Avoid changing PWM duty directly from noisy instantaneous power readings.
Consider analog constant-current LED drivers if event camera sees PWM carrier.
```
