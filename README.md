![publish](https://github.com/l-johnston/nirfsg/workflows/publish/badge.svg)
![PyPI](https://img.shields.io/pypi/v/nirfsg?style=plastic)
# `nirfsg`
Python control of NI RF Signal Generators using NI-RFSG

## Installation

    > pip install nirfsg

Or, after cloning repo:

    > pip install .

## Documentation
Currently supported models:
- PXIe-5654


```
> from nirfsg import PXIe_5654
> sig_gen = PXIe_5654(<resource>)
> sig_gen.rf_frequency = 2e6 # Hz
> sig_gen.rf_power = 0 # dBm
> sig_gen.initiate()
...
> sig_gen.close()
```

As a context manager:

```
> with PXIe_5654(<resource>) as sig_gen:
    sig_gen.rf_frequency = 20e9 # Hz
    sig_gen.rf_power = 13 # dBm
    sig_gen.initiate()
    # do some measurements
```

Context manager will close the session at exit, which will stop generation.

To discover available methods and attributes use tab-completion, dir() and help():

```
In [1]: from nirfsg import PXIe_5654

In [2]: sg = PXIe_5654("PXI1Slot7")

In [3]: dir(sg)
Out[3]:
['abort',
 'amplitude_settling',
 'automatic_thermal_correction',
 'check_status',
 'clock',
 'close',
 'configurationlist',
 'configure_rf',
 'device_temperature',
 'events',
 'external_cal',
 'fast_tuning',
 'frequency_settling',
 'frequency_settling_units',
 'generation_mode',
 'initiate',
 'instrument_model',
 'modulation',
 'module_revision',
 'output_enabled',
 'pulse_modulation_enabled',
 'pulse_modulation_mode',
 'rf_frequency',
 'rf_power',
 'serial_number',
 'triggers',
 'wait_until_settled']

In [4]: dir(sg.clock)
Out[4]: ['reference_clock_output_terminal', 'reference_clock_source']

In [5]: sg.clock.reference_clock_source
Out[5]: <reference_clock_source.onboard clock: 'OnboardClock'>

In [6]: help(type(sg.clock.reference_clock_source))
Help on class reference_clock_source in module nirfsg.attributemonger:

class reference_clock_source(enum.Enum)
 |  reference_clock_source(value, names=None, *, module=None, qualname=None, type=None, start=1)
 |
 |  An enumeration.
 |
 |  Method resolution order:
 |      reference_clock_source
 |      enum.Enum
 |      builtins.object
 |
 |  Data and other attributes defined here:
 |
 |  none = <reference_clock_source.none: 'None'>
 |
 |  onboard clock = <reference_clock_source.onboard clock: 'OnboardClock'>
 |
 |  pxi clk = <reference_clock_source.pxi clk: 'PXI_CLK'>
 |
 |  pxi clk master = <reference_clock_source.pxi clk master: 'PXI_ClkMaste...
 |
 |  ref in = <reference_clock_source.ref in: 'RefIn'>
 |
 |  ref in 2 = <reference_clock_source.ref in 2: 'RefIn2'>
 ```
 