# `nirfsg`
Python control of NI RF Signal Generators using NI-RFSG

## Installation
After cloning repo:

    > pip install .

## Documentation
Currently supported models:
- PXIe-5654 (partial)


```
> from nirfsg import PXIe_5654
> sig_gen = PXIe_5654("PXI1Slot11")
> sig_gen.rf_frequency = 2e6 # Hz
> sig_gen.rf_power = 0 # dBm
> sig_gen.initiate()
```
